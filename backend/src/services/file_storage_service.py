"""
File storage service for uploaded declaration files

Handles saving files to Docker volume with atomic writes.
"""
import os
import shutil
import uuid
from pathlib import Path
from typing import Dict, List
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
    FILE_TYPE_MAP = {
        "arrival_notice": "AN",
        "bill_of_lading": "BOL",
        "certificate_of_origin": "CO",
        "invoice": "INVOICE",
        "good_list": "GOODLIST",
        "tariff": "TARIFF"
    }

    def __init__(self):
        """Initialize file storage service and ensure base directory exists"""
        # Create base upload directory if it doesn't exist
        self.UPLOAD_BASE_DIR.mkdir(parents=True, exist_ok=True)

    async def save_declaration_files(
        self,
        declaration_id: uuid.UUID,
        files: Dict[str, UploadFile]
    ) -> List[Dict[str, any]]:
        """
        Save all uploaded files for a declaration

        Creates directory structure: /app/data/uploads/{declaration_id}/

        Args:
            declaration_id: UUID of the declaration
            files: Dictionary mapping file field names to UploadFile objects

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

            for field_name, file in files.items():
                if file is not None:
                    metadata = await self._save_single_file(
                        declaration_dir,
                        field_name,
                        file
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
        file: UploadFile
    ) -> Dict[str, any]:
        """
        Save a single uploaded file with atomic write

        Args:
            declaration_dir: Directory to save file to
            field_name: File field name (e.g., "arrival_notice")
            file: FastAPI UploadFile object

        Returns:
            File metadata dictionary

        Raises:
            OSError: If file write fails
        """
        # Get file type and original filename
        file_type = self.FILE_TYPE_MAP.get(field_name, field_name.upper())
        filename = self._sanitize_filename(file.filename)

        # Construct file paths
        final_path = declaration_dir / filename
        temp_path = declaration_dir / f"{filename}.tmp"

        # Get file size
        await file.seek(0, 2)
        file_size = await file.tell()
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
