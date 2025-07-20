import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    def __init__(self):
        # Basic app settings
        self.app_name = os.getenv("APP_NAME", "Backend")
        self.app_version = os.getenv("APP_VERSION", "1.0.0")
        self.debug = os.getenv("DEBUG", "true").lower() == "true"
        self.host = os.getenv("HOST", "127.0.0.1")
        self.port = int(os.getenv("PORT", "8000"))
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.pinecone_api_key = os.getenv("Pinecone_API_KEY")
        self.memory_max_recent_messages = int(os.getenv("MEMORY_MAX_RECENT", "5"))
        self.memory_max_retrieved = int(os.getenv("MEMORY_MAX_RETRIEVED", "3"))
        self.openai_timeout = int(os.environ.get("OPENAI_TIMEOUT", "30"))
        self.openai_max_retries = int(os.environ.get("OPENAI_MAX_RETRIES", "2"))
        
        # CORS settings for frontend
        allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
        self.allowed_origins = [
            "http://localhost:3000",
           "http://localhost:8080", 
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8080",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "https://conv-ai-six.vercel.app",
        ]

# Create settings instance
settings = Settings()