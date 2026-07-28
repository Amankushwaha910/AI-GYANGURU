"""
User and Profile schemas.
"""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class ProfileResponse(BaseModel):
    """Public profile data."""
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    education_level: Optional[str] = None
    exam_target: Optional[str] = None
    preferred_language: str = "en"

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    """Public user data returned from API responses."""
    id: uuid.UUID
    email: EmailStr
    role: UserRole
    is_active: bool
    is_email_verified: bool
    created_at: datetime
    profile: Optional[ProfileResponse] = None

    model_config = {"from_attributes": True}


class ProfileUpdateRequest(BaseModel):
    """Schema for updating user profile."""
    full_name: Optional[str] = Field(None, max_length=255)
    bio: Optional[str] = Field(None, max_length=1000)
    education_level: Optional[str] = Field(None, max_length=100)
    exam_target: Optional[str] = Field(None, max_length=100)
    preferred_language: Optional[str] = Field(None, max_length=10)
