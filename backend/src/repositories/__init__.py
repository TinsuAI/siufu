"""
Repository package for database access layer
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.repositories.base import BaseRepository
from src.repositories.user_repository import UserRepository
from src.repositories.declaration_repository import DeclarationRepository


def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """Dependency injection for UserRepository"""
    return UserRepository(db)


def get_declaration_repository(db: AsyncSession = Depends(get_db)) -> DeclarationRepository:
    """Dependency injection for DeclarationRepository"""
    return DeclarationRepository(db)


__all__ = [
    "BaseRepository",
    "UserRepository",
    "DeclarationRepository",
    "get_user_repository",
    "get_declaration_repository",
]
