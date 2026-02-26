from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# User schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None


class UserResponse(UserBase):
    id: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


# Token schemas
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    type: Optional[str] = None
    exp: Optional[datetime] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# Login schema
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# API Key schemas
class ApiKeyBase(BaseModel):
    key_name: str = Field(..., max_length=100)
    platform_id: str


class ApiKeyCreate(ApiKeyBase):
    api_key_value: str
    expires_at: Optional[datetime] = None


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


class ApiKeyListResponse(BaseModel):
    id: str
    key_name: str
    platform_id: str
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Platform schemas
class PlatformBase(BaseModel):
    name: str = Field(..., max_length=50)
    display_name: str = Field(..., max_length=100)
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


# Error response schema
class ErrorResponse(BaseModel):
    error: dict
    code: str
    message: str
    details: Optional[list] = None
