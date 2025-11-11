"""
Companies API endpoints for master data management
Handles both importers and exporters
"""
import math
from datetime import datetime, timezone
from typing import List, Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from src.core.database import get_db
from src.core.deps import get_current_user
from src.models.declaration import Declaration
from src.models.exporter import Exporter
from src.models.importer import Importer
from src.schemas.company import CompanyListResponse, DuplicatePair, MergeRequest
from src.schemas.exporter import ExporterCreate, ExporterDetail, ExporterListItem, ExporterUpdate
from src.schemas.importer import ImporterCreate, ImporterDetail, ImporterListItem, ImporterUpdate
from src.services import master_data_service

router = APIRouter()


@router.get("/", response_model=CompanyListResponse)
async def list_companies(
    request: Request,
    type: Literal["importers", "exporters"] = Query(..., description="Type of companies to list"),
    search: Optional[str] = Query(None, description="Search by name or tax code (importers only)"),
    filter: Literal["all", "verified", "unverified"] = Query("all", description="Filter by verification status"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: Literal["name", "declaration_count", "updated_at"] = Query("updated_at", description="Sort field"),
    sort_order: Literal["asc", "desc"] = Query("desc", description="Sort direction"),
    db: AsyncSession = Depends(get_db)
) -> CompanyListResponse:
    """
    List companies (importers or exporters) with pagination, search, and filtering

    Query Parameters:
    - type: "importers" or "exporters" (required)
    - search: Search by name or tax code (optional)
    - filter: "all", "verified", or "unverified" (default: "all")
    - page: Page number (default: 1, min: 1)
    - limit: Items per page (default: 20, min: 1, max: 100)
    - sort_by: Sort field - "name", "declaration_count", or "updated_at" (default: "updated_at")
    - sort_order: "asc" or "desc" (default: "desc")

    Returns:
        CompanyListResponse with paginated items and metadata

    Raises:
        HTTPException 400: Invalid query parameters
        HTTPException 401: Not authenticated
    """
    # Authenticate user
    current_user = await get_current_user(request, db)

    # Select model based on type
    Model = Importer if type == "importers" else Exporter
    ListItemSchema = ImporterListItem if type == "importers" else ExporterListItem

    # Build base query
    stmt: Select = select(Model).where(
        and_(
            Model.organization_id == current_user.organization_id,
            Model.deleted_at.is_(None)
        )
    )

    # Apply search filter
    if search:
        search_term = f"%{search}%"
        if type == "importers":
            stmt = stmt.where(
                or_(
                    Model.name.ilike(search_term),
                    Model.tax_code.ilike(search_term)
                )
            )
        else:
            stmt = stmt.where(Model.name.ilike(search_term))

    # Apply verification filter
    if filter == "verified":
        stmt = stmt.where(Model.is_verified == True)
    elif filter == "unverified":
        stmt = stmt.where(Model.is_verified == False)

    # Get total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    result = await db.execute(count_stmt)
    total = result.scalar_one()

    # Calculate pagination
    total_pages = math.ceil(total / limit) if total > 0 else 0
    offset = (page - 1) * limit

    # Apply sorting
    sort_column = getattr(Model, sort_by)
    if sort_order == "asc":
        stmt = stmt.order_by(sort_column.asc())
    else:
        stmt = stmt.order_by(sort_column.desc())

    # Apply pagination
    stmt = stmt.offset(offset).limit(limit)

    # Execute query
    result = await db.execute(stmt)
    companies = result.scalars().all()

    # Convert to list items
    items = [ListItemSchema.model_validate(company) for company in companies]

    return CompanyListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages
    )


@router.get("/{id}", response_model=ImporterDetail | ExporterDetail)
async def get_company(
    id: UUID,
    type: Literal["importers", "exporters"] = Query(..., description="Type of company"),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
) -> ImporterDetail | ExporterDetail:
    """
    Get company details by ID

    Args:
        id: Company UUID
        type: "importers" or "exporters"

    Returns:
        ImporterDetail or ExporterDetail

    Raises:
        HTTPException 404: Company not found
        HTTPException 403: Not authorized to access this company
        HTTPException 401: Not authenticated
    """
    # Authenticate user
    current_user = await get_current_user(request, db)

    # Select model based on type
    Model = Importer if type == "importers" else Exporter
    DetailSchema = ImporterDetail if type == "importers" else ExporterDetail

    # Query company
    stmt = select(Model).where(Model.id == id)
    result = await db.execute(stmt)
    company = result.scalars().first()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{type.rstrip('s').capitalize()} {id} not found"
        )

    # Check organization access
    if company.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this company"
        )

    return DetailSchema.model_validate(company)


