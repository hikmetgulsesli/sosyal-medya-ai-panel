import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from app.db.database import Base, get_db
from app.models.models import User, Platform
from app.core.security import get_password_hash


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
def test_user(client):
    """Create a test user."""
    from sqlalchemy.orm import Session
    db = TestingSessionLocal()
    
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
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
    from sqlalchemy.orm import Session
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
