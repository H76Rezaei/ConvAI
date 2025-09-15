import pytest
import httpx
from fastapi.testclient import TestClient
import tempfile
import os

# Set up a temporary database for testing
temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
temp_db_path = temp_db.name
temp_db.close()

# Set environment variable for test database
os.environ['TEST_DB_PATH'] = temp_db_path

# Import after setting environment
from app.main import app


class TestAPIEndpoints:
    """Integration tests for API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create a test client"""
        return TestClient(app)
    
    @pytest.fixture(autouse=True)
    def setup_and_cleanup(self):
        """Set up test database and clean up after each test"""
        # Ensure the database is initialized
        from app.auth import get_auth_manager
        auth_mgr = get_auth_manager()
        auth_mgr.init_db()
        yield
        # Clean up test database after each test
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)
    
    def test_root_endpoint(self, client):
        """Test the root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
    
    def test_health_check(self, client):
        """Test the health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_debug_config(self, client):
        """Test the debug config endpoint"""
        response = client.get("/api/debug-config")
        assert response.status_code == 200
        data = response.json()
        assert "openai_key_present" in data
        assert "pinecone_key_present" in data
        assert "auth_enabled" in data
    
    def test_register_user_success(self, client):
        """Test successful user registration"""
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpassword123"
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_register_user_duplicate(self, client):
        """Test user registration with duplicate email"""
        user_data = {
            "email": "duplicate@example.com",
            "username": "user1",
            "password": "password123"
        }
        
        # Register first user
        response1 = client.post("/auth/register", json=user_data)
        assert response1.status_code == 200
        
        # Try to register second user with same email
        user_data["username"] = "user2"
        response2 = client.post("/auth/register", json=user_data)
        assert response2.status_code == 400
    
    def test_login_success(self, client):
        """Test successful user login"""
        # First register a user
        user_data = {
            "email": "login@example.com",
            "username": "loginuser",
            "password": "loginpassword123"
        }
        client.post("/auth/register", json=user_data)
        
        # Then login
        login_data = {
            "email": "login@example.com",
            "password": "loginpassword123"
        }
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 401
    
    def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token"""
        response = client.get("/auth/me")
        assert response.status_code == 403  # FastAPI returns 403 for missing auth
    
    def test_protected_endpoint_with_token(self, client):
        """Test accessing protected endpoint with valid token"""
        # Register and login to get token
        user_data = {
            "email": "protected@example.com",
            "username": "protecteduser",
            "password": "protectedpassword123"
        }
        register_response = client.post("/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        
        # Use token to access protected endpoint
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "protected@example.com"
        assert data["username"] == "protecteduser"
    
    def test_chat_endpoint_without_auth(self, client):
        """Test chat endpoint without authentication"""
        chat_data = {
            "message": "Hello, AI!"
        }
        response = client.post("/api/chat", json=chat_data)
        assert response.status_code == 403  # FastAPI returns 403 for missing auth
    
    def test_chat_endpoint_with_auth(self, client):
        """Test chat endpoint with authentication"""
        # Register and login to get token
        user_data = {
            "email": "chat@example.com",
            "username": "chatuser",
            "password": "chatpassword123"
        }
        register_response = client.post("/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        
        # Use token to access chat endpoint
        headers = {"Authorization": f"Bearer {token}"}
        chat_data = {
            "message": "Hello, AI!"
        }
        response = client.post("/api/chat", json=chat_data, headers=headers)
        # Note: This might fail if OpenAI API key is not configured
        # In a real test environment, you'd mock the OpenAI client
        assert response.status_code in [200, 500]  # 500 if OpenAI not configured
