from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List


# User schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: str
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Token schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[datetime] = None
    type: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# API Key schemas
class ApiKeyBase(BaseModel):
    key_name: str
    platform_id: str


class ApiKeyCreate(ApiKeyBase):
    api_key: str
    expires_at: Optional[datetime] = None


class ApiKeyUpdate(BaseModel):
    key_name: Optional[str] = None
    is_active: Optional[bool] = None


class ApiKeyResponse(ApiKeyBase):
    id: str
    user_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Platform schemas
class PlatformBase(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None


class PlatformCreate(PlatformBase):
    supports_scraping: bool = False
    supports_api: bool = True


class PlatformResponse(PlatformBase):
    id: str
    is_active: bool
    supports_scraping: bool
    supports_api: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Auth schemas
class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRegister(UserCreate):
    pass


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


# Competitor Profile schemas
class CompetitorProfileBase(BaseModel):
    platform_id: str
    username: str
    display_name: Optional[str] = None
    profile_url: Optional[str] = None


class CompetitorProfileCreate(CompetitorProfileBase):
    pass


class CompetitorProfileResponse(CompetitorProfileBase):
    id: str
    user_id: str
    follower_count: Optional[int] = None
    following_count: Optional[int] = None
    post_count: Optional[int] = None
    bio: Optional[str] = None
    is_active: bool
    last_scraped_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Post schemas
class PostBase(BaseModel):
    content: Optional[str] = None
    media_urls: Optional[List[str]] = None


class PostResponse(PostBase):
    id: str
    competitor_id: str
    platform_id: str
    external_id: str
    posted_at: datetime
    like_count: int
    reply_count: int
    repost_count: int
    view_count: Optional[int] = None
    is_viral: bool
    viral_score: Optional[float] = None
    scraped_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


# Scheduled Post schemas
class ScheduledPostBase(BaseModel):
    platform_id: str
    content: str
    media_urls: Optional[List[str]] = None
    scheduled_at: datetime


class ScheduledPostCreate(ScheduledPostBase):
    pass


class ScheduledPostUpdate(BaseModel):
    content: Optional[str] = None
    media_urls: Optional[List[str]] = None
    scheduled_at: Optional[datetime] = None
    status: Optional[str] = None


class ScheduledPostResponse(ScheduledPostBase):
    id: str
    user_id: str
    status: str
    published_at: Optional[datetime] = None
    external_post_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Analytics schemas
class AnalyticsEventBase(BaseModel):
    post_id: str
    event_type: str
    metric_name: str
    metric_value: int


class AnalyticsEventCreate(AnalyticsEventBase):
    pass


class AnalyticsEventResponse(AnalyticsEventBase):
    id: str
    recorded_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True
