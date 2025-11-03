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


class UploadedFileMetadata(BaseModel):
    """Schema for uploaded file metadata"""
    file_type: str = Field(description="Type of file (AN, BOL, CO, INVOICE, GOODLIST, TARIFF)")
    filename: str = Field(description="Original filename")
    size: int = Field(description="File size in bytes")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "file_type": "AN",
                "filename": "AN.pdf",
                "size": 2048576
            }
        }
    )


class DeclarationUploadResponse(BaseModel):
    """Schema for declaration upload response"""
    declaration_id: UUID = Field(description="Unique identifier for the declaration")
    status: DeclarationStatus = Field(description="Initial status (UPLOADED)")
    uploaded_files: List[UploadedFileMetadata] = Field(description="List of uploaded file metadata")
    celery_task_id: Optional[str] = Field(
        default=None,
        description="Celery task ID if auto_process=true"
    )
    message: str = Field(description="Success message")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "declaration_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "UPLOADED",
                "uploaded_files": [
                    {"file_type": "AN", "filename": "AN.pdf", "size": 2048576},
                    {"file_type": "BOL", "filename": "BOL.pdf", "size": 1536000},
                    {"file_type": "CO", "filename": "CO.pdf", "size": 1843200},
                    {"file_type": "INVOICE", "filename": "INVOICE.pdf", "size": 3145728},
                    {"file_type": "GOODLIST", "filename": "goodlist1.xls", "size": 102400},
                    {"file_type": "TARIFF", "filename": "EXIM-Tariff.xlsx", "size": 204800}
                ],
                "celery_task_id": None,
                "message": "Declaration uploaded successfully. Ready for processing."
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
    source_metadata: Optional[Dict[str, Dict[str, Any]]] = None  # NEW: field_path -> {source, page, bbox}
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
