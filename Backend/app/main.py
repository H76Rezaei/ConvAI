import os
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
import uvicorn
from datetime import datetime
from openai import OpenAI
from pydantic import BaseModel
from app.core.memory import get_memory_instance
from app.auth import auth_manager, UserRegister, UserLogin, get_current_user  
from pinecone import Pinecone
import logging
import time
import uuid
from typing import Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI instance
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    description="AI chat backend with OpenAI integration and user authentication"  
)

# Initialize OpenAI client with direct environment check
openai_api_key = os.environ.get("OPENAI_API_KEY") or settings.openai_api_key
pinecone_api_key = os.environ.get("PINECONE_API_KEY") or settings.pinecone_api_key

if openai_api_key:
    logger.info("Initializing OpenAI client...")
    openai_client = OpenAI(
        api_key=openai_api_key,
        timeout=30.0,
        max_retries=0,
    )
    logger.info("OpenAI client initialized successfully")
else:
    logger.error("OpenAI API key not found!")
    openai_client = None

if pinecone_api_key:
    logger.info("Pinecone API key found")
    pinecone_client = Pinecone(api_key=pinecone_api_key)
else:
    logger.error("Pinecone API key not found!")
    pinecone_client = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Local development
        "http://127.0.0.1:5173",  # Local development alternative
        "https://conv-ai-six.vercel.app",  # Vercel app URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============= AUTHENTICATION ROUTES =============
@app.post("/auth/register", tags=["Authentication"])
async def register(user_data: UserRegister):
    """Register a new user"""
    user = auth_manager.create_user(user_data.email, user_data.username, user_data.password)
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Email or username already registered"
        )
    
    token = auth_manager.create_token(user)
    return {
        "user": user,
        "access_token": token,
        "token_type": "bearer"
    }

@app.post("/auth/login", tags=["Authentication"])
async def login(user_credentials: UserLogin):
    """Login user"""
    user = auth_manager.authenticate_user(user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
    
    token = auth_manager.create_token(user)
    return {
        "user": user,
        "access_token": token,
        "token_type": "bearer"
    }

@app.get("/auth/me", tags=["Authentication"])
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return current_user

# ============= CHAT MODELS =============
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None  # Optional session ID for continuing conversations

# ============= BACKGROUND TASKS =============
async def store_conversation_background(user_id: str, user_message: str, ai_response: str, session_id: str = None):
    """
    Store conversation in memory as a background task with session support
    This runs after the response is sent to the user
    """
    try:
        start_time = time.time()
        
        # Get memory instance
        memory = get_memory_instance(settings.openai_api_key, settings.pinecone_api_key)
        
        # Store the conversation with session_id
        returned_session_id = memory.add_conversation_turn(user_id, user_message, ai_response, session_id)
        
        storage_time = time.time() - start_time
        logger.info(f"Background memory storage completed in {storage_time:.2f}s for user {user_id}, session {returned_session_id}")
        
    except Exception as e:
        logger.error(f"Background memory storage failed for user {user_id}: {e}")
        # Don't raise exception - this is background task

# ============= MAIN ROUTES =============
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version
    }

