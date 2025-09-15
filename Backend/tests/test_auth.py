import pytest
import tempfile
import os
from app.auth import AuthManager, UserRegister, UserLogin


class TestAuthManager:
    """Test cases for the AuthManager class"""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        yield db_path
        os.unlink(db_path)
    
    @pytest.fixture
    def auth_manager(self, temp_db):
        """Create an AuthManager instance with temporary database"""
        return AuthManager(db_path=temp_db, secret_key="test-secret-key")
    
    def test_init_db(self, auth_manager):
        """Test database initialization"""
        # Database should be created and accessible
        assert os.path.exists(auth_manager.db_path)
    
    def test_create_user_success(self, auth_manager):
        """Test successful user creation"""
        user = auth_manager.create_user(
            email="test@example.com",
            username="testuser",
            password="testpassword123"
        )
        
        assert user is not None
        assert user["email"] == "test@example.com"
        assert user["username"] == "testuser"
        assert "id" in user
        assert "created_at" in user
    
    def test_create_user_duplicate_email(self, auth_manager):
        """Test user creation with duplicate email"""
        # Create first user
        auth_manager.create_user("test@example.com", "user1", "password123")
        
        # Try to create second user with same email
        user = auth_manager.create_user("test@example.com", "user2", "password456")
        assert user is None
    
    def test_create_user_duplicate_username(self, auth_manager):
        """Test user creation with duplicate username"""
        # Create first user
        auth_manager.create_user("user1@example.com", "testuser", "password123")
        
        # Try to create second user with same username
        user = auth_manager.create_user("user2@example.com", "testuser", "password456")
        assert user is None
    
    def test_authenticate_user_success(self, auth_manager):
        """Test successful user authentication"""
        # Create a user first
        auth_manager.create_user("test@example.com", "testuser", "testpassword123")
        
        # Authenticate the user
        user = auth_manager.authenticate_user("test@example.com", "testpassword123")
        
        assert user is not None
        assert user["email"] == "test@example.com"
        assert user["username"] == "testuser"
    
    def test_authenticate_user_wrong_password(self, auth_manager):
        """Test authentication with wrong password"""
        # Create a user first
        auth_manager.create_user("test@example.com", "testuser", "testpassword123")
        
        # Try to authenticate with wrong password
        user = auth_manager.authenticate_user("test@example.com", "wrongpassword")
        assert user is None
    
    def test_authenticate_user_nonexistent(self, auth_manager):
        """Test authentication with non-existent user"""
        user = auth_manager.authenticate_user("nonexistent@example.com", "password")
        assert user is None
    
    def test_create_token(self, auth_manager):
        """Test JWT token creation"""
        user_data = {
            "id": 1,
            "email": "test@example.com",
            "username": "testuser"
        }
        
        token = auth_manager.create_token(user_data)
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_token_success(self, auth_manager):
        """Test successful token verification"""
        user_data = {
            "id": 1,
            "email": "test@example.com",
            "username": "testuser"
        }
        
        token = auth_manager.create_token(user_data)
        verified_data = auth_manager.verify_token(token)
        
        assert verified_data is not None
        assert verified_data["user_id"] == user_data["id"]
        assert verified_data["email"] == user_data["email"]
        assert verified_data["username"] == user_data["username"]
    
    def test_verify_token_invalid(self, auth_manager):
        """Test token verification with invalid token"""
        verified_data = auth_manager.verify_token("invalid-token")
        assert verified_data is None


class TestPydanticModels:
    """Test cases for Pydantic models"""
    
    def test_user_register_valid(self):
        """Test valid user registration data"""
        user_data = UserRegister(
            email="test@example.com",
            username="testuser",
            password="testpassword123"
        )
        
        assert user_data.email == "test@example.com"
        assert user_data.username == "testuser"
        assert user_data.password == "testpassword123"
    
    def test_user_register_invalid_email(self):
        """Test user registration with invalid email"""
        with pytest.raises(ValueError):
            UserRegister(
                email="invalid-email",
                username="testuser",
                password="testpassword123"
            )
    
    def test_user_login_valid(self):
        """Test valid user login data"""
        login_data = UserLogin(
            email="test@example.com",
            password="testpassword123"
        )
        
        assert login_data.email == "test@example.com"
        assert login_data.password == "testpassword123"
