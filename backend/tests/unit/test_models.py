"""Unit tests for database models."""

import pytest
from datetime import datetime, timezone
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.organization import Organization
from src.models.user import User, UserRole
from src.models.declaration import Declaration, DeclarationStatus


@pytest.mark.unit
class TestOrganizationModel:
    """Tests for Organization model."""

    async def test_organization_creation(self, db_session: AsyncSession):
        """Test creating an organization with required fields."""
        # Arrange
        org = Organization(name="Test Company Ltd")

        # Act
        db_session.add(org)
        await db_session.flush()

        # Assert
        assert org.id is not None
        assert isinstance(org.id, uuid.UUID)
        assert org.name == "Test Company Ltd"
        assert isinstance(org.created_at, datetime)
        assert isinstance(org.updated_at, datetime)
        assert org.created_at == org.updated_at

    async def test_organization_repr(self):
        """Test Organization string representation."""
        # Arrange
        org = Organization(name="Repr Test Co")
        org.id = uuid.uuid4()

        # Act
        repr_str = repr(org)

        # Assert
        assert "Organization" in repr_str
        assert str(org.id) in repr_str
        assert "Repr Test Co" in repr_str


@pytest.mark.unit
class TestUserModel:
    """Tests for User model."""

    async def test_user_creation_with_all_fields(self, db_session: AsyncSession):
        """Test creating a user with all required fields."""
        # Arrange - Create organization first
        org = Organization(name="Test Org")
        db_session.add(org)
        await db_session.flush()

        # Create user
        user = User(
            email="test@example.com",
            hashed_password="hashed_password_123",
            full_name="Test User",
            role=UserRole.processor,
            organization_id=org.id
        )

        # Act
        db_session.add(user)
        await db_session.flush()

        # Assert
        assert user.id is not None
        assert isinstance(user.id, uuid.UUID)
        assert user.email == "test@example.com"
        assert user.hashed_password == "hashed_password_123"
        assert user.full_name == "Test User"
        assert user.role == UserRole.processor
        assert user.is_active is True  # Default value
        assert user.organization_id == org.id
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)

    async def test_user_role_enum_values(self, db_session: AsyncSession):
        """Test User role enum accepts valid values."""
        # Arrange
        org = Organization(name="Test Org")
        db_session.add(org)
        await db_session.flush()

        # Test processor role
        processor = User(
            email="processor@example.com",
            hashed_password="hash",
            full_name="Processor User",
            role=UserRole.processor,
            organization_id=org.id
        )

        # Test admin role
        admin = User(
            email="admin@example.com",
            hashed_password="hash",
            full_name="Admin User",
            role=UserRole.admin,
            organization_id=org.id
        )

        # Act
        db_session.add(processor)
        db_session.add(admin)
        await db_session.flush()

        # Assert
        assert processor.role == UserRole.processor
        assert admin.role == UserRole.admin

    async def test_user_default_role_is_processor(self, db_session: AsyncSession):
        """Test that default user role is 'processor'."""
        # Arrange
        org = Organization(name="Test Org")
        db_session.add(org)
        await db_session.flush()

        user = User(
            email="default@example.com",
            hashed_password="hash",
            full_name="Default User",
            organization_id=org.id
            # Note: role not specified, should default to processor
        )

        # Act
        db_session.add(user)
        await db_session.flush()

        # Assert
        assert user.role == UserRole.processor

    async def test_user_inactive_flag(self, db_session: AsyncSession):
        """Test creating an inactive user."""
        # Arrange
        org = Organization(name="Test Org")
        db_session.add(org)
        await db_session.flush()

        inactive_user = User(
            email="inactive@example.com",
            hashed_password="hash",
            full_name="Inactive User",
            organization_id=org.id,
            is_active=False
        )

        # Act
        db_session.add(inactive_user)
        await db_session.flush()

        # Assert
        assert inactive_user.is_active is False

    async def test_user_email_uniqueness(self, db_session: AsyncSession):
        """Test that email must be unique (constraint will be enforced at DB level)."""
        # Arrange
        org = Organization(name="Test Org")
        db_session.add(org)
        await db_session.flush()

        user1 = User(
            email="unique@example.com",
            hashed_password="hash1",
            full_name="User 1",
            organization_id=org.id
        )

        user2 = User(
            email="unique@example.com",  # Same email
            hashed_password="hash2",
            full_name="User 2",
            organization_id=org.id
        )

        # Act & Assert
        db_session.add(user1)
        await db_session.flush()

        db_session.add(user2)
        with pytest.raises(Exception):  # Will raise IntegrityError
            await db_session.flush()

    async def test_user_repr(self):
        """Test User string representation."""
        # Arrange
        user = User(
            email="repr@example.com",
            hashed_password="hash",
            full_name="Repr User",
            role=UserRole.admin,
            organization_id=uuid.uuid4()
        )
        user.id = uuid.uuid4()

        # Act
        repr_str = repr(user)

        # Assert
        assert "User" in repr_str
        assert str(user.id) in repr_str
        assert "repr@example.com" in repr_str
        assert "UserRole.admin" in repr_str


