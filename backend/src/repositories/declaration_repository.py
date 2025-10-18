"""
Declaration repository with declaration-specific queries
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.declaration import Declaration, DeclarationStatus
from src.repositories.base import BaseRepository


class DeclarationRepository(BaseRepository[Declaration]):
    """Repository for Declaration model with custom queries"""

    def __init__(self, db: AsyncSession):
        super().__init__(Declaration, db)

    async def get_by_status(
        self,
        status: DeclarationStatus,
        skip: int = 0,
        limit: int = 100
    ) -> List[Declaration]:
        """
        Get declarations by status with pagination

        Args:
            status: Declaration status enum value
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of declarations matching status
        """
        result = await self.db.execute(
            select(Declaration)
            .where(Declaration.status == status)
            .where(Declaration.deleted_at.is_(None))  # Exclude soft-deleted
            .order_by(Declaration.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_draft_data(self, declaration_id: UUID, draft_data: dict) -> Optional[Declaration]:
        """
        Merge partial updates into draft_data JSONB field

        This implements the auto-save functionality for the draft editor.
        Existing draft_data is preserved and only specified fields are updated.

        Args:
            declaration_id: UUID of declaration
            draft_data: Dictionary of fields to merge into draft_data

        Returns:
            Updated declaration or None if not found
        """
        declaration = await self.get_by_id(declaration_id)
        if not declaration:
            return None

        # Merge new data into existing draft_data
        existing_data = declaration.draft_data or {}
        merged_data = {**existing_data, **draft_data}
        declaration.draft_data = merged_data

        await self.db.flush()
        await self.db.refresh(declaration)
        return declaration

    async def get_by_organization(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Declaration]:
        """
        Get all declarations for an organization

        Args:
            organization_id: UUID of organization
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of declarations for the organization
        """
        result = await self.db.execute(
            select(Declaration)
            .where(Declaration.organization_id == organization_id)
            .where(Declaration.deleted_at.is_(None))
            .order_by(Declaration.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
