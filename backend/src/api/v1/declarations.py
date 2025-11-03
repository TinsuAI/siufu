"""
Declaration API endpoints
"""
from uuid import UUID
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Response, File, UploadFile, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.deps import get_current_user
from src.models.user import User
from src.repositories.declaration_repository import DeclarationRepository
from src.schemas.declaration import DeclarationStatusResponse, DeclarationUploadResponse, UploadedFileMetadata
from src.services.file_validation_service import FileValidationService, FileValidationError, FileSizeLimitExceeded
from src.services.file_storage_service import FileStorageService

router = APIRouter()


@router.get("")
async def list_declarations(db: AsyncSession = Depends(get_db)):
    """
    List all declarations with pagination

    Query params: skip, limit, status filter
    """
    return {"message": "List declarations endpoint - to be implemented"}


@router.post("/upload", response_model=DeclarationUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_declaration(
    request: Request,
    arrival_notice: UploadFile = File(..., description="Arrival Notice PDF"),
    bill_of_lading: UploadFile = File(..., description="Bill of Lading PDF"),
    certificate_of_origin: List[UploadFile] = File(..., description="Certificate of Origin PDFs (1-20 files)"),
    invoice: UploadFile = File(..., description="Invoice (PDF, JPG, or PNG)"),
    auto_process: bool = Query(
        default=False,
        description="Automatically trigger processing after upload"
    ),
    db: AsyncSession = Depends(get_db)
) -> DeclarationUploadResponse:
    """
    Upload 4 declaration file types to create new declaration
    Updated in Story 3.3.1: Certificate of Origin supports multiple files (1-20)

    Accepts multipart/form-data with 4 required file types:
    - arrival_notice: Arrival Notice (AN.pdf) - PDF only - 1 file
    - bill_of_lading: Bill of Lading (BOL.pdf) - PDF only - 1 file
    - certificate_of_origin: Certificate of Origin (CO.pdf) - PDF only - 1-20 files
    - invoice: Invoice - PDF, JPG, or PNG - 1 file

    File size limits:
    - PDFs: Max 10MB per file
    - Images: Max 5MB per file

    Returns:
        DeclarationUploadResponse with declaration_id, status, and file metadata

    Raises:
        HTTPException 400: Validation failed (missing files, wrong types, C/O count out of range)
        HTTPException 401: Not authenticated
        HTTPException 413: File size exceeded
        HTTPException 507: Insufficient storage space
    """
    # Authenticate user (requires JWT token in cookie or Authorization header)
    current_user = await get_current_user(request, db)

    # Validate C/O file count (1-20 files)
    if not certificate_of_origin or len(certificate_of_origin) < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "invalid_co_count",
                "message": "At least 1 Certificate of Origin file is required",
                "count": len(certificate_of_origin) if certificate_of_origin else 0
            }
        )

    if len(certificate_of_origin) > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "invalid_co_count",
                "message": "Maximum 20 Certificate of Origin files allowed",
                "count": len(certificate_of_origin)
            }
        )

    # Initialize services
    validation_service = FileValidationService()
    storage_service = FileStorageService()

    # Collect all files (CO is now a list)
    files = {
        "arrival_notice": arrival_notice,
        "bill_of_lading": bill_of_lading,
        "certificate_of_origin": certificate_of_origin,  # Now a list
        "invoice": invoice
    }

    try:
        # Validate all files (type and size)
        await validation_service.validate_all_files(files)

    except FileValidationError as e:
        # Return 400 Bad Request with detailed validation errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "file_validation_failed",
                "message": "File validation failed",
                "errors": e.errors
            }
        )

    except FileSizeLimitExceeded as e:
        # Return 413 Payload Too Large with size details
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "error": "file_too_large",
                "message": "File size limit exceeded",
                "file": e.file_field,
                "size": e.size,
                "max_size": e.max_size
            }
        )

    # Create declaration record
    repo = DeclarationRepository(db)

    # Get organization and user IDs from authenticated user
    organization_id = current_user.organization_id
    created_by_user_id = current_user.id

    try:
        # Create declaration with UPLOADED status
        declaration = await repo.create({
            "organization_id": organization_id,
            "created_by_user_id": created_by_user_id,
            "status": "UPLOADED"
        })

        # Save files to storage
        file_metadata = await storage_service.save_declaration_files(
            declaration.id,
            files
        )

        # Update declaration with file metadata
        declaration.uploaded_files = file_metadata
        declaration.processing_progress = 0.0
        await db.commit()
        await db.refresh(declaration)

        # Optionally trigger Celery processing task
        celery_task_id = None
        message = "Declaration uploaded successfully. Ready for processing."

        if auto_process:
            from src.workers.declaration_processor import process_declaration_task

            # Trigger Celery task
            task = process_declaration_task.delay(str(declaration.id))
            celery_task_id = task.id

            # Update declaration with task ID
            declaration.celery_task_id = celery_task_id
            declaration.status = "PROCESSING"
            await db.commit()

            message = "Declaration uploaded successfully. Processing started."

        # Build response
        uploaded_files_response = [
            UploadedFileMetadata(
                file_type=metadata["file_type"],
                filename=metadata["filename"],
                size=metadata["size"]
            )
            for metadata in file_metadata
        ]

        return DeclarationUploadResponse(
            declaration_id=declaration.id,
            status=declaration.status,
            uploaded_files=uploaded_files_response,
            celery_task_id=celery_task_id,
            message=message
        )

    except OSError as e:
        # Handle disk full errors
        await db.rollback()
        if "Insufficient storage" in str(e):
            raise HTTPException(
                status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
                detail={
                    "error": "insufficient_storage",
                    "message": "Insufficient storage space available"
                }
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "file_storage_error",
                "message": "Failed to store uploaded files"
            }
        )

    except Exception as e:
        # Rollback database transaction
        await db.rollback()

        # Clean up any saved files
        if 'declaration' in locals():
            await storage_service.cleanup_declaration_files(declaration.id)

        # Log error to Sentry (if configured)
        # TODO: Add Sentry logging

        # DEBUG: Print error for investigation
        import traceback
        print(f"ERROR in upload endpoint: {type(e).__name__}: {str(e)}")
        print(traceback.format_exc())

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "upload_failed",
                "message": "Failed to upload declaration files",
                "debug_error": f"{type(e).__name__}: {str(e)}"
            }
        )


