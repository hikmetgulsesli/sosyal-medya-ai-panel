import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.models.models import Platform as PlatformModel
from main import app

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def seed_test_platforms(db):
    """Seed platforms for testing."""
    platforms = [
        PlatformModel(
            name="twitter",
            display_name="Twitter / X",
            description="Twitter (now X) social media platform",
            is_active=True,
            supports_scraping=True,
            supports_api=True,
        ),
        PlatformModel(
            name="linkedin",
            display_name="LinkedIn",
            description="Professional networking platform",
            is_active=True,
            supports_scraping=True,
            supports_api=True,
        ),
        PlatformModel(
            name="instagram",
            display_name="Instagram",
            description="Photo and video sharing platform",
            is_active=True,
            supports_scraping=False,
            supports_api=True,
        ),
        PlatformModel(
            name="bluesky",
            display_name="Bluesky",
            description="Decentralized social network using AT Protocol",
            is_active=True,
            supports_scraping=True,
            supports_api=True,
        ),
    ]
    for platform in platforms:
        db.add(platform)
    db.commit()


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
    
    # Seed platforms
    db = TestingSessionLocal()
    seed_test_platforms(db)
    db.close()
    
    with TestClient(app) as c:
        yield c
    
    # Drop tables after test
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed_test_platforms(db)
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
