"""
Pydantic schemas package
"""
from src.schemas.common import ErrorResponse, PaginatedResponse
from src.schemas.declaration import (
    DeclarationBase,
    DeclarationCreate,
    DeclarationResponse,
    DeclarationStatus,
    DeclarationUpdate,
)
from src.schemas.user import UserBase, UserCreate, UserResponse, UserUpdate

__all__ = [
    "ErrorResponse",
    "PaginatedResponse",
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "DeclarationStatus",
    "DeclarationBase",
    "DeclarationCreate",
    "DeclarationUpdate",
    "DeclarationResponse",
]
