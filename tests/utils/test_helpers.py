# ================================================================================================
# 🛠️ TEST UTILITIES - HELPER FUNCTIONS & TEST INFRASTRUCTURE
# ================================================================================================
# Production-grade test utilities for semiconductor manufacturing platform
# Coverage: Test data management, assertion helpers, mocking utilities
# Features: Database seeding, API testing helpers, performance monitoring
# ================================================================================================

import asyncio
import json
import os
import time
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Callable
from contextlib import asynccontextmanager, contextmanager
import uuid

import pytest
import httpx
import aiofiles
from PIL import Image
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch

# ================================================================================================
# 🗄️ DATABASE TEST UTILITIES
# ================================================================================================

class DatabaseTestUtils:
    """Utilities for database testing operations."""
    
    @staticmethod
    async def seed_test_data(db_session, scenario: str = "basic") -> Dict[str, Any]:
        """Seed database with test data based on scenario."""
        
        from tests.fixtures.manufacturing_factories import (
            BatchFactory, InspectionFactory, UserFactory, QualityAlertFactory
        )
        
        seeded_data = {
            "batches": [],
            "inspections": [],
            "users": [],
            "alerts": []
        }
        
        if scenario == "basic":
            # Create basic test data
            seeded_data["users"] = [UserFactory() for _ in range(5)]
            seeded_data["batches"] = [BatchFactory() for _ in range(3)]
            
            for batch in seeded_data["batches"]:
                batch_inspections = [
                    InspectionFactory(batch_id=batch["batch_id"]) 
                    for _ in range(10)
                ]
                seeded_data["inspections"].extend(batch_inspections)
        
        elif scenario == "production_load":
            # Create production-like data volume
            seeded_data["users"] = [UserFactory() for _ in range(50)]
            seeded_data["batches"] = [BatchFactory() for _ in range(20)]
            
            for batch in seeded_data["batches"]:
                batch_inspections = [
                    InspectionFactory(batch_id=batch["batch_id"]) 
                    for _ in range(100)
                ]
                seeded_data["inspections"].extend(batch_inspections)
                
            # Add some quality alerts
            seeded_data["alerts"] = [
                QualityAlertFactory(batch_id=batch["batch_id"])
                for batch in seeded_data["batches"][:5]
            ]
        
        elif scenario == "quality_crisis":
            # Create crisis scenario data
            from tests.fixtures.manufacturing_factories import FactoryUtils
            crisis_scenario = FactoryUtils.create_quality_crisis_scenario()
            
            seeded_data["batches"] = [crisis_scenario["crisis_batch"]]
            seeded_data["inspections"] = []
            seeded_data["alerts"] = []
            
            for event in crisis_scenario["timeline"]:
                if "inspections" in event:
                    seeded_data["inspections"].extend(event["inspections"])
                elif event["event_type"] == "quality_alert":
                    seeded_data["alerts"].append(event["data"])
        
        # Insert data into database (mock implementation)
        for table_name, records in seeded_data.items():
            for record in records:
                await DatabaseTestUtils._insert_record(db_session, table_name, record)
        
        return seeded_data
    
    @staticmethod
    async def _insert_record(db_session, table_name: str, record: Dict[str, Any]):
        """Insert a single record into database (mock implementation)."""
        # In real implementation, would use actual SQL/ORM
        # For testing, we'll just simulate the operation
        await asyncio.sleep(0.001)  # Simulate database operation
        
        # Mock SQL insertion
        fields = ", ".join(record.keys())
        placeholders = ", ".join([f":{key}" for key in record.keys()])
        sql = f"INSERT INTO {table_name} ({fields}) VALUES ({placeholders})"
        
        # Execute mock query
        await db_session.execute(sql, record)
    
    @staticmethod
    async def cleanup_test_data(db_session, seeded_data: Dict[str, Any]):
        """Clean up test data from database."""
        # Clean up in reverse order to handle foreign key constraints
        cleanup_order = ["alerts", "inspections", "batches", "users"]
        
        for table_name in cleanup_order:
            if table_name in seeded_data:
                for record in seeded_data[table_name]:
                    await DatabaseTestUtils._delete_record(db_session, table_name, record)
    
    @staticmethod
    async def _delete_record(db_session, table_name: str, record: Dict[str, Any]):
        """Delete a single record from database."""
        # Determine primary key field
        pk_fields = {
            "users": "user_id",
            "batches": "batch_id", 
            "inspections": "inspection_id",
            "alerts": "alert_id"
        }
        
        pk_field = pk_fields.get(table_name, "id")
        pk_value = record.get(pk_field)
        
        if pk_value:
            sql = f"DELETE FROM {table_name} WHERE {pk_field} = :{pk_field}"
            await db_session.execute(sql, {pk_field: pk_value})
    
    @staticmethod
    async def verify_data_integrity(db_session, seeded_data: Dict[str, Any]) -> bool:
        """Verify data integrity after operations."""
        integrity_checks = []
        
        # Check foreign key relationships
        for inspection in seeded_data.get("inspections", []):
            batch_exists = any(
                batch["batch_id"] == inspection["batch_id"]
                for batch in seeded_data.get("batches", [])
            )
            integrity_checks.append(batch_exists)
        
        # Check data consistency
        for batch in seeded_data.get("batches", []):
            batch_inspections = [
                insp for insp in seeded_data.get("inspections", [])
                if insp["batch_id"] == batch["batch_id"]
            ]
            
            if batch_inspections:
                # Verify quality metrics consistency
                pass_count = sum(1 for insp in batch_inspections if insp["pass_fail_status"] == "PASS")
                calculated_yield = pass_count / len(batch_inspections) if batch_inspections else 0
                
                # Allow for some variance in calculated vs stored yield
                yield_diff = abs(calculated_yield - batch.get("current_yield", 0))
                integrity_checks.append(yield_diff < 0.1)  # Within 10%
        
        return all(integrity_checks)


