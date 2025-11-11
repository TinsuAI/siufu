"""
Pydantic schemas for Correction API (Story 3.6 Expansion)
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CorrectionCreate(BaseModel):
    """Schema for creating a new correction"""
    field_name: str = Field(..., description="Dot-notation field path (e.g., 'importer.tax_code')")
    original_value: Optional[str] = Field(None, description="Original extracted value (null if not extracted)")
    corrected_value: str = Field(..., description="User-corrected value")
    correction_category: str = Field(
        ...,
        description="Category: 'AI Extraction Error', 'Wrong HS Code', 'Calculation Error', 'Missing Data', 'Format Issue', 'Other'"
    )
    expected_value: str = Field(..., max_length=500, description="Required: What the correct value should be")
    notes: str = Field(..., max_length=500, description="Required: Explanation of why this is wrong and where the correct value is located")
    screenshots: Optional[list[str]] = Field(None, description="Optional: URLs of uploaded screenshot images (max 3)")


class CorrectionResponse(BaseModel):
    """Schema for correction response"""
    id: UUID
    declaration_id: UUID
    field_name: str
    original_value: Optional[str]
    corrected_value: str
    correction_category: str
    expected_value: str
    notes: str
    screenshots: Optional[list[str]]
    user_id: UUID
    user_name: str  # Joined from User table
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class CorrectionListResponse(BaseModel):
    """Schema for list of corrections"""
    corrections: list[CorrectionResponse]
    count: int
