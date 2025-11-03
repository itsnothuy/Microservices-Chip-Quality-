"""File handling utilities"""

import hashlib
import mimetypes
from pathlib import Path
from typing import BinaryIO, Optional
from uuid import UUID

from app.core.config import settings
from app.core.exceptions import FileValidationError, FileTooLargeError, InvalidFileTypeError


def calculate_sha256(file_obj: BinaryIO, chunk_size: int = 8192) -> str:
    """
    Calculate SHA256 checksum of a file
    
    Args:
        file_obj: File object to hash
        chunk_size: Size of chunks to read
        
    Returns:
        Hexadecimal SHA256 checksum
    """
    sha256_hash = hashlib.sha256()
    
    # Reset file position
    file_obj.seek(0)
    
    # Read and hash file in chunks
    while chunk := file_obj.read(chunk_size):
        sha256_hash.update(chunk)
    
    # Reset file position for subsequent reads
    file_obj.seek(0)
    
    return sha256_hash.hexdigest()


def validate_file_size(file_size: int) -> None:
    """
    Validate file size against maximum allowed size
    
    Args:
        file_size: Size of file in bytes
        
    Raises:
        FileTooLargeError: If file exceeds maximum size
    """
    if file_size > settings.max_upload_size_bytes:
        raise FileTooLargeError(file_size, settings.max_upload_size_bytes)


def validate_content_type(content_type: str) -> None:
    """
    Validate content type against allowed types
    
    Args:
        content_type: MIME type of the file
        
    Raises:
        InvalidFileTypeError: If content type is not allowed
    """
    if content_type not in settings.allowed_content_types:
        raise InvalidFileTypeError(content_type, settings.allowed_content_types)


def generate_storage_path(
    inspection_id: UUID,
    artifact_type: str,
    filename: str
) -> str:
    """
    Generate organized storage path for artifact
    
    Args:
        inspection_id: Inspection UUID
        artifact_type: Type of artifact
        filename: Original filename
        
    Returns:
        Storage path in format: artifacts/{inspection_id}/{artifact_type}/{filename}
    """
    # Sanitize filename
    safe_filename = Path(filename).name
    
    # Create hierarchical path
    path = f"artifacts/{inspection_id}/{artifact_type}/{safe_filename}"
    
    return path


def get_content_type(filename: str) -> str:
    """
    Determine content type from filename
    
    Args:
        filename: Name of the file
        
    Returns:
        MIME type string
    """
    content_type, _ = mimetypes.guess_type(filename)
    return content_type or "application/octet-stream"


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def extract_file_metadata(
    filename: str,
    content_type: str,
    file_size: int,
    checksum: str
) -> dict:
    """
    Extract and compile file metadata
    
    Args:
        filename: Name of the file
        content_type: MIME type
        file_size: Size in bytes
        checksum: SHA256 checksum
        
    Returns:
        Dictionary of metadata
    """
    file_extension = Path(filename).suffix.lower()
    
    metadata = {
        "original_filename": filename,
        "file_extension": file_extension,
        "content_type": content_type,
        "file_size_bytes": file_size,
        "file_size_formatted": format_file_size(file_size),
        "checksum_sha256": checksum
    }
    
    return metadata