# ================================================================================================
# 🌐 API TEST UTILITIES
# ================================================================================================

class APITestUtils:
    """Utilities for API testing operations."""
    
    @staticmethod
    async def make_authenticated_request(
        client: httpx.AsyncClient,
        method: str,
        url: str,
        user_role: str = "operator",
        **kwargs
    ) -> httpx.Response:
        """Make authenticated API request with specified user role."""
        
        # Generate mock JWT token for role
        token = APITestUtils.generate_mock_jwt_token(user_role)
        
        # Add authentication header
        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"Bearer {token}"
        kwargs["headers"] = headers
        
        # Make request
        response = await getattr(client, method.lower())(url, **kwargs)
        return response
    
    @staticmethod
    def generate_mock_jwt_token(user_role: str) -> str:
        """Generate mock JWT token for testing."""
        # In real implementation, would use actual JWT library
        # For testing, return a predictable mock token
        return f"mock_jwt_token_for_{user_role}_{int(time.time())}"
    
    @staticmethod
    async def upload_test_image(
        client: httpx.AsyncClient,
        endpoint: str,
        image: Image.Image,
        filename: str = "test_chip.jpg",
        additional_data: Optional[Dict[str, Any]] = None
    ) -> httpx.Response:
        """Upload test image via API."""
        
        # Save image to temporary buffer
        import io
        image_buffer = io.BytesIO()
        image.save(image_buffer, format="JPEG")
        image_buffer.seek(0)
        
        # Prepare multipart form data
        files = {"image": (filename, image_buffer, "image/jpeg")}
        data = additional_data or {}
        
        response = await client.post(endpoint, files=files, data=data)
        return response
    
    @staticmethod
    async def wait_for_async_operation(
        client: httpx.AsyncClient,
        status_url: str,
        timeout_seconds: int = 30,
        check_interval: float = 1.0
    ) -> Dict[str, Any]:
        """Wait for asynchronous operation to complete."""
        
        start_time = time.time()
        
        while time.time() - start_time < timeout_seconds:
            response = await client.get(status_url)
            
            if response.status_code == 200:
                status_data = response.json()
                
                if status_data.get("status") in ["COMPLETED", "FAILED", "ERROR"]:
                    return status_data
            
            await asyncio.sleep(check_interval)
        
        raise TimeoutError(f"Operation did not complete within {timeout_seconds} seconds")
    
    @staticmethod
    def assert_api_response_structure(
        response: httpx.Response,
        expected_fields: List[str],
        status_code: int = 200
    ):
        """Assert API response has expected structure."""
        assert response.status_code == status_code, f"Expected {status_code}, got {response.status_code}"
        
        response_data = response.json()
        
        for field in expected_fields:
            if "." in field:  # Nested field like "data.batch_id"
                parts = field.split(".")
                current = response_data
                
                for part in parts:
                    assert part in current, f"Missing field: {field}"
                    current = current[part]
            else:
                assert field in response_data, f"Missing field: {field}"
    
    @staticmethod
    async def simulate_concurrent_requests(
        client: httpx.AsyncClient,
        requests: List[Dict[str, Any]],
        max_concurrent: int = 10
    ) -> List[httpx.Response]:
        """Simulate concurrent API requests."""
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def make_request(request_config: Dict[str, Any]) -> httpx.Response:
            async with semaphore:
                method = request_config["method"]
                url = request_config["url"]
                kwargs = request_config.get("kwargs", {})
                
                return await getattr(client, method.lower())(url, **kwargs)
        
        tasks = [make_request(req) for req in requests]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return successful responses
        return [resp for resp in responses if isinstance(resp, httpx.Response)]


