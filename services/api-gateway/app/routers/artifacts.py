"""Artifact endpoints - proxy to artifact service"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import structlog

from app.core.auth import User, get_current_user, require_artifact_read, require_artifact_write
from app.core.http_client import get_artifact_client
from app.core.rate_limiting import get_limiter


logger = structlog.get_logger()
router = APIRouter()
limiter = get_limiter()


class ArtifactResponse(BaseModel):
    """Artifact response model"""
    id: str
    inspection_id: str
    chip_id: str
    artifact_type: str
    filename: str
    content_type: str
    size_bytes: int
    storage_path: str
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class ArtifactCreate(BaseModel):
    """Create artifact metadata"""
    inspection_id: str = Field(..., description="Associated inspection ID")
    chip_id: str = Field(..., description="Associated chip ID")
    artifact_type: str = Field(..., description="Type of artifact (image, measurement, log, etc.)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


@router.post("/upload", response_model=ArtifactResponse)
@limiter.limit("10/minute")
async def upload_artifact(
    request: Request,
    file: UploadFile = File(...),
    inspection_id: str = Query(..., description="Inspection ID"),
    chip_id: str = Query(..., description="Chip ID"),
    artifact_type: str = Query(..., description="Artifact type"),
    current_user: User = Depends(require_artifact_write),
    artifact_client = Depends(get_artifact_client)
):
    """Upload artifact file"""
    
    try:
        # Prepare multipart form data
        files = {"file": (file.filename, file.file, file.content_type)}
        data = {
            "inspection_id": inspection_id,
            "chip_id": chip_id,
            "artifact_type": artifact_type
        }
        
        # Forward request to artifact service
        response = await artifact_client.post(
            "/api/v1/artifacts/upload",
            files=files,
            data=data,
            headers={
                "X-User-ID": current_user.id,
                "X-User-Scopes": ",".join(current_user.scopes)
            }
        )
        
        if response.status_code == 201:
            logger.info(
                "Artifact uploaded successfully",
                artifact_id=response.json().get("id"),
                filename=file.filename,
                inspection_id=inspection_id,
                chip_id=chip_id,
                user_id=current_user.id
            )
            return response.json()
        else:
            logger.error(
                "Failed to upload artifact",
                status_code=response.status_code,
                response=response.text,
                filename=file.filename
            )
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to upload artifact: {response.text}"
            )
            
    except Exception as e:
        logger.error(
            "Error uploading artifact",
            error=str(e),
            filename=file.filename,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while uploading artifact"
        )


@router.get("/", response_model=List[ArtifactResponse])
@limiter.limit("60/minute")
async def list_artifacts(
    request: Request,
    limit: int = Query(default=50, le=100, description="Number of artifacts to return"),
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    inspection_id: Optional[str] = Query(None, description="Filter by inspection ID"),
    chip_id: Optional[str] = Query(None, description="Filter by chip ID"),
    artifact_type: Optional[str] = Query(None, description="Filter by artifact type"),
    current_user: User = Depends(require_artifact_read),
    artifact_client = Depends(get_artifact_client)
):
    """List artifacts with filtering and pagination"""
    
    try:
        # Build query parameters
        params = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        if inspection_id:
            params["inspection_id"] = inspection_id
        if chip_id:
            params["chip_id"] = chip_id
        if artifact_type:
            params["artifact_type"] = artifact_type
        
        # Forward request to artifact service
        response = await artifact_client.get(
            "/api/v1/artifacts",
            params=params,
            headers={
                "X-User-ID": current_user.id,
                "X-User-Scopes": ",".join(current_user.scopes)
            }
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to list artifacts: {response.text}"
            )
            
    except Exception as e:
        logger.error("Error listing artifacts", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=500,
            detail="Internal server error while listing artifacts"
        )


@router.get("/{artifact_id}", response_model=ArtifactResponse)
@limiter.limit("100/minute")
async def get_artifact(
    artifact_id: str,
    current_user: User = Depends(require_artifact_read),
    artifact_client = Depends(get_artifact_client)
):
    """Get artifact metadata by ID"""
    
    try:
        response = await artifact_client.get(
            f"/api/v1/artifacts/{artifact_id}",
            headers={
                "X-User-ID": current_user.id,
                "X-User-Scopes": ",".join(current_user.scopes)
            }
        )
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            raise HTTPException(status_code=404, detail="Artifact not found")
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to get artifact: {response.text}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error getting artifact",
            artifact_id=artifact_id,
            error=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while getting artifact"
        )


@router.get("/{artifact_id}/download")
@limiter.limit("30/minute")
async def download_artifact(
    artifact_id: str,
    current_user: User = Depends(require_artifact_read),
    artifact_client = Depends(get_artifact_client)
):
    """Download artifact file"""
    
    try:
        response = await artifact_client.get(
            f"/api/v1/artifacts/{artifact_id}/download",
            headers={
                "X-User-ID": current_user.id,
                "X-User-Scopes": ",".join(current_user.scopes)
            }
        )
        
        if response.status_code == 200:
            # Stream the file content
            async def generate():
                async for chunk in response.aiter_bytes(chunk_size=8192):
                    yield chunk
            
            headers = {
                "Content-Disposition": response.headers.get("Content-Disposition", ""),
                "Content-Type": response.headers.get("Content-Type", "application/octet-stream"),
                "Content-Length": response.headers.get("Content-Length", "")
            }
            
            return StreamingResponse(
                generate(),
                headers=headers,
                media_type=response.headers.get("Content-Type", "application/octet-stream")
            )
        elif response.status_code == 404:
            raise HTTPException(status_code=404, detail="Artifact not found")
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to download artifact: {response.text}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error downloading artifact",
            artifact_id=artifact_id,
            error=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while downloading artifact"
        )


@router.delete("/{artifact_id}")
@limiter.limit("10/minute")
async def delete_artifact(
    artifact_id: str,
    current_user: User = Depends(require_artifact_write),
    artifact_client = Depends(get_artifact_client)
):
    """Delete artifact"""
    
    try:
        response = await artifact_client.delete(
            f"/api/v1/artifacts/{artifact_id}",
            headers={
                "X-User-ID": current_user.id,
                "X-User-Scopes": ",".join(current_user.scopes)
            }
        )
        
        if response.status_code == 204:
            logger.info(
                "Artifact deleted successfully",
                artifact_id=artifact_id,
                user_id=current_user.id
            )
            return {"message": "Artifact deleted successfully"}
        elif response.status_code == 404:
            raise HTTPException(status_code=404, detail="Artifact not found")
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to delete artifact: {response.text}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error deleting artifact",
            artifact_id=artifact_id,
            error=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while deleting artifact"
        )