"""
Celery application for async task processing
"""
from celery import Celery

from src.core.config import settings

# Create Celery app
celery_app = Celery(
    "customs_automation",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.REDIS_URL,
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)

# Auto-discover tasks from workers module
# celery_app.autodiscover_tasks(['src.workers'])


@celery_app.task(name="health_check")
def health_check() -> dict:
    """Health check task to verify Celery worker is operational"""
    return {"status": "healthy", "message": "Celery worker is running"}