# ================================================================================================
# 📊 PERFORMANCE TEST UTILITIES
# ================================================================================================

class PerformanceTestUtils:
    """Utilities for performance testing and monitoring."""
    
    @staticmethod
    @asynccontextmanager
    async def monitor_performance(operation_name: str = "test_operation"):
        """Context manager to monitor performance of operations."""
        
        import psutil
        
        # Record start metrics
        start_time = time.perf_counter()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        start_cpu = psutil.cpu_percent(interval=None)
        
        metrics = {
            "operation_name": operation_name,
            "start_time": start_time,
            "start_memory_mb": start_memory
        }
        
        try:
            yield metrics
        finally:
            # Record end metrics
            end_time = time.perf_counter()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            end_cpu = psutil.cpu_percent(interval=None)
            
            metrics.update({
                "end_time": end_time,
                "duration_seconds": end_time - start_time,
                "end_memory_mb": end_memory,
                "memory_delta_mb": end_memory - start_memory,
                "peak_cpu_percent": max(start_cpu, end_cpu)
            })
    
    @staticmethod
    async def benchmark_function(
        func: Callable,
        iterations: int = 100,
        warmup_iterations: int = 10,
        *args,
        **kwargs
    ) -> Dict[str, float]:
        """Benchmark function performance."""
        
        # Warmup runs
        for _ in range(warmup_iterations):
            if asyncio.iscoroutinefunction(func):
                await func(*args, **kwargs)
            else:
                func(*args, **kwargs)
        
        # Benchmark runs
        execution_times = []
        
        for _ in range(iterations):
            start_time = time.perf_counter()
            
            if asyncio.iscoroutinefunction(func):
                await func(*args, **kwargs)
            else:
                func(*args, **kwargs)
            
            end_time = time.perf_counter()
            execution_times.append(end_time - start_time)
        
        # Calculate statistics
        import statistics
        
        return {
            "mean_seconds": statistics.mean(execution_times),
            "median_seconds": statistics.median(execution_times),
            "min_seconds": min(execution_times),
            "max_seconds": max(execution_times),
            "std_dev_seconds": statistics.stdev(execution_times) if len(execution_times) > 1 else 0,
            "iterations": iterations,
            "total_time_seconds": sum(execution_times)
        }
    
    @staticmethod
    def assert_performance_sla(
        metrics: Dict[str, float],
        max_duration_seconds: Optional[float] = None,
        max_memory_mb: Optional[float] = None,
        max_cpu_percent: Optional[float] = None
    ):
        """Assert performance metrics meet SLA requirements."""
        
        if max_duration_seconds is not None:
            duration = metrics.get("duration_seconds", 0)
            assert duration <= max_duration_seconds, \
                f"Operation took {duration:.3f}s, expected <= {max_duration_seconds}s"
        
        if max_memory_mb is not None:
            memory_delta = metrics.get("memory_delta_mb", 0)
            assert memory_delta <= max_memory_mb, \
                f"Memory usage increased by {memory_delta:.2f}MB, expected <= {max_memory_mb}MB"
        
        if max_cpu_percent is not None:
            cpu_usage = metrics.get("peak_cpu_percent", 0)
            assert cpu_usage <= max_cpu_percent, \
                f"CPU usage peaked at {cpu_usage:.1f}%, expected <= {max_cpu_percent}%"


