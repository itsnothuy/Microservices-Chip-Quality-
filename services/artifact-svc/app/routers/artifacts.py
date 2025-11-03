"""Artifact CRUD and file management endpoints"""

from typing import Optional, List
from uuid import UUID
import io

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    Query,
    status
)
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.dependencies import get_db_session
from app.core.exceptions import (
    ArtifactServiceError,
    ArtifactNotFoundError,
    FileUploadError,
    FileValidationError
)
from app.models.artifact import ArtifactType
from app.schemas.artifact import (
    ArtifactCreate,
    ArtifactResponse,
    ArtifactListResponse,
    ArtifactUpdate,
    UploadResponse
)
from app.services.artifact_service import ArtifactService
from app.services.storage_service import StorageService


logger = structlog.get_logger()
router = APIRouter()


def get_storage_service() -> StorageService:
    """Dependency for storage service"""
    return StorageService()


def get_artifact_service(
    db: AsyncSession = Depends(get_db_session),
    storage: StorageService = Depends(get_storage_service)
) -> ArtifactService:
    """Dependency for artifact service"""
    return ArtifactService(db, storage)


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_artifact(
    file: UploadFile = File(...),
    inspection_id: str = Form(...),
    artifact_type: str = Form(...),
    inference_job_id: Optional[str] = Form(None),
    artifact_service: ArtifactService = Depends(get_artifact_service)
):
    """
    Upload artifact file with metadata
    
    - **file**: File to upload
    - **inspection_id**: Associated inspection ID
    - **artifact_type**: Type of artifact (image, video, document, etc.)
    - **inference_job_id**: Optional inference job ID
    """
    try:
        # Parse UUIDs
        inspection_uuid = UUID(inspection_id)
        inference_job_uuid = UUID(inference_job_id) if inference_job_id else None
        
        # Parse artifact type
        try:
            artifact_type_enum = ArtifactType(artifact_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid artifact type: {artifact_type}"
            )
        
        # Get file content
        file_content = await file.read()
        file_size = len(file_content)
        file_obj = io.BytesIO(file_content)
        
        # Create artifact data
        artifact_data = ArtifactCreate(
            inspection_id=inspection_uuid,
            artifact_type=artifact_type_enum,
            inference_job_id=inference_job_uuid,
            metadata={},
            tags=[]
        )
        
        # Upload and create artifact
        artifact = await artifact_service.create_artifact(
            file_obj=file_obj,
            filename=file.filename,
            file_size=file_size,
            content_type=file.content_type or "application/octet-stream",
            artifact_data=artifact_data
        )
        
        logger.info(
            "Artifact uploaded via API",
            artifact_id=str(artifact.id),
            filename=file.filename,
            size=file_size
        )
        
        return UploadResponse(
            artifact_id=artifact.id,
            file_name=artifact.file_name,
            file_size_bytes=artifact.file_size_bytes,
            content_type=artifact.content_type,
            checksum_sha256=artifact.checksum_sha256,
            storage_path=artifact.file_path
        )
        
    except FileValidationError as e:
        logger.warning("File validation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )
    except FileUploadError as e:
        logger.error("File upload failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID format: {str(e)}"
        )
    except Exception as e:
        logger.error("Unexpected error during upload", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during upload"
        )


@router.get("/", response_model=ArtifactListResponse)
async def list_artifacts(
    limit: int = Query(default=50, le=100, description="Number of artifacts to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    inspection_id: Optional[str] = Query(None, description="Filter by inspection ID"),
    artifact_type: Optional[str] = Query(None, description="Filter by artifact type"),
    artifact_service: ArtifactService = Depends(get_artifact_service)
):
    """
    List artifacts with filtering and pagination
    
    - **limit**: Maximum number of results (max 100)
    - **offset**: Offset for pagination
    - **inspection_id**: Filter by inspection ID
    - **artifact_type**: Filter by artifact type
    """
    try:
        # Parse optional filters
        inspection_uuid = UUID(inspection_id) if inspection_id else None
        artifact_type_enum = ArtifactType(artifact_type) if artifact_type else None
        
        # List artifacts
        artifacts = await artifact_service.list_artifacts(
            limit=limit,
            offset=offset,
            inspection_id=inspection_uuid,
            artifact_type=artifact_type_enum
        )
        
        return artifacts
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid parameter: {str(e)}"
        )
    except Exception as e:
        logger.error("Error listing artifacts", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while listing artifacts"
        )


@router.get("/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(
    artifact_id: str,
    artifact_service: ArtifactService = Depends(get_artifact_service)
):
    """
    Get artifact metadata by ID
    
    - **artifact_id**: Artifact UUID
    """
    try:
        artifact_uuid = UUID(artifact_id)
        artifact = await artifact_service.get_artifact(artifact_uuid)
        return artifact
        
    except ArtifactNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact not found: {artifact_id}"
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid artifact ID format"
        )
    except Exception as e:
        logger.error("Error getting artifact", artifact_id=artifact_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while getting artifact"
        )


@router.get("/{artifact_id}/download")
async def download_artifact(
    artifact_id: str,
    artifact_service: ArtifactService = Depends(get_artifact_service)
):
    """
    Download artifact file
    
    - **artifact_id**: Artifact UUID
    """
    try:
        artifact_uuid = UUID(artifact_id)
        
        # Get file stream and metadata
        file_stream, artifact = await artifact_service.get_download_stream(artifact_uuid)
        
        # Create streaming response
        def iterfile():
            while True:
                chunk = file_stream.read(8192)
                if not chunk:
                    break
                yield chunk
        
        headers = {
            "Content-Disposition": f'attachment; filename="{artifact.file_name}"',
            "Content-Type": artifact.content_type,
            "Content-Length": str(artifact.file_size_bytes),
            "X-Artifact-ID": str(artifact.id),
            "X-Checksum-SHA256": artifact.checksum_sha256
        }
        
        logger.info(
            "Artifact download started",
            artifact_id=str(artifact.id),
            filename=artifact.file_name
        )
        
        return StreamingResponse(
            iterfile(),
            media_type=artifact.content_type,
            headers=headers
        )
        
    except ArtifactNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact not found: {artifact_id}"
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid artifact ID format"
        )
    except Exception as e:
        logger.error("Error downloading artifact", artifact_id=artifact_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while downloading artifact"
        )


@router.put("/{artifact_id}", response_model=ArtifactResponse)
async def update_artifact(
    artifact_id: str,
    update_data: ArtifactUpdate,
    artifact_service: ArtifactService = Depends(get_artifact_service)
):
    """
    Update artifact metadata
    
    - **artifact_id**: Artifact UUID
    - **update_data**: Fields to update
    """
    try:
        artifact_uuid = UUID(artifact_id)
        artifact = await artifact_service.update_artifact(artifact_uuid, update_data)
        return artifact
        
    except ArtifactNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact not found: {artifact_id}"
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid artifact ID format"
        )
    except Exception as e:
        logger.error("Error updating artifact", artifact_id=artifact_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while updating artifact"
        )


@router.delete("/{artifact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_artifact(
    artifact_id: str,
    artifact_service: ArtifactService = Depends(get_artifact_service)
):
    """
    Delete artifact and associated file
    
    - **artifact_id**: Artifact UUID
    """
    try:
        artifact_uuid = UUID(artifact_id)
        await artifact_service.delete_artifact(artifact_uuid)
        
        logger.info("Artifact deleted via API", artifact_id=artifact_id)
        
    except ArtifactNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact not found: {artifact_id}"
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid artifact ID format"
        )
    except Exception as e:
        logger.error("Error deleting artifact", artifact_id=artifact_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while deleting artifact"
        )
