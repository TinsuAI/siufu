"""
Declaration API endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db

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
async def process_declaration(declaration_id: str, db: AsyncSession = Depends(get_db)):
    """
    Trigger async AI processing for declaration

    Starts background Celery task for OCR + LLM extraction
    """
    return {"message": f"Process declaration {declaration_id} endpoint - to be implemented"}


@router.get("/{declaration_id}/status")
async def get_declaration_status(declaration_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get processing status and progress for declaration

    Returns: status, progress percentage, errors if any
    """
    return {"message": f"Get declaration {declaration_id} status endpoint - to be implemented"}


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