# ================================================================================================
# 🖼️ IMAGE TEST UTILITIES
# ================================================================================================

class ImageTestUtils:
    """Utilities for image-related testing."""
    
    @staticmethod
    def create_test_image_batch(
        count: int = 10,
        size: tuple = (512, 512),
        defect_probability: float = 0.2
    ) -> List[Image.Image]:
        """Create batch of test images with varying quality."""
        
        from tests.fixtures.manufacturing_factories import ChipImageFactory
        
        images = []
        
        for i in range(count):
            # Randomly add defects based on probability
            defect_type = None
            if np.random.random() < defect_probability:
                defect_type = np.random.choice([
                    "scratch", "crack", "contamination", "discoloration"
                ])
            
            image = ChipImageFactory.create_chip_image(
                size=size,
                defect_type=defect_type,
                noise_level=np.random.uniform(0.05, 0.2)
            )
            
            images.append(image)
        
        return images
    
    @staticmethod
    def save_images_to_temp_dir(images: List[Image.Image]) -> Path:
        """Save images to temporary directory and return path."""
        
        temp_dir = Path(tempfile.mkdtemp())
        
        for i, image in enumerate(images):
            image_path = temp_dir / f"test_chip_{i:04d}.jpg"
            image.save(image_path, "JPEG", quality=95)
        
        return temp_dir
    
    @staticmethod
    def compare_images(image1: Image.Image, image2: Image.Image, threshold: float = 0.95) -> bool:
        """Compare two images for similarity."""
        
        # Convert to arrays
        arr1 = np.array(image1)
        arr2 = np.array(image2)
        
        # Ensure same shape
        if arr1.shape != arr2.shape:
            return False
        
        # Calculate similarity (normalized cross-correlation)
        correlation = np.corrcoef(arr1.flatten(), arr2.flatten())[0, 1]
        
        return correlation >= threshold
    
    @staticmethod
    def extract_image_features(image: Image.Image) -> Dict[str, float]:
        """Extract basic features from image for testing."""
        
        arr = np.array(image)
        
        return {
            "mean_brightness": np.mean(arr),
            "std_brightness": np.std(arr),
            "contrast": np.max(arr) - np.min(arr),
            "aspect_ratio": image.width / image.height,
            "total_pixels": image.width * image.height
        }


# ================================================================================================
# 🧹 TEST CLEANUP UTILITIES
# ================================================================================================

class TestCleanupUtils:
    """Utilities for test cleanup and resource management."""
    
    @staticmethod
    @contextmanager
    def temp_file_cleanup(*temp_paths: Union[str, Path]):
        """Context manager for automatic temporary file cleanup."""
        paths = [Path(p) for p in temp_paths]
        
        try:
            yield paths
        finally:
            for path in paths:
                if path.exists():
                    if path.is_file():
                        path.unlink()
                    elif path.is_dir():
                        shutil.rmtree(path)
    
    @staticmethod
    @asynccontextmanager
    async def mock_external_services():
        """Context manager for mocking external services."""
        
        mocks = {}
        
        # Mock Triton Inference Server
        mock_triton = AsyncMock()
        mock_triton.is_server_ready.return_value = True
        mock_triton.is_model_ready.return_value = True
        mocks["triton"] = mock_triton
        
        # Mock Kafka
        mock_kafka_producer = AsyncMock()
        mock_kafka_consumer = AsyncMock()
        mocks["kafka_producer"] = mock_kafka_producer
        mocks["kafka_consumer"] = mock_kafka_consumer
        
        # Mock MinIO
        mock_minio = AsyncMock()
        mocks["minio"] = mock_minio
        
        try:
            yield mocks
        finally:
            # Cleanup mocks if needed
            pass
    
    @staticmethod
    async def reset_test_environment():
        """Reset test environment to clean state."""
        
        # Clear any cached data
        cache_dirs = [
            Path("./test_cache"),
            Path("./temp_test_data"),
            Path("./test_uploads")
        ]
        
        for cache_dir in cache_dirs:
            if cache_dir.exists():
                shutil.rmtree(cache_dir)
        
        # Reset environment variables to test defaults
        test_env_vars = {
            "ENVIRONMENT": "test",
            "LOG_LEVEL": "DEBUG",
            "DATABASE_URL": "postgresql://test:test@localhost:5432/test_db",
            "REDIS_URL": "redis://localhost:6379/1"
        }
        
        for key, value in test_env_vars.items():
            os.environ[key] = value


