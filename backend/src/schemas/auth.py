"""
Authentication request and response schemas
"""
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Request schema for user login"""

    email: EmailStr
    password: str = Field(..., min_length=8)


class RegisterRequest(BaseModel):
    """Request schema for user registration"""

    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    full_name: str = Field(..., min_length=1, description="User's full name")


class User(BaseModel):
    """User profile schema"""

    id: str
    email: str
    full_name: str
    role: str  # 'processor' | 'admin'
    is_active: bool
    organization_id: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True  # Enable ORM mode for SQLAlchemy models


class LoginResponse(BaseModel):
    """Response schema for successful login"""

    user: User
    access_token: str
    token_type: str = "bearer"
