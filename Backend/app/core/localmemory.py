from langchain.memory import ConversationSummaryBufferMemory
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.schema import HumanMessage, AIMessage
import uuid
from datetime import datetime

class SmartConversationMemory:
    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key
        self.llm = ChatOpenAI(openai_api_key=openai_api_key, model="gpt-3.5-turbo")
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        self.vector_stores = {}
        self.user_memories = {}

    def _get_user_vector_store(self, user_id: str):
        if user_id not in self.vector_stores:
            self.vector_stores[user_id] = Chroma(
                persist_directory=f"./memory_db/{user_id}",
                embedding_function=self.embeddings,
                collection_name=f"memory_{user_id}"
            )
        return self.vector_stores[user_id]
    
    def get_conversation_memory(self, user_id: str) -> ConversationSummaryBufferMemory:
        if user_id not in self.user_memories:
            self.user_memories[user_id] = ConversationSummaryBufferMemory(
                llm=self.llm,
                max_token_limit=1000,  # Auto-summarize when too long
                return_messages=True,
                memory_key="chat_history"
            )
        return self.user_memories[user_id]

    def add_conversation_turn(self, user_id: str, user_message: str, ai_response: str):
        """Add new conversation turn to both recent and long-term memory"""
        timestamp = datetime.now().isoformat()
        
        # Add to recent conversation buffer
        memory = self.get_conversation_memory(user_id)
        memory.save_context({"input": user_message}, {"output": ai_response})

        # Create searchable text combining user message and AI response
        conversation_text = f"User: {user_message}\nAI: {ai_response}"
        metadata = {
        "user_message": user_message,
        "ai_response": ai_response,
        "timestamp": timestamp,
        "user_id": user_id
        }
        
        vector_store = self._get_user_vector_store(user_id)
        # Store in vector database
        doc_id = str(uuid.uuid4())
        vector_store.add_texts(
            texts=[conversation_text],
            metadatas=[metadata],
            ids=[doc_id]
            )

    
    def get_relevant_context(self, user_id: str, current_message: str, max_recent: int = 5, max_retrieved: int = 3):
        context_messages = []
    
        # Get recent messages and convert to consistent format
        memory = self.get_conversation_memory(user_id)
        recent_langchain_messages = memory.chat_memory.messages
    
        # Convert LangChain messages to OpenAI format
        recent_messages = []
        for msg in recent_langchain_messages[-max_recent*2:]:  # *2 because each turn has user+ai
            if isinstance(msg, HumanMessage):
                recent_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                recent_messages.append({"role": "assistant", "content": msg.content})
    
        # Get relevant past conversations
        try:
            vector_store = self._get_user_vector_store(user_id)
            docs = vector_store.similarity_search(current_message, k=max_retrieved)
        
            # Extract unique conversations not in recent messages
            recent_user_messages = {msg["content"] for msg in recent_messages if msg["role"] == "user"}
        
            for doc in docs:
                metadata = doc.metadata
                if metadata['user_message'] not in recent_user_messages:
                    context_messages.extend([
                        {"role": "user", "content": metadata['user_message']},
                        {"role": "assistant", "content": metadata['ai_response']}
                    ])
        except Exception as e:
            print(f"Error retrieving relevant context: {e}")
    
        # Combine: relevant past conversations + recent conversations
        return context_messages + recent_messages

# Global memory instance
smart_memory = None

def get_memory_instance(openai_api_key: str):
    global smart_memory
    if smart_memory is None:
        smart_memory = SmartConversationMemory(openai_api_key)
    return smart_memory