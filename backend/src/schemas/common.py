"""
Common Pydantic schemas for API responses
"""
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar('T')


class ErrorResponse(BaseModel):
    """RFC 7807 Problem Details error response"""
    type: str
    title: str
    status: int
    detail: str
    errors: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "/errors/validation-error",
                "title": "Validation Error",
                "status": 422,
                "detail": "Request validation failed",
                "errors": {
                    "email": ["Invalid email format"]
                }
            }
        }
    )


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper"""
    items: List[T]
    total: int
    skip: int
    limit: int

    model_config = ConfigDict(from_attributes=True)
