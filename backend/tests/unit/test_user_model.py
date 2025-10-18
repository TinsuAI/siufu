"""Unit tests for User model."""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.user import User, Base


@pytest.mark.unit
async def test_user_creation(db_session: AsyncSession):
    """Test creating a user with required fields."""
    # Arrange
    user = User(
        email="test@example.com",
        hashed_password="hashed_password_123",
        full_name="Test User"
    )

    # Act
    db_session.add(user)
    await db_session.flush()  # Flush to get the ID without committing

    # Assert
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.hashed_password == "hashed_password_123"
    assert user.full_name == "Test User"
    assert user.is_active is True  # Default value
    assert user.is_superuser is False  # Default value
    assert isinstance(user.created_at, datetime)
    assert isinstance(user.updated_at, datetime)


@pytest.mark.unit
async def test_user_creation_minimal_fields(db_session: AsyncSession):
    """Test creating a user with only required fields."""
    # Arrange
    user = User(
        email="minimal@example.com",
        hashed_password="hashed_password_456"
    )

    # Act
    db_session.add(user)
    await db_session.flush()

    # Assert
    assert user.id is not None
    assert user.email == "minimal@example.com"
    assert user.full_name is None  # Optional field
    assert user.is_active is True
    assert user.is_superuser is False


@pytest.mark.unit
async def test_user_superuser_flag(db_session: AsyncSession):
    """Test creating a superuser."""
    # Arrange
    admin_user = User(
        email="admin@example.com",
        hashed_password="admin_password_hash",
        full_name="Admin User",
        is_superuser=True
    )

    # Act
    db_session.add(admin_user)
    await db_session.flush()

    # Assert
    assert admin_user.is_superuser is True
    assert admin_user.is_active is True


@pytest.mark.unit
async def test_user_inactive_flag(db_session: AsyncSession):
    """Test creating an inactive user."""
    # Arrange
    inactive_user = User(
        email="inactive@example.com",
        hashed_password="inactive_password_hash",
        is_active=False
    )

    # Act
    db_session.add(inactive_user)
    await db_session.flush()

    # Assert
    assert inactive_user.is_active is False


@pytest.mark.unit
async def test_user_repr():
    """Test User string representation."""
    # Arrange
    user = User(
        email="repr@example.com",
        hashed_password="password_hash",
        is_active=True
    )
    user.id = 42  # Manually set ID for testing

    # Act
    repr_str = repr(user)

    # Assert
    assert "User" in repr_str
    assert "id=42" in repr_str
    assert "email='repr@example.com'" in repr_str
    assert "is_active=True" in repr_str


@pytest.mark.unit
async def test_user_timestamps(db_session: AsyncSession):
    """Test that timestamps are automatically set."""
    # Arrange
    user = User(
        email="timestamp@example.com",
        hashed_password="password_hash"
    )

    # Act
    db_session.add(user)
    await db_session.flush()
    created_at = user.created_at
    updated_at = user.updated_at

    # Assert
    assert created_at is not None
    assert updated_at is not None
    assert created_at == updated_at  # Should be equal on creation
    assert isinstance(created_at, datetime)
    assert isinstance(updated_at, datetime)
