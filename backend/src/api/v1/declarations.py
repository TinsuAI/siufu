"""
Declaration API endpoints
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.repositories.declaration_repository import DeclarationRepository
from src.schemas.declaration import DeclarationStatusResponse

router = APIRouter()


@router.get("")
async def list_declarations(db: AsyncSession = Depends(get_db)):
    """
    List all declarations with pagination

    Query params: skip, limit, status filter
    """
    return {"message": "List declarations endpoint - to be implemented"}


@router.post("/upload")
async def upload_declaration(db: AsyncSession = Depends(get_db)):
    """
    Upload 6 declaration files to create new declaration

    Files: invoice, packing_list, contract, transport_doc, insurance, other
    """
    return {"message": "Upload declaration endpoint - to be implemented"}


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
