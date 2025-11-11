"""
Corrections API endpoints (Story 3.6 Expansion)
Allows users to flag field corrections with category and notes
"""
import csv
import io
import os
from pathlib import Path
from typing import List, Literal
from uuid import UUID

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.database import get_db
from src.core.deps import get_current_user
from src.models.correction import Correction
from src.models.declaration import Declaration
from src.schemas.correction import CorrectionCreate, CorrectionListResponse, CorrectionResponse

router = APIRouter()


@router.post("/declarations/{declaration_id}/corrections", response_model=CorrectionResponse, status_code=status.HTTP_201_CREATED)
async def create_correction(
    declaration_id: UUID,
    correction_data: CorrectionCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> CorrectionResponse:
    """
    Create or update a correction flag for a field

    This endpoint allows users to flag corrections they made to AI-extracted data,
    providing feedback to improve future extractions.

    If a correction already exists for the same field, it will be updated instead of creating a duplicate.

    Args:
        declaration_id: UUID of the declaration
        correction_data: Correction details (field_name, original_value, corrected_value, category, notes)

    Returns:
        CorrectionResponse with created/updated correction details

    Raises:
        HTTPException 404: Declaration not found or user doesn't have access
        HTTPException 401: Not authenticated
    """
    # Authenticate user
    current_user = await get_current_user(request, db)

    # Check if declaration exists and user has access
    result = await db.execute(
        select(Declaration).where(
            Declaration.id == declaration_id,
            Declaration.created_by_user_id == current_user.id,
            Declaration.deleted_at.is_(None)
        )
    )
    declaration = result.scalar_one_or_none()

    if not declaration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Declaration {declaration_id} not found or you don't have access"
        )

    # Check if correction already exists for this field
    existing_result = await db.execute(
        select(Correction).where(
            Correction.declaration_id == declaration_id,
            Correction.field_name == correction_data.field_name
        )
    )
    existing_correction = existing_result.scalar_one_or_none()

    if existing_correction:
        # Update existing correction
        existing_correction.original_value = correction_data.original_value
        existing_correction.corrected_value = correction_data.corrected_value
        existing_correction.correction_category = correction_data.correction_category
        existing_correction.expected_value = correction_data.expected_value
        existing_correction.notes = correction_data.notes
        existing_correction.screenshots = correction_data.screenshots

        await db.commit()
        await db.refresh(existing_correction)
        await db.refresh(existing_correction, ["user"])

        correction = existing_correction
    else:
        # Create new correction record
        correction = Correction(
            declaration_id=declaration_id,
            field_name=correction_data.field_name,
            original_value=correction_data.original_value,
            corrected_value=correction_data.corrected_value,
            correction_category=correction_data.correction_category,
            expected_value=correction_data.expected_value,
            notes=correction_data.notes,
            screenshots=correction_data.screenshots,
            user_id=current_user.id,
            # Legacy fields - set defaults for backward compatibility
            correction_type="OTHER",
            original_confidence=None,
            source_document=None,
            extra_metadata=None
        )

        db.add(correction)
        await db.commit()
        await db.refresh(correction)

        # Load user relationship for response
        await db.refresh(correction, ["user"])

    return CorrectionResponse(
        id=correction.id,
        declaration_id=correction.declaration_id,
        field_name=correction.field_name,
        original_value=correction.original_value,
        corrected_value=correction.corrected_value,
        correction_category=correction.correction_category,
        expected_value=correction.expected_value,
        notes=correction.notes,
        screenshots=correction.screenshots,
        user_id=correction.user_id,
        user_name=correction.user.full_name or correction.user.email,
        created_at=correction.created_at
    )


