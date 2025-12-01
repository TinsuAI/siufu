"""Unit tests for repository pattern."""

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.declaration import Declaration, DeclarationStatus
from src.models.organization import Organization
from src.models.user import User, UserRole
from src.repositories.base import BaseRepository
from src.repositories.declaration_repository import DeclarationRepository
from src.repositories.user_repository import UserRepository


@pytest.mark.unit
class TestBaseRepository:
    """Tests for BaseRepository CRUD operations."""

    async def test_create(self, db_session: AsyncSession):
        """Test repository create method."""
        # Arrange
        repo = BaseRepository(Organization, db_session)
        org_data = {"name": "Created Org"}

        # Act
        org = await repo.create(org_data)

        # Assert
        assert org.id is not None
        assert org.name == "Created Org"
        assert isinstance(org.created_at, datetime)

    async def test_get_by_id(self, db_session: AsyncSession):
        """Test repository get_by_id method."""
        # Arrange
        repo = BaseRepository(Organization, db_session)
        org = Organization(name="Find Me")
        db_session.add(org)
        await db_session.flush()
        org_id = org.id

        # Act
        found = await repo.get_by_id(org_id)

        # Assert
        assert found is not None
        assert found.id == org_id
        assert found.name == "Find Me"

    async def test_get_by_id_not_found(self, db_session: AsyncSession):
        """Test get_by_id returns None for non-existent ID."""
        # Arrange
        repo = BaseRepository(Organization, db_session)
        fake_id = uuid.uuid4()

        # Act
        found = await repo.get_by_id(fake_id)

        # Assert
        assert found is None

    async def test_get_multi_with_pagination(self, db_session: AsyncSession):
        """Test repository get_multi with pagination."""
        # Arrange
        repo = BaseRepository(Organization, db_session)

        # Create 5 organizations
        for i in range(5):
            org = Organization(name=f"Org {i}")
            db_session.add(org)
        await db_session.flush()

        # Act - Get first 2
        results = await repo.get_multi(skip=0, limit=2)

        # Assert
        assert len(results) == 2

        # Act - Get next 2
        results = await repo.get_multi(skip=2, limit=2)

        # Assert
        assert len(results) == 2

    async def test_get_multi_with_filters(self, db_session: AsyncSession):
        """Test repository get_multi with filters."""
        # Arrange
        org1 = Organization(name="Test Org 1")
        org2 = Organization(name="Test Org 2")
        db_session.add_all([org1, org2])
        await db_session.flush()

        # Create users for org1 and org2
        user1 = User(
            email="user1@org1.com",
            hashed_password="hash",
            full_name="User 1",
            organization_id=org1.id
        )
        user2 = User(
            email="user2@org2.com",
            hashed_password="hash",
            full_name="User 2",
            organization_id=org2.id
        )
        db_session.add_all([user1, user2])
        await db_session.flush()

        repo = BaseRepository(User, db_session)

        # Act - Filter by organization_id
        results = await repo.get_multi(filters={"organization_id": org1.id})

        # Assert
        assert len(results) == 1
        assert results[0].email == "user1@org1.com"

    async def test_update(self, db_session: AsyncSession):
        """Test repository update method."""
        # Arrange
        repo = BaseRepository(Organization, db_session)
        org = Organization(name="Old Name")
        db_session.add(org)
        await db_session.flush()
        org_id = org.id

        # Act
        updated = await repo.update(org_id, {"name": "New Name"})

        # Assert
        assert updated is not None
        assert updated.id == org_id
        assert updated.name == "New Name"

    async def test_update_not_found(self, db_session: AsyncSession):
        """Test update returns None for non-existent ID."""
        # Arrange
        repo = BaseRepository(Organization, db_session)
        fake_id = uuid.uuid4()

        # Act
        updated = await repo.update(fake_id, {"name": "Will Not Work"})

        # Assert
        assert updated is None

    async def test_delete_hard_delete(self, db_session: AsyncSession):
        """Test hard delete for models without deleted_at column."""
        # Arrange
        repo = BaseRepository(Organization, db_session)
        org = Organization(name="To Delete")
        db_session.add(org)
        await db_session.flush()
        org_id = org.id

        # Act
        result = await repo.delete(org_id)

        # Assert
        assert result is True
        found = await repo.get_by_id(org_id)
        assert found is None  # Hard deleted

    async def test_delete_soft_delete(self, db_session: AsyncSession):
        """Test soft delete for models with deleted_at column."""
        # Arrange
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

        declaration = Declaration(
            organization_id=org.id,
            created_by_user_id=user.id
        )
        db_session.add(declaration)
        await db_session.flush()
        decl_id = declaration.id

        repo = BaseRepository(Declaration, db_session)

        # Act
        result = await repo.delete(decl_id)

        # Assert
        assert result is True
        found = await repo.get_by_id(decl_id)
        assert found is not None  # Still exists
        assert found.deleted_at is not None  # But marked as deleted

    async def test_delete_not_found(self, db_session: AsyncSession):
        """Test delete returns False for non-existent ID."""
        # Arrange
        repo = BaseRepository(Organization, db_session)
        fake_id = uuid.uuid4()

        # Act
        result = await repo.delete(fake_id)

        # Assert
        assert result is False

    async def test_count_without_filters(self, db_session: AsyncSession):
        """Test repository count method without filters."""
        # Arrange
        repo = BaseRepository(Organization, db_session)

        # Get initial count (may have pre-existing organizations from other tests)
        initial_count = await repo.count()

        # Create 3 organizations
        for i in range(3):
            org = Organization(name=f"Org {i}")
            db_session.add(org)
        await db_session.flush()

        # Act
        count = await repo.count()

        # Assert - should have 3 more than initial
        assert count == initial_count + 3

    async def test_count_with_filters(self, db_session: AsyncSession):
        """Test repository count method with filters."""
        # Arrange
        org = Organization(name="Test Org")
        db_session.add(org)
        await db_session.flush()

        repo = BaseRepository(User, db_session)

        # Get initial counts (may have pre-existing users from other tests)
        initial_active_count = await repo.count(filters={"is_active": True})
        initial_inactive_count = await repo.count(filters={"is_active": False})

        # Create active and inactive users
        active_user = User(
            email="active@example.com",
            hashed_password="hash",
            full_name="Active",
            is_active=True,
            organization_id=org.id
        )
        inactive_user = User(
            email="inactive@example.com",
            hashed_password="hash",
            full_name="Inactive",
            is_active=False,
            organization_id=org.id
        )
        db_session.add_all([active_user, inactive_user])
        await db_session.flush()

        # Act
        active_count = await repo.count(filters={"is_active": True})
        inactive_count = await repo.count(filters={"is_active": False})

        # Assert - should have 1 more than initial for each
        assert active_count == initial_active_count + 1
        assert inactive_count == initial_inactive_count + 1


