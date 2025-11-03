"""Custom exceptions for artifact service"""


class ArtifactServiceError(Exception):
    """Base exception for artifact service errors"""
    
    def __init__(self, error_code: str, message: str, details: dict = None):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ArtifactNotFoundError(ArtifactServiceError):
    """Raised when artifact is not found"""
    
    def __init__(self, artifact_id: str):
        super().__init__(
            error_code="ARTIFACT_NOT_FOUND",
            message=f"Artifact not found: {artifact_id}",
            details={"artifact_id": artifact_id}
        )


class FileUploadError(ArtifactServiceError):
    """Raised when file upload fails"""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            error_code="FILE_UPLOAD_ERROR",
            message=message,
            details=details
        )


class FileValidationError(ArtifactServiceError):
    """Raised when file validation fails"""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            error_code="FILE_VALIDATION_ERROR",
            message=message,
            details=details
        )


class StorageError(ArtifactServiceError):
    """Raised when storage operation fails"""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            error_code="STORAGE_ERROR",
            message=message,
            details=details
        )


class FileTooLargeError(ArtifactServiceError):
    """Raised when file exceeds size limit"""
    
    def __init__(self, file_size: int, max_size: int):
        super().__init__(
            error_code="FILE_TOO_LARGE",
            message=f"File size {file_size} bytes exceeds maximum allowed size {max_size} bytes",
            details={"file_size": file_size, "max_size": max_size}
        )


class InvalidFileTypeError(ArtifactServiceError):
    """Raised when file type is not allowed"""
    
    def __init__(self, content_type: str, allowed_types: list[str]):
        super().__init__(
            error_code="INVALID_FILE_TYPE",
            message=f"File type '{content_type}' is not allowed",
            details={"content_type": content_type, "allowed_types": allowed_types}
        )


class ChecksumMismatchError(ArtifactServiceError):
    """Raised when file checksum doesn't match"""
    
    def __init__(self, expected: str, actual: str):
        super().__init__(
            error_code="CHECKSUM_MISMATCH",
            message="File integrity check failed",
            details={"expected": expected, "actual": actual}
        )
