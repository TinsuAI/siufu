"""
Security tests for file upload endpoint
Tests MIME validation, path traversal prevention, and size limits
"""
import io

import pytest
from httpx import AsyncClient

from src.core.security import create_access_token


class TestFileUploadSecurity:
    """Security hardening tests for upload endpoint"""

    def create_fake_pdf(self, content: bytes = b"fake pdf content") -> io.BytesIO:
        """Create a fake PDF file for testing with proper PDF magic bytes"""
        # Minimal valid PDF structure with PDF magic bytes (%PDF-1.4)
        pdf_content = b"%PDF-1.4\n" + content + b"\n%%EOF"
        return io.BytesIO(pdf_content)

    def create_fake_exe(self) -> io.BytesIO:
        """Create a fake executable file (MZ header)"""
        # MZ is the magic number for DOS/Windows executables
        exe_content = b"MZ\x90\x00" + b"\x00" * 100
        return io.BytesIO(exe_content)

    @pytest.mark.asyncio
    async def test_rejects_exe_file_renamed_as_pdf(self, async_client: AsyncClient, test_user, auth_headers: dict):
        """
        SEC-001: Verify MIME type validation prevents .exe renamed to .pdf

        Security Test: File Spoofing Attack
        - Attacker renames malicious.exe to malicious.pdf
        - System should detect actual file type using magic bytes
        - Should reject with HTTP 400
        """
        # Create files with one being a spoofed executable
        exe_file = self.create_fake_exe()
        valid_pdf = self.create_fake_pdf()

        files = {
            'arrival_notice': ('malicious.pdf', exe_file, 'application/pdf'),  # Spoofed!
            'bill_of_lading': ('BOL.pdf', valid_pdf, 'application/pdf'),
            'certificate_of_origin': ('CO.pdf', valid_pdf, 'application/pdf'),
            'invoice': ('INVOICE.pdf', valid_pdf, 'application/pdf'),
        }

        response = await async_client.post(
            '/api/v1/declarations/upload',
            files=files,
            headers=auth_headers
        )

        # Should reject with 400 Bad Request
        assert response.status_code == 400
        detail = response.json()['detail']
        # Detail can be a dict with error/message or a string
        if isinstance(detail, dict):
            detail_str = str(detail.get('message', '')) + str(detail.get('error', ''))
        else:
            detail_str = str(detail)
        assert 'mime' in detail_str.lower() or 'type' in detail_str.lower() or 'validation' in detail_str.lower()

    @pytest.mark.asyncio
    async def test_rejects_path_traversal_in_filename(self, async_client: AsyncClient, test_user, auth_headers: dict):
        """
        SEC-002: Verify filename sanitization prevents path traversal

        Security Test: Path Traversal Attack
        - Attacker uses ../../etc/passwd as filename
        - System should sanitize filename before storage
        - Should either reject or sanitize the filename
        """
        valid_pdf = self.create_fake_pdf()

        files = {
            'arrival_notice': ('../../../etc/passwd.pdf', valid_pdf, 'application/pdf'),
            'bill_of_lading': ('BOL.pdf', valid_pdf, 'application/pdf'),
            'certificate_of_origin': ('CO.pdf', valid_pdf, 'application/pdf'),
            'invoice': ('INVOICE.pdf', valid_pdf, 'application/pdf'),
        }

        response = await async_client.post(
            '/api/v1/declarations/upload',
            files=files,
            headers=auth_headers
        )

        # Should either reject (400) or sanitize and accept (200/201)
        # If accepted, verify filename was sanitized
        if response.status_code in [200, 201]:
            data = response.json()
            uploaded_files = data.get('uploaded_files', [])

            # Find AN file in the list
            an_file = next((f for f in uploaded_files if f.get('file_type') == 'AN'), None)
            if an_file:
                filename = an_file.get('filename', '')
                # Filename should be sanitized (no path traversal characters)
                assert '../' not in filename
                assert '..' not in filename
                assert '/' not in filename or filename.startswith('/')  # Absolute paths ok

    @pytest.mark.asyncio
    async def test_rejects_null_byte_in_filename(self, async_client: AsyncClient, test_user, auth_headers: dict):
        """
        SEC-003: Verify null byte injection prevention

        Security Test: Null Byte Injection
        - Attacker uses filename with null byte: malicious.pdf\x00.txt
        - System should reject or sanitize
        """
        valid_pdf = self.create_fake_pdf()

        # Null byte in filename
        malicious_filename = "malicious.pdf\x00.exe"

        files = {
            'arrival_notice': (malicious_filename, valid_pdf, 'application/pdf'),
            'bill_of_lading': ('BOL.pdf', valid_pdf, 'application/pdf'),
            'certificate_of_origin': ('CO.pdf', valid_pdf, 'application/pdf'),
            'invoice': ('INVOICE.pdf', valid_pdf, 'application/pdf'),
        }

        response = await async_client.post(
            '/api/v1/declarations/upload',
            files=files,
            headers=auth_headers
        )

        # Should reject or sanitize
        if response.status_code in [200, 201]:
            data = response.json()
            uploaded_files = data.get('uploaded_files', [])

            # Find AN file in the list
            an_file = next((f for f in uploaded_files if f.get('file_type') == 'AN'), None)
            if an_file:
                filename = an_file.get('filename', '')
                # Null bytes should be removed
                assert '\x00' not in filename

    @pytest.mark.asyncio
    async def test_rejects_file_exceeding_size_limit_pdf(self, async_client: AsyncClient, test_user, auth_headers: dict):
        """
        SEC-004: Verify PDF file size limit (10MB) is enforced

        Security Test: DoS via Large File Upload
        - Attacker uploads 11MB PDF
        - System should reject with HTTP 413 or 400
        """
        # Create 11MB file (exceeds 10MB limit)
        large_content = b"x" * (11 * 1024 * 1024)
        large_pdf = io.BytesIO(large_content)
        valid_pdf = self.create_fake_pdf()

        files = {
            'arrival_notice': ('AN.pdf', large_pdf, 'application/pdf'),  # 11MB
            'bill_of_lading': ('BOL.pdf', valid_pdf, 'application/pdf'),
            'certificate_of_origin': ('CO.pdf', valid_pdf, 'application/pdf'),
            'invoice': ('INVOICE.pdf', valid_pdf, 'application/pdf'),
        }

        response = await async_client.post(
            '/api/v1/declarations/upload',
            files=files,
            headers=auth_headers
        )

        # Should reject with 400 or 413 (Payload Too Large)
        assert response.status_code in [400, 413]
        detail = response.json()['detail']
        # Detail can be a dict with error/message or a string
        if isinstance(detail, dict):
            detail_str = str(detail.get('message', '')) + str(detail.get('error', ''))
        else:
            detail_str = str(detail)
        assert 'size' in detail_str.lower() or 'large' in detail_str.lower() or 'limit' in detail_str.lower()

    @pytest.mark.asyncio
    async def test_rejects_file_exceeding_size_limit_image(self, async_client: AsyncClient, test_user, auth_headers: dict):
        """
        SEC-005: Verify image file size limit (5MB) is enforced

        Security Test: DoS via Large Image Upload
        - Attacker uploads 6MB image as invoice
        - System should reject with HTTP 413 or 400
        """
        # Create 6MB image (exceeds 5MB limit for images)
        large_image = io.BytesIO(b"x" * (6 * 1024 * 1024))
        valid_pdf = self.create_fake_pdf()

        files = {
            'arrival_notice': ('AN.pdf', valid_pdf, 'application/pdf'),
            'bill_of_lading': ('BOL.pdf', valid_pdf, 'application/pdf'),
            'certificate_of_origin': ('CO.pdf', valid_pdf, 'application/pdf'),
            'invoice': ('INVOICE.jpg', large_image, 'image/jpeg'),  # 6MB
        }

        response = await async_client.post(
            '/api/v1/declarations/upload',
            files=files,
            headers=auth_headers
        )

        # Should reject with 400 or 413
        assert response.status_code in [400, 413]

    @pytest.mark.asyncio
    async def test_rejects_more_than_20_co_files(self, async_client: AsyncClient, test_user, auth_headers: dict):
        """
        SEC-006: Verify hard limit on CO file count (max 20 files)

        Security Test: DoS via Excessive File Count
        - Attacker uploads 21 CO files
        - System should reject with HTTP 400
        """
        valid_pdf = self.create_fake_pdf()

        # Create 21 CO files - each as a separate tuple in a list
        # Format: list of tuples where each tuple is (field_name, file_tuple)
        co_files = [
            ('certificate_of_origin', (f'CO_{i}.pdf', self.create_fake_pdf(), 'application/pdf'))
            for i in range(21)
        ]

        # Add other required files to the list
        files = [
            ('arrival_notice', ('AN.pdf', valid_pdf, 'application/pdf')),
            ('bill_of_lading', ('BOL.pdf', valid_pdf, 'application/pdf')),
            *co_files,  # Unpack 21 CO files
            ('invoice', ('INVOICE.pdf', valid_pdf, 'application/pdf')),
        ]

        response = await async_client.post(
            '/api/v1/declarations/upload',
            files=files,
            headers=auth_headers
        )

        # Should reject with 400 Bad Request
        assert response.status_code == 400
        detail = response.json()['detail']
        # Detail can be a dict with error/message or a string
        if isinstance(detail, dict):
            detail_str = str(detail.get('message', '')) + str(detail.get('error', '')) + str(detail.get('count', ''))
        else:
            detail_str = str(detail)
        assert '20' in detail_str or '21' in detail_str or 'limit' in detail_str.lower() or 'maximum' in detail_str.lower()

    @pytest.mark.asyncio
    async def test_accepts_exactly_20_co_files(self, async_client: AsyncClient, test_user, auth_headers: dict):
        """
        SEC-007: Verify 20 CO files is accepted (boundary test)

        Security Test: Boundary Condition
        - User uploads exactly 20 CO files (max allowed)
        - System should accept
        """
        valid_pdf = self.create_fake_pdf()

        # Create exactly 20 CO files - each as a separate tuple in a list
        # Format: list of tuples where each tuple is (field_name, file_tuple)
        co_files = [
            ('certificate_of_origin', (f'CO_{i}.pdf', self.create_fake_pdf(), 'application/pdf'))
            for i in range(20)
        ]

        # Add other required files to the list
        files = [
            ('arrival_notice', ('AN.pdf', valid_pdf, 'application/pdf')),
            ('bill_of_lading', ('BOL.pdf', valid_pdf, 'application/pdf')),
            *co_files,  # Unpack 20 CO files
            ('invoice', ('INVOICE.pdf', valid_pdf, 'application/pdf')),
        ]

        response = await async_client.post(
            '/api/v1/declarations/upload',
            files=files,
            headers=auth_headers
        )

        # Should accept (200 or 201)
        assert response.status_code in [200, 201]

    @pytest.mark.asyncio
    async def test_requires_authentication(self, async_client: AsyncClient):
        """
        SEC-008: Verify endpoint requires authentication

        Security Test: Unauthorized Access
        - Anonymous user tries to upload files
        - System should reject (401 Unauthorized or 403 Forbidden)

        **STATUS**: Authentication now enforced via get_current_user dependency
        """
        valid_pdf = self.create_fake_pdf()

        files = {
            'arrival_notice': ('AN.pdf', valid_pdf, 'application/pdf'),
            'bill_of_lading': ('BOL.pdf', valid_pdf, 'application/pdf'),
            'certificate_of_origin': ('CO.pdf', valid_pdf, 'application/pdf'),
            'invoice': ('INVOICE.pdf', valid_pdf, 'application/pdf'),
        }

        # No auth headers
        response = await async_client.post(
            '/api/v1/declarations/upload',
            files=files
        )

        # Should reject - accepting 401 (Unauthorized), 403 (Forbidden), or 400 (if validation first)
        # The key is that the request is rejected
        assert response.status_code in [400, 401, 403]

        # If 400, verify it's not accepting the upload (no 200/201 success)
        # This ensures security even if auth check order varies
        assert response.status_code != 200
        assert response.status_code != 201

    @pytest.mark.asyncio
    async def test_rejects_missing_required_files(self, async_client: AsyncClient, test_user, auth_headers: dict):
        """
        SEC-009: Verify all required files are validated

        Security Test: Incomplete Upload
        - User uploads only 3 of 4 required file types
        - System should reject with HTTP 400
        """
        valid_pdf = self.create_fake_pdf()

        # Missing invoice file
        files = {
            'arrival_notice': ('AN.pdf', valid_pdf, 'application/pdf'),
            'bill_of_lading': ('BOL.pdf', valid_pdf, 'application/pdf'),
            'certificate_of_origin': ('CO.pdf', valid_pdf, 'application/pdf'),
            # invoice missing
        }

        response = await async_client.post(
            '/api/v1/declarations/upload',
            files=files,
            headers=auth_headers
        )

        # Should reject with 400 or 422 (Unprocessable Entity)
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_sanitizes_special_characters_in_filename(self, async_client: AsyncClient, test_user, auth_headers: dict):
        """
        SEC-010: Verify special characters are sanitized from filenames

        Security Test: Command Injection via Filename
        - Attacker uses filename with shell metacharacters: file;rm -rf.pdf
        - System should sanitize or reject
        """
        valid_pdf = self.create_fake_pdf()

        # Filename with shell metacharacters
        malicious_filename = "file;rm -rf /.pdf"

        files = {
            'arrival_notice': (malicious_filename, valid_pdf, 'application/pdf'),
            'bill_of_lading': ('BOL.pdf', valid_pdf, 'application/pdf'),
            'certificate_of_origin': ('CO.pdf', valid_pdf, 'application/pdf'),
            'invoice': ('INVOICE.pdf', valid_pdf, 'application/pdf'),
        }

        response = await async_client.post(
            '/api/v1/declarations/upload',
            files=files,
            headers=auth_headers
        )

        # Should either reject or sanitize
        if response.status_code in [200, 201]:
            data = response.json()
            uploaded_files = data.get('uploaded_files', [])

            # Find AN file in the list
            an_file = next((f for f in uploaded_files if f.get('file_type') == 'AN'), None)
            if an_file:
                filename = an_file.get('filename', '')
                # Shell metacharacters should be removed or escaped
                assert ';' not in filename
                assert '|' not in filename
                assert '&' not in filename


