from langchain.memory import ConversationSummaryBufferMemory
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.schema import HumanMessage, AIMessage
from pinecone import Pinecone
from typing import List, Dict, Any
import logging
from .Pinecone_Utils import PineconeVectorStore, ConversationFormatter  

class SmartConversationMemory:
    def __init__(self, openai_api_key: str, pinecone_api_key: str, cloud: str = "aws", region: str = "us-east-1"):
        self.pinecone_api_key = Pinecone(api_key=pinecone_api_key)
        self.llm = ChatOpenAI(openai_api_key=openai_api_key, model="gpt-3.5-turbo")
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        
        # Initialize Pinecone vector store
        self.vector_store = PineconeVectorStore(
            api_key=pinecone_api_key,
            cloud=cloud,
            region=region
        )
        
        # Keep in-memory conversation buffers for recent context
        self.user_memories = {}

    def get_conversation_memory(self, user_id: str) -> ConversationSummaryBufferMemory:
        """Get or create conversation buffer for user"""
        if user_id not in self.user_memories:
            self.user_memories[user_id] = ConversationSummaryBufferMemory(
                llm=self.llm,
                max_token_limit=1000,
                return_messages=True,
                memory_key="chat_history"
            )
        return self.user_memories[user_id]

    def add_conversation_turn(self, user_id: str, user_message: str, ai_response: str):
        """Add conversation to both buffer memory and vector store"""
        # Add to recent conversation buffer
        memory = self.get_conversation_memory(user_id)
        memory.save_context({"input": user_message}, {"output": ai_response})
        
        # Store in vector database
        try:
            conversation_text = ConversationFormatter.format_conversation(user_message, ai_response)

            embedding = self.embeddings.embed_query(conversation_text)
            
            metadata = ConversationFormatter.create_metadata(
                user_id=user_id,
                user_message=user_message,
                ai_response=ai_response
            )

            doc_id = self.vector_store.store_conversation(
                user_id=user_id,
                conversation_text=conversation_text,
                embedding=embedding,
                metadata=metadata
            )
            
            logging.info(f"Successfully added conversation turn for user {user_id}, doc_id: {doc_id}")
            
        except Exception as e:
            logging.error(f"Error storing conversation in vector store: {e}")
            # Continue execution - buffer memory still works

    def get_relevant_context(self, user_id: str, current_message: str, max_recent: int = 5, max_retrieved: int = 3) -> List[Dict[str, str]]:
        """Get context from both recent buffer and relevant past conversations"""
        context_messages = []
        
        # Get recent messages from buffer
        memory = self.get_conversation_memory(user_id)
        recent_langchain_messages = memory.chat_memory.messages
        
        recent_messages = []
        for msg in recent_langchain_messages[-max_recent*2:]:  # *2 because each turn has user+ai
            if isinstance(msg, HumanMessage):
                recent_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                recent_messages.append({"role": "assistant", "content": msg.content})

        # Get relevant past conversations from vector store
        try:
            query_embedding = self.embeddings.embed_query(current_message)
            similar_conversations = self.vector_store.similarity_search(
                user_id=user_id,
                query_embedding=query_embedding,
                top_k=max_retrieved
            )

            # Process results and avoid duplicates
            recent_user_messages = {msg["content"] for msg in recent_messages if msg["role"] == "user"}

            for conversation in similar_conversations:
                metadata = conversation.get('metadata', {})
                user_msg = metadata.get('user_message')
                ai_msg = metadata.get('ai_response')
                
                # Only add if not already in recent messages and both messages exist
                if user_msg and ai_msg and user_msg not in recent_user_messages:
                    context_messages.extend([
                        {"role": "user", "content": user_msg},
                        {"role": "assistant", "content": ai_msg}
                    ])
            
        except Exception as e:
            logging.error(f"Error retrieving relevant context: {e}")
        
        # Return relevant past conversations + recent conversations
        return context_messages + recent_messages

    def delete_user_conversations(self, user_id: str) -> bool:
        """Delete all stored conversations for a user (GDPR compliance)"""
        try:
            # Clear buffer memory
            if user_id in self.user_memories:
                del self.user_memories[user_id]
                logging.info(f"Cleared buffer memory for user {user_id}")
            
            # Delete from vector store
            success = self.vector_store.delete_user_data(user_id)
            
            if success:
                logging.info(f"Successfully deleted all conversations for user {user_id}")
            else:
                logging.warning(f"Failed to delete vector store data for user {user_id}")
                
            return success
            
        except Exception as e:
            logging.error(f"Error deleting user conversations: {e}")
            return False

# Global memory instance
smart_memory = None

def get_memory_instance(openai_api_key: str, pinecone_api_key: str, cloud: str = "aws", region: str = "us-east-1"):
    global smart_memory
    if smart_memory is None:
        smart_memory = SmartConversationMemory(openai_api_key, pinecone_api_key, cloud, region)
    return smart_memory