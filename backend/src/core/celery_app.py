"""
Celery application for async task processing
"""
import logging
import os

import sentry_sdk
from celery import Celery
from redis.exceptions import ConnectionError as RedisConnectionError
from sentry_sdk.integrations.celery import CeleryIntegration

from src.core.config import settings

logger = logging.getLogger(__name__)

# Initialize Sentry for Celery if DSN is configured
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[CeleryIntegration()],
        traces_sample_rate=0.1,  # 10% of tasks for performance monitoring
        environment="production" if "prod" in settings.DATABASE_URL else "development"
    )
    logger.info("Sentry integration initialized for Celery")

# Create Celery app with Redis as broker and result backend
celery_app = Celery(
    "customs_automation",
    broker=settings.celery_broker,
    backend=settings.celery_broker,  # Use same Redis instance for results
)

# Configure Celery per Task 1 requirements
celery_app.conf.update(
    # Security: JSON serializer only (no pickle)
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # Timezone settings
    timezone="UTC",
    enable_utc=True,

    # Task tracking
    task_track_started=True,

    # Task time limits (30 minutes max for LLM processing)
    task_time_limit=1800,  # 30 minutes hard limit (LLM can take 5-10 min)
    task_soft_time_limit=1500,  # 25 minutes soft limit (warning)

    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_backend_transport_options={
        'master_name': 'mymaster',
    },
)

# Verify Redis connection on initialization (fail fast if Redis unavailable)
# Skip connection check in test environment to allow module import during testing
if os.getenv("ENVIRONMENT") != "test":
    try:
        celery_app.connection().ensure_connection(max_retries=3)
        logger.info("✓ Celery app initialized successfully - Redis connection verified")
    except RedisConnectionError as e:
        logger.error(f"✗ Failed to connect to Redis broker: {e}")
        raise RuntimeError(f"Celery cannot connect to Redis at {settings.celery_broker}") from e
else:
    logger.info("ℹ Celery app initialized in test mode - skipping Redis connection check")

# Auto-discover tasks from workers module
celery_app.autodiscover_tasks(['src.workers'])


@celery_app.task(name="health_check")
def health_check() -> dict:
    """Health check task to verify Celery worker is operational"""
    return {"status": "healthy", "message": "Celery worker is running"}
