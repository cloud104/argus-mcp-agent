# app/auth/models.py
"""Pydantic models for authentication and authorization."""

from typing import Optional, Literal
from pydantic import BaseModel, EmailStr, Field


class User(BaseModel):
    """User model for API responses."""
    username: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Literal["admin", "developer", "viewer"] = "viewer"
    disabled: bool = False


class UserInDB(User):
    """User model with hashed password for database storage."""
    hashed_password: str


class UserCreate(BaseModel):
    """Model for user creation requests."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None
    password: str = Field(..., min_length=8)
    role: Literal["admin", "developer", "viewer"] = "viewer"


class UserLogin(BaseModel):
    """Model for login requests."""
    username: str
    password: str


class Token(BaseModel):
    """Model for token responses."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Model for decoded token data."""
    username: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None
    type: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    """Model for refresh token requests."""
    refresh_token: str


class PasswordChange(BaseModel):
    """Model for password change requests."""
    old_password: str
    new_password: str = Field(..., min_length=8)
