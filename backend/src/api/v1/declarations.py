"""
Declaration API endpoints
"""
from typing import List, Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.database import get_db
from src.core.deps import get_current_user
from src.models.declaration import Declaration
from src.models.exporter import Exporter
from src.models.importer import Importer
from src.repositories.declaration_repository import DeclarationRepository
from src.schemas.declaration import (
    DeclarationApproveResponse,
    DeclarationListItem,
    DeclarationListResponse,
    DeclarationRejectRequest,
    DeclarationRejectResponse,
    DeclarationStatusResponse,
    DeclarationUploadResponse,
    UploadedFileMetadata,
)
from src.services import master_data_service
from src.services.file_storage_service import FileStorageService
from src.services.file_validation_service import (
    FileSizeLimitExceeded,
    FileValidationError,
    FileValidationService,
)

router = APIRouter()


@router.get("", response_model=DeclarationListResponse)
async def list_declarations(
    request: Request,
    page: int = Query(default=1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(default=20, ge=1, le=100, description="Items per page (max 100)"),
    status_filter: Optional[str] = Query(default=None, alias="status", description="Filter by status (e.g., APPROVED)"),
    search: Optional[str] = Query(default=None, description="Search by declaration ID (partial match)"),
    sort_by: str = Query(default="created_at", description="Sort field (created_at or status)"),
    sort_order: str = Query(default="desc", description="Sort direction (asc or desc)"),
    db: AsyncSession = Depends(get_db)
) -> DeclarationListResponse:
    """
    List declarations with pagination, filtering, and sorting

    Query Parameters:
    - page: Page number (default: 1, min: 1)
    - limit: Items per page (default: 20, min: 1, max: 100)
    - status: Filter by status (optional) - e.g., "APPROVED", "PROCESSING"
    - search: Search by declaration ID (optional) - partial match
    - sort_by: Sort field (default: "created_at") - options: "created_at", "status"
    - sort_order: Sort direction (default: "desc") - options: "asc", "desc"

    Returns:
        DeclarationListResponse with paginated items and metadata

    Raises:
        HTTPException 400: Invalid query parameters
        HTTPException 401: Not authenticated
    """
    import math

    from sqlalchemy import String, cast, func, select

    from src.models.declaration import Declaration

    # Authenticate user
    current_user = await get_current_user(request, db)

    # Validate sort_by parameter
    if sort_by not in ["created_at", "status"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid sort_by parameter: '{sort_by}'. Must be 'created_at' or 'status'."
        )

    # Validate sort_order parameter
    if sort_order not in ["asc", "desc"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid sort_order parameter: '{sort_order}'. Must be 'asc' or 'desc'."
        )

    # Build query: Filter by authenticated user and exclude soft-deleted
    query = select(Declaration).where(
        Declaration.created_by_user_id == current_user.id,
        Declaration.deleted_at.is_(None)
    )

    # Apply status filter if provided
    if status_filter:
        # Validate status value
        try:
            from src.models.declaration import DeclarationStatus as ModelDeclarationStatus
            status_enum = ModelDeclarationStatus(status_filter)
            query = query.where(Declaration.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: '{status_filter}'. Must be one of: {[s.value for s in ModelDeclarationStatus]}"
            )

    # Apply search filter if provided (partial match on declaration ID)
    if search:
        # Convert UUID to string for partial matching
        query = query.where(
            cast(Declaration.id, String).ilike(f"%{search}%")
        )

    # Count total matching declarations (before pagination)
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Apply sorting
    if sort_by == "created_at":
        order_column = Declaration.created_at
    else:  # status
        order_column = Declaration.status

    if sort_order == "asc":
        query = query.order_by(order_column.asc())
    else:  # desc
        query = query.order_by(order_column.desc())

    # Apply pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)

    # Execute query
    result = await db.execute(query)
    declarations = result.scalars().all()

    # Build response items with products_count
    items = []
    for declaration in declarations:
        # Calculate products_count from draft_data.products array
        products_count = 0
        if declaration.draft_data and isinstance(declaration.draft_data, dict):
            products = declaration.draft_data.get("products")
            if isinstance(products, list):
                products_count = len(products)

        items.append(DeclarationListItem(
            id=declaration.id,
            status=declaration.status,
            created_at=declaration.created_at,
            updated_at=declaration.updated_at,
            approved_at=declaration.approved_at,
            products_count=products_count
        ))

    # Calculate total pages
    total_pages = math.ceil(total / limit) if total > 0 else 0

    return DeclarationListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages
    )


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
    1. UPLOADED (progress: 0.0)
    2. PROCESSING (progress: 0.2) - OCR extraction from PDFs
    3. PROCESSING (progress: 0.4) - LLM data extraction
    4. VALIDATING (progress: 0.7) - Data validation
    5. READY_FOR_REVIEW (progress: 1.0) - Complete

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
        celery_task_id=declaration.celery_task_id,
        processing_log=declaration.processing_log or [],
        created_at=declaration.created_at
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
    declaration_result = await db.execute(
        select(Declaration)
        .options(
            selectinload(Declaration.importer),
            selectinload(Declaration.exporter)
        )
        .where(Declaration.id == declaration_id)
    )
    declaration = declaration_result.scalars().first()

    if not declaration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Declaration {declaration_id} not found"
        )

    importer_summary = None
    if declaration.importer:
        importer_summary = {
            "id": str(declaration.importer.id),
            "name": declaration.importer.name,
            "is_verified": declaration.importer.is_verified,
            "declaration_count": declaration.importer.declaration_count,
        }

    exporter_summary = None
    if declaration.exporter:
        exporter_summary = {
            "id": str(declaration.exporter.id),
            "name": declaration.exporter.name,
            "is_verified": declaration.exporter.is_verified,
            "declaration_count": declaration.exporter.declaration_count,
        }

    # Build response with all fields (including source_metadata from Story 3.7)
    response = {
        "id": str(declaration.id),
        "status": declaration.status,
        "uploaded_files": declaration.uploaded_files or {},
        "extracted_data": declaration.extracted_data or {},
        "draft_data": declaration.draft_data or {},  # Draft data for review form
        "confidence_scores": declaration.confidence_scores or {},
        "source_metadata": declaration.source_metadata or {},  # NEW: Story 3.7
        "processing_progress": declaration.processing_progress or 0.0,
        "processing_error": declaration.processing_error,
        "celery_task_id": declaration.celery_task_id,
        "importer_id": str(declaration.importer_id) if declaration.importer_id else None,
        "exporter_id": str(declaration.exporter_id) if declaration.exporter_id else None,
        "importer_summary": importer_summary,
        "exporter_summary": exporter_summary,
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


@router.post("/{declaration_id}/approve", response_model=DeclarationApproveResponse)
async def approve_declaration(
    declaration_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> DeclarationApproveResponse:
    """
    Approve declaration and lock for editing

    Sets status to APPROVED, records approver and timestamp (per FR20)

    Args:
        declaration_id: UUID of declaration to approve
        request: FastAPI Request object for authentication
        db: Database session

    Returns:
        DeclarationApproveResponse with updated status and approval details

    Raises:
        HTTPException 404: If declaration not found
        HTTPException 400: If invalid status transition (can only approve READY_FOR_REVIEW declarations)
        HTTPException 401: If not authenticated
    """
    # Authenticate user
    current_user = await get_current_user(request, db)

    # Get declaration
    repo = DeclarationRepository(db)
    declaration = await repo.get_by_id(declaration_id)

    if not declaration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Declaration {declaration_id} not found"
        )

    # Validate status - can only approve READY_FOR_REVIEW declarations
    if declaration.status != "READY_FOR_REVIEW":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve declaration with status '{declaration.status}'. Only READY_FOR_REVIEW declarations can be approved."
        )

    # Update declaration status to APPROVED
    from datetime import datetime, timezone
    declaration.status = "APPROVED"
    declaration.approved_by_user_id = current_user.id
    declaration.approved_at = datetime.now(timezone.utc)

    # Story 3.10: Create or update importer master data
    if declaration.draft_data and "importer" in declaration.draft_data:
        importer_data = declaration.draft_data["importer"]

        if declaration.importer_id:
            # Update existing importer
            from sqlalchemy import select
            stmt = select(Importer).where(Importer.id == declaration.importer_id)
            result = await db.execute(stmt)
            importer = result.scalars().first()

            if importer:
                importer.name = importer_data.get("name", importer.name)
                importer.name_normalized = master_data_service.normalize_company_name(importer_data.get("name", importer.name))
                importer.tax_code = master_data_service.normalize_tax_code(importer_data.get("tax_code", importer.tax_code))
                importer.postal_code = importer_data.get("postal_code")
                importer.address = importer_data.get("address")
                importer.phone = importer_data.get("phone")
                importer.last_reviewed_by_user_id = current_user.id
                importer.last_reviewed_at = datetime.now(timezone.utc)
        else:
            # Create new importer
            new_importer = Importer(
                tax_code=master_data_service.normalize_tax_code(importer_data.get("tax_code", "")),
                name=importer_data.get("name", ""),
                name_normalized=master_data_service.normalize_company_name(importer_data.get("name", "")),
                postal_code=importer_data.get("postal_code"),
                address=importer_data.get("address"),
                phone=importer_data.get("phone"),
                organization_id=declaration.organization_id,
                first_seen_declaration_id=declaration.id,
                last_seen_declaration_id=declaration.id,
                declaration_count=1,
                is_verified=True,
                confidence_score=1.0,
                last_reviewed_by_user_id=current_user.id,
                last_reviewed_at=datetime.now(timezone.utc)
            )
            db.add(new_importer)
            await db.flush()  # Get the ID
            declaration.importer_id = new_importer.id

    # Story 3.10: Create or update exporter master data
    if declaration.draft_data and "exporter" in declaration.draft_data:
        exporter_data = declaration.draft_data["exporter"]

        if declaration.exporter_id:
            # Update existing exporter
            from sqlalchemy import select
            stmt = select(Exporter).where(Exporter.id == declaration.exporter_id)
            result = await db.execute(stmt)
            exporter = result.scalars().first()

            if exporter:
                exporter.name = exporter_data.get("name", exporter.name)
                exporter.name_normalized = master_data_service.normalize_company_name(exporter_data.get("name", exporter.name))
                exporter.country_code = exporter_data.get("country_code", exporter.country_code).upper()
                exporter.address_line1 = exporter_data.get("address_line1")
                exporter.address_line2 = exporter_data.get("address_line2")
                exporter.address_line3 = exporter_data.get("address_line3")
                exporter.last_reviewed_by_user_id = current_user.id
                exporter.last_reviewed_at = datetime.now(timezone.utc)
        else:
            # Create new exporter
            new_exporter = Exporter(
                name=exporter_data.get("name", ""),
                name_normalized=master_data_service.normalize_company_name(exporter_data.get("name", "")),
                country_code=exporter_data.get("country_code", "").upper(),
                address_line1=exporter_data.get("address_line1"),
                address_line2=exporter_data.get("address_line2"),
                address_line3=exporter_data.get("address_line3"),
                organization_id=declaration.organization_id,
                first_seen_declaration_id=declaration.id,
                last_seen_declaration_id=declaration.id,
                declaration_count=1,
                is_verified=True,
                confidence_score=1.0,
                last_reviewed_by_user_id=current_user.id,
                last_reviewed_at=datetime.now(timezone.utc)
            )
            db.add(new_exporter)
            await db.flush()  # Get the ID
            declaration.exporter_id = new_exporter.id

    await db.commit()
    await db.refresh(declaration)

    # Return success response
    return DeclarationApproveResponse(
        id=declaration.id,
        status=declaration.status,
        approved_at=declaration.approved_at,
        approved_by_user_id=declaration.approved_by_user_id,
        message="Declaration approved successfully"
    )