@app.post("/api/chat", tags=["Chat"])
async def chat_endpoint(
    request: ChatRequest, 
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Chat endpoint with session support and authentication
    Each conversation has a unique session_id 
    """
    try:
        start_time = time.time()
        user_message = request.message.strip()
        user_id = str(current_user["user_id"])
        session_id = request.session_id  # Get session_id from request (None for new conversations)
        
        if not user_message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        if not openai_client:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        # Get smart memory instance for context retrieval
        memory = get_memory_instance(settings.openai_api_key, settings.pinecone_api_key)
        
        # Get relevant context (recent + semantically similar)
        relevant_context = []
        if len(user_message) > 10:  # Only for substantial messages
            try:
                context_start = time.time()
                relevant_context = memory.get_relevant_context(
                    user_id=user_id, 
                    current_message=user_message,
                    max_recent=2,      # Keep it small for Railway
                    max_retrieved=1    # Keep it small for Railway
                )
                context_time = time.time() - context_start
                logger.info(f"Context retrieval took {context_time:.2f}s")
                
                # If context retrieval takes too long, skip it
                if context_time > 3.0:
                    logger.warning(f"Context retrieval too slow ({context_time:.2f}s), skipping")
                    relevant_context = []
                    
            except Exception as e:
                logger.error(f"Context retrieval failed: {e}")
                relevant_context = []  # Continue without context if it fails
        
        # Build messages for OpenAI
        messages = [
            {"role": "system", "content": f"You are a helpful AI assistant talking to {current_user['username']}. Use the conversation history to provide personalized and contextual responses."}
        ]
        
        # Add the smart context (limit total context to avoid token limits)
        if relevant_context:
            # Limit context to last 6 messages to avoid token overflow
            limited_context = relevant_context[-6:] if len(relevant_context) > 6 else relevant_context
            
            # Calculate approximate token count
            context_tokens = sum(len(msg["content"].split()) for msg in limited_context)
            logger.info(f"Context: {len(limited_context)} messages, ~{context_tokens} tokens")
            
            # If still too large, further limit
            if context_tokens > 800:  # Conservative token limit
                limited_context = limited_context[-4:]
                logger.warning("Further reduced context due to token size")
            
            messages.extend(limited_context)
        
        # Add the new user message
        messages.append({"role": "user", "content": user_message})
        
        # Call OpenAI with smart context
        response_start = time.time()
        try:
            logger.info(f"Calling OpenAI with {len(messages)} messages for user {current_user['username']}")
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo-1106",  # Try specific version
                messages=messages,
                max_tokens=200,
                temperature=0.7,
                timeout=45.0  # Longer timeout
            )
            logger.info("OpenAI call successful")
        except Exception as openai_error:
            logger.error(f"OpenAI call failed: {type(openai_error).__name__}: {openai_error}")
            
            # Fallback: try with minimal context
            if len(messages) > 2:  # If we have context, try without it
                logger.info("Retrying with minimal context...")
                fallback_messages = [
                    {"role": "system", "content": f"You are a helpful AI assistant talking to {current_user['username']}."},
                    {"role": "user", "content": user_message}
                ]
                try:
                    response = openai_client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=fallback_messages,
                        max_tokens=150,
                        temperature=0.7,
                        timeout=20.0
                    )
                    logger.info("Fallback OpenAI call successful")
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {fallback_error}")
                    # Return a static response as last resort
                    return {
                        "user_message": user_message,
                        "ai_response": f"Hi {current_user['username']}, I'm experiencing some connectivity issues right now. Please try again in a moment.",
                        "user_id": user_id,
                        "session_id": session_id or str(uuid.uuid4())[:8],
                        "timestamp": datetime.now().isoformat(),
                        "error": "openai_connection_error"
                    }
            else:
                # If minimal messages also fail, return error response
                return {
                    "user_message": user_message,
                    "ai_response": f"Hi {current_user['username']}, I'm having trouble connecting to the AI service. Please try again.",
                    "user_id": user_id,
                    "session_id": session_id or str(uuid.uuid4())[:8],
                    "timestamp": datetime.now().isoformat(),
                    "error": "openai_connection_error"
                }
                
        response_time = time.time() - response_start
        logger.info(f"OpenAI response took {response_time:.2f}s")
        
        ai_response = response.choices[0].message.content
        
        # Generate session_id if not provided (new conversation)
        if not session_id:
            session_id = str(uuid.uuid4())[:8]  # Short session ID like "a1b2c3d4"
            logger.info(f"Created new session {session_id} for user {current_user['username']}")
        
        # Add memory storage as background task with session_id
        background_tasks.add_task(
            store_conversation_background,
            user_id=user_id,
            user_message=user_message,
            ai_response=ai_response,
            session_id=session_id
        )
        
        total_time = time.time() - start_time
        logger.info(f"Total response time: {total_time:.2f}s for session {session_id}")
        
        return {
            "user_message": user_message,
            "ai_response": ai_response,
            "user_id": user_id,
            "username": current_user['username'],
            "session_id": session_id,  # Return session_id to frontend
            "timestamp": datetime.now().isoformat(),
            "response_time": round(total_time, 2)
        }
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail="Error processing your request")

# ============= CONVERSATION MANAGEMENT =============
@app.get("/api/conversations", tags=["Conversations"])
async def get_user_conversations(current_user: dict = Depends(get_current_user)):
    """Get all conversation sessions for the current user (like Claude's sidebar)"""
    try:
        user_id = str(current_user["user_id"])
        memory = get_memory_instance(settings.openai_api_key, settings.pinecone_api_key)
        
        # Get conversation list (you'll implement this in memory.py)
        conversations = memory.get_conversation_list(user_id)
        
        logger.info(f"Retrieved {len(conversations)} conversations for user {current_user['username']}")
        
        return {
            "conversations": conversations,
            "user_id": user_id,
            "username": current_user['username'],
            "total_conversations": len(conversations)
        }
    except Exception as e:
        logger.error(f"Error getting conversations: {e}")
        # Return empty list if method doesn't exist yet
        return {
            "conversations": [],
            "user_id": str(current_user["user_id"]),
            "username": current_user['username'],
            "note": "Conversation list feature not implemented yet"
        }

@app.get("/api/conversations/{session_id}", tags=["Conversations"])
async def get_conversation_details(
    session_id: str, 
    current_user: dict = Depends(get_current_user)
):
    """Get all messages from a specific conversation session"""
    try:
        user_id = str(current_user["user_id"])
        memory = get_memory_instance(settings.openai_api_key, settings.pinecone_api_key)
        
        # Get messages for this session (you'll implement this in memory.py)
        # For now, return a placeholder
        conversation = {
            "session_id": session_id,
            "messages": [],
            "user_id": user_id,
            "note": "Session detail feature not implemented yet"
        }
        
        return conversation
        
    except Exception as e:
        logger.error(f"Error getting conversation details: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving conversation details")

@app.delete("/api/conversations/{session_id}", tags=["Conversations"])
async def delete_conversation(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a specific conversation session"""
    try:
        user_id = str(current_user["user_id"])
        # TODO: Implement session deletion in memory.py
        
        logger.info(f"Deleted session {session_id} for user {current_user['username']}")
        
        return {
            "message": "Conversation deleted successfully",
            "session_id": session_id,
            "user_id": user_id
        }
        
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(status_code=500, detail="Error deleting conversation")

# ============= USER MANAGEMENT =============
@app.delete("/api/user/data", tags=["User Management"])
async def delete_user_data(current_user: dict = Depends(get_current_user)):
    """Delete all user conversations (GDPR compliance)"""
    try:
        user_id = str(current_user["user_id"])
        memory = get_memory_instance(settings.openai_api_key, settings.pinecone_api_key)
        
        success = memory.delete_user_conversations(user_id)
        if success:
            logger.info(f"Successfully deleted all data for user {current_user['username']} (ID: {user_id})")
            return {"message": "User data deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete user data")
    except Exception as e:
        logger.error(f"Error deleting user data: {e}")
        raise HTTPException(status_code=500, detail="Error deleting user data")

@app.get("/api/user/stats", tags=["User Management"])
async def get_current_user_stats(current_user: dict = Depends(get_current_user)):
    """Get conversation statistics for the current authenticated user"""
    try:
        user_id = str(current_user["user_id"])
        memory = get_memory_instance(settings.openai_api_key, settings.pinecone_api_key)
        
        # Get basic stats
        conversations = memory.get_conversation_list(user_id) if hasattr(memory, 'get_conversation_list') else []
        
        stats = {
            "user_id": user_id,
            "username": current_user['username'],
            "email": current_user['email'],
            "total_conversations": len(conversations),
            "total_messages": sum(conv.get("message_count", 0) for conv in conversations),
        }
        
        return {
            "user_id": user_id,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        return {
            "user_id": str(current_user["user_id"]),
            "stats": {
                "username": current_user['username'],
                "email": current_user['email'],
                "note": "Stats feature not fully implemented yet"
            },
            "timestamp": datetime.now().isoformat()
        }

# ============= DEBUG AND HEALTH =============
@app.get("/api/debug-config", tags=["Debug"])
async def debug_config():
    """Debug configuration - DO NOT EXPOSE FULL KEYS IN PRODUCTION"""
    return {
        "openai_key_present": bool(settings.openai_api_key),
        "openai_key_prefix": settings.openai_api_key[:7] + "..." if settings.openai_api_key else "None",
        "pinecone_key_present": bool(settings.pinecone_api_key),
        "openai_client_initialized": openai_client is not None,
        "env_vars_count": len([k for k in os.environ.keys() if "API" in k.upper()]),
        "auth_enabled": True
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "message": "ConvAI API is running",
        "timestamp": datetime.now().isoformat()
    }

# ============= OPTIONAL: PUBLIC ENDPOINT FOR TESTING =============
@app.post("/api/chat/public", tags=["Public"])
async def public_chat_endpoint(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    Public chat endpoint for testing (no authentication required)
    Remove this once authentication is fully implemented in frontend
    """
    user_id = "anonymous"
    
    try:
        start_time = time.time()
        user_message = request.message.strip()
        
        if not user_message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        if not openai_client:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        # Simple response without memory for public endpoint
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": user_message}
        ]
        
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=150,
            temperature=0.7,
            timeout=20.0
        )
        
        ai_response = response.choices[0].message.content
        total_time = time.time() - start_time
        
        return {
            "user_message": user_message,
            "ai_response": ai_response,
            "user_id": user_id,
            "session_id": "public",
            "timestamp": datetime.now().isoformat(),
            "response_time": round(total_time, 2),
            "note": "This is a public endpoint - sign up for personalized memory and conversations!"
        }
        
    except Exception as e:
        logger.error(f"Error in public chat endpoint: {e}")
        raise HTTPException(status_code=500, detail="Error processing your request")

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )