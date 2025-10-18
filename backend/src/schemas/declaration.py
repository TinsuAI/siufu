"""
Declaration Pydantic schemas for API request/response
"""
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class DeclarationStatus(str, Enum):
    """Declaration status enumeration"""
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    PROCESSING_OCR = "PROCESSING_OCR"
    PROCESSING_LLM = "PROCESSING_LLM"
    VALIDATING = "VALIDATING"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class DeclarationBase(BaseModel):
    """Base declaration schema"""
    status: DeclarationStatus = DeclarationStatus.UPLOADED


class DeclarationCreate(DeclarationBase):
    """Schema for creating a new declaration"""
    organization_id: UUID
    created_by_user_id: UUID


class DeclarationUpdate(BaseModel):
    """Schema for updating declaration draft data"""
    draft_data: Dict[str, Any] = Field(description="Partial updates to draft data (will be merged)")


class DeclarationStatusResponse(BaseModel):
    """Schema for declaration status polling response"""
    id: UUID
    status: DeclarationStatus
    progress: float = Field(ge=0.0, le=1.0, description="Processing progress from 0.0 to 1.0")
    processing_error: Optional[str] = None
    celery_task_id: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "PROCESSING_LLM",
                "progress": 0.4,
                "processing_error": None,
                "celery_task_id": "abc123-def456-ghi789"
            }
        }
    )


class DeclarationResponse(DeclarationBase):
    """Schema for declaration response"""
    id: UUID
    uploaded_files: Optional[Dict[str, str]] = None
    extracted_data: Optional[Dict[str, Any]] = None
    draft_data: Optional[Dict[str, Any]] = None
    validation_warnings: Optional[List[Dict[str, Any]]] = None
    confidence_scores: Optional[Dict[str, float]] = None
    processing_progress: Optional[float] = None
    processing_error: Optional[str] = None
    celery_task_id: Optional[str] = None
    approved_by_user_id: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    organization_id: UUID
    created_by_user_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "323e4567-e89b-12d3-a456-426614174000",
                "status": "READY_FOR_REVIEW",
                "uploaded_files": {
                    "invoice": "/uploads/invoice_123.pdf",
                    "packing_list": "/uploads/packing_123.pdf"
                },
                "draft_data": {
                    "importer_name": "ABC Company",
                    "total_value": 10000.50
                },
                "processing_progress": 1.0,
                "organization_id": "223e4567-e89b-12d3-a456-426614174000",
                "created_by_user_id": "123e4567-e89b-12d3-a456-426614174000",
                "created_at": "2025-10-18T10:00:00Z",
                "updated_at": "2025-10-18T10:30:00Z"
            }
        }
    )
