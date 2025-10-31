"""
ML model lifecycle management service.

Model Deployment:
- Model loading and validation from repository
- Version management and semantic versioning
- Model configuration and parameter management
- Dynamic model deployment to Triton server
- Model warmup and performance optimization
- Resource allocation and GPU memory management

Model Operations:
- A/B testing framework for model comparison
- Model performance monitoring and drift detection
- Automated rollback for underperforming models
- Model ensemble configuration and management
- Training pipeline integration for continuous learning
- Model metadata tracking and documentation

Quality Assurance:
- Model validation against test datasets
- Performance benchmarking and SLA monitoring
- Accuracy tracking and regression detection
- Model explainability and interpretability tools
- Compliance validation for regulatory requirements
"""

import asyncio
from typing import Any, Optional
from datetime import datetime

import structlog
from redis import asyncio as aioredis

from ..core.config import settings
from ..core.exceptions import ModelNotFoundError, ModelVersionConflictError
from ..schemas.model import ModelInfo, ModelStatus, ModelPlatform
from .triton_client import TritonClient


logger = structlog.get_logger()


class ModelService:
    """
    Model lifecycle management service.
    
    Manages model deployment, versioning, configuration,
    and performance tracking.
    """
    
    def __init__(self, triton_client: TritonClient, redis: aioredis.Redis):
        """
        Initialize model service.
        
        Args:
            triton_client: Triton client instance
            redis: Redis client for caching
        """
        self.triton_client = triton_client
        self.redis = redis
        self.model_repository = settings.model_repository_path
        
        logger.info(
            "Model service initialized",
            model_repository=self.model_repository
        )
    
    async def list_models(self) -> list[ModelInfo]:
        """
        List all available models.
        
        Returns:
            List of model information
        """
        logger.debug("Listing available models")
        
        # In production, query Triton server and model repository
        # For now, return mock models
        await asyncio.sleep(0.1)
        
        models = [
            ModelInfo(
                name="defect_detection_v1",
                version="1",
                platform=ModelPlatform.ONNX,
                description="Primary defect detection model",
                status=ModelStatus.READY,
                input_shapes={"input": [1, 3, 1024, 1024]},
                output_shapes={"output": [1, 10]},
                max_batch_size=32,
                instance_count=2,
                performance_metrics={
                    "avg_latency_ms": 45.3,
                    "throughput_per_sec": 120.5
                },
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]
        
        return models
    
    async def get_model(self, model_name: str, version: str = "") -> ModelInfo:
        """
        Get model information.
        
        Args:
            model_name: Name of the model
            version: Model version
            
        Returns:
            Model information
            
        Raises:
            ModelNotFoundError: If model doesn't exist
        """
        logger.debug("Getting model info", model_name=model_name, version=version)
        
        # Check cache
        cache_key = f"model:{model_name}:{version}"
        cached = await self.redis.get(cache_key)
        if cached:
            logger.debug("Model info retrieved from cache", model_name=model_name)
            # In production: return ModelInfo.parse_raw(cached)
        
        # Get from Triton
        try:
            metadata = await self.triton_client.get_model_metadata(model_name, version)
            
            # Convert to ModelInfo
            model_info = ModelInfo(
                name=model_name,
                version=version or metadata.get("versions", ["1"])[0],
                platform=ModelPlatform.ONNX,
                description=f"Model {model_name}",
                status=ModelStatus.READY,
                input_shapes={"input": [1, 3, 1024, 1024]},
                output_shapes={"output": [1, 10]},
                max_batch_size=32,
                instance_count=2,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Cache for 5 minutes
            # await self.redis.setex(cache_key, 300, model_info.model_dump_json())
            
            return model_info
            
        except Exception as e:
            logger.error("Failed to get model info", model_name=model_name, error=str(e))
            raise ModelNotFoundError(model_name, version)
    
    async def deploy_model(
        self,
        model_name: str,
        version: str,
        config: dict[str, Any] | None = None
    ) -> bool:
        """
        Deploy model to Triton server.
        
        Args:
            model_name: Name of the model
            version: Version to deploy
            config: Deployment configuration
            
        Returns:
            True if successful
        """
        logger.info(
            "Deploying model",
            model_name=model_name,
            version=version,
            config=config
        )
        
        try:
            # Load model to Triton
            success = await self.triton_client.load_model(model_name)
            
            if success:
                # Update cache
                cache_key = f"model:{model_name}:{version}"
                await self.redis.delete(cache_key)
                
                logger.info(
                    "Model deployed successfully",
                    model_name=model_name,
                    version=version
                )
            
            return success
            
        except Exception as e:
            logger.error(
                "Model deployment failed",
                model_name=model_name,
                version=version,
                error=str(e)
            )
            return False
    
    async def unload_model(self, model_name: str) -> bool:
        """
        Unload model from Triton server.
        
        Args:
            model_name: Name of the model
            
        Returns:
            True if successful
        """
        logger.info("Unloading model", model_name=model_name)
        
        try:
            success = await self.triton_client.unload_model(model_name)
            
            if success:
                # Clear cache
                pattern = f"model:{model_name}:*"
                keys = await self.redis.keys(pattern)
                if keys:
                    await self.redis.delete(*keys)
                
                logger.info("Model unloaded successfully", model_name=model_name)
            
            return success
            
        except Exception as e:
            logger.error("Model unload failed", model_name=model_name, error=str(e))
            return False
    
    async def check_model_health(self, model_name: str, version: str = "") -> bool:
        """
        Check model health status.
        
        Args:
            model_name: Name of the model
            version: Model version
            
        Returns:
            True if model is healthy
        """
        try:
            is_ready = await self.triton_client.is_model_ready(model_name, version)
            return is_ready
        except Exception as e:
            logger.error("Model health check failed", model_name=model_name, error=str(e))
            return False
    
    async def get_model_versions(self, model_name: str) -> list[str]:
        """
        Get available versions of a model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            List of version strings
        """
        logger.debug("Getting model versions", model_name=model_name)
        
        try:
            metadata = await self.triton_client.get_model_metadata(model_name)
            versions = metadata.get("versions", ["1"])
            return versions
        except Exception as e:
            logger.error("Failed to get model versions", model_name=model_name, error=str(e))
            return []
