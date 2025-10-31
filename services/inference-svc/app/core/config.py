"""
ML Inference Service Configuration.

Environment-based configuration for the inference service.
"""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings for ML Inference Service."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )
    
    # Application settings
    app_name: str = "Inference Service"
    environment: str = Field(default="development", description="Environment name")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # API Configuration
    api_v1_prefix: str = "/api/v1"
    
    # Database settings
    database_url: str = Field(
        default="postgresql+asyncpg://chip_quality_user:dev_password_123@localhost:5432/chip_quality",
        description="PostgreSQL database URL"
    )
    database_pool_size: int = Field(default=20, description="Database connection pool size")
    database_max_overflow: int = Field(default=10, description="Max overflow connections")
    
    # Redis settings
    redis_url: str = Field(
        default="redis://:dev_redis_password@localhost:6379/2",
        description="Redis URL for caching"
    )
    redis_cache_ttl: int = Field(default=300, description="Cache TTL in seconds")
    
    # NVIDIA Triton settings
    triton_server_url: str = Field(
        default="localhost:8001",
        description="Triton Inference Server gRPC URL"
    )
    triton_http_url: str = Field(
        default="http://localhost:8000",
        description="Triton Inference Server HTTP URL"
    )
    triton_timeout: int = Field(default=30, description="Triton request timeout in seconds")
    triton_max_retries: int = Field(default=3, description="Max retry attempts for Triton")
    triton_model_name: str = Field(
        default="defect_detection_v1",
        description="Default model name"
    )
    triton_preferred_batch_sizes: list[int] = Field(
        default=[4, 8, 16],
        description="Preferred batch sizes for dynamic batching"
    )
    triton_max_batch_size: int = Field(default=32, description="Maximum batch size")
    
    # Model settings
    model_repository_path: str = Field(
        default="/app/models",
        description="Path to model repository"
    )
    model_confidence_threshold: float = Field(
        default=0.75,
        description="Minimum confidence threshold for predictions"
    )
    
    # Image preprocessing settings
    image_max_size: int = Field(default=10 * 1024 * 1024, description="Max image size in bytes (10MB)")
    image_target_width: int = Field(default=1024, description="Target image width for inference")
    image_target_height: int = Field(default=1024, description="Target image height for inference")
    image_supported_formats: list[str] = Field(
        default=["jpeg", "jpg", "png", "tiff", "bmp"],
        description="Supported image formats"
    )
    
    # Performance settings
    inference_batch_timeout_ms: int = Field(
        default=500,
        description="Max queue delay for batch formation in milliseconds"
    )
    max_concurrent_requests: int = Field(
        default=50,
        description="Maximum concurrent inference requests"
    )
    
    # Kafka settings
    kafka_bootstrap_servers: str = Field(
        default="localhost:9092",
        description="Kafka bootstrap servers"
    )
    kafka_inference_topic: str = Field(
        default="chip-quality.inference.requested",
        description="Kafka topic for inference requests"
    )
    kafka_result_topic: str = Field(
        default="chip-quality.inference.completed",
        description="Kafka topic for inference results"
    )
    kafka_consumer_group: str = Field(
        default="inference-service",
        description="Kafka consumer group ID"
    )
    
    # OpenTelemetry settings
    otel_exporter_otlp_endpoint: Optional[str] = Field(
        default=None,
        description="OpenTelemetry OTLP endpoint"
    )
    otel_service_name: str = Field(
        default="inference-service",
        description="Service name for tracing"
    )
    
    # Security settings
    jwt_secret_key: str = Field(
        default="dev-jwt-secret-key-for-local-development-only",
        description="JWT secret key"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    
    # Rate limiting
    rate_limit_requests: int = Field(default=100, description="Rate limit requests per minute")
    rate_limit_window: int = Field(default=60, description="Rate limit window in seconds")
    
    # Health check settings
    health_check_interval: int = Field(default=30, description="Health check interval in seconds")


# Global settings instance
settings = Settings()
