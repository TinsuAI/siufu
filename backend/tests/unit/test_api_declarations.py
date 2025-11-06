"""
Unit tests for declaration approval, rejection, and export API endpoints
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, timezone
from pathlib import Path
from fastapi import HTTPException
from httpx import AsyncClient

from src.models.declaration import DeclarationStatus


@pytest.fixture
def mock_declaration():
    """Create mock declaration for testing"""
    declaration = Mock()
    declaration.id = uuid4()
    declaration.status = DeclarationStatus.READY_FOR_REVIEW
    declaration.uploaded_files = {}
    declaration.extracted_data = {}
    declaration.draft_data = {}
    declaration.processing_progress = 1.0
    declaration.processing_error = None
    declaration.approved_by_user_id = None
    declaration.approved_at = None
    declaration.organization_id = uuid4()
    declaration.created_by_user_id = uuid4()
    return declaration


@pytest.fixture
def mock_user():
    """Create mock user for authentication"""
    user = Mock()
    user.id = uuid4()
    user.organization_id = uuid4()
    user.email = "test@example.com"
    return user


@pytest.fixture
def mock_db():
    """Create mock database session"""
    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()
    return db


class TestApproveEndpoint:
    """Tests for POST /api/declarations/{id}/approve endpoint"""

    @pytest.mark.asyncio
    async def test_approve_success(self, mock_declaration, mock_user, mock_db):
        """Test successful approval of READY_FOR_REVIEW declaration"""
        from src.api.v1.declarations import approve_declaration
        from fastapi import Request

        # Setup
        mock_declaration.status = DeclarationStatus.READY_FOR_REVIEW
        mock_request = Mock(spec=Request)

        # Mock dependencies
        with patch('src.api.v1.declarations.get_current_user', return_value=mock_user) as mock_get_user, \
             patch('src.api.v1.declarations.DeclarationRepository') as MockRepo:

            mock_repo = MockRepo.return_value
            mock_repo.get_by_id = AsyncMock(return_value=mock_declaration)

            # Execute
            result = await approve_declaration(
                declaration_id=mock_declaration.id,
                request=mock_request,
                db=mock_db
            )

            # Assert
            assert result.id == mock_declaration.id
            assert result.status == "APPROVED"
            assert result.approved_by_user_id == mock_user.id
            assert result.approved_at is not None
            assert result.message == "Declaration approved successfully"
            assert mock_declaration.status == "APPROVED"
            assert mock_declaration.approved_by_user_id == mock_user.id
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_approve_declaration_not_found(self, mock_user, mock_db):
        """Test approval fails when declaration does not exist"""
        from src.api.v1.declarations import approve_declaration
        from fastapi import Request

        mock_request = Mock(spec=Request)
        declaration_id = uuid4()

        with patch('src.api.v1.declarations.get_current_user', return_value=mock_user), \
             patch('src.api.v1.declarations.DeclarationRepository') as MockRepo:

            mock_repo = MockRepo.return_value
            mock_repo.get_by_id = AsyncMock(return_value=None)

            # Execute & Assert
            with pytest.raises(HTTPException) as exc_info:
                await approve_declaration(
                    declaration_id=declaration_id,
                    request=mock_request,
                    db=mock_db
                )

            assert exc_info.value.status_code == 404
            assert "not found" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_approve_invalid_status(self, mock_declaration, mock_user, mock_db):
        """Test approval fails when declaration is not READY_FOR_REVIEW"""
        from src.api.v1.declarations import approve_declaration
        from fastapi import Request

        # Setup - declaration in UPLOADED status (not ready for approval)
        mock_declaration.status = DeclarationStatus.UPLOADED
        mock_request = Mock(spec=Request)

        with patch('src.api.v1.declarations.get_current_user', return_value=mock_user), \
             patch('src.api.v1.declarations.DeclarationRepository') as MockRepo:

            mock_repo = MockRepo.return_value
            mock_repo.get_by_id = AsyncMock(return_value=mock_declaration)

            # Execute & Assert
            with pytest.raises(HTTPException) as exc_info:
                await approve_declaration(
                    declaration_id=mock_declaration.id,
                    request=mock_request,
                    db=mock_db
                )

            assert exc_info.value.status_code == 400
            assert "READY_FOR_REVIEW" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_approve_records_timestamp_utc(self, mock_declaration, mock_user, mock_db):
        """Test that approval timestamp is recorded in UTC"""
        from src.api.v1.declarations import approve_declaration
        from fastapi import Request

        mock_declaration.status = DeclarationStatus.READY_FOR_REVIEW
        mock_request = Mock(spec=Request)

        with patch('src.api.v1.declarations.get_current_user', return_value=mock_user), \
             patch('src.api.v1.declarations.DeclarationRepository') as MockRepo:

            mock_repo = MockRepo.return_value
            mock_repo.get_by_id = AsyncMock(return_value=mock_declaration)

            result = await approve_declaration(
                declaration_id=mock_declaration.id,
                request=mock_request,
                db=mock_db
            )

            # Assert timestamp is set and has timezone info
            assert mock_declaration.approved_at is not None
            assert mock_declaration.approved_at.tzinfo is not None


class TestRejectEndpoint:
    """Tests for POST /api/declarations/{id}/reject endpoint"""

    @pytest.mark.asyncio
    async def test_reject_success(self, mock_declaration, mock_user, mock_db):
        """Test successful rejection of READY_FOR_REVIEW declaration"""
        from src.api.v1.declarations import reject_declaration
        from src.schemas.declaration import DeclarationRejectRequest
        from fastapi import Request

        # Setup
        mock_declaration.status = DeclarationStatus.READY_FOR_REVIEW
        mock_request = Mock(spec=Request)
        reject_request = DeclarationRejectRequest(
            rejection_reason="Incomplete invoice information"
        )

        with patch('src.api.v1.declarations.get_current_user', return_value=mock_user), \
             patch('src.api.v1.declarations.DeclarationRepository') as MockRepo:

            mock_repo = MockRepo.return_value
            mock_repo.get_by_id = AsyncMock(return_value=mock_declaration)

            # Execute
            result = await reject_declaration(
                declaration_id=mock_declaration.id,
                reject_request=reject_request,
                request=mock_request,
                db=mock_db
            )

            # Assert
            assert result.id == mock_declaration.id
            assert result.status == "REJECTED"
            assert result.rejection_reason == "Incomplete invoice information"
            assert result.message == "Declaration rejected successfully"
            assert mock_declaration.status == "REJECTED"
            assert mock_declaration.processing_error == "Incomplete invoice information"
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_reject_declaration_not_found(self, mock_user, mock_db):
        """Test rejection fails when declaration does not exist"""
        from src.api.v1.declarations import reject_declaration
        from src.schemas.declaration import DeclarationRejectRequest
        from fastapi import Request

        mock_request = Mock(spec=Request)
        declaration_id = uuid4()
        reject_request = DeclarationRejectRequest(
            rejection_reason="Test rejection reason"
        )

        with patch('src.api.v1.declarations.get_current_user', return_value=mock_user), \
             patch('src.api.v1.declarations.DeclarationRepository') as MockRepo:

            mock_repo = MockRepo.return_value
            mock_repo.get_by_id = AsyncMock(return_value=None)

            # Execute & Assert
            with pytest.raises(HTTPException) as exc_info:
                await reject_declaration(
                    declaration_id=declaration_id,
                    reject_request=reject_request,
                    request=mock_request,
                    db=mock_db
                )

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_reject_invalid_status(self, mock_declaration, mock_user, mock_db):
        """Test rejection fails when declaration is not READY_FOR_REVIEW"""
        from src.api.v1.declarations import reject_declaration
        from src.schemas.declaration import DeclarationRejectRequest
        from fastapi import Request

        # Setup - declaration already APPROVED
        mock_declaration.status = DeclarationStatus.APPROVED
        mock_request = Mock(spec=Request)
        reject_request = DeclarationRejectRequest(
            rejection_reason="Test rejection reason"
        )

        with patch('src.api.v1.declarations.get_current_user', return_value=mock_user), \
             patch('src.api.v1.declarations.DeclarationRepository') as MockRepo:

            mock_repo = MockRepo.return_value
            mock_repo.get_by_id = AsyncMock(return_value=mock_declaration)

            # Execute & Assert
            with pytest.raises(HTTPException) as exc_info:
                await reject_declaration(
                    declaration_id=mock_declaration.id,
                    reject_request=reject_request,
                    request=mock_request,
                    db=mock_db
                )

            assert exc_info.value.status_code == 400
            assert "READY_FOR_REVIEW" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_reject_validation_min_length(self):
        """Test that rejection reason must be at least 10 characters"""
        from src.schemas.declaration import DeclarationRejectRequest
        from pydantic import ValidationError

        # Test rejection reason too short
        with pytest.raises(ValidationError) as exc_info:
            DeclarationRejectRequest(rejection_reason="Short")

        assert "at least 10 characters" in str(exc_info.value).lower()


class TestExportEndpoint:
    """Tests for GET /api/declarations/{id}/export endpoint"""

    @pytest.mark.asyncio
    async def test_export_success(self, mock_declaration, mock_user, mock_db, tmp_path):
        """Test successful export of APPROVED declaration"""
        from src.api.v1.declarations import export_declaration
        from fastapi import Request

        # Setup
        mock_declaration.status = DeclarationStatus.APPROVED
        mock_request = Mock(spec=Request)

        # Create temporary Excel file
        export_dir = tmp_path / "data" / "exports" / str(mock_declaration.id)
        export_dir.mkdir(parents=True)
        excel_file = export_dir / "CD.xlsx"
        excel_file.write_bytes(b"fake excel content")

        with patch('src.api.v1.declarations.get_current_user', return_value=mock_user), \
             patch('src.api.v1.declarations.DeclarationRepository') as MockRepo, \
             patch('pathlib.Path') as MockPath:

            mock_repo = MockRepo.return_value
            mock_repo.get_by_id = AsyncMock(return_value=mock_declaration)

            # Mock Path to return our temp file
            mock_path_instance = Mock()
            mock_path_instance.exists = Mock(return_value=True)
            mock_path_instance.__str__ = Mock(return_value=str(excel_file))
            MockPath.return_value = mock_path_instance

            # Execute
            result = await export_declaration(
                declaration_id=mock_declaration.id,
                request=mock_request,
                db=mock_db
            )

            # Assert
            assert result.path == str(excel_file)
            assert result.filename == f"CD_{mock_declaration.id}.xlsx"
            assert result.media_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            assert "Cache-Control" in result.headers
            assert "private, max-age=3600" in result.headers["Cache-Control"]

    @pytest.mark.asyncio
    async def test_export_declaration_not_found(self, mock_user, mock_db):
        """Test export fails when declaration does not exist"""
        from src.api.v1.declarations import export_declaration
        from fastapi import Request

        mock_request = Mock(spec=Request)
        declaration_id = uuid4()

        with patch('src.api.v1.declarations.get_current_user', return_value=mock_user), \
             patch('src.api.v1.declarations.DeclarationRepository') as MockRepo:

            mock_repo = MockRepo.return_value
            mock_repo.get_by_id = AsyncMock(return_value=None)

            # Execute & Assert
            with pytest.raises(HTTPException) as exc_info:
                await export_declaration(
                    declaration_id=declaration_id,
                    request=mock_request,
                    db=mock_db
                )

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_export_not_approved(self, mock_declaration, mock_user, mock_db):
        """Test export fails when declaration is not APPROVED"""
        from src.api.v1.declarations import export_declaration
        from fastapi import Request

        # Setup - declaration in READY_FOR_REVIEW status
        mock_declaration.status = DeclarationStatus.READY_FOR_REVIEW
        mock_request = Mock(spec=Request)

        with patch('src.api.v1.declarations.get_current_user', return_value=mock_user), \
             patch('src.api.v1.declarations.DeclarationRepository') as MockRepo:

            mock_repo = MockRepo.return_value
            mock_repo.get_by_id = AsyncMock(return_value=mock_declaration)

            # Execute & Assert
            with pytest.raises(HTTPException) as exc_info:
                await export_declaration(
                    declaration_id=mock_declaration.id,
                    request=mock_request,
                    db=mock_db
                )

            assert exc_info.value.status_code == 403
            assert "APPROVED" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_export_file_not_generated(self, mock_declaration, mock_user, mock_db):
        """Test export fails when Excel file does not exist"""
        from src.api.v1.declarations import export_declaration
        from fastapi import Request

        # Setup
        mock_declaration.status = DeclarationStatus.APPROVED
        mock_request = Mock(spec=Request)

        with patch('src.api.v1.declarations.get_current_user', return_value=mock_user), \
             patch('src.api.v1.declarations.DeclarationRepository') as MockRepo, \
             patch('pathlib.Path') as MockPath:

            mock_repo = MockRepo.return_value
            mock_repo.get_by_id = AsyncMock(return_value=mock_declaration)

            # Mock Path.exists() to return False
            mock_path_instance = Mock()
            mock_path_instance.exists = Mock(return_value=False)
            MockPath.return_value = mock_path_instance

            # Execute & Assert
            with pytest.raises(HTTPException) as exc_info:
                await export_declaration(
                    declaration_id=mock_declaration.id,
                    request=mock_request,
                    db=mock_db
                )

            assert exc_info.value.status_code == 404
            assert "not yet generated" in str(exc_info.value.detail).lower()


class TestListDeclarationsEndpoint:
    """Tests for GET /api/declarations endpoint (Story 3.9)"""

    @pytest.mark.asyncio
    async def test_list_declarations_default_pagination(self, mock_user, mock_db):
        """Test listing declarations with default pagination"""
        from src.api.v1.declarations import list_declarations
        from fastapi import Request

        # Setup - create mock declarations
        mock_declarations = []
        for i in range(5):
            decl = Mock()
            decl.id = uuid4()
            decl.status = DeclarationStatus.APPROVED
            decl.created_at = datetime.now(timezone.utc)
            decl.updated_at = datetime.now(timezone.utc)
            decl.approved_at = datetime.now(timezone.utc)
            decl.deleted_at = None
            decl.draft_data = {"products": [{"name": f"Product {j}"} for j in range(10)]}
            decl.created_by_user_id = mock_user.id
            mock_declarations.append(decl)

        mock_request = Mock(spec=Request)

        # Mock database execution
        mock_result = Mock()
        mock_result.scalars = Mock(return_value=Mock(all=Mock(return_value=mock_declarations)))
        mock_result.scalar_one = Mock(return_value=5)  # total count

        with patch('src.api.v1.declarations.get_current_user', return_value=mock_user):
            # Mock execute to return results for both count and select queries
            mock_db.execute = AsyncMock(side_effect=[
                Mock(scalar_one=Mock(return_value=5)),  # count query
                mock_result  # select query
            ])

            # Execute
            result = await list_declarations(
                request=mock_request,
                page=1,
                limit=20,
                status_filter=None,
                search=None,
                sort_by="created_at",
                sort_order="desc",
                db=mock_db
            )

            # Assert
            assert result.total == 5
            assert result.page == 1
            assert result.limit == 20
            assert result.total_pages == 1
            assert len(result.items) == 5
            assert result.items[0].products_count == 10

    @pytest.mark.asyncio
    async def test_list_declarations_with_status_filter(self, mock_user, mock_db):
        """Test listing declarations filtered by status"""
        from src.api.v1.declarations import list_declarations
        from fastapi import Request

        mock_request = Mock(spec=Request)
        mock_result = Mock()
        mock_result.scalars = Mock(return_value=Mock(all=Mock(return_value=[])))

        with patch('src.api.v1.declarations.get_current_user', return_value=mock_user):
            mock_db.execute = AsyncMock(side_effect=[
                Mock(scalar_one=Mock(return_value=0)),  # count
                mock_result  # select
            ])

            # Execute with status filter
            result = await list_declarations(
                request=mock_request,
                page=1,
                limit=20,
                status_filter="APPROVED",
                search=None,
                sort_by="created_at",
                sort_order="desc",
                db=mock_db
            )

            # Assert
            assert result.total == 0
            assert len(result.items) == 0

    @pytest.mark.asyncio
    async def test_list_declarations_with_search(self, mock_user, mock_db):
        """Test listing declarations with search by ID"""
        from src.api.v1.declarations import list_declarations
        from fastapi import Request

        mock_request = Mock(spec=Request)
        mock_result = Mock()
        mock_result.scalars = Mock(return_value=Mock(all=Mock(return_value=[])))

        with patch('src.api.v1.declarations.get_current_user', return_value=mock_user):
            mock_db.execute = AsyncMock(side_effect=[
                Mock(scalar_one=Mock(return_value=0)),
                mock_result
            ])

            # Execute with search
            result = await list_declarations(
                request=mock_request,
                page=1,
                limit=20,
                status_filter=None,
                search="abc123",
                sort_by="created_at",
                sort_order="desc",
                db=mock_db
            )

            assert result.total == 0

    @pytest.mark.asyncio
    async def test_list_declarations_invalid_sort_by(self, mock_user, mock_db):
        """Test listing declarations with invalid sort_by parameter"""
        from src.api.v1.declarations import list_declarations
        from fastapi import Request

        mock_request = Mock(spec=Request)

        with patch('src.api.v1.declarations.get_current_user', return_value=mock_user):
            # Execute with invalid sort_by
            with pytest.raises(HTTPException) as exc_info:
                await list_declarations(
                    request=mock_request,
                    page=1,
                    limit=20,
                    status_filter=None,
                    search=None,
                    sort_by="invalid_field",
                    sort_order="desc",
                    db=mock_db
                )

            assert exc_info.value.status_code == 400
            assert "Invalid sort_by" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_list_declarations_calculates_products_count(self, mock_user, mock_db):
        """Test that products_count is calculated correctly from draft_data"""
        from src.api.v1.declarations import list_declarations
        from fastapi import Request

        # Setup - declaration with products in draft_data
        decl = Mock()
        decl.id = uuid4()
        decl.status = DeclarationStatus.READY_FOR_REVIEW
        decl.created_at = datetime.now(timezone.utc)
        decl.updated_at = datetime.now(timezone.utc)
        decl.approved_at = None
        decl.deleted_at = None
        decl.draft_data = {"products": [{"name": "P1"}, {"name": "P2"}, {"name": "P3"}]}
        decl.created_by_user_id = mock_user.id

        mock_request = Mock(spec=Request)
        mock_result = Mock()
        mock_result.scalars = Mock(return_value=Mock(all=Mock(return_value=[decl])))

        with patch('src.api.v1.declarations.get_current_user', return_value=mock_user):
            mock_db.execute = AsyncMock(side_effect=[
                Mock(scalar_one=Mock(return_value=1)),
                mock_result
            ])

            result = await list_declarations(
                request=mock_request,
                page=1,
                limit=20,
                status_filter=None,
                search=None,
                sort_by="created_at",
                sort_order="desc",
                db=mock_db
            )

            # Assert products_count is 3
            assert len(result.items) == 1
            assert result.items[0].products_count == 3


class TestDeleteDeclarationEndpoint:
    """Tests for DELETE /api/declarations/{id} endpoint (Story 3.9)"""

    @pytest.mark.asyncio
    async def test_delete_declaration_success(self, mock_declaration, mock_user, mock_db):
        """Test successful soft delete of declaration"""
        from src.api.v1.declarations import delete_declaration
        from fastapi import Request

        # Setup
        mock_declaration.created_by_user_id = mock_user.id
        mock_declaration.deleted_at = None
        mock_request = Mock(spec=Request)

        with patch('src.api.v1.declarations.get_current_user', return_value=mock_user), \
             patch('src.api.v1.declarations.DeclarationRepository') as MockRepo:

            mock_repo = MockRepo.return_value
            mock_repo.get_by_id = AsyncMock(return_value=mock_declaration)

            # Execute
            result = await delete_declaration(
                declaration_id=mock_declaration.id,
                request=mock_request,
                db=mock_db
            )

            # Assert
            assert result.status_code == 204
            assert mock_declaration.deleted_at is not None
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_declaration_not_found(self, mock_user, mock_db):
        """Test delete fails when declaration does not exist"""
        from src.api.v1.declarations import delete_declaration
        from fastapi import Request

        mock_request = Mock(spec=Request)
        declaration_id = uuid4()

        with patch('src.api.v1.declarations.get_current_user', return_value=mock_user), \
             patch('src.api.v1.declarations.DeclarationRepository') as MockRepo:

            mock_repo = MockRepo.return_value
            mock_repo.get_by_id = AsyncMock(return_value=None)

            # Execute & Assert
            with pytest.raises(HTTPException) as exc_info:
                await delete_declaration(
                    declaration_id=declaration_id,
                    request=mock_request,
                    db=mock_db
                )

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_declaration_unauthorized(self, mock_declaration, mock_user, mock_db):
        """Test delete fails when user doesn't own the declaration"""
        from src.api.v1.declarations import delete_declaration
        from fastapi import Request

        # Setup - declaration owned by different user
        mock_declaration.created_by_user_id = uuid4()  # Different user ID
        mock_declaration.deleted_at = None
        mock_request = Mock(spec=Request)

        with patch('src.api.v1.declarations.get_current_user', return_value=mock_user), \
             patch('src.api.v1.declarations.DeclarationRepository') as MockRepo:

            mock_repo = MockRepo.return_value
            mock_repo.get_by_id = AsyncMock(return_value=mock_declaration)

            # Execute & Assert
            with pytest.raises(HTTPException) as exc_info:
                await delete_declaration(
                    declaration_id=mock_declaration.id,
                    request=mock_request,
                    db=mock_db
                )

            assert exc_info.value.status_code == 403
            assert "not authorized" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_delete_already_deleted_declaration(self, mock_declaration, mock_user, mock_db):
        """Test delete fails when declaration already deleted"""
        from src.api.v1.declarations import delete_declaration
        from fastapi import Request

        # Setup - declaration already deleted
        mock_declaration.created_by_user_id = mock_user.id
        mock_declaration.deleted_at = datetime.now(timezone.utc)
        mock_request = Mock(spec=Request)

        with patch('src.api.v1.declarations.get_current_user', return_value=mock_user), \
             patch('src.api.v1.declarations.DeclarationRepository') as MockRepo:

            mock_repo = MockRepo.return_value
            mock_repo.get_by_id = AsyncMock(return_value=mock_declaration)

            # Execute & Assert
            with pytest.raises(HTTPException) as exc_info:
                await delete_declaration(
                    declaration_id=mock_declaration.id,
                    request=mock_request,
                    db=mock_db
                )

            assert exc_info.value.status_code == 404