@pytest.mark.unit
class TestDeclarationModel:
    """Tests for Declaration model."""

    async def test_declaration_creation_minimal(self, db_session: AsyncSession):
        """Test creating a declaration with minimal required fields."""
        # Arrange - Create organization and user first
        org = Organization(name="Test Org")
        db_session.add(org)
        await db_session.flush()

        user = User(
            email="creator@example.com",
            hashed_password="hash",
            full_name="Creator",
            organization_id=org.id
        )
        db_session.add(user)
        await db_session.flush()

        # Create declaration
        declaration = Declaration(
            organization_id=org.id,
            created_by_user_id=user.id
        )

        # Act
        db_session.add(declaration)
        await db_session.flush()

        # Assert
        assert declaration.id is not None
        assert isinstance(declaration.id, uuid.UUID)
        assert declaration.status == DeclarationStatus.UPLOADED  # Default
        assert declaration.organization_id == org.id
        assert declaration.created_by_user_id == user.id
        assert declaration.processing_progress == 0.0  # Default
        assert declaration.uploaded_files is None
        assert declaration.extracted_data is None
        assert declaration.draft_data is None
        assert declaration.deleted_at is None
        assert isinstance(declaration.created_at, datetime)

    async def test_declaration_status_enum_values(self, db_session: AsyncSession):
        """Test Declaration status enum accepts all valid values."""
        # Arrange
        org = Organization(name="Test Org")
        db_session.add(org)
        await db_session.flush()

        user = User(
            email="user@example.com",
            hashed_password="hash",
            full_name="User",
            organization_id=org.id
        )
        db_session.add(user)
        await db_session.flush()

        # Test each status
        statuses = [
            DeclarationStatus.UPLOADED,
            DeclarationStatus.PROCESSING,
            DeclarationStatus.VALIDATING,
            DeclarationStatus.READY_FOR_REVIEW,
            DeclarationStatus.APPROVED,
            DeclarationStatus.REJECTED,
            DeclarationStatus.FAILED
        ]

        for status in statuses:
            decl = Declaration(
                status=status,
                organization_id=org.id,
                created_by_user_id=user.id
            )
            db_session.add(decl)

        # Act
        await db_session.flush()

        # Assert - all declarations created successfully
        # (if enum values were invalid, flush would fail)

    async def test_declaration_jsonb_fields(self, db_session: AsyncSession):
        """Test Declaration JSONB field serialization."""
        # Arrange
        org = Organization(name="Test Org")
        db_session.add(org)
        await db_session.flush()

        user = User(
            email="user@example.com",
            hashed_password="hash",
            full_name="User",
            organization_id=org.id
        )
        db_session.add(user)
        await db_session.flush()

        test_data = {
            "invoice_number": "INV-2025-001",
            "total_value": 50000.00,
            "currency": "USD"
        }

        test_warnings = [
            {"field": "hs_code", "message": "Low confidence"},
            {"field": "quantity", "message": "Mismatch with invoice"}
        ]

        declaration = Declaration(
            organization_id=org.id,
            created_by_user_id=user.id,
            draft_data=test_data,
            validation_warnings=test_warnings,
            confidence_scores={"hs_code": 0.85, "quantity": 0.92}
        )

        # Act
        db_session.add(declaration)
        await db_session.flush()
        await db_session.refresh(declaration)

        # Assert
        assert declaration.draft_data == test_data
        assert declaration.validation_warnings == test_warnings
        assert declaration.confidence_scores["hs_code"] == 0.85

    async def test_declaration_approval_fields(self, db_session: AsyncSession):
        """Test Declaration approval tracking fields."""
        # Arrange
        org = Organization(name="Test Org")
        db_session.add(org)
        await db_session.flush()

        creator = User(
            email="creator@example.com",
            hashed_password="hash",
            full_name="Creator",
            organization_id=org.id
        )
        approver = User(
            email="approver@example.com",
            hashed_password="hash",
            full_name="Approver",
            role=UserRole.admin,
            organization_id=org.id
        )
        db_session.add_all([creator, approver])
        await db_session.flush()

        # Create and approve declaration
        declaration = Declaration(
            organization_id=org.id,
            created_by_user_id=creator.id,
            status=DeclarationStatus.APPROVED,
            approved_by_user_id=approver.id,
            approved_at=datetime.now(timezone.utc)
        )

        # Act
        db_session.add(declaration)
        await db_session.flush()

        # Assert
        assert declaration.approved_by_user_id == approver.id
        assert declaration.approved_at is not None
        assert isinstance(declaration.approved_at, datetime)

    async def test_declaration_soft_delete(self, db_session: AsyncSession):
        """Test Declaration soft delete functionality."""
        # Arrange
        org = Organization(name="Test Org")
        db_session.add(org)
        await db_session.flush()

        user = User(
            email="user@example.com",
            hashed_password="hash",
            full_name="User",
            organization_id=org.id
        )
        db_session.add(user)
        await db_session.flush()

        declaration = Declaration(
            organization_id=org.id,
            created_by_user_id=user.id
        )
        db_session.add(declaration)
        await db_session.flush()

        # Act - Soft delete
        declaration.deleted_at = datetime.now(timezone.utc)
        await db_session.flush()

        # Assert
        assert declaration.deleted_at is not None
        assert isinstance(declaration.deleted_at, datetime)

    async def test_declaration_repr(self):
        """Test Declaration string representation."""
        # Arrange
        declaration = Declaration(
            status=DeclarationStatus.PROCESSING,
            organization_id=uuid.uuid4(),
            created_by_user_id=uuid.uuid4()
        )
        declaration.id = uuid.uuid4()

        # Act
        repr_str = repr(declaration)

        # Assert
        assert "Declaration" in repr_str
        assert str(declaration.id) in repr_str
        assert "DeclarationStatus.PROCESSING" in repr_str
