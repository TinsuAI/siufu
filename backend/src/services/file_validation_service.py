"""
File validation service for uploaded declaration files

Validates file types using magic bytes and enforces size limits.
Updated in Story 3.3.1: Certificate of Origin supports multiple files (1-20)
"""
import magic
from typing import Dict, List, Tuple, Optional, Union
from fastapi import UploadFile, HTTPException, status


class FileValidationError(Exception):
    """Custom exception for file validation errors"""
    def __init__(self, errors: List[Dict[str, str]]):
        self.errors = errors
        super().__init__(f"File validation failed: {errors}")


class FileSizeLimitExceeded(Exception):
    """Custom exception for file size limit exceeded"""
    def __init__(self, file_field: str, size: int, max_size: int):
        self.file_field = file_field
        self.size = size
        self.max_size = max_size
        super().__init__(
            f"File {file_field} size {size} bytes exceeds limit of {max_size} bytes"
        )


class FileValidationService:
    """
    Service for validating uploaded declaration files

    Validates:
    - All 4 required file types are present
    - File types match expected MIME types using magic bytes
    - File sizes are within limits
    - Certificate of Origin has 1-20 files

    Updated in Story 3.3.1: CO is now List[UploadFile]
    """

    # File size limits in bytes
    PDF_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    IMAGE_MAX_SIZE = 5 * 1024 * 1024  # 5MB

    # C/O file count limits
    MIN_CO_FILES = 1
    MAX_CO_FILES = 20

    # Required file fields (4 file types)
    REQUIRED_FIELDS = [
        "arrival_notice",
        "bill_of_lading",
        "certificate_of_origin",
        "invoice"
    ]

    # Allowed MIME types for each file
    ALLOWED_TYPES = {
        "arrival_notice": ["application/pdf"],
        "bill_of_lading": ["application/pdf"],
        "certificate_of_origin": ["application/pdf"],
        "invoice": ["application/pdf", "image/jpeg", "image/png"]
    }

    # Friendly names for error messages
    FILE_TYPE_NAMES = {
        "arrival_notice": "Arrival Notice (AN.pdf)",
        "bill_of_lading": "Bill of Lading (BOL.pdf)",
        "certificate_of_origin": "Certificate of Origin (CO.pdf)",
        "invoice": "Invoice"
    }

    def __init__(self):
        self.mime = magic.Magic(mime=True)

    async def validate_all_files_present(
        self,
        files: Dict[str, Union[Optional[UploadFile], List[UploadFile]]]
    ) -> List[Dict[str, str]]:
        """
        Validate that all 4 required file types are present
        Updated in Story 3.3.1: CO is a list of files

        Args:
            files: Dictionary mapping file field names to UploadFile or List[UploadFile]

        Returns:
            List of error dictionaries (empty if all files present)
        """
        errors = []

        for field in self.REQUIRED_FIELDS:
            if field not in files:
                errors.append({
                    "file": field,
                    "reason": f"{self.FILE_TYPE_NAMES[field]} is required but not provided"
                })
            elif field == "certificate_of_origin":
                # CO should be a list with at least 1 file
                co_files = files[field]
                if not isinstance(co_files, list) or len(co_files) < self.MIN_CO_FILES:
                    errors.append({
                        "file": field,
                        "reason": f"{self.FILE_TYPE_NAMES[field]} requires at least {self.MIN_CO_FILES} file(s)"
                    })
                elif len(co_files) > self.MAX_CO_FILES:
                    errors.append({
                        "file": field,
                        "reason": f"{self.FILE_TYPE_NAMES[field]} allows maximum {self.MAX_CO_FILES} files (got {len(co_files)})"
                    })
            else:
                # Other files should be single UploadFile
                if files[field] is None:
                    errors.append({
                        "file": field,
                        "reason": f"{self.FILE_TYPE_NAMES[field]} is required but not provided"
                    })

        return errors

    async def validate_file_type(
        self,
        file: UploadFile,
        field_name: str
    ) -> Optional[Dict[str, str]]:
        """
        Validate file type using magic bytes

        Args:
            file: FastAPI UploadFile object
            field_name: Name of the file field (e.g., "arrival_notice")

        Returns:
            Error dictionary if validation fails, None if valid
        """
        allowed_types = self.ALLOWED_TYPES.get(field_name, [])

        # Read first 2048 bytes for magic byte detection
        await file.seek(0)
        file_header = await file.read(2048)
        await file.seek(0)  # Reset file pointer

        # Detect MIME type from magic bytes
        detected_type = self.mime.from_buffer(file_header)

        # Check if detected type is allowed
        if detected_type not in allowed_types:
            allowed_str = " or ".join(self._format_mime_type(t) for t in allowed_types)
            detected_str = self._format_mime_type(detected_type)

            return {
                "file": field_name,
                "reason": f"Expected {allowed_str}, got {detected_str}"
            }

        return None

    async def validate_file_size(
        self,
        file: UploadFile,
        field_name: str
    ) -> None:
        """
        Validate file size against limits

        Args:
            file: FastAPI UploadFile object
            field_name: Name of the file field

        Raises:
            FileSizeLimitExceeded: If file size exceeds limit
        """
        # Get file size by reading the entire file
        await file.seek(0)
        content = await file.read()
        file_size = len(content)
        await file.seek(0)  # Reset to beginning for later processing

        # Determine max size based on file type
        max_size = self._get_max_size(field_name, file)

        if file_size > max_size:
            raise FileSizeLimitExceeded(field_name, file_size, max_size)

    async def validate_all_files(
        self,
        files: Dict[str, Union[Optional[UploadFile], List[UploadFile]]]
    ) -> Tuple[List[Dict[str, str]], Optional[FileSizeLimitExceeded]]:
        """
        Validate all uploaded files
        Updated in Story 3.3.1: Handles CO as List[UploadFile]

        Args:
            files: Dictionary mapping file field names to UploadFile or List[UploadFile]

        Returns:
            Tuple of (validation_errors, size_limit_error)

        Raises:
            FileValidationError: If validation fails (contains all errors)
        """
        errors = []

        # Step 1: Check all required files are present
        missing_errors = await self.validate_all_files_present(files)
        if missing_errors:
            errors.extend(missing_errors)
            # If files are missing, don't proceed with type/size validation
            raise FileValidationError(errors)

        # Step 2: Validate file sizes (do this first to avoid reading large files)
        for field_name, file_or_files in files.items():
            if field_name == "certificate_of_origin" and isinstance(file_or_files, list):
                # Validate each CO file
                for idx, co_file in enumerate(file_or_files):
                    try:
                        await self.validate_file_size(co_file, f"{field_name}_{idx + 1}")
                    except FileSizeLimitExceeded as e:
                        # Re-raise size errors immediately
                        raise e
            elif file_or_files is not None:
                # Single file validation
                try:
                    await self.validate_file_size(file_or_files, field_name)
                except FileSizeLimitExceeded as e:
                    # Re-raise size errors immediately
                    raise e

        # Step 3: Validate file types using magic bytes
        for field_name, file_or_files in files.items():
            if field_name == "certificate_of_origin" and isinstance(file_or_files, list):
                # Validate each CO file
                for idx, co_file in enumerate(file_or_files):
                    error = await self.validate_file_type(co_file, field_name)
                    if error:
                        error["file"] = f"{field_name}_{idx + 1}"
                        errors.append(error)
            elif file_or_files is not None:
                # Single file validation
                error = await self.validate_file_type(file_or_files, field_name)
                if error:
                    errors.append(error)

        if errors:
            raise FileValidationError(errors)

        return errors, None

    def _get_max_size(self, field_name: str, file: UploadFile) -> int:
        """
        Get maximum allowed file size based on field name and type

        Args:
            field_name: Name of the file field
            file: UploadFile object

        Returns:
            Maximum size in bytes
        """
        if field_name in ["arrival_notice", "bill_of_lading", "certificate_of_origin"]:
            return self.PDF_MAX_SIZE
        elif field_name == "invoice":
            # Invoice can be PDF or image
            content_type = file.content_type or ""
            if "image" in content_type:
                return self.IMAGE_MAX_SIZE
            else:
                return self.PDF_MAX_SIZE
        else:
            return self.PDF_MAX_SIZE  # Default to PDF limit

    def _format_mime_type(self, mime_type: str) -> str:
        """
        Format MIME type for user-friendly error messages

        Args:
            mime_type: MIME type string

        Returns:
            Human-readable file type name
        """
        mime_map = {
            "application/pdf": "PDF file",
            "image/jpeg": "JPEG image",
            "image/png": "PNG image",
            "application/vnd.ms-excel": "Excel file (.xls)",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "Excel file (.xlsx)",
            "application/msword": "Word document",
            "text/plain": "text file",
            "application/octet-stream": "unknown file type"
        }

        return mime_map.get(mime_type, mime_type)
