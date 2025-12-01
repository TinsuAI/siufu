"""
Application configuration
"""
import os

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables"""

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str
    CELERY_BROKER_URL: str | None = None

    # Auth
    JWT_SECRET_KEY: str  # No default - must be explicitly set
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 8

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        """Validate JWT secret key meets security requirements"""
        if not v or len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
        if v == "dev-secret-key-change-in-production":
            raise ValueError("JWT_SECRET_KEY must be changed from default value")
        return v

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    # External APIs
    OPENROUTER_API_KEY: str = ""

    # Vision OCR Settings (Gemini via OpenRouter)
    VISION_OCR_MODEL: str = "google/gemini-3-pro-preview"
    VISION_MAX_PAGES: int = 20  # Max pages per vision API request
    VISION_IMAGE_DPI: int = 150  # DPI for PDF to image conversion

    # Legacy Google Cloud settings (deprecated - kept for backward compatibility)
    GOOGLE_CLOUD_PROJECT_ID: str = ""
    GOOGLE_CLOUD_LOCATION: str = "us"
    GOOGLE_CLOUD_PROCESSOR_ID: str = ""

    # Monitoring
    SENTRY_DSN: str = ""

    class Config:
        # Use .env.test if ENVIRONMENT=test, otherwise .env
        env_file = ".env.test" if os.getenv("ENVIRONMENT") == "test" else ".env"
        case_sensitive = True

    @property
    def celery_broker(self) -> str:
        """Get Celery broker URL, fallback to REDIS_URL if not set"""
        return self.CELERY_BROKER_URL or self.REDIS_URL


settings = Settings()
