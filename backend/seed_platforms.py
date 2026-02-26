"""
Seed script to populate platforms table with initial data.
Run this after database migrations: python seed_platforms.py
"""
from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine, Base
from app.models.models import Platform


def seed_platforms():
    db = SessionLocal()
    try:
        platforms = [
            Platform(
                name="twitter",
                display_name="Twitter / X",
                description="Twitter (now X) social media platform",
                is_active=True,
                supports_scraping=True,
                supports_api=True,
            ),
            Platform(
                name="linkedin",
                display_name="LinkedIn",
                description="Professional networking platform",
                is_active=True,
                supports_scraping=True,
                supports_api=True,
            ),
            Platform(
                name="instagram",
                display_name="Instagram",
                description="Photo and video sharing platform",
                is_active=True,
                supports_scraping=False,
                supports_api=True,
            ),
            Platform(
                name="bluesky",
                display_name="Bluesky",
                description="Decentralized social network using AT Protocol",
                is_active=True,
                supports_scraping=True,
                supports_api=True,
            ),
        ]
        
        for platform in platforms:
            # Check if platform already exists
            existing = db.query(Platform).filter(Platform.name == platform.name).first()
            if not existing:
                db.add(platform)
                print(f"Added platform: {platform.display_name}")
            else:
                print(f"Platform already exists: {platform.display_name}")
        
        db.commit()
        print("Platform seeding completed!")
    
    finally:
        db.close()


if __name__ == "__main__":
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    seed_platforms()
