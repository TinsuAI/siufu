"""
FastAPI dependencies for authentication and authorization
"""
from uuid import UUID

from fastapi import HTTPException, Request, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import verify_token
from src.models.user import User
from src.repositories.user_repository import UserRepository


async def get_current_user(request: Request, db: AsyncSession) -> User:
    """
    Dependency to get the current authenticated user from JWT token.

    Extracts JWT token from httpOnly cookie (or Authorization header as fallback),
    validates it, and returns the User object.

    Args:
        request: FastAPI Request object
        db: Database session

    Returns:
        User object of the authenticated user

    Raises:
        HTTPException: 401 if token is invalid, expired, or user not found/inactive
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Try to get token from cookie first (primary method)
    token = request.cookies.get("access_token")

    # Fallback to Authorization header (for API clients)
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")

    if not token:
        raise credentials_exception

    try:
        # Verify and decode the JWT token
        payload = verify_token(token)
        user_id_str: str = payload.get("sub")

        if user_id_str is None:
            raise credentials_exception

        user_id = UUID(user_id_str)

    except (JWTError, ValueError):
        raise credentials_exception

    # Get user from database
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise credentials_exception

    return user


async def get_current_active_user(request: Request, db: AsyncSession) -> User:
    """
    Dependency to get the current active user.
    This is a convenience wrapper around get_current_user.

    Args:
        request: FastAPI Request object
        db: Database session

    Returns:
        Active User object

    Raises:
        HTTPException: 401 if user is not authenticated or not active
    """
    user = await get_current_user(request, db)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user"
        )

    return user


async def get_current_admin_user(request: Request, db: AsyncSession) -> User:
    """
    Dependency to get the current user and verify they have admin role.

    Args:
        request: FastAPI Request object
        db: Database session

    Returns:
        User object with admin role

    Raises:
        HTTPException: 401 if user is not authenticated
        HTTPException: 403 if user is not an admin
    """
    user = await get_current_user(request, db)

    if user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    return user