@router.post("/{declaration_id}/process")
async def process_declaration(
    declaration_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger async processing for uploaded declaration

    Triggers Celery task to process all document types (AN, BOL, CO (multiple), INVOICE)
    through OCR and LLM extraction pipeline.

    **Processing Stages:**
    1. PENDING_PROCESSING (progress: 0.0)
    2. PROCESSING_OCR (progress: 0.2) - OCR extraction from PDFs
    3. PROCESSING_LLM (progress: 0.6) - GPT-5 data extraction
    4. READY_FOR_REVIEW (progress: 1.0) - Complete

    **Expected Duration:** 46-72 seconds (avg 59s, within 90s NFR1 target)
    Note: Duration may increase with multiple C/O files

    Args:
        declaration_id: UUID of declaration to process
        db: Database session

    Returns:
        202 Accepted with Celery task ID for status polling

    Raises:
        HTTPException 404: If declaration not found
        HTTPException 400: If declaration not in UPLOADED status (cannot reprocess COMPLETED declarations)
        HTTPException 503: If Celery worker unavailable
    """
    from src.workers.declaration_processor import process_declaration_task

    repo = DeclarationRepository(db)
    declaration = await repo.get_by_id(declaration_id)

    if not declaration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Declaration {declaration_id} not found"
        )

    # Validate declaration status - can only process UPLOADED declarations
    if declaration.status != "UPLOADED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot process declaration with status '{declaration.status}'. Only UPLOADED declarations can be processed."
        )

    # Trigger Celery task
    task = process_declaration_task.delay(str(declaration_id))

    # Update declaration status to PROCESSING
    declaration.celery_task_id = task.id
    declaration.status = "PROCESSING"
    declaration.processing_progress = 0.0
    await db.commit()

    return {
        "declaration_id": str(declaration_id),
        "status": "PROCESSING",
        "celery_task_id": task.id,
        "message": "Processing started. Poll /api/declarations/{id}/status for updates."
    }


@router.get("/{declaration_id}/status", response_model=DeclarationStatusResponse)
async def get_declaration_status(
    declaration_id: UUID,
    response: Response,
    db: AsyncSession = Depends(get_db)
) -> DeclarationStatusResponse:
    """
    Get processing status and progress for declaration

    Used for polling task progress during async processing.
    Frontend should poll this endpoint to display real-time progress.

    Args:
        declaration_id: UUID of declaration
        response: FastAPI Response object for setting headers
        db: Database session

    Returns:
        DeclarationStatusResponse with current status, progress, and task ID

    Raises:
        HTTPException 404: If declaration not found

    Response Headers:
        Cache-Control: no-store (status changes frequently, don't cache)
    """
    # Set Cache-Control header to prevent caching (status changes frequently)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    repo = DeclarationRepository(db)
    declaration = await repo.get_by_id(declaration_id)

    if not declaration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Declaration {declaration_id} not found"
        )

    # Build response with current status and progress
    return DeclarationStatusResponse(
        id=declaration.id,
        status=declaration.status,
        progress=declaration.processing_progress or 0.0,
        processing_error=declaration.processing_error,
        celery_task_id=declaration.celery_task_id
    )


@router.get("/{declaration_id}")
async def get_declaration(
    declaration_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get complete declaration details including extracted data

    Returns full declaration record with:
    - Declaration metadata (id, status, timestamps)
    - Uploaded files metadata
    - Extracted data (JSON) from LLM
    - Confidence scores per field
    - Processing progress and errors

    Args:
        declaration_id: UUID of declaration
        db: Database session

    Returns:
        Complete declaration details as JSON

    Raises:
        HTTPException 404: If declaration not found
    """
    repo = DeclarationRepository(db)
    declaration = await repo.get_by_id(declaration_id)

    if not declaration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Declaration {declaration_id} not found"
        )

    # Build response with all fields (including source_metadata from Story 3.7)
    response = {
        "id": str(declaration.id),
        "status": declaration.status,
        "uploaded_files": declaration.uploaded_files or {},
        "extracted_data": declaration.extracted_data or {},
        "confidence_scores": declaration.confidence_scores or {},
        "source_metadata": declaration.source_metadata or {},  # NEW: Story 3.7
        "processing_progress": declaration.processing_progress or 0.0,
        "processing_error": declaration.processing_error,
        "celery_task_id": declaration.celery_task_id,
        "organization_id": str(declaration.organization_id),
        "created_by_user_id": str(declaration.created_by_user_id),
        "created_at": declaration.created_at.isoformat() if declaration.created_at else None,
        "updated_at": declaration.updated_at.isoformat() if declaration.updated_at else None
    }

    return response


@router.patch("/{declaration_id}")
async def update_declaration(declaration_id: str, db: AsyncSession = Depends(get_db)):
    """
    Update declaration draft data (auto-save)

    Merges partial updates into draft_data JSONB field
    """
    return {"message": f"Update declaration {declaration_id} endpoint - to be implemented"}


@router.post("/{declaration_id}/approve")
async def approve_declaration(declaration_id: str, db: AsyncSession = Depends(get_db)):
    """
    Approve declaration and lock for editing

    Sets status to APPROVED, records approver and timestamp
    """
    return {"message": f"Approve declaration {declaration_id} endpoint - to be implemented"}


@router.post("/{declaration_id}/reject")
async def reject_declaration(declaration_id: str, db: AsyncSession = Depends(get_db)):
    """
    Reject declaration with reason

    Sets status to REJECTED, allows re-editing
    """
    return {"message": f"Reject declaration {declaration_id} endpoint - to be implemented"}


@router.get("/{declaration_id}/export")
async def export_declaration(declaration_id: str, db: AsyncSession = Depends(get_db)):
    """
    Export declaration to Excel using template

    Returns: Excel file download
    """
    return {"message": f"Export declaration {declaration_id} endpoint - to be implemented"}