@pytest.mark.unit
class TestUserRepository:
    """Tests for UserRepository specific methods."""

    async def test_get_by_email(self, db_session: AsyncSession):
        """Test UserRepository.get_by_email method."""
        # Arrange
        org = Organization(name="Test Org")
        db_session.add(org)
        await db_session.flush()

        user = User(
            email="findme@example.com",
            hashed_password="hash",
            full_name="Find Me",
            organization_id=org.id
        )
        db_session.add(user)
        await db_session.flush()

        repo = UserRepository(db_session)

        # Act
        found = await repo.get_by_email("findme@example.com")

        # Assert
        assert found is not None
        assert found.email == "findme@example.com"
        assert found.full_name == "Find Me"

    async def test_get_by_email_not_found(self, db_session: AsyncSession):
        """Test get_by_email returns None for non-existent email."""
        # Arrange
        repo = UserRepository(db_session)

        # Act
        found = await repo.get_by_email("nonexistent@example.com")

        # Assert
        assert found is None

    async def test_create_user_with_defaults(self, db_session: AsyncSession):
        """Test UserRepository.create with default role."""
        # Arrange
        from src.schemas.auth import RegisterRequest
        org = Organization(name="Test Org")
        db_session.add(org)
        await db_session.flush()

        repo = UserRepository(db_session)
        user_data = RegisterRequest(
            email="newuser@example.com",
            password="PlainText123!",  # Must have uppercase, lowercase, number, special char
            full_name="New User"
        )

        # Act
        user = await repo.create(
            user_data=user_data,
            organization_id=org.id
        )

        # Assert
        assert user.id is not None
        assert user.email == "newuser@example.com"
        assert user.full_name == "New User"
        assert user.hashed_password is not None  # Password should be hashed
        assert user.role == UserRole.processor  # Default
        assert user.is_active is True

    async def test_create_user_with_admin_role(self, db_session: AsyncSession):
        """Test creating user and then updating role to admin."""
        # Arrange
        from src.schemas.auth import RegisterRequest
        org = Organization(name="Test Org")
        db_session.add(org)
        await db_session.flush()

        repo = UserRepository(db_session)
        user_data = RegisterRequest(
            email="admin@example.com",
            password="AdminPassword123!",  # Must have uppercase, lowercase, number, special char
            full_name="Admin User"
        )

        # Act - create user with default role
        admin = await repo.create(
            user_data=user_data,
            organization_id=org.id
        )

        # Update role to admin
        admin.role = UserRole.admin
        await db_session.commit()
        await db_session.refresh(admin)

        # Assert
        assert admin.role == UserRole.admin


