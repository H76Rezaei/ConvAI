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
            content_type = metadata.get('content_type', 'conversation')
            namespace = f"user_{user_id}"

            # Add conversation_text to metadata for reference
            metadata_with_text = dict(metadata)
            metadata_with_text["conversation_text"] = conversation_text
            
            # Prepare upsert data: (id, embedding, metadata)
            upsert_data = [(doc_id, embedding, metadata_with_text)]
            
            # Upsert into Pinecone with user namespace
            self.index.upsert(vectors=upsert_data, namespace=namespace)
            
            logging.info(f"Successfully stored {content_type} {doc_id} for user {user_id}")
            
        except Exception as e:
            logging.error(f"Error storing content: {e}")
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
    def similarity_search_with_filter(self, user_id: str, query_embedding: List[float], 
                                 top_k: int = 3, filter_condition: Dict = None) -> List[Dict[str, Any]]:
        

        try:
            namespace = f"user_{user_id}"
        
            # Build the query
            query_params = {
                "vector": query_embedding,
                "namespace": namespace,
                "top_k": top_k,
                "include_metadata": True
            }
        
            # Add filter if provided
            if filter_condition:
                query_params["filter"] = filter_condition
            
            query_response = self.index.query(**query_params)

            # After the query but before returning results:
            logging.info(f"=== STORAGE DEBUG ===")
            # Query without filter first to see what's actually stored
            no_filter_response = self.index.query(
                vector=query_embedding,
                namespace=namespace,
                top_k=10,
                include_metadata=True
            )
            logging.info(f"Total items in namespace: {len(no_filter_response.get('matches', []))}")
            for i, match in enumerate(no_filter_response.get('matches', [])[:3]):
                metadata = match.get('metadata', {})
                logging.info(f"Stored item {i}: document_id='{metadata.get('document_id')}', filename='{metadata.get('filename')}'")
            logging.info(f"Looking for document_id: {filter_condition}")
            logging.info(f"=== END STORAGE DEBUG ===")


            results = []
            for match in query_response.get("matches", []):
                results.append({
                    "id": match.get("id"),
                    "score": match.get("score"),
                    "metadata": match.get("metadata", {})
                })
        
            logging.info(f"Filtered search found {len(results)} results in namespace {namespace}")
            return results
        
        except Exception as e:
            logging.error(f"Error in filtered similarity search: {e}")
            return []

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
        return simple_format
        
    @staticmethod
    def create_conversation_id(user_id: str, timestamp: str = None) -> str:
        """
        Create a conversation ID for grouping related messages
        """
        if not timestamp:
            timestamp = datetime.now().isoformat()
    
        date_part = timestamp.split("T")[0]
        return f"conv_{user_id}_{date_part}"
         
    @staticmethod
    def create_metadata(user_id: str, user_message: str, ai_response: str, session_id: str = None, **kwargs) -> Dict[str, Any]:
        """Create metadata dictionary for conversation"""
        # Generate session_id if not provided
        if not session_id:
            session_id = str(uuid.uuid4())[:8]
        base_metadata = {
            "user_id": user_id,
            "session_id": session_id,
            "user_message": user_message,
            "ai_response": ai_response,
            "session_id": session_id,  
            "timestamp": datetime.now().isoformat(),
            "user_message_length": len(user_message),
            "ai_response_length": len(ai_response)
        }
    
        # Add any additional metadata
        base_metadata.update(kwargs)
        return base_metadata

    def delete_document_chunks(self, user_id: str, document_id: str) -> bool:
        """Delete all chunks for a specific document"""
        try:
            # Use documents namespace 
            namespace = f"user_{user_id}_docs"
        
            # Query for all vectors with this document_id
            query_response = self.index.query(
                vector=[0.0] * 1536,  # OpenAI embeddings are 1536 dimensions
                namespace=namespace,
                filter={"document_id": {"$eq": document_id}},
                top_k=10000,  
                include_metadata=True, 
                include_values=False  
            )
        
            # Extract IDs to delete
            ids_to_delete = [match["id"] for match in query_response.get("matches", [])]
        
            if ids_to_delete:
                # Delete them by their IDs
                self.index.delete(ids=ids_to_delete, namespace=namespace)
                logging.info(f"Deleted {len(ids_to_delete)} chunks for document {document_id}")
                return True
            else:
                logging.warning(f"No chunks found for document {document_id}")
                return False
            
        except Exception as e:
            logging.error(f"Error deleting document chunks: {e}")
            return False

    def delete_user_data(self, user_id: str) -> bool:
        """Delete all data for a user (both conversations and documents)"""
        try:
            success = True
        
            # Delete conversation data
            chat_namespace = f"user_{user_id}"
            try:
                self.index.delete(delete_all=True, namespace=chat_namespace)
                logging.info(f"Deleted all conversation data for user {user_id}")
            except Exception as e:
                logging.error(f"Failed to delete conversation data for user {user_id}: {e}")
                success = False
        
            # Delete document data
            docs_namespace = f"user_{user_id}_docs"
            try:
                self.index.delete(delete_all=True, namespace=docs_namespace)
                logging.info(f"Deleted all document data for user {user_id}")
            except Exception as e:
                logging.error(f"Failed to delete document data for user {user_id}: {e}")
                success = False
            
            return success
        
        except Exception as e:
            logging.error(f"Error deleting user data: {e}")
            return False