"""Artifact Pydantic schemas for validation and serialization"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.artifact import ArtifactType, StorageLocation


class ArtifactBase(BaseModel):
    """Base artifact schema"""
    inspection_id: UUID = Field(..., description="Associated inspection ID")
    artifact_type: ArtifactType = Field(..., description="Type of artifact")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    tags: List[str] = Field(default_factory=list, description="Searchable tags")


class ArtifactCreate(ArtifactBase):
    """Schema for creating an artifact"""
    inference_job_id: Optional[UUID] = Field(None, description="Associated inference job ID")


class ArtifactUpdate(BaseModel):
    """Schema for updating artifact metadata"""
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    storage_location: Optional[StorageLocation] = None


class ArtifactResponse(ArtifactBase):
    """Schema for artifact response"""
    id: UUID
    inference_job_id: Optional[UUID]
    file_name: str
    file_path: str
    content_type: str
    file_size_bytes: int
    checksum_sha256: str
    storage_location: StorageLocation
    created_at: datetime
    archived_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ArtifactListResponse(BaseModel):
    """Schema for paginated artifact list response"""
    data: List[ArtifactResponse]
    total: int
    has_more: bool
    cursor: Optional[str] = None


class UploadRequest(BaseModel):
    """Schema for file upload request metadata"""
    inspection_id: UUID = Field(..., description="Associated inspection ID")
    artifact_type: ArtifactType = Field(..., description="Type of artifact")
    inference_job_id: Optional[UUID] = Field(None, description="Associated inference job ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    tags: List[str] = Field(default_factory=list, description="Searchable tags")


class UploadResponse(BaseModel):
    """Schema for file upload response"""
    artifact_id: UUID
    file_name: str
    file_size_bytes: int
    content_type: str
    checksum_sha256: str
    storage_path: str
    message: str = "File uploaded successfully"


class DownloadResponse(BaseModel):
    """Schema for download URL response"""
    artifact_id: UUID
    download_url: str
    expires_in_seconds: int
    file_name: str
    content_type: str
    file_size_bytes: int
