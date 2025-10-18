"""
Declaration API endpoints
"""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response, File, UploadFile, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
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
    arrival_notice: UploadFile = File(..., description="Arrival Notice PDF"),
    bill_of_lading: UploadFile = File(..., description="Bill of Lading PDF"),
    certificate_of_origin: UploadFile = File(..., description="Certificate of Origin PDF"),
    invoice: UploadFile = File(..., description="Invoice (PDF, JPG, or PNG)"),
    good_list: UploadFile = File(..., description="Good List Excel file"),
    tariff: UploadFile = File(..., description="Tariff Excel file"),
    auto_process: bool = Query(
        default=False,
        description="Automatically trigger processing after upload"
    ),
    db: AsyncSession = Depends(get_db)
) -> DeclarationUploadResponse:
    """
    Upload 6 declaration files to create new declaration

    Accepts multipart/form-data with 6 required files:
    - arrival_notice: Arrival Notice (AN.pdf) - PDF only
    - bill_of_lading: Bill of Lading (BOL.pdf) - PDF only
    - certificate_of_origin: Certificate of Origin (CO.pdf) - PDF only
    - invoice: Invoice - PDF, JPG, or PNG
    - good_list: Good List - Excel (.xls or .xlsx)
    - tariff: Tariff - Excel (.xls or .xlsx)

    File size limits:
    - PDFs: Max 10MB
    - Images: Max 5MB
    - Excel files: Max 2MB

    Returns:
        DeclarationUploadResponse with declaration_id, status, and file metadata

    Raises:
        HTTPException 400: Validation failed (missing files, wrong types)
        HTTPException 413: File size exceeded
        HTTPException 507: Insufficient storage space
    """
    # Initialize services
    validation_service = FileValidationService()
    storage_service = FileStorageService()

    # Collect all files
    files = {
        "arrival_notice": arrival_notice,
        "bill_of_lading": bill_of_lading,
        "certificate_of_origin": certificate_of_origin,
        "invoice": invoice,
        "good_list": good_list,
        "tariff": tariff
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

    # TODO: Get from JWT token when auth is implemented
    # For now, use placeholder UUIDs
    from uuid import uuid4
    organization_id = uuid4()
    created_by_user_id = uuid4()

    try:
        # Create declaration with UPLOADED status
        declaration = await repo.create(
            organization_id=organization_id,
            created_by_user_id=created_by_user_id,
            status="UPLOADED"
        )

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

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "upload_failed",
                "message": "Failed to upload declaration files"
            }
        )


@router.post("/{declaration_id}/process")
async def process_declaration(
    declaration_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger async AI processing for declaration

    Starts background Celery task for OCR + LLM extraction.
    Returns immediately with task ID and initial status.
    Client should poll GET /declarations/{id}/status for progress.

    Args:
        declaration_id: UUID of declaration to process
        db: Database session

    Returns:
        dict with declaration_id, task_id, and initial status

    Raises:
        HTTPException 404: If declaration not found
        HTTPException 400: If declaration already processing or completed
    """
    from src.workers.declaration_processor import process_declaration_task

    repo = DeclarationRepository(db)
    declaration = await repo.get_by_id(declaration_id)

    if not declaration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Declaration {declaration_id} not found"
        )

    # Check if already processing
    if declaration.status in [
        "PROCESSING_OCR",
        "PROCESSING_LLM",
        "VALIDATING",
        "READY_FOR_REVIEW",
        "APPROVED"
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Declaration already processed or in progress (status: {declaration.status})"
        )

    # Trigger Celery task
    task = process_declaration_task.delay(str(declaration_id))

    # Store task ID in database
    declaration.celery_task_id = task.id
    declaration.status = "PROCESSING"
    declaration.processing_progress = 0.0
    await db.commit()

    return {
        "declaration_id": str(declaration_id),
        "task_id": task.id,
        "status": "PENDING",
        "message": "Processing started. Poll /declarations/{id}/status for progress."
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
async def get_declaration(declaration_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get full declaration details including draft data

    Returns: All fields, uploaded files, extracted data, validation warnings
    """
    return {"message": f"Get declaration {declaration_id} endpoint - to be implemented"}


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
