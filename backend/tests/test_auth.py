import pytest
from datetime import datetime, timedelta


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "docs" in data


class TestUserRegistration:
    """Tests for user registration endpoint."""
    
    def test_register_user_success(self, client):
        """Test successful user registration."""
        user_data = {
            "email": "test@example.com",
            "password": "securepassword123",
            "full_name": "Test User"
        }
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["full_name"] == user_data["full_name"]
        assert "id" in data
        assert "hashed_password" not in data
        assert data["is_active"] is True
        assert data["is_superuser"] is False
    
    def test_register_duplicate_email(self, client):
        """Test registration with duplicate email fails."""
        user_data = {
            "email": "test@example.com",
            "password": "securepassword123",
            "full_name": "Test User"
        }
        # First registration
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 201
        
        # Second registration with same email
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 409
        assert "already registered" in response.json()["detail"].lower()
    
    def test_register_invalid_email(self, client):
        """Test registration with invalid email fails."""
        user_data = {
            "email": "invalid-email",
            "password": "securepassword123",
            "full_name": "Test User"
        }
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 422
    
    def test_register_short_password(self, client):
        """Test registration with short password fails."""
        user_data = {
            "email": "test@example.com",
            "password": "short",
            "full_name": "Test User"
        }
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 422


class TestUserLogin:
    """Tests for user login endpoint."""
    
    def test_login_success(self, client):
        """Test successful login with valid credentials."""
        # Register user first
        user_data = {
            "email": "test@example.com",
            "password": "securepassword123",
            "full_name": "Test User"
        }
        client.post("/api/auth/register", json=user_data)
        
        # Login
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }
        response = client.post("/api/auth/login", data=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
    
    def test_login_json_success(self, client):
        """Test successful login with JSON payload."""
        # Register user first
        user_data = {
            "email": "test@example.com",
            "password": "securepassword123",
            "full_name": "Test User"
        }
        client.post("/api/auth/register", json=user_data)
        
        # Login with JSON
        login_data = {
            "email": user_data["email"],
            "password": user_data["password"]
        }
        response = client.post("/api/auth/login/json", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_login_invalid_password(self, client):
        """Test login with invalid password fails."""
        # Register user first
        user_data = {
            "email": "test@example.com",
            "password": "securepassword123",
            "full_name": "Test User"
        }
        client.post("/api/auth/register", json=user_data)
        
        # Login with wrong password
        login_data = {
            "username": user_data["email"],
            "password": "wrongpassword"
        }
        response = client.post("/api/auth/login", data=login_data)
        assert response.status_code == 401
    
    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user fails."""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "somepassword"
        }
        response = client.post("/api/auth/login", data=login_data)
        assert response.status_code == 401


class TestTokenRefresh:
    """Tests for token refresh endpoint."""
    
    def test_refresh_token_success(self, client):
        """Test successful token refresh."""
        # Register and login
        user_data = {
            "email": "test@example.com",
            "password": "securepassword123",
            "full_name": "Test User"
        }
        client.post("/api/auth/register", json=user_data)
        
        login_response = client.post("/api/auth/login", data={
            "username": user_data["email"],
            "password": user_data["password"]
        })
        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh token
        response = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_refresh_invalid_token(self, client):
        """Test refresh with invalid token fails."""
        response = client.post("/api/auth/refresh", json={"refresh_token": "invalid-token"})
        assert response.status_code == 401
    
    def test_refresh_access_token_fails(self, client):
        """Test that using access token as refresh token fails."""
        # Register and login
        user_data = {
            "email": "test@example.com",
            "password": "securepassword123",
            "full_name": "Test User"
        }
        client.post("/api/auth/register", json=user_data)
        
        login_response = client.post("/api/auth/login", data={
            "username": user_data["email"],
            "password": user_data["password"]
        })
        access_token = login_response.json()["access_token"]
        
        # Try to use access token as refresh token
        response = client.post("/api/auth/refresh", json={"refresh_token": access_token})
        assert response.status_code == 401


class TestGetCurrentUser:
    """Tests for getting current user information."""
    
    def test_get_me_success(self, client):
        """Test getting current user info with valid token."""
        # Register and login
        user_data = {
            "email": "test@example.com",
            "password": "securepassword123",
            "full_name": "Test User"
        }
        client.post("/api/auth/register", json=user_data)
        
        login_response = client.post("/api/auth/login", data={
            "username": user_data["email"],
            "password": user_data["password"]
        })
        access_token = login_response.json()["access_token"]
        
        # Get current user
        response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {access_token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["full_name"] == user_data["full_name"]
    
    def test_get_me_no_token(self, client):
        """Test getting current user without token fails."""
        response = client.get("/api/auth/me")
        assert response.status_code == 401
    
    def test_get_me_invalid_token(self, client):
        """Test getting current user with invalid token fails."""
        response = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid-token"})
        assert response.status_code == 401


class TestUpdateCurrentUser:
    """Tests for updating current user information."""
    
    def test_update_me_success(self, client):
        """Test updating current user info."""
        # Register and login
        user_data = {
            "email": "test@example.com",
            "password": "securepassword123",
            "full_name": "Test User"
        }
        client.post("/api/auth/register", json=user_data)
        
        login_response = client.post("/api/auth/login", data={
            "username": user_data["email"],
            "password": user_data["password"]
        })
        access_token = login_response.json()["access_token"]
        
        # Update user
        update_data = {"full_name": "Updated Name"}
        response = client.patch("/api/auth/me", json=update_data, headers={"Authorization": f"Bearer {access_token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"
    
    def test_update_me_email_conflict(self, client):
        """Test updating email to one that's already taken fails."""
        # Register two users
        user1_data = {
            "email": "user1@example.com",
            "password": "securepassword123",
            "full_name": "User One"
        }
        client.post("/api/auth/register", json=user1_data)
        
        user2_data = {
            "email": "user2@example.com",
            "password": "securepassword123",
            "full_name": "User Two"
        }
        client.post("/api/auth/register", json=user2_data)
        
        # Login as user2
        login_response = client.post("/api/auth/login", data={
            "username": user2_data["email"],
            "password": user2_data["password"]
        })
        access_token = login_response.json()["access_token"]
        
        # Try to update email to user1's email
        update_data = {"email": user1_data["email"]}
        response = client.patch("/api/auth/me", json=update_data, headers={"Authorization": f"Bearer {access_token}"})
        assert response.status_code == 409


class TestPasswordHashing:
    """Tests for password hashing functionality."""
    
    def test_password_not_stored_plaintext(self, client, db):
        """Test that passwords are not stored in plaintext."""
        from app.models.models import User
        from app.core.security import verify_password
        
        user_data = {
            "email": "test@example.com",
            "password": "securepassword123",
            "full_name": "Test User"
        }
        client.post("/api/auth/register", json=user_data)
        
        # Check database
        user = db.query(User).filter(User.email == user_data["email"]).first()
        assert user is not None
        assert user.hashed_password != user_data["password"]
        assert user.hashed_password.startswith("$2")  # bcrypt hash prefix
        
        # Verify password can be checked
        assert verify_password(user_data["password"], user.hashed_password)


class TestLastLoginUpdate:
    """Tests for last login timestamp update."""
    
    def test_last_login_updated_on_login(self, client, db):
        """Test that last_login is updated when user logs in."""
        from app.models.models import User
        
        user_data = {
            "email": "test@example.com",
            "password": "securepassword123",
            "full_name": "Test User"
        }
        client.post("/api/auth/register", json=user_data)
        
        # Check initial state
        user = db.query(User).filter(User.email == user_data["email"]).first()
        assert user.last_login is None
        
        # Login
        client.post("/api/auth/login", data={
            "username": user_data["email"],
            "password": user_data["password"]
        })
        
        # Check last_login was updated
        db.refresh(user)
        assert user.last_login is not None
        assert isinstance(user.last_login, datetime)
