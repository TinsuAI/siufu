"""
Base repository pattern for async database operations
"""
from typing import Generic, List, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """
    Base repository with common CRUD operations

    All repositories should extend this class for consistency
    """

    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get_by_id(self, id: UUID) -> Optional[ModelType]:
        """
        Get a single record by ID

        Args:
            id: UUID primary key

        Returns:
            Model instance or None if not found
        """
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalars().first()

    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[dict] = None
    ) -> List[ModelType]:
        """
        Get multiple records with pagination

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Optional dict of filter conditions

        Returns:
            List of model instances
        """
        query = select(self.model)

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, obj_in: dict) -> ModelType:
        """
        Create a new record

        Args:
            obj_in: Dictionary of model fields

        Returns:
            Created model instance
        """
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(self, id: UUID, obj_in: dict) -> Optional[ModelType]:
        """
        Update an existing record

        Args:
            id: UUID primary key
            obj_in: Dictionary of fields to update

        Returns:
            Updated model instance or None if not found
        """
        db_obj = await self.get_by_id(id)
        if db_obj:
            for field, value in obj_in.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)
            await self.db.flush()
            await self.db.refresh(db_obj)
        return db_obj

    async def delete(self, id: UUID) -> bool:
        """
        Delete a record (soft delete if deleted_at column exists, otherwise hard delete)

        Args:
            id: UUID primary key

        Returns:
            True if deleted, False if not found
        """
        db_obj = await self.get_by_id(id)
        if db_obj:
            if hasattr(db_obj, 'deleted_at'):
                # Soft delete
                db_obj.deleted_at = func.now()
                await self.db.flush()
            else:
                # Hard delete
                await self.db.delete(db_obj)
                await self.db.flush()
            return True
        return False

    async def count(self, filters: Optional[dict] = None) -> int:
        """
        Count records matching filters

        Args:
            filters: Optional dict of filter conditions

        Returns:
            Count of matching records
        """
        query = select(func.count(self.model.id))

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)

        result = await self.db.execute(query)
        return result.scalar_one()
