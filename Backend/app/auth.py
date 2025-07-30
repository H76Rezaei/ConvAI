# app/auth.py
import sqlite3
import hashlib
import secrets
import jwt
import os
from datetime import datetime, timedelta
import time
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
import logging

logger = logging.getLogger(__name__)
security = HTTPBearer()

class AuthManager:
    def __init__(self, db_path: str = "users.db", secret_key: str = None):
        self.db_path = db_path
        self.secret_key = secret_key or os.getenv("JWT_SECRET_KEY", "your-default-secret-key-change-in-production")
        self.init_db()
    
    def init_db(self):
        """Initialize the users table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            conn.commit()
            conn.close()
            logger.info("User database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing user database: {e}")
            raise
    
    def hash_password(self, password: str, salt: str) -> str:
        """Hash password with salt using PBKDF2"""
        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
    
    def create_user(self, email: str, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Create a new user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE email = ? OR username = ?", (email, username))
            if cursor.fetchone():
                conn.close()
                logger.info(f"User creation failed: email {email} or username {username} already exists")
                return None
            
            # Create user
            salt = secrets.token_hex(32)
            password_hash = self.hash_password(password, salt)
            
            cursor.execute('''
                INSERT INTO users (email, username, password_hash, salt)
                VALUES (?, ?, ?, ?)
            ''', (email, username, password_hash, salt))
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Created new user: {username} (ID: {user_id})")
            
            return {
                "id": user_id,
                "email": email,
                "username": username,
                "created_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user and return user data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, email, username, password_hash, salt, created_at 
                FROM users WHERE email = ? AND is_active = 1
            ''', (email,))
            
            user = cursor.fetchone()
            conn.close()
            
            if user:
                # user[4] is salt, user[3] is password_hash
                stored_hash = user[3]
                salt = user[4]
                computed_hash = self.hash_password(password, salt)
                
                logger.debug(f"Auth attempt for {email}: stored_hash exists: {bool(stored_hash)}, computed_hash exists: {bool(computed_hash)}")
                
                if computed_hash == stored_hash:
                    logger.info(f"Successful authentication for user: {user[2]}")
                    return {
                        "id": user[0],
                        "email": user[1], 
                        "username": user[2],
                        "created_at": user[5]
                    }
                else:
                    logger.warning(f"Failed authentication attempt for email: {email} - password mismatch")
                    return None
            else:
                logger.warning(f"Failed authentication attempt for email: {email} - user not found")
                return None
                
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None


    def create_token(self, user_data: Dict[str, Any]) -> str:
        """Create JWT token for user"""
        try:
            now = datetime.utcnow()  # More compatible
            payload = {
                "user_id": user_data["id"],
                "email": user_data["email"],
                "username": user_data["username"],
                "exp": int((now + timedelta(days=30)).timestamp()),
                "iat": int(now.timestamp())
            }
            token = jwt.encode(payload, self.secret_key, algorithm="HS256")
            logger.info(f"Created token for user: {user_data['username']}")
            return token
        except Exception as e:
            logger.error(f"Error creating token: {e}")
            raise
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return user data"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return {
                "user_id": payload["user_id"],
                "email": payload["email"],
                "username": payload["username"]
            }
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return None

# Global auth instance
auth_manager = AuthManager()

# Pydantic models for request/response
class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "john_doe",
                "password": "your_secure_password"
            }
        }

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "your_secure_password"
            }
        }

# Dependency to get current user
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    FastAPI dependency to get the current authenticated user
    Usage: current_user: dict = Depends(get_current_user)
    """
    try:
        user_data = auth_manager.verify_token(credentials.credentials)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_current_user: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication error",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Optional: Create an optional dependency for routes that can work with or without auth
async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))) -> Optional[Dict[str, Any]]:
    """
    Optional authentication dependency
    Returns user data if authenticated, None if not
    """
    if not credentials:
        return None
    
    try:
        return auth_manager.verify_token(credentials.credentials)
    except Exception:
        return None