"""
Exporter Pydantic schemas for master data management
"""
from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ExporterBase(BaseModel):
    """Base schema for exporter with common fields"""
    name: str = Field(..., max_length=255)
    country_code: str = Field(..., max_length=2, description="ISO 3166-1 alpha-2 (e.g., 'CN', 'US')")
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    address_line3: Optional[str] = Field(None, max_length=255)


class ExporterCreate(ExporterBase):
    """Schema for creating a new exporter"""
    pass


class ExporterUpdate(BaseModel):
    """Schema for updating an exporter (all fields optional)"""
    name: Optional[str] = Field(None, max_length=255)
    country_code: Optional[str] = Field(None, max_length=2)
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    address_line3: Optional[str] = Field(None, max_length=255)


class ExporterDetail(ExporterBase):
    """Complete exporter schema including metadata and audit fields"""
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


class ExporterListItem(BaseModel):
    """Summary schema for exporter list view"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    country_code: str
    declaration_count: int
    is_verified: bool
    last_seen_declaration_id: Optional[UUID]
    updated_at: datetime
