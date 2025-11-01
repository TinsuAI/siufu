"""
File storage service for uploaded declaration files

Handles saving files to Docker volume with atomic writes.
Updated in Story 3.3.1: Supports multiple CO files
"""
import os
import shutil
import uuid
from pathlib import Path
from typing import Dict, List, Union
from datetime import datetime, timezone
from fastapi import UploadFile
import aiofiles


class FileStorageService:
    """
    Service for storing uploaded declaration files

    Features:
    - Creates unique directory per declaration (UUID)
    - Atomic file writes (temp file + rename)
    - Proper error handling with cleanup on failure
    - Returns file metadata for database storage
    """

    # Base upload directory (Docker volume mount point)
    UPLOAD_BASE_DIR = Path("/app/data/uploads")

    # Field name to file type mapping
    # Updated in Story 3.3.1: Removed GOODLIST and TARIFF
    FILE_TYPE_MAP = {
        "arrival_notice": "AN",
        "bill_of_lading": "BOL",
        "certificate_of_origin": "CO",
        "invoice": "INVOICE"
    }

    def __init__(self):
        """Initialize file storage service and ensure base directory exists"""
        # Create base upload directory if it doesn't exist
        self.UPLOAD_BASE_DIR.mkdir(parents=True, exist_ok=True)

    async def save_declaration_files(
        self,
        declaration_id: uuid.UUID,
        files: Dict[str, Union[UploadFile, List[UploadFile]]]
    ) -> List[Dict[str, any]]:
        """
        Save all uploaded files for a declaration
        Updated in Story 3.3.1: Handles CO as List[UploadFile]

        Creates directory structure: /app/data/uploads/{declaration_id}/

        Args:
            declaration_id: UUID of the declaration
            files: Dictionary mapping file field names to UploadFile or List[UploadFile]

        Returns:
            List of file metadata dictionaries for database storage

        Raises:
            OSError: If disk is full or file write fails
        """
        declaration_dir = self.UPLOAD_BASE_DIR / str(declaration_id)

        try:
            # Create declaration directory
            declaration_dir.mkdir(parents=True, exist_ok=True)

            # Save all files and collect metadata
            file_metadata = []

            for field_name, file_or_files in files.items():
                if field_name == "certificate_of_origin" and isinstance(file_or_files, list):
                    # Handle multiple CO files
                    for idx, co_file in enumerate(file_or_files):
                        metadata = await self._save_single_file(
                            declaration_dir,
                            field_name,
                            co_file,
                            file_index=idx + 1  # 1-indexed for filenames
                        )
                        file_metadata.append(metadata)
                elif file_or_files is not None:
                    # Handle single file
                    metadata = await self._save_single_file(
                        declaration_dir,
                        field_name,
                        file_or_files
                    )
                    file_metadata.append(metadata)

            return file_metadata

        except Exception as e:
            # Clean up on failure (rollback)
            await self.cleanup_declaration_files(declaration_id)
            raise e

    async def _save_single_file(
        self,
        declaration_dir: Path,
        field_name: str,
        file: UploadFile,
        file_index: int = None
    ) -> Dict[str, any]:
        """
        Save a single uploaded file with atomic write
        Updated in Story 3.3.1: Supports file_index for multiple CO files

        Args:
            declaration_dir: Directory to save file to
            field_name: File field name (e.g., "arrival_notice")
            file: FastAPI UploadFile object
            file_index: Optional index for multi-file fields (e.g., CO_1, CO_2)

        Returns:
            File metadata dictionary

        Raises:
            OSError: If file write fails
        """
        # Get file type and original filename
        file_type = self.FILE_TYPE_MAP.get(field_name, field_name.upper())

        # For multi-file fields (CO), append index to file type
        if file_index is not None:
            file_type = f"{file_type}_{file_index}"

        filename = self._sanitize_filename(file.filename)

        # If this is a CO file with an index, rename it to CO_1.pdf, CO_2.pdf, etc.
        if file_index is not None and field_name == "certificate_of_origin":
            # Extract extension from original filename
            ext = Path(filename).suffix or ".pdf"
            filename = f"CO_{file_index}{ext}"

        # Construct file paths
        final_path = declaration_dir / filename
        temp_path = declaration_dir / f"{filename}.tmp"

        # Get file size by reading content
        await file.seek(0)
        content_preview = await file.read()
        file_size = len(content_preview)
        await file.seek(0)

        try:
            # Write to temporary file first (atomic write)
            async with aiofiles.open(temp_path, 'wb') as out_file:
                # Read and write in chunks to avoid memory issues
                chunk_size = 1024 * 1024  # 1MB chunks
                while True:
                    chunk = await file.read(chunk_size)
                    if not chunk:
                        break
                    await out_file.write(chunk)

            # Rename temp file to final filename (atomic operation)
            temp_path.rename(final_path)

            # Set file permissions (read-only for worker, read-write for API)
            os.chmod(final_path, 0o644)

            # Return metadata for database storage
            return {
                "file_type": file_type,
                "filename": filename,
                "path": str(final_path),  # Absolute path in container
                "size": file_size,
                "content_type": file.content_type or "application/octet-stream",
                "uploaded_at": datetime.now(timezone.utc).isoformat()
            }

        except OSError as e:
            # Handle disk full or permission errors
            if temp_path.exists():
                temp_path.unlink()
            if e.errno == 28:  # ENOSPC - No space left on device
                raise OSError("Insufficient storage space available") from e
            raise e

        finally:
            # Reset file pointer
            await file.seek(0)

    async def cleanup_declaration_files(self, declaration_id: uuid.UUID) -> None:
        """
        Delete all files for a declaration (rollback on error)

        Args:
            declaration_id: UUID of the declaration
        """
        declaration_dir = self.UPLOAD_BASE_DIR / str(declaration_id)

        if declaration_dir.exists() and declaration_dir.is_dir():
            try:
                shutil.rmtree(declaration_dir)
            except Exception:
                # Log error but don't raise (cleanup is best-effort)
                pass

    def _sanitize_filename(self, filename: str) -> str:
        r"""
        Sanitize filename to prevent path traversal attacks

        Removes special characters: . / \ :

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        if not filename:
            return "unnamed_file"

        # Remove path components
        filename = os.path.basename(filename)

        # Replace dangerous characters
        dangerous_chars = ['..', '/', '\\', ':', '|', '<', '>', '"', '?', '*']
        for char in dangerous_chars:
            filename = filename.replace(char, '_')

        # Ensure filename is not empty after sanitization
        if not filename or filename == '.':
            return "unnamed_file"

        return filename

    def get_declaration_directory(self, declaration_id: uuid.UUID) -> Path:
        """
        Get the directory path for a declaration

        Args:
            declaration_id: UUID of the declaration

        Returns:
            Path object for the declaration directory
        """
        return self.UPLOAD_BASE_DIR / str(declaration_id)

    def declaration_files_exist(self, declaration_id: uuid.UUID) -> bool:
        """
        Check if files exist for a declaration

        Args:
            declaration_id: UUID of the declaration

        Returns:
            True if declaration directory exists and contains files
        """
        declaration_dir = self.get_declaration_directory(declaration_id)
        return declaration_dir.exists() and any(declaration_dir.iterdir())
