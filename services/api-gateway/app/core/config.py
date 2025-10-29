"""Core configuration management"""

import os
from typing import List, Optional
from functools import lru_cache

from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    environment: str = Field(default="development", description="Environment name")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Security
    secret_key: str = Field(..., description="Secret key for JWT tokens")
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(default=30, description="Access token expiry")
    refresh_token_expire_days: int = Field(default=7, description="Refresh token expiry")
    
    # CORS and security
    allowed_hosts: List[str] = Field(default=["*"], description="Allowed hosts")
    cors_origins: List[str] = Field(default=["*"], description="CORS origins")
    
    # Database
    database_url: str = Field(..., description="Database connection URL")
    database_pool_size: int = Field(default=10, description="Database connection pool size")
    database_max_overflow: int = Field(default=20, description="Database max overflow")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379", description="Redis connection URL")
    
    # Rate limiting
    rate_limit_per_minute: int = Field(default=100, description="Rate limit per minute")
    rate_limit_burst: int = Field(default=200, description="Rate limit burst")
    
    # Services URLs
    ingestion_service_url: str = Field(
        default="http://ingestion-svc:8001", 
        description="Ingestion service URL"
    )
    inference_service_url: str = Field(
        default="http://inference-svc:8002", 
        description="Inference service URL"
    )
    metadata_service_url: str = Field(
        default="http://metadata-svc:8003", 
        description="Metadata service URL"
    )
    artifact_service_url: str = Field(
        default="http://artifact-svc:8004", 
        description="Artifact service URL"
    )
    report_service_url: str = Field(
        default="http://report-svc:8005", 
        description="Report service URL"
    )
    
    # Observability
    otel_exporter_otlp_endpoint: Optional[str] = Field(
        default=None, 
        description="OpenTelemetry OTLP endpoint"
    )
    otel_service_name: str = Field(
        default="api-gateway", 
        description="OpenTelemetry service name"
    )
    otel_service_version: str = Field(
        default="0.1.0", 
        description="OpenTelemetry service version"
    )
    
    # Timeouts
    http_timeout: int = Field(default=30, description="HTTP client timeout")
    upstream_timeout: int = Field(default=60, description="Upstream service timeout")
    
    @validator("environment")
    def validate_environment(cls, v):
        valid_environments = ["development", "staging", "production", "test"]
        if v not in valid_environments:
            raise ValueError(f"Environment must be one of: {valid_environments}")
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == "development"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()