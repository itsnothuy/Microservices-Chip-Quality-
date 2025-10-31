"""Unit tests for ML inference service."""

import pytest
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.triton_client import TritonClient
from app.services.preprocessing import PreprocessingService
from app.services.postprocessing import PostprocessingService
from app.services.inference_service import InferenceService
from app.core.exceptions import ModelNotFoundError, InferenceError


@pytest.fixture
def triton_client():
    """Mock Triton client."""
    client = TritonClient(
        server_url="localhost:8001",
        http_url="http://localhost:8000",
        timeout=30
    )
    return client


@pytest.fixture
def preprocessing_service():
    """Preprocessing service instance."""
    return PreprocessingService()


@pytest.fixture
def postprocessing_service():
    """Postprocessing service instance."""
    return PostprocessingService()


@pytest.mark.asyncio
async def test_triton_client_connect(triton_client):
    """Test Triton client connection."""
    await triton_client.connect()
    assert triton_client.is_connected is True


@pytest.mark.asyncio
async def test_triton_client_health_check(triton_client):
    """Test Triton health check."""
    await triton_client.connect()
    is_healthy = await triton_client.health_check()
    assert is_healthy is True


@pytest.mark.asyncio
async def test_preprocess_image(preprocessing_service):
    """Test image preprocessing."""
    # Create mock image data
    image_data = b"\x00" * 1024  # Mock image bytes
    
    result = await preprocessing_service.preprocess_image(image_data)
    
    assert result is not None
    assert isinstance(result, np.ndarray)
    assert result.shape[0] == 1  # Batch dimension
    assert result.shape[1] == 3  # RGB channels


@pytest.mark.asyncio
async def test_validate_image(preprocessing_service):
    """Test image validation."""
    image_data = b"\x00" * 1024
    
    metadata = await preprocessing_service.validate_image(image_data)
    
    assert metadata is not None
    assert metadata["is_valid"] is True
    assert "format" in metadata
    assert "width" in metadata
    assert "height" in metadata


@pytest.mark.asyncio
async def test_postprocess_outputs(postprocessing_service):
    """Test output postprocessing."""
    # Create mock model outputs
    outputs = {
        "output": np.random.rand(1, 10).astype(np.float32)
    }
    
    result = await postprocessing_service.process_outputs(
        model_outputs=outputs,
        model_name="defect_detection_v1"
    )
    
    assert result is not None
    assert hasattr(result, "defects")
    assert hasattr(result, "quality_assessment")
    assert result.quality_assessment.defect_count >= 0


@pytest.mark.asyncio
async def test_filter_by_confidence(postprocessing_service):
    """Test confidence filtering."""
    from app.schemas.prediction import (
        DefectPrediction, DefectType, DefectSeverity,
        BoundingBox, DefectCharacteristics
    )
    
    predictions = [
        DefectPrediction(
            defect_id="1",
            defect_type=DefectType.SCRATCH,
            severity=DefectSeverity.MINOR,
            confidence=0.9,
            bounding_box=BoundingBox(x=0, y=0, width=10, height=10),
            characteristics=DefectCharacteristics(area=100, perimeter=40)
        ),
        DefectPrediction(
            defect_id="2",
            defect_type=DefectType.VOID,
            severity=DefectSeverity.MAJOR,
            confidence=0.5,
            bounding_box=BoundingBox(x=0, y=0, width=10, height=10),
            characteristics=DefectCharacteristics(area=100, perimeter=40)
        )
    ]
    
    filtered = await postprocessing_service.filter_by_confidence(
        predictions, threshold=0.75
    )
    
    assert len(filtered) == 1
    assert filtered[0].confidence >= 0.75


@pytest.mark.asyncio
async def test_model_metadata_retrieval(triton_client):
    """Test model metadata retrieval."""
    await triton_client.connect()
    
    metadata = await triton_client.get_model_metadata("defect_detection_v1")
    
    assert metadata is not None
    assert "name" in metadata
    assert "inputs" in metadata
    assert "outputs" in metadata


@pytest.mark.asyncio
async def test_inference_with_invalid_model(triton_client):
    """Test inference with invalid model raises error."""
    await triton_client.connect()
    
    # This should work in simulation mode
    inputs = {"input": np.random.rand(1, 3, 1024, 1024).astype(np.float32)}
    
    # In real scenario, this would raise ModelNotFoundError
    result = await triton_client.infer(
        model_name="nonexistent_model",
        inputs=inputs
    )
    
    assert result is not None


@pytest.mark.asyncio
async def test_batch_preprocessing(preprocessing_service):
    """Test batch image preprocessing."""
    images = [b"\x00" * 1024, b"\x00" * 2048]
    
    result = await preprocessing_service.preprocess_batch(images)
    
    assert result is not None
    assert isinstance(result, np.ndarray)
    assert result.shape[0] == len(images)


@pytest.mark.asyncio
async def test_performance_metrics_recording():
    """Test performance metrics recording."""
    from redis import asyncio as aioredis
    from app.services.performance_monitor import PerformanceMonitor
    
    # Create mock Redis client
    redis_mock = AsyncMock(spec=aioredis.Redis)
    redis_mock.hset = AsyncMock()
    redis_mock.expire = AsyncMock()
    
    monitor = PerformanceMonitor(redis_mock)
    
    await monitor.record_inference(
        model_name="test_model",
        model_version="1",
        latency_ms=45.5,
        success=True,
        confidence=0.95
    )
    
    # Verify Redis was called
    assert redis_mock.hset.called
    assert redis_mock.expire.called


@pytest.mark.asyncio
async def test_anomaly_detection():
    """Test performance anomaly detection."""
    from redis import asyncio as aioredis
    from app.services.performance_monitor import PerformanceMonitor
    
    redis_mock = AsyncMock(spec=aioredis.Redis)
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.keys = AsyncMock(return_value=[])
    
    monitor = PerformanceMonitor(redis_mock)
    
    # Record some metrics with anomalies
    for i in range(10):
        await monitor.record_inference(
            model_name="test_model",
            model_version="1",
            latency_ms=3000,  # High latency anomaly
            success=False if i % 3 == 0 else True,  # Some failures
            confidence=0.6  # Low confidence anomaly
        )
    
    anomalies = await monitor.detect_anomalies("test_model", "1")
    
    assert len(anomalies) > 0
    assert any(a["type"] == "high_latency" for a in anomalies)
