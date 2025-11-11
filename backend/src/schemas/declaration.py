"""
Declaration Pydantic schemas for API request/response
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DeclarationStatus(str, Enum):
    """Declaration status enumeration"""
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
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


class ProcessingLogEntry(BaseModel):
    """Schema for a single processing log entry"""
    timestamp: str = Field(description="ISO 8601 timestamp")
    level: str = Field(description="Log level: info, success, warning, error")
    message: str = Field(description="Log message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional details")


class DeclarationStatusResponse(BaseModel):
    """Schema for declaration status polling response"""
    id: UUID
    status: DeclarationStatus
    progress: float = Field(ge=0.0, le=1.0, description="Processing progress from 0.0 to 1.0")
    processing_error: Optional[str] = None
    celery_task_id: Optional[str] = None
    processing_log: List[ProcessingLogEntry] = Field(default_factory=list, description="Processing activity log")
    created_at: datetime = Field(description="Declaration creation timestamp")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "PROCESSING",
                "progress": 0.4,
                "processing_error": None,
                "celery_task_id": "abc123-def456-ghi789",
                "processing_log": [
                    {
                        "timestamp": "2025-11-04T07:00:00Z",
                        "level": "info",
                        "message": "Starting OCR processing",
                        "details": {"file_count": 4}
                    }
                ],
                "created_at": "2025-11-04T07:00:00Z"
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


class DeclarationApproveResponse(BaseModel):
    """Schema for declaration approval response"""
    id: UUID
    status: DeclarationStatus
    approved_at: datetime
    approved_by_user_id: UUID
    message: str

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "323e4567-e89b-12d3-a456-426614174000",
                "status": "APPROVED",
                "approved_at": "2025-11-03T10:30:00Z",
                "approved_by_user_id": "123e4567-e89b-12d3-a456-426614174000",
                "message": "Declaration approved successfully"
            }
        }
    )


class DeclarationRejectRequest(BaseModel):
    """Schema for declaration rejection request"""
    rejection_reason: str = Field(
        min_length=10,
        description="Reason for rejecting the declaration (minimum 10 characters)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "rejection_reason": "Incomplete invoice information - missing product descriptions"
            }
        }
    )


class DeclarationRejectResponse(BaseModel):
    """Schema for declaration rejection response"""
    id: UUID
    status: DeclarationStatus
    rejection_reason: str
    message: str

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "323e4567-e89b-12d3-a456-426614174000",
                "status": "REJECTED",
                "rejection_reason": "Incomplete invoice information - missing product descriptions",
                "message": "Declaration rejected successfully"
            }
        }
    )


class DeclarationListItem(BaseModel):
    """Schema for declaration list item (optimized - excludes large fields)"""
    id: UUID
    status: DeclarationStatus
    created_at: datetime
    updated_at: datetime
    approved_at: Optional[datetime] = None
    products_count: int = Field(
        default=0,
        description="Number of products in the declaration (calculated from draft_data.products)"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "323e4567-e89b-12d3-a456-426614174000",
                "status": "APPROVED",
                "created_at": "2025-11-03T10:00:00Z",
                "updated_at": "2025-11-03T11:30:00Z",
                "approved_at": "2025-11-03T11:30:00Z",
                "products_count": 15
            }
        }
    )


class DeclarationListResponse(BaseModel):
    """Schema for paginated declaration list response"""
    items: List[DeclarationListItem] = Field(description="List of declarations")
    total: int = Field(description="Total count of matching declarations")
    page: int = Field(description="Current page number")
    limit: int = Field(description="Items per page")
    total_pages: int = Field(description="Total number of pages")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": "323e4567-e89b-12d3-a456-426614174000",
                        "status": "APPROVED",
                        "created_at": "2025-11-03T10:00:00Z",
                        "updated_at": "2025-11-03T11:30:00Z",
                        "approved_at": "2025-11-03T11:30:00Z",
                        "products_count": 15
                    }
                ],
                "total": 156,
                "page": 1,
                "limit": 20,
                "total_pages": 8
            }
        }
    )
