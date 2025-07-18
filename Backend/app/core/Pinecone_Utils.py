from pinecone import Pinecone, ServerlessSpec
import uuid
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

class PineconeVectorStore:
    def __init__(self, api_key: str = None, index_name: str = "conversation-memory", 
                 cloud: str = "aws", region: str = "us-east-1"):
        # Use provided API key or get from environment
        self.api_key = api_key or os.environ.get("PINECONE_API_KEY")
        if not self.api_key:
            raise ValueError("Pinecone API key not found. Provide api_key parameter or set PINECONE_API_KEY environment variable.")
        
        self.index_name = index_name
        self.cloud = cloud
        self.region = region
        self.pc = None
        self.index = None
        self._initialize_pinecone()
    
    def _initialize_pinecone(self):
        try:
            # Initialize Pinecone client
            self.pc = Pinecone(api_key=self.api_key)
            logging.info("Pinecone client initialized successfully")
            
            # Check if index exists, create if not
            if not self.pc.has_index(self.index_name):
                self.pc.create_index(
                    name=self.index_name,
                    dimension=1536,  # OpenAI embeddings dimension
                    metric="cosine",
                    spec=ServerlessSpec(cloud=self.cloud, region=self.region)
                )
                logging.info(f"Created Pinecone index '{self.index_name}'")
            else:
                logging.info(f"Pinecone index '{self.index_name}' already exists")
                
            # Connect to index
            self.index = self.pc.Index(self.index_name)
            logging.info(f"Connected to Pinecone index '{self.index_name}'")

        except Exception as e:
            logging.error(f"Error initializing Pinecone: {e}")
            raise
    
    def store_conversation(self, user_id: str, conversation_text: str, embedding: List[float], metadata: Dict[str, Any]) -> str:
        doc_id = str(uuid.uuid4())
        
        try:
            namespace = f"user_{user_id}"
            
            # Add conversation_text to metadata for reference
            metadata_with_text = dict(metadata)
            metadata_with_text["conversation_text"] = conversation_text
            
            # Prepare upsert data: (id, embedding, metadata)
            upsert_data = [(doc_id, embedding, metadata_with_text)]
            
            # Upsert into Pinecone with user namespace
            self.index.upsert(vectors=upsert_data, namespace=namespace)
            
            logging.info(f"Successfully stored conversation {doc_id} for user {user_id}")
            
        except Exception as e:
            logging.error(f"Error storing conversation: {e}")
            raise
        
        return doc_id
    
    def similarity_search(self, user_id: str, query_embedding: List[float], top_k: int = 3) -> List[Dict[str, Any]]:
        try:
            namespace = f"user_{user_id}"
            query_response = self.index.query(
                vector=query_embedding,
                namespace=namespace,
                top_k=top_k,
                include_metadata=True
            )
            results = []
            for match in query_response.get("matches", []):
                results.append({
                    "id": match.get("id"),
                    "score": match.get("score"),
                    "metadata": match.get("metadata", {})
                })
            
            logging.info(f"Found {len(results)} similar conversations for user {user_id}")
            return results
            
        except Exception as e:
            logging.error(f"Error in similarity search: {e}")
            return []
    
    def delete_user_data(self, user_id: str) -> bool:
        """Delete all conversations for a specific user (GDPR compliance)"""
        try:
            namespace = f"user_{user_id}"
            # Delete all vectors in the user's namespace
            self.index.delete(delete_all=True, namespace=namespace)
            logging.info(f"Deleted all conversations for user {user_id} in namespace {namespace}")
            return True
        except Exception as e:
            logging.error(f"Error deleting user data: {e}")
            return False

class ConversationFormatter:
    """Helper class to format conversations for vector storage"""
    
    @staticmethod
    def format_conversation(user_message: str, ai_response: str) -> str:
        """
        Format conversation for embedding generation
        Using simple format for better semantic search results
        """
        # Strategy 1: Simple (recommended for semantic search)
        simple_format = f"User: {user_message}\nAI: {ai_response}"
        
        '''
        # Strategy 2: Context-rich (add flow markers and timestamp)
        timestamp = datetime.now().isoformat()
        context_rich_format = (
            f"[Conversation Start] ({timestamp})\n"
            f"[User Message]: {user_message}\n"
            f"[AI Response]: {ai_response}\n"
            f"[Conversation End]"
        )

        # Strategy 3: Semantic (placeholder for topic/entity extraction)
        semantic_format = (
            f"Key Points:\n"
            f"- User said: {user_message}\n"
            f"- AI replied: {ai_response}"
        )
        '''

        return simple_format
    
    @staticmethod
    def create_metadata(user_id: str, user_message: str, ai_response: str, **kwargs) -> Dict[str, Any]:
        """Create metadata dictionary for conversation"""
        base_metadata = {
            "user_id": user_id,
            "user_message": user_message,
            "ai_response": ai_response,
            "timestamp": datetime.now().isoformat(),
            "user_message_length": len(user_message),
            "ai_response_length": len(ai_response)
        }
        
        # Add any additional metadata
        base_metadata.update(kwargs)
        return base_metadata