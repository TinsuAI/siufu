"""
Authentication request and response schemas
"""
import re

from pydantic import BaseModel, EmailStr, Field, field_validator


class LoginRequest(BaseModel):
    """Request schema for user login"""

    email: EmailStr
    password: str = Field(..., min_length=8)


class RegisterRequest(BaseModel):
    """Request schema for user registration"""

    email: EmailStr
    password: str = Field(
        ...,
        min_length=8,
        description="Password must be at least 8 characters with uppercase, lowercase, number, and special character"
    )
    full_name: str = Field(..., min_length=1, description="User's full name")

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        """Validate password meets complexity requirements"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)")
        return v


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
