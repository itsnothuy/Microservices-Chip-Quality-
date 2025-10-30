"""Artifact models for file storage and metadata management."""

from decimal import Decimal
from typing import Dict, Any, Optional, List
from datetime import datetime

from sqlalchemy import (
    Column, String, Text, Integer, BigInteger, DateTime,
    ForeignKey, Index, Boolean, LargeBinary
)
from sqlalchemy.dialects.postgresql import JSONB, UUID, ARRAY
from sqlalchemy.orm import relationship, validates

from database.base import BaseModel, TimestampMixin
from database.enums import ArtifactTypeEnum, StorageLocationEnum


class Artifact(BaseModel, TimestampMixin):
    """File storage metadata and artifact management."""
    
    __tablename__ = "artifacts"
    
    # Core identification
    artifact_id = Column(
        String(50),
        nullable=False,
        unique=True,
        comment="Unique artifact identifier"
    )
    filename = Column(
        String(255),
        nullable=False,
        comment="Original filename"
    )
    file_path = Column(
        String(1000),
        nullable=False,
        comment="Full file path in storage system"
    )
    
    # File metadata
    artifact_type = Column(
        ArtifactTypeEnum,
        nullable=False,
        comment="Type of artifact (image, document, etc.)"
    )
    content_type = Column(
        String(100),
        nullable=False,
        comment="MIME content type"
    )
    file_size = Column(
        BigInteger,
        nullable=False,
        comment="File size in bytes"
    )
    file_extension = Column(
        String(10),
        nullable=True,
        comment="File extension"
    )
    
    # Storage information
    storage_location = Column(
        StorageLocationEnum,
        nullable=False,
        comment="Storage location (local, S3, etc.)"
    )
    storage_path = Column(
        String(1000),
        nullable=False,
        comment="Path within storage system"
    )
    storage_bucket = Column(
        String(100),
        nullable=True,
        comment="Storage bucket/container name"
    )
    storage_key = Column(
        String(500),
        nullable=True,
        comment="Storage key/object name"
    )
    
    # File integrity
    checksum_sha256 = Column(
        String(64),
        nullable=False,
        comment="SHA-256 checksum for integrity verification"
    )
    checksum_md5 = Column(
        String(32),
        nullable=True,
        comment="MD5 checksum for compatibility"
    )
    is_encrypted = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether file is encrypted at rest"
    )
    encryption_key_id = Column(
        String(100),
        nullable=True,
        comment="Encryption key identifier"
    )
    
    # Image-specific metadata (for image artifacts)
    image_width = Column(
        Integer,
        nullable=True,
        comment="Image width in pixels"
    )
    image_height = Column(
        Integer,
        nullable=True,
        comment="Image height in pixels"
    )
    image_channels = Column(
        Integer,
        nullable=True,
        comment="Number of image channels"
    )
    image_format = Column(
        String(20),
        nullable=True,
        comment="Image format (JPEG, PNG, etc.)"
    )
    image_metadata = Column(
        JSONB,
        nullable=True,
        comment="Additional image metadata (EXIF, etc.)"
    )
    
    # Document-specific metadata
    document_pages = Column(
        Integer,
        nullable=True,
        comment="Number of pages (for documents)"
    )
    document_metadata = Column(
        JSONB,
        nullable=True,
        comment="Document metadata (author, title, etc.)"
    )
    extracted_text = Column(
        Text,
        nullable=True,
        comment="Extracted text content (OCR, etc.)"
    )
    
    # Processing information
    is_processed = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether file has been processed"
    )
    processed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When file processing was completed"
    )
    processing_results = Column(
        JSONB,
        nullable=True,
        comment="Results from file processing"
    )
    
    # Thumbnails and previews
    thumbnail_path = Column(
        String(1000),
        nullable=True,
        comment="Path to thumbnail image"
    )
    preview_path = Column(
        String(1000),
        nullable=True,
        comment="Path to preview/converted file"
    )
    
    # Classification and tagging
    tags = Column(
        ARRAY(String(50)),
        nullable=True,
        comment="Tags for categorization and search"
    )
    category = Column(
        String(50),
        nullable=True,
        comment="Artifact category"
    )
    classification = Column(
        JSONB,
        nullable=True,
        comment="Automatic classification results"
    )
    
    # Relationships and references
    inspection_id = Column(
        UUID(as_uuid=True),
        ForeignKey("inspections.id", ondelete="SET NULL"),
        nullable=True,
        comment="Associated inspection ID"
    )
    defect_id = Column(
        UUID(as_uuid=True),
        ForeignKey("defects.id", ondelete="SET NULL"),
        nullable=True,
        comment="Associated defect ID"
    )
    inference_job_id = Column(
        UUID(as_uuid=True),
        ForeignKey("inference_jobs.id", ondelete="SET NULL"),
        nullable=True,
        comment="Associated inference job ID"
    )
    parent_artifact_id = Column(
        UUID(as_uuid=True),
        ForeignKey("artifacts.id", ondelete="SET NULL"),
        nullable=True,
        comment="Parent artifact (for derived files)"
    )
    
    # Access control
    is_public = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether artifact is publicly accessible"
    )
    access_permissions = Column(
        JSONB,
        nullable=True,
        comment="Access permissions and restrictions"
    )
    uploaded_by = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User who uploaded the artifact"
    )
    
    # Lifecycle management
    retention_policy = Column(
        String(50),
        nullable=True,
        comment="Retention policy identifier"
    )
    expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When artifact expires and can be deleted"
    )
    is_archived = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether artifact is archived"
    )
    archived_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When artifact was archived"
    )
    
    # External references
    external_id = Column(
        String(100),
        nullable=True,
        comment="External system identifier"
    )
    source_system = Column(
        String(50),
        nullable=True,
        comment="Source system that created the artifact"
    )
    correlation_id = Column(
        String(100),
        nullable=True,
        comment="Correlation ID for tracking"
    )
    
    # Versioning
    version = Column(
        Integer,
        nullable=False,
        default=1,
        comment="Artifact version number"
    )
    is_latest = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether this is the latest version"
    )
    
    # Additional metadata
    custom_metadata = Column(
        JSONB,
        nullable=True,
        comment="Custom metadata fields"
    )
    notes = Column(
        Text,
        nullable=True,
        comment="Additional notes and comments"
    )
    
    # Relationships
    inspection = relationship(
        "Inspection",
        foreign_keys=[inspection_id],
        post_update=True
    )
    defect = relationship(
        "Defect",
        foreign_keys=[defect_id],
        post_update=True
    )
    inference_job = relationship(
        "InferenceJob",
        foreign_keys=[inference_job_id],
        post_update=True
    )
    parent_artifact = relationship(
        "Artifact",
        remote_side=[BaseModel.id],
        foreign_keys=[parent_artifact_id]
    )
    child_artifacts = relationship(
        "Artifact",
        remote_side=[parent_artifact_id],
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_artifacts_id", "artifact_id"),
        Index("idx_artifacts_filename", "filename"),
        Index("idx_artifacts_type", "artifact_type"),
        Index("idx_artifacts_content_type", "content_type"),
        Index("idx_artifacts_storage", "storage_location", "storage_bucket"),
        Index("idx_artifacts_checksum", "checksum_sha256"),
        Index("idx_artifacts_inspection", "inspection_id"),
        Index("idx_artifacts_defect", "defect_id"),
        Index("idx_artifacts_inference", "inference_job_id"),
        Index("idx_artifacts_parent", "parent_artifact_id"),
        Index("idx_artifacts_uploaded_by", "uploaded_by"),
        Index("idx_artifacts_tags", "tags", postgresql_using="gin"),
        Index("idx_artifacts_processed", "is_processed"),
        Index("idx_artifacts_public", "is_public"),
        Index("idx_artifacts_archived", "is_archived"),
        Index("idx_artifacts_latest", "is_latest"),
        Index("idx_artifacts_expires", "expires_at"),
        Index("idx_artifacts_metadata", "custom_metadata", postgresql_using="gin"),
    )
    
    @validates('artifact_id')
    def validate_artifact_id(self, key, value):
        """Validate artifact ID format."""
        if not value or len(value.strip()) < 5:
            raise ValueError("Artifact ID must be at least 5 characters")
        return value.strip()
    
    @validates('filename')
    def validate_filename(self, key, value):
        """Validate filename."""
        if not value or len(value.strip()) == 0:
            raise ValueError("Filename cannot be empty")
        # Check for dangerous characters
        dangerous_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*']
        for char in dangerous_chars:
            if char in value:
                raise ValueError(f"Filename cannot contain '{char}'")
        return value.strip()
    
    @validates('file_size')
    def validate_file_size(self, key, value):
        """Validate file size is positive."""
        if value is not None and value <= 0:
            raise ValueError("File size must be positive")
        return value
    
    @validates('checksum_sha256')
    def validate_checksum_sha256(self, key, value):
        """Validate SHA-256 checksum format."""
        if value and (len(value) != 64 or not all(c in '0123456789abcdef' for c in value.lower())):
            raise ValueError("Invalid SHA-256 checksum format")
        return value.lower() if value else value
    
    @validates('checksum_md5')
    def validate_checksum_md5(self, key, value):
        """Validate MD5 checksum format."""
        if value and (len(value) != 32 or not all(c in '0123456789abcdef' for c in value.lower())):
            raise ValueError("Invalid MD5 checksum format")
        return value.lower() if value else value
    
    def __repr__(self):
        return f"<Artifact(id='{self.artifact_id}', filename='{self.filename}', type='{self.artifact_type}')>"
    
    @property
    def is_image(self) -> bool:
        """Check if artifact is an image."""
        return self.artifact_type == ArtifactTypeEnum.IMAGE
    
    @property
    def is_document(self) -> bool:
        """Check if artifact is a document."""
        return self.artifact_type == ArtifactTypeEnum.DOCUMENT
    
    @property
    def is_expired(self) -> bool:
        """Check if artifact has expired."""
        return self.expires_at is not None and self.expires_at < datetime.utcnow()
    
    @property
    def size_mb(self) -> float:
        """Get file size in MB."""
        return self.file_size / (1024 * 1024) if self.file_size else 0
    
    @property
    def has_thumbnail(self) -> bool:
        """Check if artifact has a thumbnail."""
        return self.thumbnail_path is not None
    
    @property
    def has_preview(self) -> bool:
        """Check if artifact has a preview."""
        return self.preview_path is not None
    
    def get_image_dimensions(self) -> Optional[tuple]:
        """Get image dimensions as (width, height)."""
        if self.is_image and self.image_width and self.image_height:
            return (self.image_width, self.image_height)
        return None
    
    def get_image_aspect_ratio(self) -> Optional[float]:
        """Calculate image aspect ratio."""
        dimensions = self.get_image_dimensions()
        if dimensions:
            return dimensions[0] / dimensions[1]
        return None
    
    def add_tag(self, tag: str):
        """Add a tag to the artifact."""
        if self.tags is None:
            self.tags = []
        tag = tag.strip().lower()
        if tag and tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str):
        """Remove a tag from the artifact."""
        if self.tags:
            tag = tag.strip().lower()
            self.tags = [t for t in self.tags if t != tag]
    
    def has_tag(self, tag: str) -> bool:
        """Check if artifact has a specific tag."""
        return self.tags is not None and tag.strip().lower() in self.tags