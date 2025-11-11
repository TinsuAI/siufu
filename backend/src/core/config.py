"""
Application configuration
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables"""

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str
    CELERY_BROKER_URL: str | None = None

    # Auth
    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 8

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    # External APIs
    OPENROUTER_API_KEY: str = ""
    GOOGLE_CLOUD_PROJECT_ID: str = ""
    GOOGLE_CLOUD_LOCATION: str = "us"
    GOOGLE_CLOUD_PROCESSOR_ID: str = ""

    # Monitoring
    SENTRY_DSN: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def celery_broker(self) -> str:
        """Get Celery broker URL, fallback to REDIS_URL if not set"""
        return self.CELERY_BROKER_URL or self.REDIS_URL


settings = Settings()
