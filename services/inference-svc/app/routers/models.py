"""
Model management API endpoints.

Model lifecycle management endpoints:

Model Deployment:
POST   /deploy            - Deploy new model version
GET    /                  - List available models
GET    /{name}            - Get model information
POST   /{name}/load       - Load model to Triton
POST   /{name}/unload     - Unload model from Triton

Model Configuration:
GET    /{name}/versions   - List model versions
GET    /{name}/status     - Get model health status
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
import structlog

from ..core.dependencies import get_model_service, get_triton_client
from ..schemas.model import (
    ModelInfo,
    ModelListResponse,
    ModelVersionInfo,
    ModelVersionListResponse,
    ModelDeployRequest,
    ModelDeployResponse,
    ModelStatus
)
from ..services.model_service import ModelService
from ..services.triton_client import TritonClient


logger = structlog.get_logger()
router = APIRouter()


@router.get("/", response_model=ModelListResponse)
async def list_models(
    model_service: ModelService = Depends(get_model_service)
):
    """
    List all available models.
    
    Returns information about all models in the repository.
    """
    logger.info("Listing available models")
    
    try:
        models = await model_service.list_models()
        
        return ModelListResponse(
            models=models,
            total=len(models)
        )
        
    except Exception as e:
        logger.error("Failed to list models", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list models: {str(e)}"
        )


@router.get("/{model_name}", response_model=ModelInfo)
async def get_model_info(
    model_name: str,
    version: Optional[str] = Query(None, description="Model version"),
    model_service: ModelService = Depends(get_model_service)
):
    """
    Get model information and schema.
    
    Returns detailed information about a specific model.
    """
    logger.info("Getting model info", model_name=model_name, version=version)
    
    try:
        model_info = await model_service.get_model(model_name, version or "")
        return model_info
        
    except Exception as e:
        logger.error(
            "Failed to get model info",
            model_name=model_name,
            error=str(e)
        )
        raise HTTPException(
            status_code=404,
            detail=f"Model {model_name} not found"
        )


@router.get("/{model_name}/versions", response_model=ModelVersionListResponse)
async def list_model_versions(
    model_name: str,
    model_service: ModelService = Depends(get_model_service)
):
    """
    List model versions.
    
    Returns all available versions of a model.
    """
    logger.info("Listing model versions", model_name=model_name)
    
    try:
        versions = await model_service.get_model_versions(model_name)
        
        from datetime import datetime
        version_infos = [
            ModelVersionInfo(
                version=v,
                status=ModelStatus.READY,
                is_default=(v == versions[0] if versions else False),
                deployment_date=datetime.utcnow(),
                performance_score=0.95,
                accuracy_metrics={"accuracy": 0.95}
            )
            for v in versions
        ]
        
        return ModelVersionListResponse(
            model_name=model_name,
            versions=version_infos,
            total=len(version_infos)
        )
        
    except Exception as e:
        logger.error(
            "Failed to list model versions",
            model_name=model_name,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list versions: {str(e)}"
        )


@router.get("/{model_name}/status")
async def get_model_status(
    model_name: str,
    version: Optional[str] = Query(None, description="Model version"),
    model_service: ModelService = Depends(get_model_service)
):
    """
    Get model health status.
    
    Returns current health and readiness of the model.
    """
    logger.info("Getting model status", model_name=model_name, version=version)
    
    try:
        is_healthy = await model_service.check_model_health(model_name, version or "")
        
        return {
            "model_name": model_name,
            "version": version or "latest",
            "status": "ready" if is_healthy else "unavailable",
            "is_ready": is_healthy
        }
        
    except Exception as e:
        logger.error(
            "Failed to check model status",
            model_name=model_name,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check status: {str(e)}"
        )


@router.post("/deploy", response_model=ModelDeployResponse)
async def deploy_model(
    request: ModelDeployRequest,
    model_service: ModelService = Depends(get_model_service)
):
    """
    Deploy new model version.
    
    Deploys a model version to the Triton inference server.
    """
    logger.info(
        "Deploying model",
        model_name=request.model_name,
        version=request.version
    )
    
    try:
        success = await model_service.deploy_model(
            model_name=request.model_name,
            version=request.version,
            config=request.config
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Model deployment failed"
            )
        
        from datetime import datetime
        return ModelDeployResponse(
            model_name=request.model_name,
            version=request.version,
            status=ModelStatus.READY,
            message="Model deployed successfully",
            deployed_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(
            "Model deployment failed",
            model_name=request.model_name,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Deployment failed: {str(e)}"
        )


@router.post("/{model_name}/load")
async def load_model(
    model_name: str,
    triton_client: TritonClient = Depends(get_triton_client)
):
    """
    Load model to Triton server.
    
    Loads a model into the Triton inference server.
    """
    logger.info("Loading model to Triton", model_name=model_name)
    
    try:
        success = await triton_client.load_model(model_name)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to load model"
            )
        
        return {
            "status": "success",
            "message": f"Model {model_name} loaded successfully"
        }
        
    except Exception as e:
        logger.error("Failed to load model", model_name=model_name, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load model: {str(e)}"
        )


@router.post("/{model_name}/unload")
async def unload_model(
    model_name: str,
    model_service: ModelService = Depends(get_model_service)
):
    """
    Unload model from Triton server.
    
    Removes a model from the Triton inference server.
    """
    logger.info("Unloading model from Triton", model_name=model_name)
    
    try:
        success = await model_service.unload_model(model_name)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to unload model"
            )
        
        return {
            "status": "success",
            "message": f"Model {model_name} unloaded successfully"
        }
        
    except Exception as e:
        logger.error("Failed to unload model", model_name=model_name, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to unload model: {str(e)}"
        )
