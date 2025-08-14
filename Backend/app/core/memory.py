from langchain.memory import ConversationSummaryBufferMemory
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.schema import HumanMessage, AIMessage
from pinecone import Pinecone
from typing import List, Dict, Any, Optional
import datetime
import logging
import uuid
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
        # Add document metadata store
        self.document_store = DocumentMetadataStore()
        # Change this to store by session instead of user
        self.session_memories = {}  # {session_id: ConversationSummaryBufferMemory}

    def get_conversation_memory(self, session_id: str) -> ConversationSummaryBufferMemory:
        """Get or create conversation buffer for specific session"""
        if session_id not in self.session_memories:
            self.session_memories[session_id] = ConversationSummaryBufferMemory(
                llm=self.llm,
                max_token_limit=1000,
                return_messages=True,
                memory_key="chat_history"
            )
        return self.session_memories[session_id]

    def add_conversation_turn(self, user_id: str, session_id: str, user_message: str, ai_response: str):
        """Add conversation to both session buffer and long-term storage"""
        # Add to session-specific buffer memory
        memory = self.get_conversation_memory(session_id)
        memory.save_context({"input": user_message}, {"output": ai_response})
        
        # Store in vector database with session metadata
        try:
            conversation_text = ConversationFormatter.format_conversation(user_message, ai_response)
            embedding = self.embeddings.embed_query(conversation_text)
            
            metadata = ConversationFormatter.create_metadata(
                user_id=user_id,
                session_id=session_id,  # Add session_id to metadata
                user_message=user_message,
                ai_response=ai_response
            )

            doc_id = self.vector_store.store_conversation(
                user_id=user_id,  # Keep user namespace for conversations
                conversation_text=conversation_text,
                embedding=embedding,
                metadata=metadata
            )
            
            logging.info(f"Successfully added conversation turn for user {user_id}, session {session_id}, doc_id: {doc_id}")
            
        except Exception as e:
            logging.error(f"Error storing conversation in vector store: {e}")

    def get_relevant_context(self, user_id: str, session_id: str, current_message: str, 
                                       max_recent: int = 5, max_retrieved: int = 3) -> List[Dict[str, str]]:
        """Get context from current session only"""
        context_messages = []
        
        # Get recent messages from current session buffer
        memory = self.get_conversation_memory(session_id)
        recent_langchain_messages = memory.chat_memory.messages
        
        recent_messages = []
        for msg in recent_langchain_messages[-max_recent*2:]:  # *2 because each turn has user+ai
            if isinstance(msg, HumanMessage):
                recent_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                recent_messages.append({"role": "assistant", "content": msg.content})

        # Get relevant past conversations from CURRENT SESSION ONLY
        try:
            query_embedding = self.embeddings.embed_query(current_message)
            
            # Use filtered search to only get conversations from current session
            similar_conversations = self.vector_store.similarity_search_with_filter(
                user_id=user_id,
                query_embedding=query_embedding,
                top_k=max_retrieved,
                filter_condition={"session_id": session_id}  # Filter by session
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
            logging.error(f"Error retrieving session context: {e}")
        
        # Return relevant past conversations + recent conversations (all from same session)
        return context_messages + recent_messages

    def delete_session(self, session_id: str) -> bool:
        """Delete specific session data"""
        try:
            # Clear session memory
            if session_id in self.session_memories:
                del self.session_memories[session_id]
                logging.info(f"Cleared session memory for session {session_id}")
            return True
            
        except Exception as e:
            logging.error(f"Error deleting session: {e}")
            return False

    def get_conversation_list(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get list of conversation sessions for the UI 
        """
        try:
            dummy_embedding = [0.0] * 1536
            namespace = f"user_{user_id}"
        
            # Get recent conversations from Pinecone
            results = self.vector_store.index.query(
                vector=dummy_embedding,
                namespace=namespace,
                top_k=100,  # Get more to find different sessions
                include_metadata=True
            )
        
            if not results.get("matches"):
                return []
        
            # Group by session_id instead of date
            sessions = {}

            for match in results["matches"]:
                metadata = match.get("metadata", {})
                session_id = metadata.get("session_id")  # We'll need to add this
                timestamp = metadata.get("timestamp", "")
                user_message = metadata.get("user_message", "")

                if not user_message:
                    continue
            
                # If no session_id, create one based on timestamp (for existing data)
                if not session_id:
                    # For existing data without session_id, group by hour
                    if timestamp:
                        # Group by date + hour (so conversations in same hour = same session)
                        session_id = timestamp[:13]  # "2024-01-15T10" 
                    else:
                        session_id = "unknown"
            
                # Create or update session
                if session_id not in sessions:
                    sessions[session_id] = {
                        "session_id": session_id,
                        "title": user_message[:60] + "..." if len(user_message) > 60 else user_message,
                        "preview": user_message[:80] + "..." if len(user_message) > 80 else user_message,
                        "message_count": 1,
                        "created_at": timestamp,
                        "last_message_at": timestamp
                    }
                else:
                    sessions[session_id]["message_count"] += 1
                    # Keep the first message as title, update last_message_at
                    if timestamp > sessions[session_id]["last_message_at"]:
                        sessions[session_id]["last_message_at"] = timestamp
                    if timestamp < sessions[session_id]["created_at"]:
                        sessions[session_id]["created_at"] = timestamp
        
            # Convert to list and sort by last message (newest first)
            session_list = list(sessions.values())
            session_list.sort(key=lambda x: x["last_message_at"], reverse=True)
        
            return session_list[:20]  # Return last 20 sessions
        
        except Exception as e:
            logging.error(f"Error getting conversation list: {e}")
            return []
        
    def store_document_metadata(self, user_id: str, document_data: Dict[str, Any]) -> bool:
        """Store document metadata"""
        return self.document_store.store_document_metadata(user_id, document_data)
    
    def get_user_documents(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all documents for a user"""
        return self.document_store.get_user_documents(user_id)
    
    def delete_document_completely(self, user_id: str, document_id: str) -> bool:
        """Delete document metadata and all its chunks from vector store"""
        try:
            # Check if document exists and belongs to user
            if not self.document_store.document_exists(user_id, document_id):
                return False
            
            # Delete from metadata store
            metadata_deleted = self.document_store.delete_document(user_id, document_id)
            
            # Delete chunks from vector store
            # This requires implementing a delete method in your PineconeVectorStore
            vector_deleted = self._delete_document_chunks(user_id, document_id)
            
            return metadata_deleted and vector_deleted
            
        except Exception as e:
            logging.error(f"Failed to delete document {document_id}: {e}")
            return False
    
    def _delete_document_chunks(self, user_id: str, document_id: str) -> bool:
        """Delete all chunks for a document from vector store"""
        return self.vector_store.delete_document_chunks(user_id, document_id)



class DocumentMetadataStore:
    """
    Simple in-memory document metadata store
    In production, you'd use a real database (PostgreSQL, MongoDB, etc.)
    """
    def __init__(self):
        self.documents = {}  # {user_id: {doc_id: metadata}}
        self.logger = logging.getLogger(__name__)
    
    def store_document_metadata(self, user_id: str, document_data: Dict[str, Any]) -> bool:
        """Store document metadata"""
        try:
            if user_id not in self.documents:
                self.documents[user_id] = {}
            
            doc_id = document_data['document_id']
            self.documents[user_id][doc_id] = {
                **document_data,
                'stored_at': datetime.now().isoformat()
            }
            
            self.logger.info(f"Stored metadata for document {doc_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store document metadata: {e}")
            return False
    
    def get_user_documents(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all documents for a user"""
        try:
            user_docs = self.documents.get(user_id, {})
            return list(user_docs.values())
        except Exception as e:
            self.logger.error(f"Failed to get user documents: {e}")
            return []
    
    def get_document(self, user_id: str, document_id: str) -> Optional[Dict[str, Any]]:
        """Get specific document metadata"""
        try:
            return self.documents.get(user_id, {}).get(document_id)
        except Exception as e:
            self.logger.error(f"Failed to get document {document_id}: {e}")
            return None
    
    def delete_document(self, user_id: str, document_id: str) -> bool:
        """Delete document metadata"""
        try:
            if user_id in self.documents and document_id in self.documents[user_id]:
                del self.documents[user_id][document_id]
                self.logger.info(f"Deleted metadata for document {document_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to delete document metadata: {e}")
            return False
    
    def document_exists(self, user_id: str, document_id: str) -> bool:
        """Check if document exists and belongs to user"""
        return user_id in self.documents and document_id in self.documents[user_id]
    

smart_memory = None

def get_memory_instance(openai_api_key: str, pinecone_api_key: str, cloud: str = "aws", region: str = "us-east-1"):
    global smart_memory
    if smart_memory is None:
        smart_memory = SmartConversationMemory(openai_api_key, pinecone_api_key, cloud, region)
    return smart_memory