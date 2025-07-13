from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
import uvicorn
from datetime import datetime
from openai import OpenAI
from pydantic import BaseModel
from app.core.memory import get_memory_instance


# Create FastAPI instance
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    description="AI chat backend with OpenAI integration"
)

# Initialize OpenAI client
if settings.openai_api_key:
    openai_client = OpenAI(api_key=settings.openai_api_key)
else:
    openai_client = None

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Request model for chat
class ChatRequest(BaseModel):
    message: str
    user_id: str = "anonymous"

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version
    }

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Chat endpoint with smart memory integration
    """
    try:
        user_message = request.message.strip()
        user_id = request.user_id
        
        if not user_message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        if not openai_client:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        # Get smart memory instance
        memory = get_memory_instance(settings.openai_api_key)
        
        # Get relevant context (recent + semantically similar)
        relevant_context = memory.get_relevant_context(
            user_id=user_id, 
            current_message=user_message,
            max_recent=5,      # Last 5 conversation turns
            max_retrieved=3    # Top 3 relevant past conversations
        )
        
        # Build messages for OpenAI
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant. Use the conversation history to provide personalized responses."}
        ]
        
        # Add the smart context
        messages.extend(relevant_context)
        
        # Add the new user message
        messages.append({"role": "user", "content": user_message})
        
        # Call OpenAI with smart context
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=150,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        
        # Save this conversation turn to smart memory
        memory.add_conversation_turn(user_id, user_message, ai_response)
        
        return {
            "user_message": user_message,
            "ai_response": ai_response,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail="Error processing your request")
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )