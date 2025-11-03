"""
Unit tests for observability logging module.
"""

import pytest
import structlog

from services.shared.observability.logging.setup import (
    setup_structured_logging,
    get_logger,
    bind_contextvars,
    unbind_contextvars,
    clear_contextvars,
)
from services.shared.observability.logging.correlation import (
    generate_correlation_id,
    generate_request_id,
    set_correlation_id,
    get_correlation_id,
    set_request_id,
    get_request_id,
    clear_context,
)


class TestLoggingSetup:
    """Tests for logging setup."""
    
    def test_setup_structured_logging_json(self):
        """Test structured logging setup with JSON format."""
        logger = setup_structured_logging(
            log_level="INFO",
            service_name="test-service",
            json_logs=True
        )
        
        assert logger is not None
        assert isinstance(logger, structlog.BoundLogger)
    
    def test_setup_structured_logging_console(self):
        """Test structured logging setup with console format."""
        logger = setup_structured_logging(
            log_level="DEBUG",
            service_name="test-service",
            json_logs=False
        )
        
        assert logger is not None
        assert isinstance(logger, structlog.BoundLogger)
    
    def test_get_logger(self):
        """Test getting a logger instance."""
        logger = get_logger("test-module")
        
        assert logger is not None
        assert isinstance(logger, structlog.BoundLogger)
    
    def test_bind_contextvars(self):
        """Test binding context variables."""
        # Should not raise an exception
        bind_contextvars(
            request_id="req-12345",
            user_id="user-67890"
        )
        
        # Clean up
        clear_contextvars()
    
    def test_unbind_contextvars(self):
        """Test unbinding context variables."""
        bind_contextvars(
            request_id="req-12345",
            user_id="user-67890"
        )
        
        # Should not raise an exception
        unbind_contextvars("request_id")
        
        # Clean up
        clear_contextvars()


class TestCorrelationID:
    """Tests for correlation ID management."""
    
    def test_generate_correlation_id(self):
        """Test generating a correlation ID."""
        corr_id = generate_correlation_id()
        
        assert corr_id.startswith("corr-")
        assert len(corr_id) > 5
    
    def test_generate_request_id(self):
        """Test generating a request ID."""
        req_id = generate_request_id()
        
        assert req_id.startswith("req-")
        assert len(req_id) > 4
    
    def test_set_and_get_correlation_id(self):
        """Test setting and getting correlation ID."""
        test_id = "corr-test-12345"
        
        set_correlation_id(test_id)
        retrieved_id = get_correlation_id()
        
        assert retrieved_id == test_id
        
        # Clean up
        clear_context()
    
    def test_set_correlation_id_auto_generate(self):
        """Test auto-generating correlation ID."""
        corr_id = set_correlation_id()
        
        assert corr_id is not None
        assert corr_id.startswith("corr-")
        
        retrieved_id = get_correlation_id()
        assert retrieved_id == corr_id
        
        # Clean up
        clear_context()
    
    def test_set_and_get_request_id(self):
        """Test setting and getting request ID."""
        test_id = "req-test-67890"
        
        set_request_id(test_id)
        retrieved_id = get_request_id()
        
        assert retrieved_id == test_id
        
        # Clean up
        clear_context()
    
    def test_set_request_id_auto_generate(self):
        """Test auto-generating request ID."""
        req_id = set_request_id()
        
        assert req_id is not None
        assert req_id.startswith("req-")
        
        retrieved_id = get_request_id()
        assert retrieved_id == req_id
        
        # Clean up
        clear_context()
    
    def test_clear_context(self):
        """Test clearing correlation context."""
        set_correlation_id("corr-12345")
        set_request_id("req-67890")
        
        clear_context()
        
        assert get_correlation_id() is None
        assert get_request_id() is None
    
    def test_multiple_ids_independent(self):
        """Test that correlation and request IDs are independent."""
        corr_id = set_correlation_id("corr-12345")
        req_id = set_request_id("req-67890")
        
        assert get_correlation_id() == corr_id
        assert get_request_id() == req_id
        assert corr_id != req_id
        
        # Clean up
        clear_context()


class TestLoggingIntegration:
    """Integration tests for logging functionality."""
    
    def test_logging_with_context(self):
        """Test logging with context variables."""
        logger = get_logger("test")
        
        bind_contextvars(
            request_id="req-12345",
            user_id="user-67890"
        )
        
        # Should not raise an exception
        logger.info("Test log message", extra_field="extra_value")
        
        # Clean up
        clear_contextvars()
    
    def test_logging_with_correlation_ids(self):
        """Test logging with correlation IDs."""
        logger = get_logger("test")
        
        set_correlation_id("corr-12345")
        set_request_id("req-67890")
        
        # Should not raise an exception
        logger.info("Test log with correlation IDs")
        
        # Clean up
        clear_context()
