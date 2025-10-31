"""
User repository with user-specific queries
"""
from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.repositories.base import BaseRepository
from src.core.security import get_password_hash
from src.schemas.auth import RegisterRequest


class UserRepository(BaseRepository[User]):
    """Repository for User model with custom queries"""

    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address

        Args:
            email: User email address

        Returns:
            User instance or None if not found
        """
        result = await self.db.execute(
            select(User).where(User.email == email, User.is_active == True)
        )
        return result.scalars().first()

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Get user by ID

        Args:
            user_id: User UUID

        Returns:
            User instance or None if not found
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id, User.is_active == True)
        )
        return result.scalars().first()

    async def create(self, user_data: RegisterRequest, organization_id: UUID) -> User:
        """
        Create new user with hashed password

        Args:
            user_data: RegisterRequest schema with email, password, full_name
            organization_id: UUID of organization

        Returns:
            Created user instance
        """
        hashed_password = get_password_hash(user_data.password)

        user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            organization_id=organization_id,
            role="processor",  # Default role
            is_active=True
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return user
