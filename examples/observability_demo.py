#!/usr/bin/env python3
"""
Simple example demonstrating the observability infrastructure.

This script shows how to use:
- Distributed tracing
- Metrics collection
- Structured logging
- Health checking

Run with: python examples/observability_demo.py
"""

import asyncio
from datetime import datetime

# Observability imports
from services.shared.observability.tracing import (
    setup_tracing,
    get_tracer,
    trace_function,
    add_span_attributes,
)
from services.shared.observability.metrics import (
    QualityMetrics,
    ProductionMetrics,
    MLPerformanceMetrics,
)
from services.shared.observability.logging import (
    setup_structured_logging,
    get_logger,
    bind_contextvars,
    set_correlation_id,
    set_request_id,
)
from services.shared.observability.health import (
    HealthChecker,
    ServiceHealthCheck,
    HealthStatus,
    HealthCheckResult,
)


async def main():
    """Main demonstration function."""
    
    print("=" * 60)
    print("Observability Infrastructure Demo")
    print("=" * 60)
    
    # 1. Setup Structured Logging
    print("\n1. Setting up structured logging...")
    setup_structured_logging(
        log_level="INFO",
        service_name="demo-service",
        json_logs=False  # Console output for demo
    )
    logger = get_logger(__name__)
    
    # Set correlation IDs
    corr_id = set_correlation_id()
    req_id = set_request_id()
    
    logger.info(
        "Observability demo started",
        correlation_id=corr_id,
        request_id=req_id
    )
    
    # 2. Setup Distributed Tracing
    print("\n2. Setting up distributed tracing...")
    tracer = setup_tracing(
        service_name="demo-service",
        service_version="1.0.0",
        otlp_endpoint=None  # No export for demo
    )
    logger.info("Tracing configured", tracer_name=tracer.__class__.__name__)
    
    # 3. Initialize Metrics
    print("\n3. Initializing metrics collectors...")
    quality_metrics = QualityMetrics()
    production_metrics = ProductionMetrics()
    ml_metrics = MLPerformanceMetrics()
    logger.info("Metrics collectors initialized")
    
    # 4. Demonstrate Tracing
    print("\n4. Demonstrating distributed tracing...")
    
    @trace_function(span_name="simulate_inspection")
    async def simulate_inspection(inspection_id: str):
        """Simulate an inspection with tracing."""
        logger.info("Starting inspection", inspection_id=inspection_id)
        
        add_span_attributes({
            "inspection.id": inspection_id,
            "inspection.type": "visual",
        })
        
        # Simulate processing
        await asyncio.sleep(0.1)
        
        logger.info("Inspection completed", inspection_id=inspection_id)
        return {"status": "passed", "quality_score": 0.95}
    
    result = await simulate_inspection("INSP-001")
    print(f"   Inspection result: {result}")
    
    # 5. Demonstrate Metrics
    print("\n5. Recording business metrics...")
    
    # Quality metrics
    quality_metrics.record_inspection_result(
        product_type="PCB-A",
        inspection_type="visual",
        passed=True,
        quality_score=0.95,
        duration_seconds=0.1
    )
    
    quality_metrics.record_defect(
        product_type="PCB-A",
        defect_type="scratch",
        severity="low"
    )
    
    # Production metrics
    production_metrics.record_batch_completion(
        product_type="PCB-A",
        batch_size=25,
        duration_seconds=120.0,
        status="completed"
    )
    
    # ML metrics
    ml_metrics.record_inference(
        model_name="defect_detector",
        model_version="v2.1",
        latency_seconds=0.125,
        confidence=0.95,
        success=True
    )
    
    logger.info("Business metrics recorded")
    print("   ✓ Quality metrics recorded")
    print("   ✓ Production metrics recorded")
    print("   ✓ ML metrics recorded")
    
    # 6. Demonstrate Health Checking
    print("\n6. Demonstrating health checks...")
    
    health_checker = HealthChecker()
    
    # Mock health check
    async def mock_database_check():
        await asyncio.sleep(0.05)
        return HealthCheckResult(
            status=HealthStatus.HEALTHY,
            component="database",
            message="Database is healthy",
            details={"connections": 5, "pool_size": 10}
        )
    
    async def mock_cache_check():
        await asyncio.sleep(0.03)
        return HealthCheckResult(
            status=HealthStatus.HEALTHY,
            component="cache",
            message="Cache is healthy",
            details={"hit_rate": 0.85}
        )
    
    health_checker.register_check(ServiceHealthCheck(
        name="database",
        check_fn=mock_database_check,
        timeout_seconds=5.0,
        critical=True
    ))
    
    health_checker.register_check(ServiceHealthCheck(
        name="cache",
        check_fn=mock_cache_check,
        timeout_seconds=5.0,
        critical=False
    ))
    
    # Run health checks
    results = await health_checker.check_all()
    overall_status = health_checker.get_overall_status()
    
    print(f"   Overall status: {overall_status.value}")
    for name, result in results.items():
        print(f"   - {name}: {result.status.value} ({result.latency_ms:.1f}ms)")
    
    # 7. Get Health Report
    print("\n7. Generating health report...")
    report = health_checker.get_health_report()
    print(f"   Status: {report['status']}")
    print(f"   Components checked: {report['summary']['total_checks']}")
    print(f"   Healthy: {report['summary']['healthy']}")
    
    # 8. Demonstrate Context Binding
    print("\n8. Demonstrating context variable binding...")
    bind_contextvars(
        user_id="user-12345",
        inspection_id="INSP-001"
    )
    
    logger.info("Processing with bound context", operation="final_check")
    print("   ✓ Context variables bound to logs")
    
    # Summary
    print("\n" + "=" * 60)
    print("Observability Demo Complete!")
    print("=" * 60)
    print("\nFeatures Demonstrated:")
    print("  ✓ Distributed tracing with OpenTelemetry")
    print("  ✓ Business and system metrics collection")
    print("  ✓ Structured logging with correlation IDs")
    print("  ✓ Health checking with parallel execution")
    print("  ✓ Context variable binding")
    print("\nNext Steps:")
    print("  - Configure OTLP endpoint for trace export")
    print("  - Setup Prometheus for metrics scraping")
    print("  - Configure Loki for log aggregation")
    print("  - Create Grafana dashboards")
    print("  - Register real health checks for dependencies")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
