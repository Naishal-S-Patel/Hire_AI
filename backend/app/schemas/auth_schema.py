"""
Pydantic schemas for Auth endpoints.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class TokenPayload(BaseModel):
    """JWT token pair returned to client."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class SignupRequest(BaseModel):
    """User registration."""
    email: str
    password: str
    full_name: Optional[str] = None
    role: Optional[str] = "USER"  # HR | USER


class LoginRequest(BaseModel):
    """Email / password login."""
    email: str
    password: str


class RefreshRequest(BaseModel):
    """Refresh-token request."""
    refresh_token: str


class GoogleUser(BaseModel):
    """Data extracted from Google OAuth2 callback."""
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None


class UserOut(BaseModel):
    """User info returned after signup/login."""
    email: str
    full_name: Optional[str] = None
    auth_provider: str = "local"
    role: str = "USER"

    model_config = {"from_attributes": True}

