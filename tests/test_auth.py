"""Tests for authentication endpoints and services."""
import pytest
from httpx import AsyncClient
from sqlmodel import Session, select
from app.models.user import User
from app.services.auth_service import AuthService
from app.core.password import hash_password, verify_password
from app.core.jwt_utils import create_access_token, verify_token, decode_token


class TestPasswordUtilities:
    """Test password hashing and verification"""
    
    def test_hash_password(self):
        """Test password hashing"""
        plain = "mypassword123"
        hashed = hash_password(plain)
        assert hashed != plain
        assert len(hashed) > 0
    
    def test_verify_password_success(self):
        """Test successful password verification"""
        plain = "mypassword123"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True
    
    def test_verify_password_failure(self):
        """Test failed password verification"""
        plain = "mypassword123"
        wrong = "wrongpassword"
        hashed = hash_password(plain)
        assert verify_password(wrong, hashed) is False


class TestJWTUtilities:
    """Test JWT token creation and verification"""
    
    def test_create_access_token(self):
        """Test token creation"""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        assert token
        assert isinstance(token, str)
    
    def test_verify_token_success(self):
        """Test successful token verification"""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        payload = verify_token(token)
        assert payload
        assert payload.get("sub") == "testuser"
    
    def test_verify_token_invalid(self):
        """Test invalid token verification"""
        invalid_token = "invalid.token.here"
        payload = verify_token(invalid_token)
        assert payload is None
    
    def test_decode_token(self):
        """Test token decoding"""
        username = "testuser"
        data = {"sub": username}
        token = create_access_token(data)
        decoded = decode_token(token)
        assert decoded == username
    
    def test_decode_token_invalid(self):
        """Test invalid token decoding"""
        decoded = decode_token("invalid.token")
        assert decoded is None


class TestAuthService:
    """Test authentication service"""
    
    def test_register_user_success(self, session):
        """Test successful user registration"""
        user = AuthService.register_user(
            username="newuser",
            email="newuser@example.com",
            password="securepass123",
            session=session,
        )
        
        assert user.id is not None
        assert user.username == "newuser"
        assert user.email == "newuser@example.com"
        assert user.is_active is True
        assert verify_password("securepass123", user.hashed_password)
    
    def test_register_user_duplicate_username(self, session):
        """Test registration with duplicate username"""
        # Register first user
        AuthService.register_user(
            username="testuser",
            email="test1@example.com",
            password="securepass123",
            session=session,
        )
        
        # Try to register with same username
        with pytest.raises(ValueError, match="already exists"):
            AuthService.register_user(
                username="testuser",
                email="test2@example.com",
                password="securepass123",
                session=session,
            )
    
    def test_register_user_duplicate_email(self, session):
        """Test registration with duplicate email"""
        # Register first user
        AuthService.register_user(
            username="user1",
            email="shared@example.com",
            password="securepass123",
            session=session,
        )
        
        # Try to register with same email
        with pytest.raises(ValueError, match="already registered"):
            AuthService.register_user(
                username="user2",
                email="shared@example.com",
                password="securepass123",
                session=session,
            )
    
    def test_login_user_success(self, session):
        """Test successful login"""
        # Register user
        AuthService.register_user(
            username="loginuser",
            email="login@example.com",
            password="securepass123",
            session=session,
        )
        
        # Login
        user, token = AuthService.login_user(
            username="loginuser",
            password="securepass123",
            session=session,
        )
        
        assert user.username == "loginuser"
        assert token
        
        # Verify token
        payload = verify_token(token)
        assert payload
        assert payload.get("sub") == "loginuser"
    
    def test_login_user_invalid_username(self, session):
        """Test login with invalid username"""
        with pytest.raises(ValueError, match="Invalid username or password"):
            AuthService.login_user(
                username="nonexistent",
                password="anypass",
                session=session,
            )
    
    def test_login_user_invalid_password(self, session):
        """Test login with invalid password"""
        # Register user
        AuthService.register_user(
            username="testuser",
            email="test@example.com",
            password="correctpass123",
            session=session,
        )
        
        # Try wrong password
        with pytest.raises(ValueError, match="Invalid username or password"):
            AuthService.login_user(
                username="testuser",
                password="wrongpass123",
                session=session,
            )
    
    def test_get_user_by_username(self, session):
        """Test fetching user by username"""
        user_created = AuthService.register_user(
            username="finduser",
            email="find@example.com",
            password="pass123",
            session=session,
        )
        
        user_found = AuthService.get_user_by_username("finduser", session)
        assert user_found
        assert user_found.username == user_created.username
    
    def test_get_user_by_id(self, session):
        """Test fetching user by ID"""
        user_created = AuthService.register_user(
            username="iduser",
            email="id@example.com",
            password="pass123",
            session=session,
        )
        
        user_found = AuthService.get_user_by_id(user_created.id, session)
        assert user_found
        assert user_found.id == user_created.id


class TestAuthEndpoints:
    """Test authentication API endpoints"""
    
    def test_register_endpoint(self, client):
        """Test user registration endpoint"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "securepass123",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["username"] == "newuser"
        assert data["user"]["email"] == "new@example.com"
    
    def test_register_endpoint_duplicate_username(self, client):
        """Test registration with duplicate username"""
        # Register first user
        client.post(
            "/api/auth/register",
            json={
                "username": "user1",
                "email": "user1@example.com",
                "password": "pass123",
            },
        )
        
        # Try duplicate
        response = client.post(
            "/api/auth/register",
            json={
                "username": "user1",
                "email": "user2@example.com",
                "password": "pass123",
            },
        )
        
        # Should fail (either 400 or 422 depending on when validation happens)
        assert response.status_code in [400, 422]
    
    def test_login_endpoint(self, client):
        """Test login endpoint"""
        # Register user
        client.post(
            "/api/auth/register",
            json={
                "username": "loginuser",
                "email": "login@example.com",
                "password": "securepass123",
            },
        )
        
        # Login
        response = client.post(
            "/api/auth/login",
            json={
                "username": "loginuser",
                "password": "securepass123",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["username"] == "loginuser"
    
    def test_login_endpoint_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "nonexistent",
                "password": "anypass",
            },
        )
        
        assert response.status_code == 401