@router.post("/{declaration_id}/reject", response_model=DeclarationRejectResponse)
async def reject_declaration(
    declaration_id: UUID,
    reject_request: DeclarationRejectRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> DeclarationRejectResponse:
    """
    Reject declaration with reason

    Sets status to REJECTED, stores rejection reason, allows re-editing

    Args:
        declaration_id: UUID of declaration to reject
        reject_request: Request body with rejection_reason (min 10 characters)
        request: FastAPI Request object for authentication
        db: Database session

    Returns:
        DeclarationRejectResponse with updated status and rejection reason

    Raises:
        HTTPException 404: If declaration not found
        HTTPException 400: If invalid status transition or missing reason
        HTTPException 401: If not authenticated
        HTTPException 422: If rejection reason too short (< 10 characters)
    """
    # Authenticate user
    await get_current_user(request, db)

    # Get declaration
    repo = DeclarationRepository(db)
    declaration = await repo.get_by_id(declaration_id)

    if not declaration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Declaration {declaration_id} not found"
        )

    # Validate status - can only reject READY_FOR_REVIEW declarations
    if declaration.status != "READY_FOR_REVIEW":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reject declaration with status '{declaration.status}'. Only READY_FOR_REVIEW declarations can be rejected."
        )

    # Update declaration status to REJECTED and store rejection reason
    declaration.status = "REJECTED"
    declaration.processing_error = reject_request.rejection_reason  # Reuse processing_error field for rejection reason
    await db.commit()
    await db.refresh(declaration)

    # Return success response
    return DeclarationRejectResponse(
        id=declaration.id,
        status=declaration.status,
        rejection_reason=reject_request.rejection_reason,
        message="Declaration rejected successfully"
    )