@pytest.mark.unit
class TestDeclarationRepository:
    """Tests for DeclarationRepository specific methods."""

    async def test_get_by_status(self, db_session: AsyncSession):
        """Test DeclarationRepository.get_by_status method."""
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

        # Create declarations with different statuses
        uploaded = Declaration(
            status=DeclarationStatus.UPLOADED,
            organization_id=org.id,
            created_by_user_id=user.id
        )
        processing = Declaration(
            status=DeclarationStatus.PROCESSING,
            organization_id=org.id,
            created_by_user_id=user.id
        )
        approved = Declaration(
            status=DeclarationStatus.APPROVED,
            organization_id=org.id,
            created_by_user_id=user.id
        )
        db_session.add_all([uploaded, processing, approved])
        await db_session.flush()

        repo = DeclarationRepository(db_session)

        # Act
        uploaded_decls = await repo.get_by_status(DeclarationStatus.UPLOADED)
        processing_decls = await repo.get_by_status(DeclarationStatus.PROCESSING)

        # Assert
        assert len(uploaded_decls) == 1
        assert uploaded_decls[0].status == DeclarationStatus.UPLOADED

        assert len(processing_decls) == 1
        assert processing_decls[0].status == DeclarationStatus.PROCESSING

    async def test_get_by_status_excludes_soft_deleted(self, db_session: AsyncSession):
        """Test get_by_status excludes soft-deleted declarations."""
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

        # Create uploaded declarations
        active = Declaration(
            status=DeclarationStatus.UPLOADED,
            organization_id=org.id,
            created_by_user_id=user.id
        )
        deleted = Declaration(
            status=DeclarationStatus.UPLOADED,
            organization_id=org.id,
            created_by_user_id=user.id,
            deleted_at=datetime.now(timezone.utc)
        )
        db_session.add_all([active, deleted])
        await db_session.flush()

        repo = DeclarationRepository(db_session)

        # Act
        results = await repo.get_by_status(DeclarationStatus.UPLOADED)

        # Assert
        assert len(results) == 1  # Only active, not deleted
        assert results[0].id == active.id

    async def test_update_draft_data_merge(self, db_session: AsyncSession):
        """Test DeclarationRepository.update_draft_data merges correctly."""
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

        # Create declaration with initial draft data
        declaration = Declaration(
            organization_id=org.id,
            created_by_user_id=user.id,
            draft_data={
                "invoice_number": "INV-001",
                "total_value": 50000.00
            }
        )
        db_session.add(declaration)
        await db_session.flush()
        decl_id = declaration.id

        repo = DeclarationRepository(db_session)

        # Act - Merge new fields
        updated = await repo.update_draft_data(
            decl_id,
            {"currency": "USD", "total_value": 55000.00}  # Update existing + add new
        )

        # Assert
        assert updated is not None
        assert updated.draft_data["invoice_number"] == "INV-001"  # Preserved
        assert updated.draft_data["total_value"] == 55000.00  # Updated
        assert updated.draft_data["currency"] == "USD"  # Added

    async def test_update_draft_data_empty_initial(self, db_session: AsyncSession):
        """Test update_draft_data works with initially empty draft_data."""
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
            created_by_user_id=user.id,
            draft_data=None  # Initially empty
        )
        db_session.add(declaration)
        await db_session.flush()

        repo = DeclarationRepository(db_session)

        # Act
        updated = await repo.update_draft_data(
            declaration.id,
            {"field1": "value1"}
        )

        # Assert
        assert updated is not None
        assert updated.draft_data == {"field1": "value1"}

    async def test_update_draft_data_not_found(self, db_session: AsyncSession):
        """Test update_draft_data returns None for non-existent declaration."""
        # Arrange
        repo = DeclarationRepository(db_session)
        fake_id = uuid.uuid4()

        # Act
        result = await repo.update_draft_data(fake_id, {"field": "value"})

        # Assert
        assert result is None

    async def test_get_by_organization(self, db_session: AsyncSession):
        """Test DeclarationRepository.get_by_organization method."""
        # Arrange
        org1 = Organization(name="Org 1")
        org2 = Organization(name="Org 2")
        db_session.add_all([org1, org2])
        await db_session.flush()

        user1 = User(
            email="user1@org1.com",
            hashed_password="hash",
            full_name="User 1",
            organization_id=org1.id
        )
        user2 = User(
            email="user2@org2.com",
            hashed_password="hash",
            full_name="User 2",
            organization_id=org2.id
        )
        db_session.add_all([user1, user2])
        await db_session.flush()

        # Create declarations for both orgs
        decl1 = Declaration(organization_id=org1.id, created_by_user_id=user1.id)
        decl2 = Declaration(organization_id=org1.id, created_by_user_id=user1.id)
        decl3 = Declaration(organization_id=org2.id, created_by_user_id=user2.id)
        db_session.add_all([decl1, decl2, decl3])
        await db_session.flush()

        repo = DeclarationRepository(db_session)

        # Act
        org1_declarations = await repo.get_by_organization(org1.id)

        # Assert
        assert len(org1_declarations) == 2
        assert all(d.organization_id == org1.id for d in org1_declarations)

    async def test_get_by_organization_excludes_soft_deleted(self, db_session: AsyncSession):
        """Test get_by_organization excludes soft-deleted declarations."""
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

        active = Declaration(
            organization_id=org.id,
            created_by_user_id=user.id
        )
        deleted = Declaration(
            organization_id=org.id,
            created_by_user_id=user.id,
            deleted_at=datetime.now(timezone.utc)
        )
        db_session.add_all([active, deleted])
        await db_session.flush()

        repo = DeclarationRepository(db_session)

        # Act
        results = await repo.get_by_organization(org.id)

        # Assert
        assert len(results) == 1  # Only active
        assert results[0].id == active.id
