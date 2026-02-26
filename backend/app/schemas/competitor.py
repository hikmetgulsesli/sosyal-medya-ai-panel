"""Competitor schemas."""
from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import Optional
from datetime import datetime
from app.core.constants import Platform


class CompetitorBase(BaseModel):
    """Base competitor schema."""
    name: str = Field(..., min_length=1, max_length=255)
    platform: Platform
    handle: str = Field(..., min_length=1, max_length=100)
    url: HttpUrl
    description: Optional[str] = Field(None, max_length=1000)

    @field_validator('handle')
    @classmethod
    def validate_handle(cls, v: str, info) -> str:
        """Validate handle based on platform rules."""
        platform = info.data.get('platform')
        
        if platform == Platform.TWITTER:
            if len(v) > 15:
                raise ValueError("Twitter handle must be 15 characters or less")
            if not v.replace('_', '').isalnum():
                raise ValueError("Twitter handle can only contain letters, numbers, and underscores")
        
        elif platform == Platform.INSTAGRAM:
            if len(v) > 30:
                raise ValueError("Instagram handle must be 30 characters or less")
            if not v.replace('_', '').replace('.', '').isalnum():
                raise ValueError("Instagram handle can only contain letters, numbers, underscores, and periods")
        
        elif platform == Platform.LINKEDIN:
            if len(v) > 100:
                raise ValueError("LinkedIn handle must be 100 characters or less")
        
        elif platform == Platform.BLUESKY:
            if '.' not in v:
                raise ValueError("Bluesky handle must include a domain (e.g., user.bsky.social)")
        
        return v

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: HttpUrl, info) -> HttpUrl:
        """Validate URL matches platform."""
        platform = info.data.get('platform')
        url_str = str(v).lower()
        
        if platform == Platform.TWITTER:
            if 'twitter.com' not in url_str and 'x.com' not in url_str:
                raise ValueError("Twitter URL must contain twitter.com or x.com")
        
        elif platform == Platform.LINKEDIN:
            if 'linkedin.com' not in url_str:
                raise ValueError("LinkedIn URL must contain linkedin.com")
        
        elif platform == Platform.INSTAGRAM:
            if 'instagram.com' not in url_str:
                raise ValueError("Instagram URL must contain instagram.com")
        
        elif platform == Platform.BLUESKY:
            if 'bsky.app' not in url_str:
                raise ValueError("Bluesky URL must contain bsky.app")
        
        return v


class CompetitorCreate(CompetitorBase):
    """Schema for creating a competitor."""
    pass


class CompetitorUpdate(BaseModel):
    """Schema for updating a competitor."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    platform: Optional[Platform] = None
    handle: Optional[str] = Field(None, min_length=1, max_length=100)
    url: Optional[HttpUrl] = None
    description: Optional[str] = Field(None, max_length=1000)


class CompetitorInDB(CompetitorBase):
    """Schema for competitor as stored in database."""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CompetitorResponse(BaseModel):
    """Response schema for single competitor."""
    data: CompetitorInDB


class CompetitorListResponse(BaseModel):
    """Response schema for competitor list."""
    data: list[CompetitorInDB]
    meta: dict
