"""Artifact database models"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    String,
    BigInteger,
    DateTime,
    Text,
    Enum as SQLEnum,
    ForeignKey,
    CheckConstraint,
    Index,
    ARRAY
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from app.core.dependencies import Base


class ArtifactType(str, enum.Enum):
    """Artifact type enumeration"""
    IMAGE = "image"
    VIDEO = "video"
    MEASUREMENT = "measurement"
    DOCUMENT = "document"
    LOG = "log"


class StorageLocation(str, enum.Enum):
    """Storage location enumeration"""
    PRIMARY = "primary"
    ARCHIVE = "archive"
    COLD_STORAGE = "cold_storage"


class Artifact(Base):
    """Artifact model for storing file metadata"""
    
    __tablename__ = "artifacts"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    inspection_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    inference_job_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # File information
    artifact_type = Column(
        SQLEnum(ArtifactType, name="artifact_type_enum"),
        nullable=False,
        index=True
    )
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False, unique=True, index=True)
    content_type = Column(String(100), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)
    
    # Integrity and storage
    checksum_sha256 = Column(String(64), nullable=False, index=True)
    storage_location = Column(
        SQLEnum(StorageLocation, name="storage_location_enum"),
        nullable=False,
        default=StorageLocation.PRIMARY,
        index=True
    )
    
    # Metadata (use artifact_metadata to avoid SQLAlchemy reserved name conflict)
    artifact_metadata = Column("metadata", JSONB, nullable=False, default=dict)
    tags = Column(ARRAY(Text), default=list)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    archived_at = Column(DateTime(timezone=True), nullable=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint("file_size_bytes >= 0", name="check_file_size_non_negative"),
        CheckConstraint(
            "checksum_sha256 ~ '^[a-f0-9]{64}$'",
            name="check_valid_sha256"
        ),
        Index("idx_artifacts_tags_gin", "tags", postgresql_using="gin"),
    )
    
    def __repr__(self) -> str:
        return f"<Artifact(id={self.id}, file_name='{self.file_name}', type={self.artifact_type})>"
