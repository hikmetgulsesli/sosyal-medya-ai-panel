from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ScheduledPostBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    media_urls: Optional[str] = None


class ScheduledPostCreate(ScheduledPostBase):
    platform_id: str
    scheduled_at: datetime


class ScheduledPostUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1, max_length=2000)
    media_urls: Optional[str] = None
    scheduled_at: Optional[datetime] = None


class ScheduledPostResponse(ScheduledPostBase):
    id: str
    user_id: str
    platform_id: str
    platform_name: Optional[str] = None
    scheduled_at: datetime
    status: str
    published_at: Optional[datetime] = None
    external_post_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScheduledPostListResponse(BaseModel):
    data: List[ScheduledPostResponse]
    meta: dict


class PublishResponse(BaseModel):
    success: bool
    message: str
    external_post_id: Optional[str] = None


class OptimalTimeRequest(BaseModel):
    platform_id: str
    days_ahead: int = Field(default=7, ge=1, le=30)


class OptimalTimeSlot(BaseModel):
    datetime: datetime
    score: float
    reason: str


class OptimalTimeResponse(BaseModel):
    platform_id: str
    optimal_slots: List[OptimalTimeSlot]
