"""
Auth request/response schemas.
"""
import re
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    """Schema for new user registration."""
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    full_name: Optional[str] = Field(None, max_length=255, description="User's display name")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        return v


class LoginRequest(BaseModel):
    """Schema for email/password login."""
    email: EmailStr = Field(..., description="Registered email address")
    password: str = Field(..., description="Account password")


class TokenResponse(BaseModel):
    """JWT token pair returned on successful authentication."""
    access_token: str = Field(..., description="Short-lived JWT access token")
    refresh_token: str = Field(..., description="Long-lived JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")


class RefreshRequest(BaseModel):
    """Schema for refreshing an access token."""
    refresh_token: str = Field(..., description="Valid refresh token")


class GoogleAuthRequest(BaseModel):
    """Schema for Google OAuth code exchange."""
    code: str = Field(..., description="Google OAuth authorization code")


class PasswordChangeRequest(BaseModel):
    """Schema for changing user password."""
    current_password: str = Field(..., description="Current password for verification")
    new_password: str = Field(..., min_length=8, description="New password")

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        return v
