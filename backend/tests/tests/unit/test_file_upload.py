"""
Unit tests for file upload functionality

Tests file validation and storage services.
"""
import uuid
from io import BytesIO
from unittest.mock import patch

import pytest
from fastapi import UploadFile

from src.services.file_storage_service import FileStorageService
from src.services.file_validation_service import (
    FileSizeLimitExceeded,
    FileValidationError,
    FileValidationService,
)


class TestFileValidationService:
    """Tests for FileValidationService"""

    @pytest.fixture
    def validation_service(self):
        """Create a FileValidationService instance"""
        return FileValidationService()

    def create_mock_upload_file(
        self,
        filename: str,
        content: bytes,
        content_type: str
    ) -> UploadFile:
        """Create a mock UploadFile for testing"""
        file_obj = BytesIO(content)
        upload_file = UploadFile(
            filename=filename,
            file=file_obj,
            content_type=content_type
        )
        # Make seek and read async
        async def async_seek(*args):
            return file_obj.seek(*args)

        async def async_read(size=-1):
            return file_obj.read(size)

        async def async_tell():
            return file_obj.tell()

        upload_file.seek = async_seek
        upload_file.read = async_read
        upload_file.tell = async_tell

        return upload_file

    @pytest.mark.asyncio
    async def test_validate_all_files_present_success(self, validation_service):
        """Test that all required files being present passes validation"""
        # Create mock files
        pdf_content = b"%PDF-1.4\n%test content"
        files = {
            "arrival_notice": self.create_mock_upload_file("AN.pdf", pdf_content, "application/pdf"),
            "bill_of_lading": self.create_mock_upload_file("BOL.pdf", pdf_content, "application/pdf"),
            "certificate_of_origin": self.create_mock_upload_file("CO.pdf", pdf_content, "application/pdf"),
            "invoice": self.create_mock_upload_file("INVOICE.pdf", pdf_content, "application/pdf"),
            "good_list": self.create_mock_upload_file("goods.xls", b"test", "application/vnd.ms-excel"),
            "tariff": self.create_mock_upload_file("tariff.xlsx", b"test", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        }

        errors = await validation_service.validate_all_files_present(files)
        assert errors == []

    @pytest.mark.asyncio
    async def test_validate_missing_file_fails(self, validation_service):
        """Test that missing files cause validation to fail"""
        pdf_content = b"%PDF-1.4\n%test content"
        files = {
            "arrival_notice": self.create_mock_upload_file("AN.pdf", pdf_content, "application/pdf"),
            "bill_of_lading": self.create_mock_upload_file("BOL.pdf", pdf_content, "application/pdf"),
            # certificate_of_origin is missing
            "invoice": self.create_mock_upload_file("INVOICE.pdf", pdf_content, "application/pdf"),
            "good_list": self.create_mock_upload_file("goods.xls", b"test", "application/vnd.ms-excel"),
            # tariff is missing
        }

        errors = await validation_service.validate_all_files_present(files)
        assert len(errors) == 2
        assert any(e["file"] == "certificate_of_origin" for e in errors)
        assert any(e["file"] == "tariff" for e in errors)

    @pytest.mark.asyncio
    async def test_validate_file_type_pdf_success(self, validation_service):
        """Test that valid PDF files pass type validation"""
        # PDF magic bytes: %PDF
        pdf_content = b"%PDF-1.4\n%test content" + b"\x00" * 2000

        upload_file = self.create_mock_upload_file(
            "AN.pdf",
            pdf_content,
            "application/pdf"
        )

        with patch.object(validation_service.mime, 'from_buffer', return_value="application/pdf"):
            error = await validation_service.validate_file_type(upload_file, "arrival_notice")
            assert error is None

    @pytest.mark.asyncio
    async def test_validate_file_type_wrong_type_fails(self, validation_service):
        """Test that wrong file types fail validation"""
        # Word document instead of PDF
        doc_content = b"PK\x03\x04" + b"\x00" * 2000  # ZIP-based format

        upload_file = self.create_mock_upload_file(
            "AN.pdf",  # Claims to be PDF
            doc_content,
            "application/pdf"
        )

        with patch.object(validation_service.mime, 'from_buffer', return_value="application/vnd.openxmlformats-officedocument.wordprocessingml.document"):
            error = await validation_service.validate_file_type(upload_file, "arrival_notice")
            assert error is not None
            assert error["file"] == "arrival_notice"
            assert "Expected" in error["reason"]

    @pytest.mark.asyncio
    async def test_validate_file_type_invoice_accepts_pdf(self, validation_service):
        """Test that invoice accepts PDF files"""
        pdf_content = b"%PDF-1.4\n%test" + b"\x00" * 2000

        upload_file = self.create_mock_upload_file(
            "INVOICE.pdf",
            pdf_content,
            "application/pdf"
        )

        with patch.object(validation_service.mime, 'from_buffer', return_value="application/pdf"):
            error = await validation_service.validate_file_type(upload_file, "invoice")
            assert error is None

    @pytest.mark.asyncio
    async def test_validate_file_type_invoice_accepts_jpeg(self, validation_service):
        """Test that invoice accepts JPEG images"""
        jpeg_content = b"\xFF\xD8\xFF\xE0" + b"\x00" * 2000  # JPEG magic bytes

        upload_file = self.create_mock_upload_file(
            "INVOICE.jpg",
            jpeg_content,
            "image/jpeg"
        )

        with patch.object(validation_service.mime, 'from_buffer', return_value="image/jpeg"):
            error = await validation_service.validate_file_type(upload_file, "invoice")
            assert error is None

    @pytest.mark.asyncio
    async def test_validate_file_size_pdf_within_limit(self, validation_service):
        """Test that PDF files within size limit pass validation"""
        # Create 5MB PDF (under 10MB limit)
        pdf_content = b"%PDF-1.4\n" + b"x" * (5 * 1024 * 1024)

        upload_file = self.create_mock_upload_file(
            "AN.pdf",
            pdf_content,
            "application/pdf"
        )

        # Should not raise exception
        await validation_service.validate_file_size(upload_file, "arrival_notice")

    @pytest.mark.asyncio
    async def test_validate_file_size_pdf_exceeds_limit(self, validation_service):
        """Test that PDF files exceeding size limit fail validation"""
        # Create 11MB PDF (over 10MB limit)
        pdf_content = b"%PDF-1.4\n" + b"x" * (11 * 1024 * 1024)

        upload_file = self.create_mock_upload_file(
            "AN.pdf",
            pdf_content,
            "application/pdf"
        )

        with pytest.raises(FileSizeLimitExceeded) as exc_info:
            await validation_service.validate_file_size(upload_file, "arrival_notice")

        assert exc_info.value.file_field == "arrival_notice"
        assert exc_info.value.size > 10 * 1024 * 1024
        assert exc_info.value.max_size == 10 * 1024 * 1024

    @pytest.mark.asyncio
    async def test_validate_file_size_image_exceeds_limit(self, validation_service):
        """Test that image files exceeding 5MB limit fail validation"""
        # Create 6MB image (over 5MB limit)
        jpeg_content = b"\xFF\xD8\xFF\xE0" + b"x" * (6 * 1024 * 1024)

        upload_file = self.create_mock_upload_file(
            "INVOICE.jpg",
            jpeg_content,
            "image/jpeg"
        )

        with pytest.raises(FileSizeLimitExceeded) as exc_info:
            await validation_service.validate_file_size(upload_file, "invoice")

        assert exc_info.value.file_field == "invoice"
        assert exc_info.value.max_size == 5 * 1024 * 1024

    @pytest.mark.asyncio
    async def test_validate_file_size_excel_exceeds_limit(self, validation_service):
        """Test that Excel files exceeding 2MB limit fail validation"""
        # Create 3MB Excel file (over 2MB limit)
        excel_content = b"PK\x03\x04" + b"x" * (3 * 1024 * 1024)

        upload_file = self.create_mock_upload_file(
            "goods.xlsx",
            excel_content,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        with pytest.raises(FileSizeLimitExceeded) as exc_info:
            await validation_service.validate_file_size(upload_file, "good_list")

        assert exc_info.value.file_field == "good_list"
        assert exc_info.value.max_size == 2 * 1024 * 1024

    @pytest.mark.asyncio
    async def test_validate_all_files_missing_files(self, validation_service):
        """Test that missing files raise FileValidationError"""
        files = {
            "arrival_notice": self.create_mock_upload_file("AN.pdf", b"%PDF", "application/pdf"),
            # Other files missing
        }

        with pytest.raises(FileValidationError) as exc_info:
            await validation_service.validate_all_files(files)

        assert len(exc_info.value.errors) == 5  # 5 files missing

    @pytest.mark.asyncio
    async def test_validate_all_files_wrong_type(self, validation_service):
        """Test that wrong file types raise FileValidationError"""
        doc_content = b"fake_doc_content" + b"\x00" * 2000
        pdf_content = b"%PDF-1.4\n" + b"\x00" * 2000
        excel_content = b"PK\x03\x04" + b"\x00" * 2000

        files = {
            "arrival_notice": self.create_mock_upload_file("AN.pdf", pdf_content, "application/pdf"),
            "bill_of_lading": self.create_mock_upload_file("BOL.pdf", pdf_content, "application/pdf"),
            "certificate_of_origin": self.create_mock_upload_file("CO.pdf", pdf_content, "application/pdf"),
            "invoice": self.create_mock_upload_file("INVOICE.pdf", pdf_content, "application/pdf"),
            "good_list": self.create_mock_upload_file("goods.xls", excel_content, "application/vnd.ms-excel"),
            "tariff": self.create_mock_upload_file("tariff.doc", doc_content, "application/msword")  # Wrong type!
        }

        with patch.object(validation_service.mime, 'from_buffer') as mock_from_buffer:
            # Return correct types for most files, wrong type for tariff
            def side_effect(buffer):
                if b"PK" in buffer[:10]:
                    return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                elif b"%PDF" in buffer[:10]:
                    return "application/pdf"
                elif b"fake_doc" in buffer[:20]:
                    return "application/msword"
                return "application/octet-stream"

            mock_from_buffer.side_effect = side_effect

            with pytest.raises(FileValidationError) as exc_info:
                await validation_service.validate_all_files(files)

            assert len(exc_info.value.errors) >= 1
            assert any(e["file"] == "tariff" for e in exc_info.value.errors)


class TestFileStorageService:
    """Tests for FileStorageService"""

    @pytest.fixture
    def storage_service(self, tmp_path):
        """Create a FileStorageService instance with temp directory"""
        service = FileStorageService()
        # Override base directory to use temp path for testing
        service.UPLOAD_BASE_DIR = tmp_path / "uploads"
        service.UPLOAD_BASE_DIR.mkdir(parents=True, exist_ok=True)
        return service

    def create_mock_upload_file(
        self,
        filename: str,
        content: bytes,
        content_type: str
    ) -> UploadFile:
        """Create a mock UploadFile for testing"""
        file_obj = BytesIO(content)
        upload_file = UploadFile(
            filename=filename,
            file=file_obj,
            content_type=content_type
        )

        # Make methods async
        async def async_seek(*args):
            return file_obj.seek(*args)

        async def async_read(size=-1):
            return file_obj.read(size)

        async def async_tell():
            return file_obj.tell()

        upload_file.seek = async_seek
        upload_file.read = async_read
        upload_file.tell = async_tell

        return upload_file

    @pytest.mark.asyncio
    async def test_save_declaration_files_creates_directory(self, storage_service):
        """Test that saving files creates declaration directory"""
        declaration_id = uuid.uuid4()
        pdf_content = b"%PDF-1.4\ntest content"

        files = {
            "arrival_notice": self.create_mock_upload_file("AN.pdf", pdf_content, "application/pdf"),
            "bill_of_lading": self.create_mock_upload_file("BOL.pdf", pdf_content, "application/pdf"),
            "certificate_of_origin": self.create_mock_upload_file("CO.pdf", pdf_content, "application/pdf"),
            "invoice": self.create_mock_upload_file("INVOICE.pdf", pdf_content, "application/pdf"),
            "good_list": self.create_mock_upload_file("goods.xls", b"excel", "application/vnd.ms-excel"),
            "tariff": self.create_mock_upload_file("tariff.xlsx", b"excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        }

        file_metadata = await storage_service.save_declaration_files(declaration_id, files)

        # Check directory was created
        declaration_dir = storage_service.UPLOAD_BASE_DIR / str(declaration_id)
        assert declaration_dir.exists()
        assert declaration_dir.is_dir()

        # Check metadata returned
        assert len(file_metadata) == 6
        assert all("file_type" in m for m in file_metadata)
        assert all("filename" in m for m in file_metadata)
        assert all("path" in m for m in file_metadata)
        assert all("size" in m for m in file_metadata)

    @pytest.mark.asyncio
    async def test_save_declaration_files_stores_files(self, storage_service):
        """Test that files are actually saved to disk"""
        declaration_id = uuid.uuid4()
        pdf_content = b"%PDF-1.4\ntest content for AN"

        files = {
            "arrival_notice": self.create_mock_upload_file("AN.pdf", pdf_content, "application/pdf"),
            "bill_of_lading": self.create_mock_upload_file("BOL.pdf", b"BOL content", "application/pdf"),
            "certificate_of_origin": self.create_mock_upload_file("CO.pdf", b"CO content", "application/pdf"),
            "invoice": self.create_mock_upload_file("INVOICE.pdf", b"Invoice", "application/pdf"),
            "good_list": self.create_mock_upload_file("goods.xls", b"goods", "application/vnd.ms-excel"),
            "tariff": self.create_mock_upload_file("tariff.xlsx", b"tariff", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        }

        await storage_service.save_declaration_files(declaration_id, files)

        # Check files exist
        declaration_dir = storage_service.UPLOAD_BASE_DIR / str(declaration_id)
        assert (declaration_dir / "AN.pdf").exists()
        assert (declaration_dir / "BOL.pdf").exists()
        assert (declaration_dir / "CO.pdf").exists()

        # Check file contents
        with open(declaration_dir / "AN.pdf", "rb") as f:
            assert f.read() == pdf_content

    @pytest.mark.asyncio
    async def test_save_declaration_files_sanitizes_filenames(self, storage_service):
        """Test that dangerous filenames are sanitized"""
        declaration_id = uuid.uuid4()

        files = {
            "arrival_notice": self.create_mock_upload_file("../../../etc/passwd", b"bad", "application/pdf"),
            "bill_of_lading": self.create_mock_upload_file("BOL<>.pdf", b"bad", "application/pdf"),
            "certificate_of_origin": self.create_mock_upload_file("CO|test.pdf", b"bad", "application/pdf"),
            "invoice": self.create_mock_upload_file("invoice.pdf", b"good", "application/pdf"),
            "good_list": self.create_mock_upload_file("goods.xls", b"good", "application/vnd.ms-excel"),
            "tariff": self.create_mock_upload_file("tariff.xlsx", b"good", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        }

        file_metadata = await storage_service.save_declaration_files(declaration_id, files)

        # Check that dangerous characters were removed/replaced
        filenames = [m["filename"] for m in file_metadata]
        assert all(".." not in fn for fn in filenames)
        assert all("/" not in fn for fn in filenames)
        assert all("\\" not in fn for fn in filenames)

    @pytest.mark.asyncio
    async def test_cleanup_declaration_files_removes_directory(self, storage_service):
        """Test that cleanup removes declaration directory"""
        declaration_id = uuid.uuid4()
        declaration_dir = storage_service.UPLOAD_BASE_DIR / str(declaration_id)
        declaration_dir.mkdir(parents=True, exist_ok=True)

        # Create some files
        (declaration_dir / "test1.pdf").write_bytes(b"test")
        (declaration_dir / "test2.pdf").write_bytes(b"test")

        assert declaration_dir.exists()

        # Cleanup
        await storage_service.cleanup_declaration_files(declaration_id)

        # Check directory was removed
        assert not declaration_dir.exists()

    @pytest.mark.asyncio
    async def test_save_declaration_files_rollback_on_error(self, storage_service):
        """Test that files are cleaned up if save fails"""
        declaration_id = uuid.uuid4()

        files = {
            "arrival_notice": self.create_mock_upload_file("AN.pdf", b"test", "application/pdf"),
            "bill_of_lading": self.create_mock_upload_file("BOL.pdf", b"test", "application/pdf"),
            "certificate_of_origin": self.create_mock_upload_file("CO.pdf", b"test", "application/pdf"),
            "invoice": self.create_mock_upload_file("INVOICE.pdf", b"test", "application/pdf"),
            "good_list": self.create_mock_upload_file("goods.xls", b"test", "application/vnd.ms-excel"),
            "tariff": self.create_mock_upload_file("tariff.xlsx", b"test", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        }

        # Simulate error during file save by patching aiofiles
        with patch("src.services.file_storage_service.aiofiles.open", side_effect=OSError("Disk full")):
            with pytest.raises(OSError):
                await storage_service.save_declaration_files(declaration_id, files)

        # Check that directory was cleaned up
        declaration_dir = storage_service.UPLOAD_BASE_DIR / str(declaration_id)
        assert not declaration_dir.exists()

    @pytest.mark.asyncio
    async def test_declaration_files_exist(self, storage_service):
        """Test checking if declaration files exist"""
        declaration_id = uuid.uuid4()
        declaration_dir = storage_service.UPLOAD_BASE_DIR / str(declaration_id)

        # Initially should not exist
        assert not storage_service.declaration_files_exist(declaration_id)

        # Create directory with files
        declaration_dir.mkdir(parents=True, exist_ok=True)
        (declaration_dir / "test.pdf").write_bytes(b"test")

        # Now should exist
        assert storage_service.declaration_files_exist(declaration_id)
