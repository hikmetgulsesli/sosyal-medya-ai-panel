"""Scheduler schemas for post scheduling."""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

from app.core.constants import Platform


class PostStatus(str, Enum):
    """Status of a scheduled post."""
    PENDING = "pending"
    QUEUED = "queued"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Priority(int, Enum):
    """Priority levels for scheduled posts."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class ScheduledPostBase(BaseModel):
    """Base schema for scheduled posts."""
    platform: Platform
    content: str = Field(..., min_length=1, max_length=3000)
    media_urls: Optional[List[str]] = Field(None, max_length=4)
    scheduled_at: datetime
    priority: Priority = Priority.NORMAL

    @field_validator('content')
    @classmethod
    def validate_content_length(cls, v: str, info) -> str:
        """Validate content length based on platform."""
        platform = info.data.get('platform')
        
        if platform == Platform.TWITTER and len(v) > 280:
            raise ValueError("Twitter posts must be 280 characters or less")
        elif platform == Platform.BLUESKY and len(v) > 300:
            raise ValueError("Bluesky posts must be 300 characters or less")
        
        return v


class ScheduledPostCreate(ScheduledPostBase):
    """Schema for creating a scheduled post."""
    pass


class ScheduledPostUpdate(BaseModel):
    """Schema for updating a scheduled post."""
    content: Optional[str] = Field(None, min_length=1, max_length=3000)
    media_urls: Optional[List[str]] = Field(None, max_length=4)
    scheduled_at: Optional[datetime] = None
    priority: Optional[Priority] = None
    status: Optional[PostStatus] = None


class ScheduledPostInDB(ScheduledPostBase):
    """Schema for scheduled post as stored in database."""
    id: str
    user_id: str
    status: PostStatus
    published_at: Optional[datetime] = None
    external_post_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScheduledPostResponse(BaseModel):
    """Response schema for single scheduled post."""
    data: ScheduledPostInDB


class ScheduledPostListResponse(BaseModel):
    """Response schema for list of scheduled posts."""
    data: List[ScheduledPostInDB]
    meta: dict


class QueueFilterParams(BaseModel):
    """Query parameters for filtering the queue."""
    status: Optional[PostStatus] = None
    platform: Optional[Platform] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)


class OptimalTimeRequest(BaseModel):
    """Request schema for optimal posting time suggestions."""
    platform: Platform
    content_type: Optional[str] = "text"  # text, image, video, thread


class OptimalTimeSlot(BaseModel):
    """A single optimal time slot suggestion."""
    suggested_time: datetime
    expected_engagement_score: float = Field(..., ge=0, le=100)
    reason: str


class OptimalTimeResponse(BaseModel):
    """Response schema for optimal posting time suggestions."""
    data: List[OptimalTimeSlot]
    platform: Platform
    timezone: str = "UTC"


class PublishImmediatelyRequest(BaseModel):
    """Request schema for immediate publishing."""
    platform: Platform
    content: str = Field(..., min_length=1, max_length=3000)
    media_urls: Optional[List[str]] = Field(None, max_length=4)


class PublishResponse(BaseModel):
    """Response schema for immediate publish."""
    data: ScheduledPostInDB
    message: str = "Post published successfully"


class QueueStats(BaseModel):
    """Queue statistics."""
    total_pending: int
    total_queued: int
    total_published: int
    total_failed: int
    by_platform: dict
    upcoming_posts: List[ScheduledPostInDB]


class QueueStatsResponse(BaseModel):
    """Response schema for queue statistics."""
    data: QueueStats
