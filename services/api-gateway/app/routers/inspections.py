"""Inspection endpoints - proxy to inspection service"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
import structlog

from app.core.auth import User, get_current_user, require_inspection_read, require_inspection_write
from app.core.http_client import get_ingestion_client
from app.core.rate_limiting import get_limiter


logger = structlog.get_logger()
router = APIRouter()
limiter = get_limiter()


class InspectionCreate(BaseModel):
    """Create inspection request"""
    batch_id: str = Field(..., description="Manufacturing batch identifier")
    chip_ids: List[str] = Field(..., description="List of chip identifiers to inspect")
    inspection_type: str = Field(..., description="Type of inspection (visual, electrical, etc.)")
    priority: str = Field(default="normal", description="Priority level (low, normal, high, critical)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    callback_url: Optional[str] = Field(None, description="Webhook URL for completion notification")


class InspectionResponse(BaseModel):
    """Inspection response"""
    id: str
    batch_id: str
    chip_ids: List[str]
    inspection_type: str
    status: str
    priority: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]
    callback_url: Optional[str]


class InspectionUpdate(BaseModel):
    """Update inspection request"""
    status: Optional[str] = None
    priority: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@router.post("/", response_model=InspectionResponse)
@limiter.limit("20/minute")
async def create_inspection(
    request: Request,
    inspection_data: InspectionCreate,
    current_user: User = Depends(require_inspection_write),
    ingestion_client = Depends(get_ingestion_client)
):
    """Create new inspection request"""
    
    try:
        # Forward request to ingestion service
        response = await ingestion_client.post(
            "/api/v1/inspections",
            json=inspection_data.model_dump(),
            headers={
                "X-User-ID": current_user.id,
                "X-User-Scopes": ",".join(current_user.scopes)
            }
        )
        
        if response.status_code == 201:
            logger.info(
                "Inspection created successfully",
                inspection_id=response.json().get("id"),
                batch_id=inspection_data.batch_id,
                user_id=current_user.id
            )
            return response.json()
        else:
            logger.error(
                "Failed to create inspection",
                status_code=response.status_code,
                response=response.text,
                batch_id=inspection_data.batch_id
            )
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to create inspection: {response.text}"
            )
            
    except Exception as e:
        logger.error(
            "Error creating inspection",
            error=str(e),
            batch_id=inspection_data.batch_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while creating inspection"
        )


@router.get("/", response_model=List[InspectionResponse])
@limiter.limit("60/minute")
async def list_inspections(
    request: Request,
    limit: int = Query(default=50, le=100, description="Number of inspections to return"),
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    status: Optional[str] = Query(None, description="Filter by status"),
    batch_id: Optional[str] = Query(None, description="Filter by batch ID"),
    current_user: User = Depends(require_inspection_read),
    ingestion_client = Depends(get_ingestion_client)
):
    """List inspections with filtering and pagination"""
    
    try:
        # Build query parameters
        params = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        if status:
            params["status"] = status
        if batch_id:
            params["batch_id"] = batch_id
        
        # Forward request to ingestion service
        response = await ingestion_client.get(
            "/api/v1/inspections",
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
                detail=f"Failed to list inspections: {response.text}"
            )
            
    except Exception as e:
        logger.error("Error listing inspections", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=500,
            detail="Internal server error while listing inspections"
        )


@router.get("/{inspection_id}", response_model=InspectionResponse)
@limiter.limit("100/minute")
async def get_inspection(
    inspection_id: str,
    current_user: User = Depends(require_inspection_read),
    ingestion_client = Depends(get_ingestion_client)
):
    """Get specific inspection by ID"""
    
    try:
        response = await ingestion_client.get(
            f"/api/v1/inspections/{inspection_id}",
            headers={
                "X-User-ID": current_user.id,
                "X-User-Scopes": ",".join(current_user.scopes)
            }
        )
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            raise HTTPException(status_code=404, detail="Inspection not found")
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to get inspection: {response.text}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error getting inspection",
            inspection_id=inspection_id,
            error=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while getting inspection"
        )


@router.patch("/{inspection_id}", response_model=InspectionResponse)
@limiter.limit("30/minute")
async def update_inspection(
    inspection_id: str,
    update_data: InspectionUpdate,
    current_user: User = Depends(require_inspection_write),
    ingestion_client = Depends(get_ingestion_client)
):
    """Update inspection"""
    
    try:
        response = await ingestion_client.patch(
            f"/api/v1/inspections/{inspection_id}",
            json=update_data.model_dump(exclude_unset=True),
            headers={
                "X-User-ID": current_user.id,
                "X-User-Scopes": ",".join(current_user.scopes)
            }
        )
        
        if response.status_code == 200:
            logger.info(
                "Inspection updated successfully",
                inspection_id=inspection_id,
                user_id=current_user.id
            )
            return response.json()
        elif response.status_code == 404:
            raise HTTPException(status_code=404, detail="Inspection not found")
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to update inspection: {response.text}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error updating inspection",
            inspection_id=inspection_id,
            error=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while updating inspection"
        )


@router.delete("/{inspection_id}")
@limiter.limit("10/minute")
async def delete_inspection(
    inspection_id: str,
    current_user: User = Depends(require_inspection_write),
    ingestion_client = Depends(get_ingestion_client)
):
    """Delete inspection"""
    
    try:
        response = await ingestion_client.delete(
            f"/api/v1/inspections/{inspection_id}",
            headers={
                "X-User-ID": current_user.id,
                "X-User-Scopes": ",".join(current_user.scopes)
            }
        )
        
        if response.status_code == 204:
            logger.info(
                "Inspection deleted successfully",
                inspection_id=inspection_id,
                user_id=current_user.id
            )
            return {"message": "Inspection deleted successfully"}
        elif response.status_code == 404:
            raise HTTPException(status_code=404, detail="Inspection not found")
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to delete inspection: {response.text}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error deleting inspection",
            inspection_id=inspection_id,
            error=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while deleting inspection"
        )