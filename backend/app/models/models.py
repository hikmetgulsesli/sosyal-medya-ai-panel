import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, ForeignKey, Float, Index
from sqlalchemy.orm import relationship

from app.db.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    api_keys = relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")
    competitor_profiles = relationship("CompetitorProfile", back_populates="user", cascade="all, delete-orphan")
    scheduled_posts = relationship("ScheduledPost", back_populates="user", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_users_email_active', 'email', 'is_active'),
    )


class ApiKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    platform_id = Column(String(36), ForeignKey("platforms.id", ondelete="CASCADE"), nullable=False, index=True)
    key_name = Column(String(100), nullable=False)
    encrypted_key = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    platform = relationship("Platform", back_populates="api_keys")
    
    __table_args__ = (
        Index('ix_api_keys_user_platform', 'user_id', 'platform_id'),
    )


class Platform(Base):
    __tablename__ = "platforms"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    supports_scraping = Column(Boolean, default=False, nullable=False)
    supports_api = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    api_keys = relationship("ApiKey", back_populates="platform")
    competitor_profiles = relationship("CompetitorProfile", back_populates="platform")
    posts = relationship("Post", back_populates="platform")
    scheduled_posts = relationship("ScheduledPost", back_populates="platform")


class CompetitorProfile(Base):
    __tablename__ = "competitor_profiles"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    platform_id = Column(String(36), ForeignKey("platforms.id", ondelete="CASCADE"), nullable=False, index=True)
    username = Column(String(100), nullable=False, index=True)
    display_name = Column(String(255), nullable=True)
    profile_url = Column(String(500), nullable=True)
    follower_count = Column(Integer, nullable=True)
    following_count = Column(Integer, nullable=True)
    post_count = Column(Integer, nullable=True)
    bio = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    last_scraped_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="competitor_profiles")
    platform = relationship("Platform", back_populates="competitor_profiles")
    posts = relationship("Post", back_populates="competitor", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_competitor_profiles_user_platform', 'user_id', 'platform_id'),
        Index('ix_competitor_profiles_username_platform', 'username', 'platform_id'),
    )


class Post(Base):
    __tablename__ = "posts"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    competitor_id = Column(String(36), ForeignKey("competitor_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    platform_id = Column(String(36), ForeignKey("platforms.id", ondelete="CASCADE"), nullable=False, index=True)
    external_id = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=True)
    media_urls = Column(Text, nullable=True)
    posted_at = Column(DateTime, nullable=False)
    like_count = Column(Integer, default=0, nullable=False)
    reply_count = Column(Integer, default=0, nullable=False)
    repost_count = Column(Integer, default=0, nullable=False)
    view_count = Column(Integer, nullable=True)
    is_viral = Column(Boolean, default=False, nullable=False)
    viral_score = Column(Float, nullable=True)
    scraped_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    competitor = relationship("CompetitorProfile", back_populates="posts")
    platform = relationship("Platform", back_populates="posts")
    analytics = relationship("AnalyticsEvent", back_populates="post", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_posts_platform_external', 'platform_id', 'external_id'),
        Index('ix_posts_posted_at', 'posted_at'),
        Index('ix_posts_viral', 'is_viral', 'viral_score'),
    )


class ScheduledPost(Base):
    __tablename__ = "scheduled_posts"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    platform_id = Column(String(36), ForeignKey("platforms.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    media_urls = Column(Text, nullable=True)
    scheduled_at = Column(DateTime, nullable=False)
    status = Column(String(20), default="pending", nullable=False)
    priority = Column(Integer, default=2, nullable=False)  # 1=LOW, 2=NORMAL, 3=HIGH, 4=URGENT
    published_at = Column(DateTime, nullable=True)
    external_post_id = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="scheduled_posts")
    platform = relationship("Platform", back_populates="scheduled_posts")
    
    __table_args__ = (
        Index('ix_scheduled_posts_user_status', 'user_id', 'status'),
        Index('ix_scheduled_posts_scheduled', 'scheduled_at', 'status'),
        Index('ix_scheduled_posts_priority', 'priority'),
    )


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    post_id = Column(String(36), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)
    metric_name = Column(String(50), nullable=False)
    metric_value = Column(Integer, nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    post = relationship("Post", back_populates="analytics")
    
    __table_args__ = (
        Index('ix_analytics_events_post_type', 'post_id', 'event_type'),
        Index('ix_analytics_events_recorded', 'recorded_at'),
    )
