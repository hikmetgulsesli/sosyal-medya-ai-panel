"""Schemas for AI content generation."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


# AI Generation Request Schemas
class GeneratePostRequest(BaseModel):
    """Request to generate a single post."""
    topic: str = Field(..., min_length=1, max_length=500, description="Topic or subject for the post")
    tone: str = Field(default="professional", description="Tone of voice: professional, casual, witty, inspirational, educational, promotional")
    max_length: int = Field(default=280, ge=50, le=2000, description="Maximum character length")
    context: Optional[str] = Field(default=None, description="Additional context for generation")
    template_id: Optional[str] = Field(default=None, description="Optional template ID to use")


class GenerateThreadRequest(BaseModel):
    """Request to generate a thread."""
    topic: str = Field(..., min_length=1, max_length=500, description="Topic or subject for the thread")
    tone: str = Field(default="professional", description="Tone of voice")
    num_posts: int = Field(default=5, ge=2, le=20, description="Number of posts in the thread")
    context: Optional[str] = Field(default=None, description="Additional context for generation")
    template_id: Optional[str] = Field(default=None, description="Optional template ID to use")


class SuggestHashtagsRequest(BaseModel):
    """Request to suggest hashtags."""
    content: str = Field(..., min_length=1, max_length=2000, description="Content to generate hashtags for")
    count: int = Field(default=5, ge=1, le=30, description="Number of hashtags to suggest")


# AI Generation Response Schemas
class AIProviderInfo(BaseModel):
    """Information about the AI provider used."""
    provider: str = Field(..., description="Provider name: minimax, openai, or none")
    model: str = Field(..., description="Model name used")
    tokens_used: Optional[int] = Field(default=None, description="Number of tokens used")


class GeneratePostResponse(BaseModel):
    """Response for single post generation."""
    content: str = Field(..., description="Generated post content")
    provider: AIProviderInfo
    char_count: int = Field(..., description="Character count of generated content")
    estimated_read_time: str = Field(default="< 1 min", description="Estimated read time")


class ThreadPost(BaseModel):
    """Single post in a thread."""
    number: int = Field(..., description="Post number in thread")
    content: str = Field(..., description="Post content")
    char_count: int = Field(..., description="Character count")


class GenerateThreadResponse(BaseModel):
    """Response for thread generation."""
    posts: List[ThreadPost] = Field(..., description="List of posts in the thread")
    provider: AIProviderInfo
    total_posts: int = Field(..., description="Total number of posts")


class SuggestHashtagsResponse(BaseModel):
    """Response for hashtag suggestions."""
    hashtags: List[str] = Field(..., description="List of suggested hashtags")
    provider: AIProviderInfo


# Content Template Schemas
class ContentTemplateBase(BaseModel):
    """Base schema for content templates."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    template_type: str = Field(..., description="Type: post, thread, or hashtag_suggestions")
    tone: str = Field(default="professional")
    prompt_template: str = Field(..., min_length=10, max_length=2000)
    max_length: int = Field(default=280, ge=50, le=2000)


class ContentTemplateCreate(ContentTemplateBase):
    """Schema for creating a content template."""
    pass


class ContentTemplateUpdate(BaseModel):
    """Schema for updating a content template."""
    name: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    tone: Optional[str] = Field(default=None)
    prompt_template: Optional[str] = Field(default=None, max_length=2000)
    max_length: Optional[int] = Field(default=None, ge=50, le=2000)
    is_active: Optional[bool] = Field(default=None)


class ContentTemplateResponse(ContentTemplateBase):
    """Schema for content template response."""
    id: str
    user_id: str
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ContentTemplateList(BaseModel):
    """Schema for listing content templates."""
    templates: List[ContentTemplateResponse]
    total: int


# AI Service Status
class AIServiceStatus(BaseModel):
    """Status of AI service providers."""
    primary_provider: str = Field(..., description="Primary provider name")
    primary_available: bool = Field(..., description="Whether primary provider is available")
    fallback_provider: str = Field(..., description="Fallback provider name")
    fallback_available: bool = Field(..., description="Whether fallback provider is available")
    status: str = Field(..., description="Overall status: ready, fallback, or unavailable")
