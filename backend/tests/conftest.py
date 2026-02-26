import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import Mock, patch

import sys
sys.path.insert(0, '/home/setrox/projects/sosyal-medya-ai-panel/backend')

# Set test database URL BEFORE importing app modules
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

# Clear any cached modules to ensure env var is picked up
modules_to_clear = [k for k in sys.modules.keys() if k.startswith('app') or k == 'main']
for m in modules_to_clear:
    if m in sys.modules:
        del sys.modules[m]

from app.db.database import Base, get_db
from app.models.models import User, Platform


# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client():
    """Create a test client with fresh database."""
    # Import app here to ensure env var is set
    from main import app
    
    # Override the database dependency
    app.dependency_overrides[get_db] = override_get_db
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    with TestClient(app) as c:
        yield c
    
    # Drop tables after test
    Base.metadata.drop_all(bind=engine)
    
    # Clear override
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(client):
    """Create a test user."""
    db = TestingSessionLocal()
    
    # Create user with simple hashed password that we can mock verify
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    yield user
    
    db.close()


@pytest.fixture(scope="function")
def test_platform(client):
    """Create a test platform (Twitter)."""
    db = TestingSessionLocal()
    
    platform = Platform(
        name="twitter",
        display_name="Twitter/X",
        description="Twitter/X social media platform",
        supports_scraping=True,
        supports_api=True
    )
    db.add(platform)
    db.commit()
    db.refresh(platform)
    
    yield platform
    
    db.close()


@pytest.fixture(scope="function")
def auth_token(client, test_user):
    """Get authentication token for test user."""
    with patch("app.core.security.verify_password") as mock_verify:
        mock_verify.return_value = True
        
        login_response = client.post("/api/auth/login", params={
            "email": "test@example.com",
            "password": "any_password"
        })
        
        return login_response.json()["access_token"]
