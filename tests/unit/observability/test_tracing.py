"""
Unit tests for observability tracing module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

from services.shared.observability.tracing.tracer import (
    setup_tracing,
    get_tracer,
    trace_function,
    add_span_attributes,
    add_span_event,
)


class TestTracingSetup:
    """Tests for tracing setup."""
    
    def test_setup_tracing_without_endpoint(self):
        """Test tracing setup without OTLP endpoint."""
        tracer = setup_tracing(
            service_name="test-service",
            service_version="1.0.0",
            otlp_endpoint=None,
        )
        
        assert tracer is not None
        assert isinstance(tracer, trace.Tracer)
    
    def test_setup_tracing_with_endpoint(self):
        """Test tracing setup with OTLP endpoint."""
        with patch('services.shared.observability.tracing.tracer.OTLPSpanExporter'):
            tracer = setup_tracing(
                service_name="test-service",
                service_version="1.0.0",
                otlp_endpoint="http://localhost:4317",
            )
            
            assert tracer is not None
            assert isinstance(tracer, trace.Tracer)
    
    def test_get_tracer(self):
        """Test getting a tracer instance."""
        tracer = get_tracer("test-component", "1.0.0")
        
        assert tracer is not None
        assert isinstance(tracer, trace.Tracer)


class TestTraceFunction:
    """Tests for trace_function decorator."""
    
    @pytest.mark.asyncio
    async def test_trace_async_function_success(self):
        """Test tracing an async function that succeeds."""
        # Setup tracing
        setup_tracing("test-service", otlp_endpoint=None)
        
        @trace_function(span_name="test_operation")
        async def test_func(x: int, y: int) -> int:
            return x + y
        
        result = await test_func(2, 3)
        assert result == 5
    
    @pytest.mark.asyncio
    async def test_trace_async_function_with_exception(self):
        """Test tracing an async function that raises an exception."""
        setup_tracing("test-service", otlp_endpoint=None)
        
        @trace_function(span_name="test_operation")
        async def test_func() -> None:
            raise ValueError("Test error")
        
        with pytest.raises(ValueError, match="Test error"):
            await test_func()
    
    def test_trace_sync_function_success(self):
        """Test tracing a sync function that succeeds."""
        setup_tracing("test-service", otlp_endpoint=None)
        
        @trace_function(span_name="sync_operation")
        def test_func(x: int, y: int) -> int:
            return x * y
        
        result = test_func(4, 5)
        assert result == 20
    
    def test_trace_sync_function_with_exception(self):
        """Test tracing a sync function that raises an exception."""
        setup_tracing("test-service", otlp_endpoint=None)
        
        @trace_function(span_name="sync_operation")
        def test_func() -> None:
            raise RuntimeError("Test error")
        
        with pytest.raises(RuntimeError, match="Test error"):
            test_func()
    
    @pytest.mark.asyncio
    async def test_trace_function_with_attributes(self):
        """Test tracing with custom attributes."""
        setup_tracing("test-service", otlp_endpoint=None)
        
        @trace_function(
            span_name="operation_with_attrs",
            attributes={"custom_key": "custom_value"}
        )
        async def test_func(param: str) -> str:
            return param.upper()
        
        result = await test_func("test")
        assert result == "TEST"


class TestSpanUtilities:
    """Tests for span utilities."""
    
    def test_add_span_attributes(self):
        """Test adding attributes to current span."""
        setup_tracing("test-service", otlp_endpoint=None)
        
        # This should not raise an error even if no span is active
        add_span_attributes({
            "test_key": "test_value",
            "number": 42,
        })
    
    def test_add_span_event(self):
        """Test adding event to current span."""
        setup_tracing("test-service", otlp_endpoint=None)
        
        # This should not raise an error even if no span is active
        add_span_event("test_event", {
            "event_key": "event_value",
        })


class TestTracingIntegration:
    """Integration tests for tracing functionality."""
    
    @pytest.mark.asyncio
    async def test_nested_traced_functions(self):
        """Test nested traced functions."""
        setup_tracing("test-service", otlp_endpoint=None)
        
        @trace_function(span_name="inner_operation")
        async def inner_func(x: int) -> int:
            return x * 2
        
        @trace_function(span_name="outer_operation")
        async def outer_func(x: int) -> int:
            result = await inner_func(x)
            return result + 1
        
        result = await outer_func(5)
        assert result == 11
