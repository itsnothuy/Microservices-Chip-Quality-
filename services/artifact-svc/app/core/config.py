"""Service configuration management"""

import os
from typing import Optional, List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Service identification
    service_name: str = "artifact-service"
    service_version: str = "1.0.0"
    environment: str = "development"
    
    # API configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    
    # Database configuration
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://chip_quality_user:dev_password_123@localhost:5432/chip_quality"
    )
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_echo: bool = False
    
    # MinIO/S3 configuration
    s3_endpoint_url: str = os.getenv("S3_ENDPOINT_URL", "http://localhost:9000")
    s3_access_key_id: str = os.getenv("S3_ACCESS_KEY_ID", "minio_admin")
    s3_secret_access_key: str = os.getenv("S3_SECRET_ACCESS_KEY", "minio_password_123")
    s3_bucket_name: str = os.getenv("S3_BUCKET_NAME", "chip-quality-artifacts")
    s3_region: str = "us-east-1"
    s3_use_ssl: bool = False
    
    # File processing configuration
    max_upload_size_bytes: int = 1024 * 1024 * 1024  # 1GB
    allowed_content_types: List[str] = [
        "image/jpeg",
        "image/png",
        "image/tiff",
        "image/bmp",
        "application/pdf",
        "text/plain",
        "text/csv",
        "application/json",
        "video/mp4",
        "video/avi"
    ]
    chunk_size: int = 8192  # 8KB chunks for streaming
    thumbnail_max_size: tuple[int, int] = (256, 256)
    
    # Redis configuration (caching)
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/3")
    cache_ttl: int = 300  # 5 minutes
    
    # Kafka configuration
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    kafka_artifact_topic: str = "artifact.events"
    
    # Performance settings
    upload_timeout: int = 300  # 5 minutes for large files
    download_timeout: int = 60
    processing_timeout: int = 120
    max_concurrent_uploads: int = 20
    
    # Observability
    enable_tracing: bool = True
    enable_metrics: bool = True
    log_level: str = "INFO"
    otel_endpoint: Optional[str] = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    
    # Security
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


# Global settings instance
settings = Settings()
