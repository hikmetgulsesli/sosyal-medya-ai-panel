import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set test environment before importing app
os.environ["ENVIRONMENT"] = "test"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.models.models import User, Platform
from main import app

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


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def client():
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    with TestClient(app) as c:
        yield c
    
    # Drop tables after test
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_user(db):
    """Create a test user."""
    # Use a pre-computed bcrypt hash to avoid backend issues in tests
    # This hash is for "testpassword123" - generated with bcrypt 4.x
    hashed_password = "$2b$12$tk0kcdk8eQPVIOq8XTWRB.7I/Il1EIniY8N.9Q5ZcyX2N4qM2wKUq"
    user = User(
        email="test@example.com",
        hashed_password=hashed_password,
        full_name="Test User",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_platform(db):
    """Create a test Twitter platform."""
    platform = Platform(
        name="twitter",
        display_name="Twitter/X",
        description="Twitter social media platform",
        is_active=True,
        supports_scraping=True,
        supports_api=True
    )
    db.add(platform)
    db.commit()
    db.refresh(platform)
    return platform
