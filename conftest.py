# ================================================================================================
# 🧪 COMPREHENSIVE TESTING FRAMEWORK CONFIGURATION
# ================================================================================================
# Production-grade testing setup for semiconductor quality platform
# Supports: Unit, Integration, E2E, Performance, Security, Compliance testing
# Features: Parallel execution, coverage reporting, test data factories, containerized testing
# ================================================================================================

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "services"))

# ================================================================================================
# 📁 PYTEST CONFIGURATION
# ================================================================================================

def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    
    # Register custom markers
    config.addinivalue_line(
        "markers",
        "unit: Unit tests - isolated, fast, no external dependencies"
    )
    config.addinivalue_line(
        "markers", 
        "integration: Integration tests - multiple components, database required"
    )
    config.addinivalue_line(
        "markers",
        "e2e: End-to-end tests - full system, all services running"
    )
    config.addinivalue_line(
        "markers",
        "slow: Slow tests - may take >30 seconds"
    )
    config.addinivalue_line(
        "markers",
        "external: Tests requiring external services (Redis, Kafka, etc.)"
    )
    config.addinivalue_line(
        "markers",
        "performance: Performance and load tests"
    )
    config.addinivalue_line(
        "markers",
        "security: Security vulnerability tests"
    )
    config.addinivalue_line(
        "markers",
        "compliance: Regulatory compliance tests (FDA 21 CFR Part 11)"
    )
    config.addinivalue_line(
        "markers",
        "gpu: Tests requiring GPU/CUDA"
    )
    config.addinivalue_line(
        "markers",
        "ml: Machine learning model tests"
    )
    config.addinivalue_line(
        "markers",
        "database: Tests requiring database connection"
    )
    config.addinivalue_line(
        "markers",
        "kafka: Tests requiring Kafka message broker"
    )
    config.addinivalue_line(
        "markers",
        "triton: Tests requiring NVIDIA Triton Inference Server"
    )
    config.addinivalue_line(
        "markers",
        "auth: Authentication and authorization tests"
    )
    config.addinivalue_line(
        "markers",
        "api: API endpoint tests"
    )

# ================================================================================================
# 🏗️ TEST FIXTURES AND SETUP
# ================================================================================================

import pytest
import asyncio
import tempfile
import shutil
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

# Test environment configuration
os.environ.update({
    "ENVIRONMENT": "test",
    "LOG_LEVEL": "DEBUG",
    "DATABASE_URL": "postgresql://test:test@localhost:5432/test_db",
    "REDIS_URL": "redis://localhost:6379/1",
    "KAFKA_BOOTSTRAP_SERVERS": "localhost:9092",
    "TRITON_SERVER_URL": "grpc://localhost:8001",
    "MINIO_ENDPOINT": "localhost:9000",
    "MINIO_ACCESS_KEY": "testkey",
    "MINIO_SECRET_KEY": "testsecret",
    "JWT_SECRET_KEY": "test-secret-key-for-testing-only",
    "ENCRYPTION_KEY": "test-encryption-key-32-bytes-long",
})

# ================================================================================================
# 🗄️ DATABASE FIXTURES
# ================================================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_database():
    """Create test database for the session."""
    from testcontainers.postgres import PostgresContainer
    
    with PostgresContainer("postgres:15") as postgres:
        # Set database URL for tests
        db_url = postgres.get_connection_url()
        os.environ["DATABASE_URL"] = db_url
        
        # Initialize database schema
        from services.api_gateway.app.database import create_tables
        await create_tables()
        
        yield db_url

@pytest.fixture
async def db_session(test_database):
    """Create database session for individual tests."""
    from services.api_gateway.app.database import get_database
    
    async with get_database() as session:
        # Start transaction
        await session.begin()
        yield session
        # Rollback transaction after test
        await session.rollback()

# ================================================================================================
# 🔴 REDIS FIXTURES
# ================================================================================================

@pytest.fixture(scope="session")
async def test_redis():
    """Create test Redis instance for the session."""
    from testcontainers.redis import RedisContainer
    
    with RedisContainer("redis:7") as redis:
        redis_url = f"redis://{redis.get_container_host_ip()}:{redis.get_exposed_port(6379)}/0"
        os.environ["REDIS_URL"] = redis_url
        yield redis_url

@pytest.fixture
async def redis_client(test_redis):
    """Create Redis client for individual tests."""
    import aioredis
    
    client = aioredis.from_url(test_redis, decode_responses=True)
    yield client
    await client.flushdb()  # Clean up after test
    await client.close()

# ================================================================================================
# 📨 KAFKA FIXTURES
# ================================================================================================

@pytest.fixture(scope="session")
async def test_kafka():
    """Create test Kafka instance for the session."""
    from testcontainers.kafka import KafkaContainer
    
    with KafkaContainer() as kafka:
        bootstrap_servers = kafka.get_bootstrap_server()
        os.environ["KAFKA_BOOTSTRAP_SERVERS"] = bootstrap_servers
        yield bootstrap_servers

