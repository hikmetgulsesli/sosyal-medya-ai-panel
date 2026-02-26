"""Schemas for AI content generation."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class PostGenerateRequest(BaseModel):
    """Request schema for generating a single post."""
    topic: str = Field(..., min_length=1, max_length=500, description="Topic or subject for the post")
    tone: str = Field(default="professional", description="Tone of the post (professional, casual, humorous, etc.)")
    platform: str = Field(default="twitter", description="Target platform (twitter, linkedin, instagram, etc.)")
    max_length: int = Field(default=280, ge=50, le=2000, description="Maximum character length")
    context: Optional[str] = Field(None, max_length=2000, description="Additional context for generation")
    template_id: Optional[str] = Field(None, description="Optional template ID to use")


class ThreadGenerateRequest(BaseModel):
    """Request schema for generating a thread."""
    topic: str = Field(..., min_length=1, max_length=500, description="Topic or subject for the thread")
    tone: str = Field(default="professional", description="Tone of the thread")
    num_posts: int = Field(default=5, ge=2, le=20, description="Number of posts in the thread")
    context: Optional[str] = Field(None, max_length=2000, description="Additional context for generation")


class HashtagSuggestRequest(BaseModel):
    """Request schema for hashtag suggestions."""
    content: str = Field(..., min_length=1, max_length=2000, description="Content to suggest hashtags for")
    platform: str = Field(default="twitter", description="Target platform")
    count: int = Field(default=5, ge=1, le=20, description="Number of hashtags to suggest")


class PostGenerateResponse(BaseModel):
    """Response schema for generated post."""
    content: str = Field(..., description="Generated post content")
    provider: str = Field(..., description="AI provider used")
    tokens_used: Optional[int] = Field(None, description="Number of tokens used")
    character_count: int = Field(..., description="Character count of the generated content")
    platform: str = Field(..., description="Target platform")
    tone: str = Field(..., description="Tone used")


class ThreadGenerateResponse(BaseModel):
    """Response schema for generated thread."""
    posts: List[str] = Field(..., description="List of thread posts")
    provider: str = Field(..., description="AI provider used")
    tokens_used: Optional[int] = Field(None, description="Number of tokens used")
    post_count: int = Field(..., description="Number of posts in the thread")
    platform: str = Field(..., description="Target platform")
    tone: str = Field(..., description="Tone used")


class HashtagSuggestResponse(BaseModel):
    """Response schema for hashtag suggestions."""
    hashtags: List[str] = Field(..., description="List of suggested hashtags")
    provider: str = Field(..., description="AI provider used")
    tokens_used: Optional[int] = Field(None, description="Number of tokens used")


class ContentTemplateBase(BaseModel):
    """Base schema for content templates."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    platform: str = Field(..., min_length=1, max_length=50)
    tone: str = Field(default="professional", min_length=1, max_length=50)
    template_prompt: str = Field(..., min_length=10, max_length=2000)
    max_length: int = Field(default=280, ge=50, le=2000)


class ContentTemplateCreate(ContentTemplateBase):
    """Schema for creating a content template."""
    pass


class ContentTemplateUpdate(BaseModel):
    """Schema for updating a content template."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    platform: Optional[str] = Field(None, min_length=1, max_length=50)
    tone: Optional[str] = Field(None, min_length=1, max_length=50)
    template_prompt: Optional[str] = Field(None, min_length=10, max_length=2000)
    max_length: Optional[int] = Field(None, ge=50, le=2000)
    is_active: Optional[bool] = None


class ContentTemplateResponse(ContentTemplateBase):
    """Response schema for content templates."""
    id: str
    user_id: Optional[str] = None
    is_system: bool
    is_active: bool
    usage_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ContentTemplateListResponse(BaseModel):
    """Response schema for listing content templates."""
    data: List[ContentTemplateResponse]
    meta: dict


class AIGenerationLogResponse(BaseModel):
    """Response schema for AI generation log entry."""
    id: str
    generation_type: str
    platform: str
    generated_content: str
    provider_used: str
    tokens_used: Optional[int]
    tone: Optional[str]
    template_id: Optional[str]
    was_used: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AIGenerationLogListResponse(BaseModel):
    """Response schema for listing AI generation logs."""
    data: List[AIGenerationLogResponse]
    meta: dict


class AIProviderStatus(BaseModel):
    """Schema for AI provider status."""
    providers: List[str] = Field(..., description="List of available providers")
    primary: str = Field(..., description="Primary provider name")
    fallback: str = Field(..., description="Fallback provider name")