@router.get("/{declaration_id}/export")
async def export_declaration(
    declaration_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> FileResponse:
    """
    Export declaration to Excel using template

    Downloads the generated CD.xlsx file for approved declarations.
    File must be generated by the processing pipeline before download.

    Args:
        declaration_id: UUID of declaration to export
        request: FastAPI Request object for authentication
        db: Database session

    Returns:
        FileResponse with Excel file download

    Raises:
        HTTPException 404: If declaration not found or Excel file not generated
        HTTPException 403: If declaration not approved (only APPROVED declarations can be exported)
        HTTPException 401: If not authenticated
    """
    from pathlib import Path

    # Authenticate user
    await get_current_user(request, db)

    # Get declaration
    repo = DeclarationRepository(db)
    declaration = await repo.get_by_id(declaration_id)

    if not declaration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Declaration {declaration_id} not found"
        )

    # Validate status - can only export APPROVED declarations
    if declaration.status != "APPROVED":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot export declaration with status '{declaration.status}'. Only APPROVED declarations can be exported."
        )

    # Check if Excel file exists
    export_file_path = Path(f"./data/exports/{declaration_id}/CD.xlsx")

    if not export_file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Excel file not yet generated. Please wait for processing to complete."
        )

    # Return file as download with correct headers
    return FileResponse(
        path=str(export_file_path),
        filename=f"CD_{declaration_id}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Cache-Control": "private, max-age=3600",
            "Content-Disposition": f'attachment; filename="CD_{declaration_id}.xlsx"'
        }
    )


@router.delete("/{declaration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_declaration(
    declaration_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Response:
    """
    Soft delete a declaration

    Sets deleted_at timestamp instead of hard deleting (preserves audit trail).
    Users can only delete their own declarations.

    Args:
        declaration_id: UUID of declaration to delete
        request: FastAPI Request object for authentication
        db: Database session

    Returns:
        204 No Content on success

    Raises:
        HTTPException 404: If declaration not found
        HTTPException 403: If user doesn't own the declaration (authorization check)
        HTTPException 401: If not authenticated
    """
    from datetime import datetime, timezone

    # Authenticate user
    current_user = await get_current_user(request, db)

    # Get declaration
    repo = DeclarationRepository(db)
    declaration = await repo.get_by_id(declaration_id)

    if not declaration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Declaration {declaration_id} not found"
        )

    # Check if already deleted
    if declaration.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Declaration {declaration_id} not found"
        )

    # Authorization: User can only delete their own declarations
    if declaration.created_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to delete this declaration. Users can only delete their own declarations."
        )

    # Soft delete: Set deleted_at timestamp
    declaration.deleted_at = datetime.now(timezone.utc)
    await db.commit()

    # Return 204 No Content
    return Response(status_code=status.HTTP_204_NO_CONTENT)