@pytest.fixture
async def kafka_producer(test_kafka):
    """Create Kafka producer for individual tests."""
    from aiokafka import AIOKafkaProducer
    
    producer = AIOKafkaProducer(bootstrap_servers=test_kafka)
    await producer.start()
    yield producer
    await producer.stop()

@pytest.fixture
async def kafka_consumer(test_kafka):
    """Create Kafka consumer for individual tests."""
    from aiokafka import AIOKafkaConsumer
    
    consumer = AIOKafkaConsumer(bootstrap_servers=test_kafka)
    await consumer.start()
    yield consumer
    await consumer.stop()

# ================================================================================================
# 🤖 ML/AI FIXTURES
# ================================================================================================

@pytest.fixture
def mock_triton_client():
    """Mock NVIDIA Triton client for testing."""
    mock_client = MagicMock()
    mock_client.is_server_ready.return_value = True
    mock_client.is_model_ready.return_value = True
    
    # Mock inference response
    mock_result = MagicMock()
    mock_result.as_numpy.return_value = [[0.95, 0.03, 0.02]]  # Mock quality scores
    mock_client.infer.return_value = mock_result
    
    return mock_client

@pytest.fixture
def sample_chip_image():
    """Generate sample chip image for testing."""
    from PIL import Image
    import numpy as np
    
    # Create a 512x512 RGB image with chip-like pattern
    img_array = np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8)
    # Add some chip-like features
    img_array[100:150, 100:150] = [200, 200, 200]  # Bright square (component)
    img_array[200:250, 200:250] = [50, 50, 50]     # Dark square (defect)
    
    return Image.fromarray(img_array)

# ================================================================================================
# 🔐 AUTHENTICATION FIXTURES
# ================================================================================================

@pytest.fixture
def mock_auth_service():
    """Mock authentication service for testing."""
    mock_auth = AsyncMock()
    
    # Mock user data
    mock_user = {
        "id": "test-user-123",
        "username": "testuser",
        "email": "test@example.com",
        "roles": ["operator", "quality_inspector"],
        "permissions": ["read:inspections", "write:inspections"],
        "is_active": True,
        "last_login": "2024-01-01T00:00:00Z"
    }
    
    mock_auth.authenticate_user.return_value = mock_user
    mock_auth.authorize_user.return_value = True
    mock_auth.create_access_token.return_value = "mock-jwt-token"
    
    return mock_auth

@pytest.fixture
def authenticated_headers():
    """Generate headers for authenticated requests."""
    return {
        "Authorization": "Bearer mock-jwt-token",
        "Content-Type": "application/json"
    }

# ================================================================================================
# 🌐 API CLIENT FIXTURES
# ================================================================================================

@pytest.fixture
async def api_client():
    """Create HTTP client for API testing."""
    import httpx
    from services.api_gateway.app.main import app
    
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
async def authenticated_client(api_client, authenticated_headers):
    """Create authenticated HTTP client for API testing."""
    api_client.headers.update(authenticated_headers)
    yield api_client

# ================================================================================================
# 📁 FILE SYSTEM FIXTURES
# ================================================================================================

