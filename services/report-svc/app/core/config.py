"""
Report Service Configuration.

Manages service configuration with environment variable support.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Report service configuration settings"""
    
    # Service metadata
    service_name: str = "report-service"
    service_version: str = "1.0.0"
    environment: str = "development"
    
    # API configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8083
    api_prefix: str = "/api/v1"
    
    # Database configuration
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/chip_quality"
    database_pool_size: int = 20
    database_max_overflow: int = 10
    database_pool_timeout: int = 30
    database_pool_recycle: int = 3600
    
    # Redis configuration
    redis_url: str = "redis://localhost:6379/0"
    redis_cache_ttl: int = 300  # 5 minutes
    
    # MinIO configuration for report storage
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False
    minio_reports_bucket: str = "reports"
    
    # Report generation settings
    report_generation_timeout: int = 300  # 5 minutes
    max_concurrent_reports: int = 10
    report_retention_days: int = 2555  # ~7 years for FDA compliance
    temp_report_retention_hours: int = 24
    
    # Analytics settings
    max_analytics_records: int = 1000000
    analytics_query_timeout: int = 60
    spc_decimal_precision: int = 6
    
    # Export settings
    pdf_page_size: str = "A4"
    excel_max_rows: int = 1048576
    csv_encoding: str = "utf-8"
    
    # CORS settings
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
