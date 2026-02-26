from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# Scheduled Post schemas
class ScheduledPostBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000, description="Post content")
    media_urls: Optional[str] = Field(None, max_length=2000, description="Comma-separated media URLs")
    scheduled_at: datetime = Field(..., description="When to publish the post")


class ScheduledPostCreate(ScheduledPostBase):
    platform_id: str = Field(..., description="Platform ID to publish to")


class ScheduledPostUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1, max_length=2000, description="Post content")
    media_urls: Optional[str] = Field(None, max_length=2000, description="Comma-separated media URLs")
    scheduled_at: Optional[datetime] = Field(None, description="When to publish the post")
    platform_id: Optional[str] = Field(None, description="Platform ID to publish to")


class ScheduledPostResponse(BaseModel):
    id: str
    user_id: str
    platform_id: str
    content: str
    media_urls: Optional[str] = None
    scheduled_at: datetime
    status: str  # pending, published, failed
    published_at: Optional[datetime] = None
    external_post_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScheduledPostListResponse(BaseModel):
    id: str
    platform_id: str
    content: str
    media_urls: Optional[str] = None
    scheduled_at: datetime
    status: str
    published_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ScheduledPostDetailResponse(ScheduledPostResponse):
    platform_name: Optional[str] = None


class PublishResponse(BaseModel):
    success: bool
    message: str
    external_post_id: Optional[str] = None


class ScheduledPostListWithMeta(BaseModel):
    data: List[ScheduledPostListResponse]
    meta: dict


# Scheduler query parameters
class SchedulerQueryParams(BaseModel):
    status: Optional[str] = Field(None, description="Filter by status: pending, published, failed")
    platform_id: Optional[str] = Field(None, description="Filter by platform ID")
    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page")