@pytest.fixture
def temp_directory():
    """Create temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def test_image_path(temp_directory, sample_chip_image):
    """Create test image file path."""
    image_path = temp_directory / "test_chip.jpg"
    sample_chip_image.save(image_path, "JPEG")
    return image_path

# ================================================================================================
# 🏭 MANUFACTURING DATA FIXTURES
# ================================================================================================

@pytest.fixture
def sample_inspection_data():
    """Generate sample inspection data for testing."""
    return {
        "batch_id": "BATCH_2024_001",
        "chip_id": "CHIP_001234",
        "inspection_type": "visual_defect_detection",
        "timestamp": "2024-01-01T12:00:00Z",
        "operator_id": "OP_001",
        "station_id": "STATION_A01",
        "quality_metrics": {
            "defect_probability": 0.02,
            "surface_roughness": 0.15,
            "dimensional_accuracy": 0.98,
            "color_consistency": 0.95
        },
        "defects_detected": [
            {
                "type": "scratch",
                "severity": "minor",
                "location": {"x": 125, "y": 200},
                "confidence": 0.89
            }
        ],
        "pass_fail_status": "PASS",
        "compliance_flags": {
            "fda_21_cfr_part_11": True,
            "iso_9001": True,
            "traceability_complete": True
        }
    }

@pytest.fixture
def sample_batch_data():
    """Generate sample batch data for testing."""
    return {
        "batch_id": "BATCH_2024_001",
        "product_line": "ADVANCED_PROCESSOR",
        "wafer_lot": "WAFER_LOT_A123",
        "production_date": "2024-01-01",
        "target_quantity": 1000,
        "current_quantity": 856,
        "quality_target": 0.98,
        "current_yield": 0.962,
        "status": "IN_PROGRESS",
        "priority": "HIGH",
        "specification": {
            "chip_size": {"width": 10.5, "height": 8.2, "thickness": 0.5},
            "tolerance": {"dimensional": 0.01, "electrical": 0.05},
            "quality_thresholds": {
                "defect_rate_max": 0.02,
                "surface_quality_min": 0.95
            }
        }
    }

# ================================================================================================
# 🔧 PERFORMANCE TESTING FIXTURES
# ================================================================================================

@pytest.fixture
def performance_test_config():
    """Configuration for performance tests."""
    return {
        "concurrent_users": 50,
        "test_duration": "30s",
        "ramp_up_time": "10s",
        "max_response_time": 2.0,  # seconds
        "min_throughput": 100,     # requests per second
        "memory_limit": "512MB",
        "cpu_limit": "80%"
    }

# ================================================================================================
# 📊 MONITORING AND OBSERVABILITY FIXTURES
# ================================================================================================

@pytest.fixture
def mock_metrics_collector():
    """Mock metrics collector for testing observability."""
    from unittest.mock import MagicMock
    
    collector = MagicMock()
    collector.increment_counter = MagicMock()
    collector.record_histogram = MagicMock()
    collector.set_gauge = MagicMock()
    collector.record_timer = MagicMock()
    
    return collector

@pytest.fixture
def mock_tracer():
    """Mock OpenTelemetry tracer for testing."""
    from unittest.mock import MagicMock
    
    tracer = MagicMock()
    span = MagicMock()
    tracer.start_span.return_value.__enter__ = MagicMock(return_value=span)
    tracer.start_span.return_value.__exit__ = MagicMock(return_value=None)
    
    return tracer

# ================================================================================================
# 🧹 CLEANUP UTILITIES
# ================================================================================================

@pytest.fixture(autouse=True)
async def cleanup_test_data():
    """Automatically clean up test data after each test."""
    yield
    
    # Clean up any test files, temporary data, etc.
    # This runs after each test automatically
    
    # Clear any cached data
    if hasattr(cleanup_test_data, "_test_cache"):
        delattr(cleanup_test_data, "_test_cache")

# ================================================================================================
# 🎯 TEST COLLECTION HOOKS
# ================================================================================================

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test paths."""
    
    for item in items:
        # Add markers based on test file path
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        elif "security" in str(item.fspath):
            item.add_marker(pytest.mark.security)
        
        # Add slow marker for tests that might be slow
        if any(keyword in item.name.lower() for keyword in ["slow", "load", "stress", "benchmark"]):
            item.add_marker(pytest.mark.slow)
        
        # Add external marker for tests requiring external services
        if any(keyword in str(item.fspath) for keyword in ["kafka", "redis", "triton", "external"]):
            item.add_marker(pytest.mark.external)

# ================================================================================================
# 📝 TEST REPORTING HOOKS
# ================================================================================================

def pytest_runtest_setup(item):
    """Setup hook for individual test items."""
    # Log test start
    print(f"\n🧪 Starting test: {item.name}")

def pytest_runtest_teardown(item, nextitem):
    """Teardown hook for individual test items."""
    # Log test completion
    print(f"✅ Completed test: {item.name}")

# ================================================================================================
# 🚀 PYTEST PLUGINS
# ================================================================================================

# Enable pytest plugins
pytest_plugins = [
    "pytest_asyncio",
    "pytest_mock",
    "pytest_cov",
    "pytest_xdist",
    "pytest_benchmark",
    "pytest_timeout",
    "pytest_html",
]

# ================================================================================================
# 📋 TEST EXECUTION SUMMARY
# ================================================================================================
"""
🧪 TESTING FRAMEWORK SUMMARY
=============================

📁 Test Organization:
   • tests/unit/          - Fast, isolated unit tests
   • tests/integration/   - Multi-component integration tests  
   • tests/e2e/          - Full system end-to-end tests
   • tests/performance/  - Load and performance tests
   • tests/security/     - Security vulnerability tests
   • tests/compliance/   - Regulatory compliance tests

🎯 Test Markers:
   • @pytest.mark.unit           - Unit tests
   • @pytest.mark.integration    - Integration tests
   • @pytest.mark.e2e           - End-to-end tests
   • @pytest.mark.slow          - Slow tests (>30s)
   • @pytest.mark.external      - Requires external services
   • @pytest.mark.performance   - Performance tests
   • @pytest.mark.security      - Security tests
   • @pytest.mark.compliance    - Compliance tests
   • @pytest.mark.gpu           - Requires GPU
   • @pytest.mark.ml            - ML model tests

🚀 Run Commands:
   • pytest                     - Run all tests
   • pytest -m unit            - Run only unit tests
   • pytest -m "not slow"      - Skip slow tests
   • pytest --cov=services     - Run with coverage
   • pytest -n auto            - Parallel execution
   • pytest --benchmark-only   - Run only benchmarks

📊 Coverage & Reporting:
   • HTML coverage: htmlcov/index.html
   • XML coverage: coverage.xml
   • JSON report: pytest-report.json
   • HTML report: pytest-report.html

🔧 Features:
   • Containerized test services (PostgreSQL, Redis, Kafka)
   • Automatic test data cleanup
   • Mocked external dependencies
   • Performance benchmarking
   • Security vulnerability testing
   • Compliance verification
   • Parallel test execution
   • Comprehensive reporting
"""