# ================================================================================================
# 📊 TEST ASSERTION UTILITIES
# ================================================================================================

class AssertionUtils:
    """Custom assertion utilities for domain-specific testing."""
    
    @staticmethod
    def assert_quality_metrics_valid(metrics: Dict[str, float]):
        """Assert quality metrics are within valid ranges."""
        
        # Check that all metrics are between 0 and 1
        for metric_name, value in metrics.items():
            assert 0.0 <= value <= 1.0, f"Metric {metric_name} = {value} is out of range [0, 1]"
        
        # Check specific metric relationships
        if "defect_probability" in metrics and "overall_quality_score" in metrics:
            # High defect probability should correlate with low quality score
            defect_prob = metrics["defect_probability"]
            quality_score = metrics["overall_quality_score"]
            
            if defect_prob > 0.5:
                assert quality_score < 0.7, \
                    f"High defect probability ({defect_prob:.2f}) should result in low quality score"
    
    @staticmethod
    def assert_batch_consistency(batch_data: Dict[str, Any], inspections: List[Dict[str, Any]]):
        """Assert batch data is consistent with its inspections."""
        
        batch_id = batch_data["batch_id"]
        
        # All inspections should belong to this batch
        for inspection in inspections:
            assert inspection["batch_id"] == batch_id, \
                f"Inspection {inspection['inspection_id']} has wrong batch_id"
        
        # Calculate and verify yield
        if inspections:
            pass_count = sum(1 for insp in inspections if insp["pass_fail_status"] == "PASS")
            calculated_yield = pass_count / len(inspections)
            stored_yield = batch_data.get("current_yield", 0)
            
            yield_diff = abs(calculated_yield - stored_yield)
            assert yield_diff < 0.1, \
                f"Yield mismatch: calculated {calculated_yield:.2f}, stored {stored_yield:.2f}"
    
    @staticmethod
    def assert_audit_trail_complete(audit_events: List[Dict[str, Any]]):
        """Assert audit trail has all required elements."""
        
        required_fields = ["event_id", "timestamp", "user_id", "action"]
        
        for event in audit_events:
            for field in required_fields:
                assert field in event, f"Audit event missing required field: {field}"
            
            # Check timestamp format
            timestamp = event["timestamp"]
            try:
                datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError:
                assert False, f"Invalid timestamp format: {timestamp}"
        
        # Events should be in chronological order
        timestamps = [
            datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
            for event in audit_events
        ]
        
        assert timestamps == sorted(timestamps), "Audit events not in chronological order"
    
    @staticmethod
    def assert_compliance_requirements(data: Dict[str, Any], requirements: List[str]):
        """Assert data meets compliance requirements."""
        
        compliance_checks = {
            "fda_21_cfr_part_11": lambda d: all([
                "electronic_signature" in d,
                "audit_trail" in d,
                "data_integrity_hash" in d
            ]),
            "iso_9001": lambda d: all([
                "quality_metrics" in d,
                "operator_id" in d,
                "timestamp" in d
            ]),
            "traceability": lambda d: all([
                "batch_id" in d,
                "operator_id" in d,
                "station_id" in d
            ])
        }
        
        for requirement in requirements:
            if requirement in compliance_checks:
                check_func = compliance_checks[requirement]
                assert check_func(data), f"Data does not meet {requirement} requirements"


# ================================================================================================
# 🎯 TEST SCENARIO UTILITIES
# ================================================================================================

