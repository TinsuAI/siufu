"""
Knowledge Base API endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db

router = APIRouter()


@router.post("/good-list/upload")
async def upload_good_list(db: AsyncSession = Depends(get_db)):
    """
    Upload new Good List Excel file

    Creates new version, parses Excel, stores entries in database
    """
    return {"message": "Upload good list endpoint - to be implemented"}


@router.post("/tariff/upload")
async def upload_tariff(db: AsyncSession = Depends(get_db)):
    """
    Upload new Tariff Rate Excel file

    Creates new version, parses Excel, stores rates in database
    """
    return {"message": "Upload tariff endpoint - to be implemented"}


@router.get("/versions")
async def list_versions(db: AsyncSession = Depends(get_db)):
    """
    List all knowledge base versions with metadata

    Returns: version history for both good list and tariff
    """
    return {"message": "List knowledge base versions endpoint - to be implemented"}
