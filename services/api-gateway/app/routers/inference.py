"""Inference endpoints - proxy to inference service"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
import structlog

from app.core.auth import User, get_current_user, require_inference_access
from app.core.http_client import get_inference_client
from app.core.rate_limiting import get_limiter


logger = structlog.get_logger()
router = APIRouter()
limiter = get_limiter()


class InferenceRequest(BaseModel):
    """Inference request model"""
    inspection_id: str = Field(..., description="Associated inspection ID")
    chip_id: str = Field(..., description="Chip identifier")
    artifact_ids: List[str] = Field(..., description="List of artifact IDs for inference")
    model_name: str = Field(..., description="ML model to use for inference")
    model_version: Optional[str] = Field(None, description="Specific model version (latest if not specified)")
    inference_config: Dict[str, Any] = Field(default_factory=dict, description="Model-specific configuration")
    callback_url: Optional[str] = Field(None, description="Webhook URL for completion notification")


class InferenceResponse(BaseModel):
    """Inference response model"""
    id: str
    inspection_id: str
    chip_id: str
    artifact_ids: List[str]
    model_name: str
    model_version: str
    status: str
    confidence_score: Optional[float]
    predictions: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]


class ModelInfo(BaseModel):
    """Model information"""
    name: str
    version: str
    description: str
    input_types: List[str]
    output_schema: Dict[str, Any]
    performance_metrics: Dict[str, float]
    status: str


@router.post("/", response_model=InferenceResponse)
@limiter.limit("50/minute")
async def create_inference(
    request: Request,
    inference_request: InferenceRequest,
    current_user: User = Depends(require_inference_access),
    inference_client = Depends(get_inference_client)
):
    """Create new inference request"""
    
    try:
        # Forward request to inference service
        response = await inference_client.post(
            "/api/v1/inference",
            json=inference_request.model_dump(),
            headers={
                "X-User-ID": current_user.id,
                "X-User-Scopes": ",".join(current_user.scopes)
            }
        )
        
        if response.status_code == 201:
            logger.info(
                "Inference request created successfully",
                inference_id=response.json().get("id"),
                inspection_id=inference_request.inspection_id,
                chip_id=inference_request.chip_id,
                model_name=inference_request.model_name,
                user_id=current_user.id
            )
            return response.json()
        else:
            logger.error(
                "Failed to create inference request",
                status_code=response.status_code,
                response=response.text,
                inspection_id=inference_request.inspection_id
            )
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to create inference request: {response.text}"
            )
            
    except Exception as e:
        logger.error(
            "Error creating inference request",
            error=str(e),
            inspection_id=inference_request.inspection_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while creating inference request"
        )


@router.get("/", response_model=List[InferenceResponse])
@limiter.limit("60/minute")
async def list_inferences(
    request: Request,
    limit: int = Query(default=50, le=100, description="Number of inferences to return"),
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    status: Optional[str] = Query(None, description="Filter by status"),
    inspection_id: Optional[str] = Query(None, description="Filter by inspection ID"),
    chip_id: Optional[str] = Query(None, description="Filter by chip ID"),
    model_name: Optional[str] = Query(None, description="Filter by model name"),
    current_user: User = Depends(require_inference_access),
    inference_client = Depends(get_inference_client)
):
    """List inference requests with filtering and pagination"""
    
    try:
        # Build query parameters
        params = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        if status:
            params["status"] = status
        if inspection_id:
            params["inspection_id"] = inspection_id
        if chip_id:
            params["chip_id"] = chip_id
        if model_name:
            params["model_name"] = model_name
        
        # Forward request to inference service
        response = await inference_client.get(
            "/api/v1/inference",
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
                detail=f"Failed to list inferences: {response.text}"
            )
            
    except Exception as e:
        logger.error("Error listing inferences", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=500,
            detail="Internal server error while listing inferences"
        )


@router.get("/{inference_id}", response_model=InferenceResponse)
@limiter.limit("100/minute")
async def get_inference(
    inference_id: str,
    current_user: User = Depends(require_inference_access),
    inference_client = Depends(get_inference_client)
):
    """Get specific inference by ID"""
    
    try:
        response = await inference_client.get(
            f"/api/v1/inference/{inference_id}",
            headers={
                "X-User-ID": current_user.id,
                "X-User-Scopes": ",".join(current_user.scopes)
            }
        )
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            raise HTTPException(status_code=404, detail="Inference not found")
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to get inference: {response.text}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error getting inference",
            inference_id=inference_id,
            error=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while getting inference"
        )


@router.post("/{inference_id}/cancel")
@limiter.limit("20/minute")
async def cancel_inference(
    inference_id: str,
    current_user: User = Depends(require_inference_access),
    inference_client = Depends(get_inference_client)
):
    """Cancel running inference"""
    
    try:
        response = await inference_client.post(
            f"/api/v1/inference/{inference_id}/cancel",
            headers={
                "X-User-ID": current_user.id,
                "X-User-Scopes": ",".join(current_user.scopes)
            }
        )
        
        if response.status_code == 200:
            logger.info(
                "Inference cancelled successfully",
                inference_id=inference_id,
                user_id=current_user.id
            )
            return response.json()
        elif response.status_code == 404:
            raise HTTPException(status_code=404, detail="Inference not found")
        elif response.status_code == 409:
            raise HTTPException(status_code=409, detail="Inference cannot be cancelled in current state")
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to cancel inference: {response.text}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error cancelling inference",
            inference_id=inference_id,
            error=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while cancelling inference"
        )


@router.get("/models/", response_model=List[ModelInfo])
@limiter.limit("30/minute")
async def list_models(
    current_user: User = Depends(require_inference_access),
    inference_client = Depends(get_inference_client)
):
    """List available ML models"""
    
    try:
        response = await inference_client.get(
            "/api/v1/models",
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
                detail=f"Failed to list models: {response.text}"
            )
            
    except Exception as e:
        logger.error("Error listing models", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=500,
            detail="Internal server error while listing models"
        )


@router.get("/models/{model_name}", response_model=ModelInfo)
@limiter.limit("60/minute")
async def get_model_info(
    model_name: str,
    version: Optional[str] = Query(None, description="Model version"),
    current_user: User = Depends(require_inference_access),
    inference_client = Depends(get_inference_client)
):
    """Get model information and schema"""
    
    try:
        params = {}
        if version:
            params["version"] = version
            
        response = await inference_client.get(
            f"/api/v1/models/{model_name}",
            params=params,
            headers={
                "X-User-ID": current_user.id,
                "X-User-Scopes": ",".join(current_user.scopes)
            }
        )
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            raise HTTPException(status_code=404, detail="Model not found")
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to get model info: {response.text}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error getting model info",
            model_name=model_name,
            error=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while getting model info"
        )