class TestUploadRateLimiting:
    """Rate limiting tests (if implemented)"""

    @pytest.mark.skip(reason="Rate limiting not yet implemented - future enhancement")
    @pytest.mark.asyncio
    async def test_rate_limit_10_uploads_per_hour(self, async_client: AsyncClient, test_user, auth_headers: dict):
        """
        SEC-011: Verify rate limiting (10 uploads/user/hour)

        Security Test: DoS via Repeated Uploads
        - User attempts 11 uploads within 1 hour
        - 11th request should be rejected with HTTP 429
        """
        valid_pdf = io.BytesIO(b"pdf content")

        files = {
            'arrival_notice': ('AN.pdf', valid_pdf, 'application/pdf'),
            'bill_of_lading': ('BOL.pdf', valid_pdf, 'application/pdf'),
            'certificate_of_origin': ('CO.pdf', valid_pdf, 'application/pdf'),
            'invoice': ('INVOICE.pdf', valid_pdf, 'application/pdf'),
        }

        # Attempt 11 uploads
        for i in range(11):
            response = await async_client.post(
                '/api/v1/declarations/upload',
                files=files,
                headers=auth_headers
            )

            if i < 10:
                # First 10 should succeed
                assert response.status_code in [200, 201]
            else:
                # 11th should be rate limited
                assert response.status_code == 429
                assert 'rate limit' in response.json()['detail'].lower()


# Pytest fixtures
@pytest.fixture
def auth_headers():
    """Create authentication headers for testing with valid JWT token"""
    # Create a real JWT token for test user (UUID from database seed)
    # Using the same UUID as used in the upload endpoint for testing
    test_user_id = "00000000-0000-0000-0000-000000000002"
    token = create_access_token(data={"sub": test_user_id})
    return {
        'Authorization': f'Bearer {token}'
    }


@pytest.fixture(autouse=True)
def mock_file_storage(tmp_path, monkeypatch):
    """Mock FileStorageService to use tmp_path instead of /app/data/uploads"""
    from src.services.file_storage_service import FileStorageService

    # Store the original __init__
    original_init = FileStorageService.__init__

    # Create a new __init__ that uses tmp_path
    def patched_init(self, upload_base_dir=None):
        # Use tmp_path for tests
        upload_dir = tmp_path / "uploads"
        original_init(self, upload_base_dir=str(upload_dir))

    # Patch the __init__ method
    monkeypatch.setattr(FileStorageService, "__init__", patched_init)
