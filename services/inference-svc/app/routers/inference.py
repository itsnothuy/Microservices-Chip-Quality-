"""
Inference API endpoints.

Comprehensive ML inference API implementation:

Real-time Inference:
POST   /predict        - Single image defect detection
POST   /batch          - Batch image processing
GET    /{id}           - Get inference job status

Performance Monitoring:
GET    /metrics        - Get inference performance metrics
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
import structlog

from ..core.dependencies import get_inference_service, get_performance_monitor
from ..schemas.inference import (
    InferenceCreate,
    InferenceResponse,
    InferenceListResponse,
    BatchInferenceRequest,
    BatchInferenceResponse,
    InferenceMetrics,
    InferenceStatus
)
from ..services.inference_service import InferenceService
from ..services.performance_monitor import PerformanceMonitor


logger = structlog.get_logger()
router = APIRouter()


@router.post("/predict", response_model=InferenceResponse)
async def create_inference(
    inspection_id: str = Query(..., description="Inspection ID"),
    chip_id: str = Query(..., description="Chip ID"),
    model_name: str = Query(..., description="Model name"),
    model_version: Optional[str] = Query(None, description="Model version"),
    image: UploadFile = File(..., description="Image file for inference"),
    inference_service: InferenceService = Depends(get_inference_service)
):
    """
    Single image defect detection inference.
    
    Performs real-time inference on uploaded image using specified model.
    """
    logger.info(
        "Creating inference request",
        inspection_id=inspection_id,
        chip_id=chip_id,
        model_name=model_name
    )
    
    try:
        # Read image data
        image_data = await image.read()
        
        # Run inference
        result = await inference_service.run_inference(
            inspection_id=inspection_id,
            chip_id=chip_id,
            image_data=image_data,
            model_name=model_name,
            model_version=model_version
        )
        
        return result
        
    except Exception as e:
        logger.error(
            "Inference request failed",
            inspection_id=inspection_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Inference failed: {str(e)}"
        )


@router.post("/batch", response_model=BatchInferenceResponse)
async def batch_inference(
    batch_request: BatchInferenceRequest,
    inference_service: InferenceService = Depends(get_inference_service)
):
    """
    Batch image processing.
    
    Processes multiple images in a single batch request.
    """
    logger.info(
        "Creating batch inference request",
        batch_size=len(batch_request.inspections)
    )
    
    try:
        # Extract model name from first request
        model_name = batch_request.inspections[0].model_name
        model_version = batch_request.inspections[0].model_version
        
        # Prepare batch requests
        # Note: In production, would fetch image data from artifact storage
        batch_requests = [
            {
                "inspection_id": req.inspection_id,
                "chip_id": req.chip_id,
                "image_data": b"",  # Would be actual image data
            }
            for req in batch_request.inspections
        ]
        
        # Run batch inference
        results = await inference_service.run_batch_inference(
            batch_requests=batch_requests,
            model_name=model_name,
            model_version=model_version,
            config=batch_request.batch_config
        )
        
        # Create batch response
        from datetime import datetime
        response = BatchInferenceResponse(
            batch_id=f"batch_{datetime.utcnow().timestamp()}",
            total_jobs=len(results),
            successful=sum(1 for r in results if r.status == InferenceStatus.COMPLETED),
            failed=sum(1 for r in results if r.status == InferenceStatus.FAILED),
            pending=0,
            jobs=results,
            created_at=datetime.utcnow()
        )
        
        return response
        
    except Exception as e:
        logger.error("Batch inference failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Batch inference failed: {str(e)}"
        )


@router.get("/{inference_id}", response_model=InferenceResponse)
async def get_inference(
    inference_id: str,
    inference_service: InferenceService = Depends(get_inference_service)
):
    """
    Get inference job status and results.
    """
    logger.info("Getting inference", inference_id=inference_id)
    
    result = await inference_service.get_inference_status(inference_id)
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Inference {inference_id} not found"
        )
    
    return result


@router.post("/{inference_id}/cancel")
async def cancel_inference(
    inference_id: str,
    inference_service: InferenceService = Depends(get_inference_service)
):
    """
    Cancel running inference job.
    """
    logger.info("Cancelling inference", inference_id=inference_id)
    
    success = await inference_service.cancel_inference(inference_id)
    
    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to cancel inference {inference_id}"
        )
    
    return {"status": "cancelled", "inference_id": inference_id}


@router.get("/metrics/summary", response_model=InferenceMetrics)
async def get_inference_metrics(
    model_name: Optional[str] = Query(None, description="Filter by model name"),
    model_version: Optional[str] = Query(None, description="Filter by model version"),
    period_minutes: int = Query(60, description="Time period in minutes"),
    performance_monitor: PerformanceMonitor = Depends(get_performance_monitor)
):
    """
    Get inference performance metrics.
    
    Returns aggregated metrics for specified time period.
    """
    logger.info(
        "Getting inference metrics",
        model_name=model_name,
        period_minutes=period_minutes
    )
    
    try:
        if not model_name:
            model_name = "defect_detection_v1"  # Default model
        
        metrics_data = await performance_monitor.get_metrics(
            model_name=model_name,
            model_version=model_version or "",
            period_minutes=period_minutes
        )
        
        from datetime import datetime, timedelta
        
        metrics = InferenceMetrics(
            total_inferences=metrics_data.get("total_requests", 0),
            successful_inferences=metrics_data.get("successful_requests", 0),
            failed_inferences=metrics_data.get("failed_requests", 0),
            avg_inference_time_ms=metrics_data.get("avg_latency_ms", 0),
            p50_inference_time_ms=metrics_data.get("p50_latency_ms", 0),
            p95_inference_time_ms=metrics_data.get("p95_latency_ms", 0),
            p99_inference_time_ms=metrics_data.get("p99_latency_ms", 0),
            throughput_per_second=metrics_data.get("throughput_per_minute", 0) / 60,
            avg_confidence_score=metrics_data.get("avg_confidence", 0),
            period_start=datetime.utcnow() - timedelta(minutes=period_minutes),
            period_end=datetime.utcnow()
        )
        
        return metrics
        
    except Exception as e:
        logger.error("Failed to get metrics", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve metrics: {str(e)}"
        )
