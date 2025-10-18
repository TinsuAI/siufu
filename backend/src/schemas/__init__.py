"""
Pydantic schemas package
"""
from src.schemas.common import ErrorResponse, PaginatedResponse
from src.schemas.user import UserBase, UserCreate, UserUpdate, UserResponse
from src.schemas.declaration import (
    DeclarationStatus,
    DeclarationBase,
    DeclarationCreate,
    DeclarationUpdate,
    DeclarationResponse,
)

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
