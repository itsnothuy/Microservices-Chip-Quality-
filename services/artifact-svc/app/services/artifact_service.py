"""Core artifact management service"""

from typing import BinaryIO, Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.models.artifact import Artifact, ArtifactType, StorageLocation
from app.schemas.artifact import (
    ArtifactCreate,
    ArtifactUpdate,
    ArtifactResponse,
    ArtifactListResponse
)
from app.services.storage_service import StorageService
from app.utils.file_utils import (
    calculate_sha256,
    validate_file_size,
    validate_content_type,
    generate_storage_path,
    get_content_type,
    extract_file_metadata
)
from app.core.exceptions import (
    ArtifactNotFoundError,
    FileUploadError,
    FileValidationError
)


logger = structlog.get_logger()


class ArtifactService:
    """Service for managing artifact CRUD operations and file handling"""
    
    def __init__(self, db: AsyncSession, storage_service: StorageService):
        """
        Initialize artifact service
        
        Args:
            db: Database session
            storage_service: Storage service instance
        """
        self.db = db
        self.storage = storage_service
    
    async def create_artifact(
        self,
        file_obj: BinaryIO,
        filename: str,
        file_size: int,
        content_type: str,
        artifact_data: ArtifactCreate
    ) -> ArtifactResponse:
        """
        Create new artifact with file upload
        
        Args:
            file_obj: File object to upload
            filename: Original filename
            file_size: Size of file in bytes
            content_type: MIME type
            artifact_data: Artifact metadata
            
        Returns:
            Created artifact response
            
        Raises:
            FileValidationError: If file validation fails
            FileUploadError: If upload fails
        """
        try:
            # Validate file
            validate_file_size(file_size)
            validate_content_type(content_type)
            
            # Calculate checksum
            checksum = calculate_sha256(file_obj)
            
            # Generate storage path
            storage_path = generate_storage_path(
                artifact_data.inspection_id,
                artifact_data.artifact_type.value,
                filename
            )
            
            # Upload to storage
            await self.storage.upload_file(
                file_path=storage_path,
                file_obj=file_obj,
                file_size=file_size,
                content_type=content_type,
                metadata=artifact_data.metadata
            )
            
            # Create database record
            artifact = Artifact(
                inspection_id=artifact_data.inspection_id,
                inference_job_id=artifact_data.inference_job_id,
                artifact_type=artifact_data.artifact_type,
                file_name=filename,
                file_path=storage_path,
                content_type=content_type,
                file_size_bytes=file_size,
                checksum_sha256=checksum,
                storage_location=StorageLocation.PRIMARY,
                metadata=artifact_data.metadata,
                tags=artifact_data.tags,
                created_at=datetime.utcnow()
            )
            
            self.db.add(artifact)
            await self.db.commit()
            await self.db.refresh(artifact)
            
            logger.info(
                "Artifact created successfully",
                artifact_id=str(artifact.id),
                filename=filename,
                size=file_size,
                inspection_id=str(artifact_data.inspection_id)
            )
            
            return ArtifactResponse.model_validate(artifact)
            
        except (FileValidationError, Exception) as e:
            await self.db.rollback()
            # Clean up storage if database operation fails
            try:
                if 'storage_path' in locals():
                    await self.storage.delete_file(storage_path)
            except Exception:
                pass
            
            logger.error(
                "Failed to create artifact",
                error=str(e),
                filename=filename
            )
            raise FileUploadError(f"Failed to create artifact: {str(e)}")
    
    async def get_artifact(self, artifact_id: UUID) -> ArtifactResponse:
        """
        Get artifact by ID
        
        Args:
            artifact_id: Artifact UUID
            
        Returns:
            Artifact response
            
        Raises:
            ArtifactNotFoundError: If artifact not found
        """
        result = await self.db.execute(
            select(Artifact).where(Artifact.id == artifact_id)
        )
        artifact = result.scalar_one_or_none()
        
        if not artifact:
            raise ArtifactNotFoundError(str(artifact_id))
        
        return ArtifactResponse.model_validate(artifact)
    
    async def list_artifacts(
        self,
        limit: int = 50,
        offset: int = 0,
        inspection_id: Optional[UUID] = None,
        artifact_type: Optional[ArtifactType] = None,
        tags: Optional[List[str]] = None
    ) -> ArtifactListResponse:
        """
        List artifacts with filtering and pagination
        
        Args:
            limit: Maximum number of results
            offset: Offset for pagination
            inspection_id: Filter by inspection ID
            artifact_type: Filter by artifact type
            tags: Filter by tags
            
        Returns:
            Paginated list of artifacts
        """
        # Build query
        query = select(Artifact)
        
        # Apply filters
        conditions = []
        if inspection_id:
            conditions.append(Artifact.inspection_id == inspection_id)
        if artifact_type:
            conditions.append(Artifact.artifact_type == artifact_type)
        if tags:
            # Filter artifacts that have all specified tags
            for tag in tags:
                conditions.append(Artifact.tags.contains([tag]))
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Add ordering
        query = query.order_by(Artifact.created_at.desc())
        
        # Get total count
        count_query = select(func.count()).select_from(Artifact)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        query = query.limit(limit).offset(offset)
        
        # Execute query
        result = await self.db.execute(query)
        artifacts = result.scalars().all()
        
        # Convert to response models
        artifact_responses = [
            ArtifactResponse.model_validate(artifact)
            for artifact in artifacts
        ]
        
        has_more = (offset + limit) < total
        
        return ArtifactListResponse(
            data=artifact_responses,
            total=total,
            has_more=has_more
        )
    
    async def update_artifact(
        self,
        artifact_id: UUID,
        update_data: ArtifactUpdate
    ) -> ArtifactResponse:
        """
        Update artifact metadata
        
        Args:
            artifact_id: Artifact UUID
            update_data: Update data
            
        Returns:
            Updated artifact response
            
        Raises:
            ArtifactNotFoundError: If artifact not found
        """
        result = await self.db.execute(
            select(Artifact).where(Artifact.id == artifact_id)
        )
        artifact = result.scalar_one_or_none()
        
        if not artifact:
            raise ArtifactNotFoundError(str(artifact_id))
        
        # Update fields
        if update_data.metadata is not None:
            artifact.metadata = update_data.metadata
        if update_data.tags is not None:
            artifact.tags = update_data.tags
        if update_data.storage_location is not None:
            artifact.storage_location = update_data.storage_location
        
        await self.db.commit()
        await self.db.refresh(artifact)
        
        logger.info(
            "Artifact updated successfully",
            artifact_id=str(artifact_id)
        )
        
        return ArtifactResponse.model_validate(artifact)
    
    async def delete_artifact(self, artifact_id: UUID) -> None:
        """
        Delete artifact and associated file
        
        Args:
            artifact_id: Artifact UUID
            
        Raises:
            ArtifactNotFoundError: If artifact not found
        """
        result = await self.db.execute(
            select(Artifact).where(Artifact.id == artifact_id)
        )
        artifact = result.scalar_one_or_none()
        
        if not artifact:
            raise ArtifactNotFoundError(str(artifact_id))
        
        # Delete from storage
        try:
            await self.storage.delete_file(artifact.file_path)
        except Exception as e:
            logger.error(
                "Failed to delete file from storage",
                artifact_id=str(artifact_id),
                error=str(e)
            )
            # Continue with database deletion even if storage deletion fails
        
        # Delete from database
        await self.db.delete(artifact)
        await self.db.commit()
        
        logger.info(
            "Artifact deleted successfully",
            artifact_id=str(artifact_id)
        )
    
    async def get_download_stream(self, artifact_id: UUID) -> tuple[BinaryIO, Artifact]:
        """
        Get file stream for downloading
        
        Args:
            artifact_id: Artifact UUID
            
        Returns:
            Tuple of (file stream, artifact metadata)
            
        Raises:
            ArtifactNotFoundError: If artifact not found
        """
        result = await self.db.execute(
            select(Artifact).where(Artifact.id == artifact_id)
        )
        artifact = result.scalar_one_or_none()
        
        if not artifact:
            raise ArtifactNotFoundError(str(artifact_id))
        
        # Download from storage
        file_stream = await self.storage.download_file(artifact.file_path)
        
        return file_stream, artifact