@router.get("/declarations/{declaration_id}/corrections")
async def get_corrections(
    declaration_id: UUID,
    format: Literal["json", "csv"] = "json",
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all corrections for a declaration

    Supports both JSON and CSV export formats.

    Args:
        declaration_id: UUID of the declaration
        format: Response format - "json" (default) or "csv"

    Returns:
        - JSON format: CorrectionListResponse with list of corrections
        - CSV format: StreamingResponse with CSV file

    Raises:
        HTTPException 404: Declaration not found or user doesn't have access
        HTTPException 401: Not authenticated
    """
    # Authenticate user
    current_user = await get_current_user(request, db)

    # Check if declaration exists and user has access
    result = await db.execute(
        select(Declaration).where(
            Declaration.id == declaration_id,
            Declaration.created_by_user_id == current_user.id,
            Declaration.deleted_at.is_(None)
        )
    )
    declaration = result.scalar_one_or_none()

    if not declaration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Declaration {declaration_id} not found or you don't have access"
        )

    # Get all corrections for this declaration
    result = await db.execute(
        select(Correction)
        .where(Correction.declaration_id == declaration_id)
        .options(selectinload(Correction.user))
        .order_by(Correction.created_at.desc())
    )
    corrections = result.scalars().all()

    # Format as JSON
    if format == "json":
        correction_list = [
            CorrectionResponse(
                id=c.id,
                declaration_id=c.declaration_id,
                field_name=c.field_name,
                original_value=c.original_value,
                corrected_value=c.corrected_value,
                correction_category=c.correction_category,
                expected_value=c.expected_value,
                notes=c.notes,
                screenshots=c.screenshots,
                user_id=c.user_id,
                user_name=c.user.full_name or c.user.email,
                created_at=c.created_at
            )
            for c in corrections
        ]

        return CorrectionListResponse(
            corrections=correction_list,
            count=len(correction_list)
        )

    # Format as CSV
    elif format == "csv":
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            "Field Name",
            "Original Value",
            "Corrected Value",
            "Expected Value",
            "Category",
            "Notes",
            "Screenshots",
            "Flagged By",
            "Timestamp"
        ])

        # Write data rows
        for c in corrections:
            writer.writerow([
                c.field_name,
                c.original_value or "(null)",
                c.corrected_value,
                c.expected_value,
                c.correction_category,
                c.notes,
                ", ".join(c.screenshots) if c.screenshots else "",
                c.user.full_name or c.user.email,
                c.created_at.isoformat()
            ])

        # Create streaming response
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=corrections_{declaration_id}.csv"
            }
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid format: '{format}'. Must be 'json' or 'csv'."
        )


@router.post("/screenshots/upload")
async def upload_screenshots(
    files: List[UploadFile] = File(..., description="Screenshot images (max 3)"),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Upload screenshot images for correction flags

    This endpoint handles file uploads and returns URLs that can be used
    when creating/updating corrections.

    Args:
        files: List of image files (max 3, accepted formats: jpg, jpeg, png, gif, webp)

    Returns:
        Dictionary with 'urls' key containing list of uploaded file URLs

    Raises:
        HTTPException 400: Invalid file format, too many files, or file too large
        HTTPException 401: Not authenticated
        HTTPException 500: File storage error
    """
    # Authenticate user
    await get_current_user(request, db)

    # Validate number of files
    if len(files) > 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 3 screenshots allowed"
        )

    # Validate file formats and sizes
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    uploaded_urls = []
    screenshots_dir = Path("/app/data/screenshots")
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    try:
        for file in files:
            # Validate file extension
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid file format: {file_ext}. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"
                )

            # Read file content to check size
            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File {file.filename} exceeds maximum size of 10MB"
                )

            # Generate unique filename
            import uuid as uuid_lib
            unique_filename = f"{uuid_lib.uuid4()}{file_ext}"
            file_path = screenshots_dir / unique_filename

            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)

            # Set file permissions
            os.chmod(file_path, 0o644)

            # Generate URL (relative path for storage)
            file_url = f"/screenshots/{unique_filename}"
            uploaded_urls.append(file_url)

    except HTTPException:
        # Clean up uploaded files on validation error
        for url in uploaded_urls:
            filename = url.split('/')[-1]
            file_path = screenshots_dir / filename
            if file_path.exists():
                file_path.unlink()
        raise
    except Exception as e:
        # Clean up uploaded files on any error
        for url in uploaded_urls:
            filename = url.split('/')[-1]
            file_path = screenshots_dir / filename
            if file_path.exists():
                file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload screenshots: {str(e)}"
        )

    return {"urls": uploaded_urls}


@router.get("/screenshots/{filename}")
async def get_screenshot(
    filename: str,
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a screenshot image by filename

    Args:
        filename: The screenshot filename (UUID + extension)

    Returns:
        FileResponse with the image file

    Raises:
        HTTPException 401: Not authenticated
        HTTPException 404: Screenshot not found
    """
    # Authenticate user
    await get_current_user(request, db)

    # Validate filename to prevent path traversal
    if '/' in filename or '\\' in filename or '..' in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename"
        )

    screenshots_dir = Path("/app/data/screenshots")
    file_path = screenshots_dir / filename

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Screenshot not found"
        )

    # Determine media type from extension
    ext = file_path.suffix.lower()
    media_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp'
    }
    media_type = media_types.get(ext, 'application/octet-stream')

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename
    )
