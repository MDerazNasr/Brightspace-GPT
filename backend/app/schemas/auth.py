# backend/app/schemas/auth.py
"""
Pydantic schemas for authentication endpoints.
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime

class UserResponse(BaseModel):
    """User information response schema."""
    id: str
    email: str
    full_name: Optional[str] = None
    brightspace_user_id: Optional[str] = None
    is_verified: bool = False
    preferences: Dict[str, Any] = {}
    created_at: datetime
    
    class Config:
        from_attributes = True

class LoginResponse(BaseModel):
    """Login response schema."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class AuthStatusResponse(BaseModel):
    """Authentication status response."""
    authenticated: bool
    brightspace_connected: bool
    user_id: Optional[str] = None

class LoginInitResponse(BaseModel):
    """Login initiation response."""
    auth_url: str
    state: str
    message: str