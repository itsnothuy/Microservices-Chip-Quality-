"""Service configuration management"""

import os
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Service identification
    service_name: str = "inspection-service"
    service_version: str = "1.0.0"
    environment: str = "development"
    
    # API configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    
    # Database configuration
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/chip_quality"
    )
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_echo: bool = False
    
    # NVIDIA Triton configuration
    triton_url: str = os.getenv("TRITON_URL", "localhost:8001")
    triton_model_name: str = "defect_detector"
    triton_timeout: int = 30
    triton_max_retries: int = 3
    
    # Kafka configuration
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    kafka_inspection_topic: str = "inspection.events"
    kafka_defect_topic: str = "defect.events"
    kafka_quality_topic: str = "quality.events"
    
    # Redis configuration (caching)
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    cache_ttl: int = 300  # 5 minutes
    
    # MinIO/S3 configuration
    s3_endpoint: str = os.getenv("S3_ENDPOINT", "localhost:9000")
    s3_access_key: str = os.getenv("S3_ACCESS_KEY", "minioadmin")
    s3_secret_key: str = os.getenv("S3_SECRET_KEY", "minioadmin")
    s3_bucket: str = "inspection-artifacts"
    s3_region: str = "us-east-1"
    
    # Quality thresholds
    quality_threshold_critical: float = 0.95
    quality_threshold_high: float = 0.85
    quality_threshold_medium: float = 0.75
    defect_confidence_threshold: float = 0.80
    
    # Performance settings
    inspection_timeout: int = 30  # seconds
    batch_size: int = 10
    max_concurrent_inspections: int = 50
    
    # Observability
    enable_tracing: bool = True
    enable_metrics: bool = True
    log_level: str = "INFO"
    otel_endpoint: Optional[str] = os.getenv("OTEL_ENDPOINT")
    
    # Security
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8080"]
    jwt_secret: str = os.getenv("JWT_SECRET", "dev-secret-key-change-in-production")
    jwt_algorithm: str = "HS256"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


# Global settings instance
settings = Settings()
