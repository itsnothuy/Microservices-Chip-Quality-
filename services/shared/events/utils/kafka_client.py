"""Kafka client configuration and management.

This module provides Kafka client configuration with production-ready settings
for reliability, performance, and observability.
"""

import os
from dataclasses import dataclass
from typing import Dict, Any, Optional

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class KafkaConfig:
    """Kafka configuration settings."""
    
    bootstrap_servers: str
    security_protocol: str = "PLAINTEXT"
    sasl_mechanism: Optional[str] = None
    sasl_username: Optional[str] = None
    sasl_password: Optional[str] = None
    
    # Producer settings
    acks: str = "all"  # Wait for all replicas
    compression_type: str = "snappy"
    max_in_flight_requests: int = 5
    retries: int = 3
    retry_backoff_ms: int = 100
    request_timeout_ms: int = 30000
    enable_idempotence: bool = True
    
    # Consumer settings
    group_id: Optional[str] = None
    auto_offset_reset: str = "earliest"
    enable_auto_commit: bool = False  # Manual commit for exactly-once
    max_poll_records: int = 500
    max_poll_interval_ms: int = 300000
    session_timeout_ms: int = 10000
    heartbeat_interval_ms: int = 3000
    
    # Schema Registry settings
    schema_registry_url: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> "KafkaConfig":
        """Create configuration from environment variables."""
        return cls(
            bootstrap_servers=os.getenv(
                "KAFKA_BOOTSTRAP_SERVERS", 
                "localhost:9092"
            ),
            security_protocol=os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
            sasl_mechanism=os.getenv("KAFKA_SASL_MECHANISM"),
            sasl_username=os.getenv("KAFKA_SASL_USERNAME"),
            sasl_password=os.getenv("KAFKA_SASL_PASSWORD"),
            schema_registry_url=os.getenv("SCHEMA_REGISTRY_URL", "http://localhost:8081"),
        )
    
    def get_producer_config(self) -> Dict[str, Any]:
        """Get producer configuration dictionary."""
        config = {
            "bootstrap_servers": self.bootstrap_servers,
            "acks": self.acks,
            "compression_type": self.compression_type,
            "max_in_flight_requests_per_connection": self.max_in_flight_requests,
            "retries": self.retries,
            "retry_backoff_ms": self.retry_backoff_ms,
            "request_timeout_ms": self.request_timeout_ms,
            "enable_idempotence": self.enable_idempotence,
        }
        
        if self.security_protocol != "PLAINTEXT":
            config["security_protocol"] = self.security_protocol
            if self.sasl_mechanism:
                config["sasl_mechanism"] = self.sasl_mechanism
                config["sasl_plain_username"] = self.sasl_username
                config["sasl_plain_password"] = self.sasl_password
        
        return config
    
    def get_consumer_config(self, group_id: Optional[str] = None) -> Dict[str, Any]:
        """Get consumer configuration dictionary."""
        config = {
            "bootstrap_servers": self.bootstrap_servers,
            "group_id": group_id or self.group_id,
            "auto_offset_reset": self.auto_offset_reset,
            "enable_auto_commit": self.enable_auto_commit,
            "max_poll_records": self.max_poll_records,
            "max_poll_interval_ms": self.max_poll_interval_ms,
            "session_timeout_ms": self.session_timeout_ms,
            "heartbeat_interval_ms": self.heartbeat_interval_ms,
        }
        
        if self.security_protocol != "PLAINTEXT":
            config["security_protocol"] = self.security_protocol
            if self.sasl_mechanism:
                config["sasl_mechanism"] = self.sasl_mechanism
                config["sasl_plain_username"] = self.sasl_username
                config["sasl_plain_password"] = self.sasl_password
        
        return config


class KafkaClientManager:
    """Manager for Kafka client lifecycle."""
    
    def __init__(self, config: Optional[KafkaConfig] = None):
        """Initialize Kafka client manager.
        
        Args:
            config: Kafka configuration. If None, loads from environment.
        """
        self.config = config or KafkaConfig.from_env()
        self.logger = logger.bind(
            bootstrap_servers=self.config.bootstrap_servers
        )
    
    async def health_check(self) -> bool:
        """Check Kafka cluster health.
        
        Returns:
            True if cluster is healthy, False otherwise.
        """
        try:
            from aiokafka import AIOKafkaProducer
            
            producer = AIOKafkaProducer(
                **self.config.get_producer_config()
            )
            await producer.start()
            await producer.stop()
            
            self.logger.info("kafka.health_check.success")
            return True
        except Exception as e:
            self.logger.error(
                "kafka.health_check.failed",
                error=str(e),
                exc_info=True
            )
            return False
