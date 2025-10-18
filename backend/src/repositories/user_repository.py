"""
User repository with user-specific queries
"""
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.repositories.base import BaseRepository


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
            select(User).where(User.email == email)
        )
        return result.scalars().first()

    async def create_user(self, email: str, password: str, full_name: str, organization_id, role: str = "processor") -> User:
        """
        Create new user with hashed password

        Args:
            email: User email
            password: Plain text password (will be hashed)
            full_name: User's full name
            organization_id: UUID of organization
            role: User role (processor or admin)

        Returns:
            Created user instance
        """
        # TODO: Import and use password hashing from auth service
        # For now, this is a placeholder - actual hashing will be in auth service
        hashed_password = f"hashed_{password}"  # Placeholder

        user_data = {
            "email": email,
            "hashed_password": hashed_password,
            "full_name": full_name,
            "organization_id": organization_id,
            "role": role,
            "is_active": True
        }
        return await self.create(user_data)
