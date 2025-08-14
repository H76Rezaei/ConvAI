from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional
import logging
from datetime import datetime
import os

from app.core.document_processor import DocumentProcessor, DocumentRetriever
from app.core.memory import get_memory_instance
from app.core.config import settings

# Create router for document-related endpoints
router = APIRouter(prefix="/api/documents", tags=["documents"])
logger = logging.getLogger(__name__)

# Initialize document processor and retriever with memory instance
memory = get_memory_instance(settings.openai_api_key, settings.pinecone_api_key)
processor = DocumentProcessor(memory.embeddings, memory.vector_store)
retriever = DocumentRetriever(memory.embeddings, memory.vector_store)

@router.post("/upload")
@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    user_id: str = Form(...)
):
    """
    Upload and process a document synchronously
    """
    document_id = f"doc_{user_id}_{int(datetime.now().timestamp())}"
    
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check file type
        allowed_types = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=415, 
                detail="File type not supported. Please upload PDF, DOCX, or TXT files."
            )
        
        # Check file size (10MB limit)
        max_size = 10 * 1024 * 1024  # 10MB
        file_content = await file.read()
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=413,
                detail="File too large. Maximum size is 10MB."
            )
        
        # Get file extension
        file_extension = file.filename.split('.')[-1].lower()
        
        logger.info(f"Processing upload: {file.filename} ({len(file_content)} bytes) for user {user_id}")

        # Process document immediately 
        result = await processor.process_document(
            file_content, file.filename, user_id, file_extension, document_id
        )
        
        if result.get("status") == "success":
            logger.info(f"Document processed successfully: {document_id}")
            return {
                "document_id": document_id,
                "filename": file.filename,
                "file_type": file_extension,
                "file_size": len(file_content),
                "status": "ready", 
                "total_chunks": result.get("stored_chunks_count", 0),
                "message": "Document uploaded and processed successfully.",
                "timestamp": datetime.now().isoformat()
            }
        else:
            logger.error(f"Document processing failed: {result.get('error', 'Unknown error')}")
            raise HTTPException(status_code=500, detail=f"Processing failed: {result.get('error', 'Unknown error')}")
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail="Error processing document upload")

@router.get("/{user_id}")
async def get_user_documents(user_id: str):
    """
    Get all documents for a user
    """
    try:
        documents = await memory.document_metadata_store.get_documents_by_user(user_id)
        return {
            "user_id": user_id,
            "documents": documents,
            "total_documents": len(documents),
            "message": "Documents retrieved successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting user documents: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving documents")

@router.delete("/{document_id}")
async def delete_document(document_id: str, user_id: str = Form(...)):
    """
    Delete a document and all its chunks
    """
    try:
        # Delete document metadata and its chunks from the vector store
        deleted = await memory.document_metadata_store.delete_document(document_id, user_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Document not found or not owned by user")

        # Remove vectors/chunks from vector store
        await memory.vector_store.delete_by_document_id(document_id)
        logger.info(f"Document deletion requested: {document_id} for user {user_id}")
        
        return {
            "document_id": document_id,
            "status": "pending",
            "message": "Document deletion not yet implemented",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail="Error deleting document")

@router.post("/search")
async def search_documents(
    query: str = Form(...),
    user_id: str = Form(...),
    top_k: int = Form(5)
):
    """
    Search through user's documents for relevant content
    """
    try:
        if not query.strip():
            raise HTTPException(status_code=400, detail="Search query cannot be empty")
        
        # Use the actual document retriever
        results = await retriever.search_documents(query, user_id, top_k)
        
        return {
            "query": query,
            "user_id": user_id,
            "results": results,
            "total_results": len(results),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        raise HTTPException(status_code=500, detail="Error searching documents")

# Background task for document processing
async def process_document_background(file_content: bytes, filename: str, user_id: str, file_type: str, document_id: str):
    """
    Background task to process uploaded document
    """
    try:
        result = await processor.process_document(
            file_content, filename, user_id, file_type, document_id
        )
        
        if result.get("status") == "success":
            logger.info(f"Successfully processed {filename}: {result.get('stored_chunks_count', 0)} chunks stored")
        else:
            logger.error(f"Failed to process {filename}: {result.get('error', 'Unknown error')}")
        
    except Exception as e:
        logger.error(f"Background processing failed for {filename}: {e}")