@router.post("/", response_model=ImporterDetail | ExporterDetail, status_code=status.HTTP_201_CREATED)
async def create_company(
    type: Literal["importers", "exporters"] = Query(..., description="Type of company to create"),
    importer_data: Optional[ImporterCreate] = None,
    exporter_data: Optional[ExporterCreate] = None,
    request: Request = None,
    db: AsyncSession = Depends(get_db)
) -> ImporterDetail | ExporterDetail:
    """
    Manually create a new company

    Args:
        type: "importers" or "exporters"
        importer_data: Importer data (if type is "importers")
        exporter_data: Exporter data (if type is "exporters")

    Returns:
        ImporterDetail or ExporterDetail

    Raises:
        HTTPException 400: Invalid request body or missing data
        HTTPException 401: Not authenticated
    """
    # Authenticate user
    current_user = await get_current_user(request, db)

    if type == "importers":
        if not importer_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="importer_data required for type 'importers'"
            )

        # Create new importer
        new_importer = Importer(
            tax_code=master_data_service.normalize_tax_code(importer_data.tax_code),
            name=importer_data.name,
            name_normalized=master_data_service.normalize_company_name(importer_data.name),
            postal_code=importer_data.postal_code,
            address=importer_data.address,
            phone=importer_data.phone,
            organization_id=current_user.organization_id,
            first_seen_declaration_id=None,
            last_seen_declaration_id=None,
            declaration_count=0,
            is_verified=True,  # Manually created companies are verified
            confidence_score=1.0,
            last_reviewed_by_user_id=current_user.id,
            last_reviewed_at=datetime.now(timezone.utc)
        )
        db.add(new_importer)
        await db.commit()
        await db.refresh(new_importer)

        return ImporterDetail.model_validate(new_importer)

    else:  # type == "exporters"
        if not exporter_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="exporter_data required for type 'exporters'"
            )

        # Create new exporter
        new_exporter = Exporter(
            name=exporter_data.name,
            name_normalized=master_data_service.normalize_company_name(exporter_data.name),
            country_code=exporter_data.country_code.upper(),
            address_line1=exporter_data.address_line1,
            address_line2=exporter_data.address_line2,
            address_line3=exporter_data.address_line3,
            organization_id=current_user.organization_id,
            first_seen_declaration_id=None,
            last_seen_declaration_id=None,
            declaration_count=0,
            is_verified=True,
            confidence_score=1.0,
            last_reviewed_by_user_id=current_user.id,
            last_reviewed_at=datetime.now(timezone.utc)
        )
        db.add(new_exporter)
        await db.commit()
        await db.refresh(new_exporter)

        return ExporterDetail.model_validate(new_exporter)


