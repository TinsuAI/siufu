"""
Authentication API endpoints
"""
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_db
from src.core.security import (
    create_access_token,
    verify_password,
)
from src.repositories.user_repository import UserRepository
from src.schemas.auth import LoginRequest, LoginResponse, RegisterRequest
from src.schemas.auth import User as UserSchema

router = APIRouter()


@router.post("/register", response_model=LoginResponse, status_code=201)
async def register(
    user_data: RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    User registration endpoint

    Creates a new user account with hashed password and returns JWT token.

    - **email**: Valid email address
    - **password**: Minimum 8 characters
    - **full_name**: User's full name

    Returns:
        LoginResponse with user profile and JWT access token
    """
    user_repo = UserRepository(db)

    # Check if email already exists
    existing_user = await user_repo.get_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Get or create demo organization (for MVP, all users belong to same org)
    from sqlalchemy import select

    from src.models.organization import Organization

    result = await db.execute(
        select(Organization).where(Organization.name == "Demo Organization")
    )
    organization = result.scalars().first()

    if not organization:
        # Create demo organization if it doesn't exist
        organization = Organization(
            name="Demo Organization"
        )
        db.add(organization)
        await db.flush()
        await db.refresh(organization)

    # Create new user
    user = await user_repo.create(user_data, organization.id)

    # Create access token
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
            "organization_id": str(user.organization_id)
        },
        expires_delta=timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)
    )

    # Set httpOnly cookie
    # In production, domain=.tinsu.ai allows cookie to work across subdomains
    # (siufu.tinsu.ai and siufu-api.tinsu.ai)
    is_production = "tinsu.ai" in settings.CORS_ORIGINS
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=is_production,  # True for HTTPS in production, False for HTTP in dev/test
        samesite="lax",  # Changed from "strict" to allow cross-subdomain navigation
        domain=".tinsu.ai" if is_production else None,
        max_age=settings.ACCESS_TOKEN_EXPIRE_HOURS * 3600  # Convert hours to seconds
    )

    # Convert user model to schema
    user_schema = UserSchema(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        is_active=user.is_active,
        organization_id=str(user.organization_id),
        created_at=user.created_at.isoformat(),
        updated_at=user.updated_at.isoformat()
    )

    return LoginResponse(
        user=user_schema,
        access_token=access_token,
        token_type="bearer"
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    credentials: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    User login endpoint

    Validates credentials and returns JWT token in httpOnly cookie.

    - **email**: User email address
    - **password**: User password

    Returns:
        LoginResponse with user profile and JWT access token
    """
    user_repo = UserRepository(db)

    # Get user by email
    user = await user_repo.get_by_email(credentials.email)

    # Validate credentials (generic error message to prevent user enumeration)
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # Create access token
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
            "organization_id": str(user.organization_id)
        },
        expires_delta=timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)
    )

    # Set httpOnly cookie
    # In production, domain=.tinsu.ai allows cookie to work across subdomains
    # (siufu.tinsu.ai and siufu-api.tinsu.ai)
    is_production = "tinsu.ai" in settings.CORS_ORIGINS
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=is_production,  # True for HTTPS in production, False for HTTP in dev/test
        samesite="lax",  # Changed from "strict" to allow cross-subdomain navigation
        domain=".tinsu.ai" if is_production else None,
        max_age=settings.ACCESS_TOKEN_EXPIRE_HOURS * 3600  # Convert hours to seconds
    )

    # Convert user model to schema
    user_schema = UserSchema(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        is_active=user.is_active,
        organization_id=str(user.organization_id),
        created_at=user.created_at.isoformat(),
        updated_at=user.updated_at.isoformat()
    )

    return LoginResponse(
        user=user_schema,
        access_token=access_token,
        token_type="bearer"
    )


@router.post("/logout")
async def logout(response: Response):
    """
    User logout endpoint

    Clears the authentication cookie to invalidate the session.
    """
    # Clear the access_token cookie by setting max_age to 0
    is_production = "tinsu.ai" in settings.CORS_ORIGINS
    response.set_cookie(
        key="access_token",
        value="",
        httponly=True,
        secure=is_production,  # True for HTTPS in production, False for HTTP in dev/test
        samesite="lax",
        domain=".tinsu.ai" if is_production else None,
        max_age=0
    )

    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserSchema)
async def get_current_user_profile(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Get current authenticated user profile

    Returns user details based on JWT token from httpOnly cookie.
    This endpoint is used for session validation and restoring user state.
    """
    from src.core.deps import get_current_user

    # Use the authentication dependency to get the user
    user = await get_current_user(request, db)

    # Convert user model to schema
    user_schema = UserSchema(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        is_active=user.is_active,
        organization_id=str(user.organization_id),
        created_at=user.created_at.isoformat(),
        updated_at=user.updated_at.isoformat()
    )

    return user_schema
