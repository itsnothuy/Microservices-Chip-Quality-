"""Unit tests for file utilities"""

import io
import pytest

from app.utils.file_utils import (
    calculate_sha256,
    validate_file_size,
    validate_content_type,
    generate_storage_path,
    get_content_type,
    format_file_size,
    extract_file_metadata
)
from app.core.exceptions import FileTooLargeError, InvalidFileTypeError
from uuid import uuid4


def test_calculate_sha256():
    """Test SHA256 checksum calculation"""
    file_content = b"test content"
    file_obj = io.BytesIO(file_content)
    
    checksum = calculate_sha256(file_obj)
    
    # Verify checksum format (64 hex chars)
    assert len(checksum) == 64
    assert all(c in "0123456789abcdef" for c in checksum)
    
    # Verify file position is reset
    assert file_obj.tell() == 0


def test_validate_file_size_success():
    """Test file size validation passes for valid size"""
    from app.core.config import settings
    
    # Should not raise exception
    validate_file_size(1024 * 1024)  # 1 MB


def test_validate_file_size_too_large():
    """Test file size validation fails for oversized file"""
    from app.core.config import settings
    
    with pytest.raises(FileTooLargeError):
        validate_file_size(settings.max_upload_size_bytes + 1)


def test_validate_content_type_success():
    """Test content type validation passes for allowed type"""
    # Should not raise exception
    validate_content_type("image/jpeg")
    validate_content_type("image/png")
    validate_content_type("application/pdf")


def test_validate_content_type_invalid():
    """Test content type validation fails for disallowed type"""
    with pytest.raises(InvalidFileTypeError):
        validate_content_type("application/x-executable")


def test_generate_storage_path():
    """Test storage path generation"""
    inspection_id = uuid4()
    artifact_type = "image"
    filename = "test_image.jpg"
    
    path = generate_storage_path(inspection_id, artifact_type, filename)
    
    assert path.startswith("artifacts/")
    assert str(inspection_id) in path
    assert artifact_type in path
    assert filename in path


def test_get_content_type():
    """Test content type detection from filename"""
    assert get_content_type("image.jpg") == "image/jpeg"
    assert get_content_type("document.pdf") == "application/pdf"
    assert get_content_type("data.csv") == "text/csv"
    assert get_content_type("unknown.xyz") == "application/octet-stream"


def test_format_file_size():
    """Test file size formatting"""
    assert format_file_size(512) == "512.00 B"
    assert format_file_size(1024) == "1.00 KB"
    assert format_file_size(1024 * 1024) == "1.00 MB"
    assert format_file_size(1024 * 1024 * 1024) == "1.00 GB"


def test_extract_file_metadata():
    """Test file metadata extraction"""
    filename = "test_image.jpg"
    content_type = "image/jpeg"
    file_size = 1024 * 1024
    checksum = "a" * 64
    
    metadata = extract_file_metadata(filename, content_type, file_size, checksum)
    
    assert metadata["original_filename"] == filename
    assert metadata["file_extension"] == ".jpg"
    assert metadata["content_type"] == content_type
    assert metadata["file_size_bytes"] == file_size
    assert metadata["checksum_sha256"] == checksum
    assert "file_size_formatted" in metadata