@router.patch("/{id}", response_model=ImporterDetail | ExporterDetail)
async def update_company(
    id: UUID,
    type: Literal["importers", "exporters"] = Query(..., description="Type of company"),
    importer_data: Optional[ImporterUpdate] = None,
    exporter_data: Optional[ExporterUpdate] = None,
    request: Request = None,
    db: AsyncSession = Depends(get_db)
) -> ImporterDetail | ExporterDetail:
    """
    Update company details

    Args:
        id: Company UUID
        type: "importers" or "exporters"
        importer_data: Partial importer update data (if type is "importers")
        exporter_data: Partial exporter update data (if type is "exporters")

    Returns:
        ImporterDetail or ExporterDetail

    Raises:
        HTTPException 404: Company not found
        HTTPException 403: Not authorized to update this company
        HTTPException 400: Invalid request body or missing data
        HTTPException 401: Not authenticated
    """
    # Authenticate user
    current_user = await get_current_user(request, db)

    # Select model based on type
    Model = Importer if type == "importers" else Exporter
    DetailSchema = ImporterDetail if type == "importers" else ExporterDetail

    # Query company
    stmt = select(Model).where(Model.id == id)
    result = await db.execute(stmt)
    company = result.scalars().first()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{type.rstrip('s').capitalize()} {id} not found"
        )

    # Check organization access
    if company.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this company"
        )

    # Update fields
    if type == "importers":
        if not importer_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="importer_data required for type 'importers'"
            )

        if importer_data.tax_code is not None:
            company.tax_code = master_data_service.normalize_tax_code(importer_data.tax_code)
        if importer_data.name is not None:
            company.name = importer_data.name
            company.name_normalized = master_data_service.normalize_company_name(importer_data.name)
        if importer_data.postal_code is not None:
            company.postal_code = importer_data.postal_code
        if importer_data.address is not None:
            company.address = importer_data.address
        if importer_data.phone is not None:
            company.phone = importer_data.phone

    else:  # type == "exporters"
        if not exporter_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="exporter_data required for type 'exporters'"
            )

        if exporter_data.name is not None:
            company.name = exporter_data.name
            company.name_normalized = master_data_service.normalize_company_name(exporter_data.name)
        if exporter_data.country_code is not None:
            company.country_code = exporter_data.country_code.upper()
        if exporter_data.address_line1 is not None:
            company.address_line1 = exporter_data.address_line1
        if exporter_data.address_line2 is not None:
            company.address_line2 = exporter_data.address_line2
        if exporter_data.address_line3 is not None:
            company.address_line3 = exporter_data.address_line3

    # Update audit fields
    company.last_reviewed_by_user_id = current_user.id
    company.last_reviewed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(company)

    return DetailSchema.model_validate(company)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    id: UUID,
    type: Literal["importers", "exporters"] = Query(..., description="Type of company"),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a company

    Args:
        id: Company UUID
        type: "importers" or "exporters"

    Returns:
        204 No Content

    Raises:
        HTTPException 404: Company not found
        HTTPException 403: Not authorized to delete this company
        HTTPException 401: Not authenticated
    """
    # Authenticate user
    current_user = await get_current_user(request, db)

    # Select model based on type
    Model = Importer if type == "importers" else Exporter

    # Query company
    stmt = select(Model).where(Model.id == id)
    result = await db.execute(stmt)
    company = result.scalars().first()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{type.rstrip('s').capitalize()} {id} not found"
        )

    # Check organization access
    if company.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this company"
        )

    # Soft delete (set deleted_at timestamp)
    company.deleted_at = datetime.now(timezone.utc)
    await db.commit()

    return None


@router.get("/duplicates/", response_model=List[DuplicatePair])
async def get_duplicates(
    type: Literal["importers", "exporters"] = Query(..., description="Type of companies to check"),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
) -> List[DuplicatePair]:
    """
    Find potential duplicate companies using fuzzy name matching (80% threshold)

    Args:
        type: "importers" or "exporters"

    Returns:
        List of DuplicatePair objects sorted by similarity (highest first)

    Raises:
        HTTPException 401: Not authenticated
    """
    # Authenticate user
    current_user = await get_current_user(request, db)

    # Select model based on type
    Model = Importer if type == "importers" else Exporter
    ListItemSchema = ImporterListItem if type == "importers" else ExporterListItem

    # Query all companies for the organization
    stmt = select(Model).where(
        and_(
            Model.organization_id == current_user.organization_id,
            Model.deleted_at.is_(None)
        )
    )
    result = await db.execute(stmt)
    companies = result.scalars().all()

    # Find duplicates using fuzzy matching
    duplicates = []
    threshold = 0.80  # 80% similarity threshold

    for i, company1 in enumerate(companies):
        for company2 in companies[i+1:]:
            # Calculate similarity on normalized names
            similarity = master_data_service.calculate_similarity(
                company1.name_normalized,
                company2.name_normalized
            )

            if similarity >= threshold:
                # Add to duplicates list
                duplicates.append({
                    "company1": ListItemSchema.model_validate(company1),
                    "company2": ListItemSchema.model_validate(company2),
                    "similarity": similarity,
                    "reason": f"Name similarity: {int(similarity * 100)}%"
                })

    # Sort by similarity (highest first)
    duplicates.sort(key=lambda x: x["similarity"], reverse=True)

    return duplicates


@router.post("/merge/", response_model=ImporterDetail | ExporterDetail)
async def merge_companies(
    type: Literal["importers", "exporters"] = Query(..., description="Type of companies to merge"),
    merge_request: MergeRequest = None,
    request: Request = None,
    db: AsyncSession = Depends(get_db)
) -> ImporterDetail | ExporterDetail:
    """
    Merge two companies - keep one, merge the other's declarations, and soft delete merged company

    Args:
        type: "importers" or "exporters"
        merge_request: keep_id and merge_id

    Returns:
        ImporterDetail or ExporterDetail (the kept company with updated counts)

    Raises:
        HTTPException 404: One or both companies not found
        HTTPException 403: Not authorized to merge these companies
        HTTPException 400: Cannot merge the same company or companies from different organizations
        HTTPException 401: Not authenticated
    """
    # Authenticate user
    current_user = await get_current_user(request, db)

    # Validate merge request
    if merge_request.keep_id == merge_request.merge_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot merge a company with itself"
        )

    # Select model based on type
    Model = Importer if type == "importers" else Exporter
    DetailSchema = ImporterDetail if type == "importers" else ExporterDetail

    # Query both companies
    stmt = select(Model).where(Model.id.in_([merge_request.keep_id, merge_request.merge_id]))
    result = await db.execute(stmt)
    companies = result.scalars().all()

    if len(companies) != 2:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both companies not found"
        )

    # Identify keep and merge companies
    keep_company = next((c for c in companies if c.id == merge_request.keep_id), None)
    merge_company = next((c for c in companies if c.id == merge_request.merge_id), None)

    if not keep_company or not merge_company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both companies not found"
        )

    # Check organization access
    if (keep_company.organization_id != current_user.organization_id or
        merge_company.organization_id != current_user.organization_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to merge these companies"
        )

    # Ensure both companies belong to same organization
    if keep_company.organization_id != merge_company.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot merge companies from different organizations"
        )

    # Update all declarations from merge_company to keep_company
    foreign_key_field = "importer_id" if type == "importers" else "exporter_id"
    update_stmt = (
        select(Declaration)
        .where(getattr(Declaration, foreign_key_field) == merge_request.merge_id)
    )
    result = await db.execute(update_stmt)
    declarations_to_update = result.scalars().all()

    for declaration in declarations_to_update:
        setattr(declaration, foreign_key_field, merge_request.keep_id)

    # Update keep_company statistics
    keep_company.declaration_count += merge_company.declaration_count
    keep_company.last_reviewed_by_user_id = current_user.id
    keep_company.last_reviewed_at = datetime.now(timezone.utc)

    # Soft delete merge_company
    merge_company.deleted_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(keep_company)

    return DetailSchema.model_validate(keep_company)
