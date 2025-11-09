"""
Importer Pydantic schemas for master data management
"""
from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ImporterBase(BaseModel):
    """Base schema for importer with common fields"""
    tax_code: str = Field(..., max_length=20, description="Vietnamese MST (10 digits)")
    name: str = Field(..., max_length=255)
    postal_code: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=50)


class ImporterCreate(ImporterBase):
    """Schema for creating a new importer"""
    pass


class ImporterUpdate(BaseModel):
    """Schema for updating an importer (all fields optional)"""
    tax_code: Optional[str] = Field(None, max_length=20)
    name: Optional[str] = Field(None, max_length=255)
    postal_code: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=50)


class ImporterDetail(ImporterBase):
    """Complete importer schema including metadata and audit fields"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name_normalized: str

    # Metadata
    organization_id: UUID
    first_seen_declaration_id: Optional[UUID]
    last_seen_declaration_id: Optional[UUID]
    declaration_count: int

    # Quality tracking
    is_verified: bool
    confidence_score: float
    last_reviewed_by_user_id: Optional[UUID]
    last_reviewed_at: Optional[datetime]

    # Audit
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]


class ImporterListItem(BaseModel):
    """Summary schema for importer list view"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tax_code: str
    name: str
    declaration_count: int
    is_verified: bool
    last_seen_declaration_id: Optional[UUID]
    updated_at: datetime
