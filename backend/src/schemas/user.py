"""
User Pydantic schemas for API request/response
"""
from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    role: str = Field(default="processor", pattern="^(processor|admin)$")


class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(min_length=8, description="Password (minimum 8 characters)")
    organization_id: UUID


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[str] = Field(None, pattern="^(processor|admin)$")
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """Schema for user response (excludes hashed_password)"""
    id: UUID
    is_active: bool
    organization_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "full_name": "John Doe",
                "role": "processor",
                "is_active": True,
                "organization_id": "223e4567-e89b-12d3-a456-426614174000",
                "created_at": "2025-10-18T10:00:00Z",
                "updated_at": "2025-10-18T10:00:00Z"
            }
        }
    )
