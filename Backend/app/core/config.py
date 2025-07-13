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
        self.memory_max_recent_messages = int(os.getenv("MEMORY_MAX_RECENT", "5"))
        self.memory_max_retrieved = int(os.getenv("MEMORY_MAX_RETRIEVED", "3"))
        
        # CORS settings for frontend
        self.allowed_origins = [
            "http://localhost:3000",
            "http://localhost:8080",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8080",
            "http://localhost:5173",
        ]

# Create settings instance
settings = Settings()