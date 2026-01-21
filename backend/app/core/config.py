"""
Application configuration using Pydantic settings
Loads from environment variables with validation
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """
    Application settings loaded from environment
    """
    # Application
    APP_NAME: str = "SafetySync Analytics Platform"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # Database - TimescaleDB
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://safety_admin:safety_dev_2024@localhost:5432/safety_analytics"
    )
    
    # Redis - for task queue and caching
    REDIS_URL: str = os.getenv(
        "REDIS_URL",
        "redis://localhost:6379/0"
    )
    
    # Data ingestion settings
    MAX_BATCH_SIZE: int = 1000  # max records per batch insert
    INGESTION_BUFFER_SIZE: int = 5000  # buffer before flushing to DB
    DATA_RETENTION_DAYS: int = 90
    
    # Data quality thresholds
    MAX_DUPLICATE_RATE: float = 0.05  # 5% duplicates triggers alert
    MAX_INVALID_RATE: float = 0.10  # 10% invalid records triggers alert
    MAX_LATE_ARRIVAL_MINUTES: int = 60  # data older than 1hr is "late"
    
    # Alert thresholds (can be overridden per equipment type)
    GAS_DETECTION_THRESHOLD: float = 10.0  # ppm
    TEMPERATURE_THRESHOLD: float = 60.0  # celsius
    PRESSURE_THRESHOLD: float = 150.0  # psi
    
    # Reporting
    REPORTS_OUTPUT_DIR: str = "/app/reports"
    REPORT_RETENTION_DAYS: int = 365
    
    # API settings
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8000"]
    
    # Celery
    CELERY_BROKER_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()