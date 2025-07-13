from langchain.memory import ConversationSummaryBufferMemory
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.schema import HumanMessage, AIMessage
import chromadb
from typing import List, Dict
import uuid
from datetime import datetime

class SmartConversationMemory:
    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key
        self.llm = ChatOpenAI(openai_api_key=openai_api_key, model="gpt-3.5-turbo")
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        
        # Initialize vector database for long-term memory
        self.chroma_client = chromadb.PersistentClient(path="./memory_db")
        
        # Store user memories and recent conversations
        self.user_memories = {}  # {user_id: Chroma collection}
        self.recent_conversations = {}  # {user_id: [recent messages]}
    
    def _get_user_memory_collection(self, user_id: str):
        """Get or create vector collection for user"""
        if user_id not in self.user_memories:
            collection_name = f"user_{user_id}_memory"
            try:
                collection = self.chroma_client.get_collection(collection_name)
            except:
                collection = self.chroma_client.create_collection(collection_name)
            self.user_memories[user_id] = collection
        return self.user_memories[user_id]
    
    def add_conversation_turn(self, user_id: str, user_message: str, ai_response: str):
        """Add new conversation turn to both recent and long-term memory"""
        timestamp = datetime.now().isoformat()
        
        # Add to recent conversation buffer
        if user_id not in self.recent_conversations:
            self.recent_conversations[user_id] = []
        
        self.recent_conversations[user_id].extend([
            {"role": "user", "content": user_message, "timestamp": timestamp},
            {"role": "assistant", "content": ai_response, "timestamp": timestamp}
        ])
        
        # Keep only last 10 recent messages
        self.recent_conversations[user_id] = self.recent_conversations[user_id][-10:]
        
        # Add to long-term vector memory (for semantic search)
        collection = self._get_user_memory_collection(user_id)
        
        # Create searchable text combining user message and AI response
        conversation_text = f"User: {user_message}\nAI: {ai_response}"
        
        # Store in vector database
        doc_id = str(uuid.uuid4())
        collection.add(
            documents=[conversation_text],
            metadatas=[{
                "user_message": user_message,
                "ai_response": ai_response,
                "timestamp": timestamp,
                "user_id": user_id
            }],
            ids=[doc_id]
        )
    
    def get_relevant_context(self, user_id: str, current_message: str, max_recent: int = 5, max_retrieved: int = 3):
        """Get relevant context: recent messages + semantically similar past conversations"""
        context_messages = []
        
        # 1. Get recent conversation (short-term memory)
        recent = self.recent_conversations.get(user_id, [])
        recent_messages = recent[-max_recent*2:] if recent else []  # *2 because each turn has user+ai
        
        # 2. Get semantically relevant past conversations (long-term memory)
        try:
            collection = self._get_user_memory_collection(user_id)
            if collection.count() > 0:
                results = collection.query(
                    query_texts=[current_message],
                    n_results=max_retrieved
                )
                
                # Add relevant past conversations
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i]
                    # Only add if not already in recent memory
                    if not any(msg['content'] == metadata['user_message'] for msg in recent_messages):
                        context_messages.extend([
                            {"role": "user", "content": metadata['user_message']},
                            {"role": "assistant", "content": metadata['ai_response']}
                        ])
        except Exception as e:
            print(f"Error retrieving relevant context: {e}")
        
        # 3. Combine and deduplicate
        all_context = context_messages + recent_messages
        
        return all_context
    
    def get_conversation_summary(self, user_id: str) -> str:
        """Get a summary of the conversation for the system prompt"""
        recent = self.recent_conversations.get(user_id, [])
        if not recent:
            return "This is the start of a new conversation."
        
        # Create a simple summary of recent topics
        user_messages = [msg['content'] for msg in recent if msg['role'] == 'user']
        if user_messages:
            return f"Recent conversation topics: {', '.join(user_messages[-3:])}"
        return "Continuing previous conversation."

# Global memory instance
smart_memory = None

def get_memory_instance(openai_api_key: str):
    global smart_memory
    if smart_memory is None:
        smart_memory = SmartConversationMemory(openai_api_key)
    return smart_memory