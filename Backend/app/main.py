import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
import uvicorn
from datetime import datetime
from openai import OpenAI
from pydantic import BaseModel
from app.core.memory import get_memory_instance
from pinecone import Pinecone
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Debug: Check environment variables at startup
logger.info(f"OPENAI_API_KEY present: {bool(os.environ.get('OPENAI_API_KEY'))}")
logger.info(f"PINECONE_API_KEY present: {bool(os.environ.get('PINECONE_API_KEY'))}")
logger.info(f"Settings openai_api_key: {bool(settings.openai_api_key)}")
logger.info(f"Settings pinecone_api_key: {bool(settings.pinecone_api_key)}")

# Create FastAPI instance
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    description="AI chat backend with OpenAI integration"
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
        "https://conv-ai-six.vercel.app",  # Your Vercel app URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model for chat
class ChatRequest(BaseModel):
    message: str
    user_id: str = "anonymous"

# Background task for memory storage
async def store_conversation_background(user_id: str, user_message: str, ai_response: str):
    """
    Store conversation in memory as a background task
    This runs after the response is sent to the user
    """
    try:
        start_time = time.time()
        
        # Get memory instance
        memory = get_memory_instance(settings.openai_api_key, settings.pinecone_api_key)
        
        # Store the conversation
        memory.add_conversation_turn(user_id, user_message, ai_response)
        
        storage_time = time.time() - start_time
        logger.info(f"Background memory storage completed in {storage_time:.2f}s for user {user_id}")
        
    except Exception as e:
        logger.error(f"Background memory storage failed for user {user_id}: {e}")
        # Don't raise exception - this is background task

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version
    }

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    Chat endpoint with optimized smart memory integration
    Memory storage happens in background for faster response
    """
    try:
        start_time = time.time()
        user_message = request.message.strip()
        user_id = request.user_id
        
        if not user_message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        if not openai_client:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        # Get smart memory instance for context retrieval only
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
            {"role": "system", "content": "You are a helpful AI assistant. Use the conversation history to provide personalized and contextual responses."}
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
            logger.info(f"Calling OpenAI with {len(messages)} messages")
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
                    {"role": "system", "content": "You are a helpful AI assistant."},
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
                        "ai_response": "I'm experiencing some connectivity issues right now. Please try again in a moment.",
                        "user_id": user_id,
                        "timestamp": datetime.now().isoformat(),
                        "error": "openai_connection_error"
                    }
            else:
                # If minimal messages also fail, return error response
                return {
                    "user_message": user_message,
                    "ai_response": "I'm having trouble connecting to the AI service. Please try again.",
                    "user_id": user_id,
                    "timestamp": datetime.now().isoformat(),
                    "error": "openai_connection_error"
                }
                
        response_time = time.time() - response_start
        logger.info(f"OpenAI response took {response_time:.2f}s")
        
        ai_response = response.choices[0].message.content
        
        # Add memory storage as background task (happens after response is sent)
        background_tasks.add_task(
            store_conversation_background,
            user_id=user_id,
            user_message=user_message,
            ai_response=ai_response
        )
        
        total_time = time.time() - start_time
        logger.info(f"Total response time: {total_time:.2f}s (before background storage)")
        
        return {
            "user_message": user_message,
            "ai_response": ai_response,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "response_time": round(total_time, 2)  # For debugging
        }
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail="Error processing your request")

@app.get("/api/debug-config")
async def debug_config():
    """Debug configuration - DO NOT EXPOSE FULL KEYS IN PRODUCTION"""
    return {
        "openai_key_present": bool(settings.openai_api_key),
        "openai_key_prefix": settings.openai_api_key[:7] + "..." if settings.openai_api_key else "None",
        "pinecone_key_present": bool(settings.pinecone_api_key),
        "openai_client_initialized": openai_client is not None,
        "env_vars_count": len([k for k in os.environ.keys() if "API" in k.upper()])
    }

@app.get("/api/user/{user_id}/stats")
async def get_user_stats(user_id: str):
    """Get conversation statistics for a user"""
    try:
        memory = get_memory_instance(settings.openai_api_key, settings.pinecone_api_key)
        stats = memory.get_user_conversation_count(user_id)
        return {
            "user_id": user_id,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving user statistics")

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )