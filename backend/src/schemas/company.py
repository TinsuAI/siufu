"""
Shared company schemas for master data management (used by both importers and exporters)
"""
from typing import Generic, List, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field

# Generic type for list items
T = TypeVar('T')


class CompanyListResponse(BaseModel, Generic[T]):
    """Paginated response for company lists"""
    items: List[T]
    total: int = Field(..., description="Total number of items across all pages")
    page: int = Field(..., description="Current page number (1-indexed)")
    limit: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")


class DuplicatePair(BaseModel):
    """Pair of potentially duplicate companies"""
    company1: BaseModel
    company2: BaseModel
    similarity: float = Field(..., ge=0.0, le=1.0, description="Similarity score (0.0-1.0)")
    reason: str = Field(..., description="Explanation of why these are potential duplicates")


class MergeRequest(BaseModel):
    """Request to merge two companies"""
    keep_id: UUID = Field(..., description="ID of the company to keep")
    merge_id: UUID = Field(..., description="ID of the company to merge and delete")