class ScenarioUtils:
    """Utilities for managing complex test scenarios."""
    
    @staticmethod
    async def run_production_simulation(
        duration_minutes: int = 60,
        batches_per_hour: int = 5,
        operators_count: int = 3
    ) -> Dict[str, Any]:
        """Run complete production simulation for testing."""
        
        from tests.fixtures.manufacturing_factories import (
            BatchFactory, InspectionFactory, UserFactory
        )
        
        # Create operators
        operators = [UserFactory(roles=["operator"]) for _ in range(operators_count)]
        
        # Simulation state
        simulation_data = {
            "start_time": datetime.utcnow(),
            "duration_minutes": duration_minutes,
            "operators": operators,
            "batches_created": [],
            "inspections_completed": [],
            "quality_alerts": [],
            "events_timeline": []
        }
        
        # Run simulation
        for minute in range(duration_minutes):
            current_time = simulation_data["start_time"] + timedelta(minutes=minute)
            
            # Create new batches periodically
            if minute % (60 // batches_per_hour) == 0:
                batch = BatchFactory()
                simulation_data["batches_created"].append(batch)
                
                simulation_data["events_timeline"].append({
                    "timestamp": current_time.isoformat(),
                    "event_type": "batch_created",
                    "data": {"batch_id": batch["batch_id"]}
                })
            
            # Process inspections
            for batch in simulation_data["batches_created"]:
                if np.random.random() < 0.3:  # 30% chance per minute
                    inspection = InspectionFactory(
                        batch_id=batch["batch_id"],
                        operator_id=np.random.choice(operators)["user_id"],
                        timestamp=current_time.isoformat()
                    )
                    simulation_data["inspections_completed"].append(inspection)
                    
                    simulation_data["events_timeline"].append({
                        "timestamp": current_time.isoformat(),
                        "event_type": "inspection_completed",
                        "data": {
                            "inspection_id": inspection["inspection_id"],
                            "result": inspection["pass_fail_status"]
                        }
                    })
            
            # Simulate processing delay
            await asyncio.sleep(0.01)  # 10ms per simulated minute
        
        # Calculate summary statistics
        total_inspections = len(simulation_data["inspections_completed"])
        pass_count = sum(
            1 for insp in simulation_data["inspections_completed"]
            if insp["pass_fail_status"] == "PASS"
        )
        
        simulation_data["summary"] = {
            "total_batches": len(simulation_data["batches_created"]),
            "total_inspections": total_inspections,
            "overall_yield": pass_count / total_inspections if total_inspections > 0 else 0,
            "throughput_per_hour": (total_inspections / duration_minutes) * 60,
            "operator_utilization": total_inspections / (operators_count * duration_minutes)
        }
        
        return simulation_data


# ================================================================================================
# 🛠️ UTILITIES SUMMARY
# ================================================================================================
"""
🛠️ TEST UTILITIES SUMMARY
=========================

📋 Available Utility Classes:
   ✅ DatabaseTestUtils - Database seeding, cleanup, integrity checks
   ✅ APITestUtils - Authentication, request helpers, concurrent testing
   ✅ PerformanceTestUtils - Performance monitoring, benchmarking, SLA validation
   ✅ ImageTestUtils - Image creation, comparison, feature extraction
   ✅ TestCleanupUtils - Resource cleanup, mocking, environment reset
   ✅ AssertionUtils - Domain-specific assertions for quality, compliance
   ✅ ScenarioUtils - Complex test scenario orchestration

🚀 Key Features:
   • Realistic test data seeding with configurable scenarios
   • Comprehensive API testing with authentication simulation
   • Performance monitoring with SLA validation
   • Image processing utilities for ML testing
   • Automated cleanup and resource management
   • Domain-specific assertions for manufacturing quality
   • Production simulation capabilities

🎯 Usage Examples:
   # Database seeding
   data = await DatabaseTestUtils.seed_test_data(db, "production_load")
   
   # API testing
   response = await APITestUtils.make_authenticated_request(
       client, "POST", "/api/v1/inspections", user_role="operator"
   )
   
   # Performance monitoring
   async with PerformanceTestUtils.monitor_performance("api_test") as metrics:
       await some_operation()
   PerformanceTestUtils.assert_performance_sla(metrics, max_duration_seconds=2.0)
   
   # Production simulation
   results = await ScenarioUtils.run_production_simulation(
       duration_minutes=30, batches_per_hour=10
   )

📊 Benefits:
   • Reduces test setup complexity
   • Ensures consistent test data quality
   • Provides realistic testing scenarios
   • Automates performance validation
   • Simplifies cleanup and maintenance
   • Enables comprehensive integration testing
"""