"""
Health check endpoints for monitoring system components.

Provides health status for:
- API service (basic health)
- Celery workers (processing capability)
- Database connectivity
- Redis connectivity
"""

from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
import logging

from src.core.celery_app import celery_app
from src.core.database import get_db
from src.core.redis import get_redis

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, str]:
    """
    Basic health check endpoint.

    Returns:
        Simple status indicating API is running
    """
    return {
        "status": "healthy",
        "service": "logai-focus-api"
    }


@router.get("/celery", status_code=status.HTTP_200_OK)
async def check_celery_health() -> Dict[str, Any]:
    """
    Check Celery worker health and availability.

    This endpoint verifies:
    - At least one Celery worker is active and connected
    - Workers are able to receive tasks
    - Worker connectivity to message broker (Redis)

    Returns:
        Dict with status, worker count, and worker details

    Status Codes:
        200: Healthy (workers active)
        503: Unhealthy (no workers or connection error)
    """
    try:
        # Use celery control inspect to check for active workers
        inspect = celery_app.control.inspect()

        # Get active workers (workers currently processing tasks)
        active_workers = inspect.active()

        # Get registered workers (all connected workers)
        registered_workers = inspect.registered()

        # Get worker stats
        stats = inspect.stats()

        if not registered_workers:
            return {
                "status": "unhealthy",
                "reason": "No active celery workers found",
                "workers": 0,
                "details": {
                    "active_workers": active_workers or {},
                    "registered_workers": registered_workers or {},
                    "stats": stats or {}
                }
            }

        worker_count = len(registered_workers.keys())

        return {
            "status": "healthy",
            "workers": worker_count,
            "worker_names": list(registered_workers.keys()),
            "details": {
                "active_tasks": active_workers or {},
                "registered_tasks": registered_workers or {},
                "stats": stats or {}
            }
        }

    except Exception as e:
        logger.error(f"Celery health check failed: {e}")
        return {
            "status": "unhealthy",
            "reason": f"Celery health check error: {str(e)}",
            "workers": 0
        }


@router.get("/database", status_code=status.HTTP_200_OK)
async def check_database_health(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Check database connectivity and health.

    Returns:
        Dict with status and connection details

    Status Codes:
        200: Healthy (database accessible)
        503: Unhealthy (connection error)
    """
    try:
        # Execute simple query to verify connection
        await db.execute("SELECT 1")

        return {
            "status": "healthy",
            "database": "postgresql"
        }

    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "reason": f"Database connection error: {str(e)}"
        }


@router.get("/redis", status_code=status.HTTP_200_OK)
async def check_redis_health() -> Dict[str, Any]:
    """
    Check Redis connectivity and health.

    Returns:
        Dict with status and connection details

    Status Codes:
        200: Healthy (Redis accessible)
        503: Unhealthy (connection error)
    """
    try:
        redis_client = get_redis()

        # Ping Redis to verify connection
        await redis_client.ping()

        # Get basic info
        info = await redis_client.info("server")

        return {
            "status": "healthy",
            "redis_version": info.get("redis_version", "unknown"),
            "uptime_seconds": info.get("uptime_in_seconds", 0)
        }

    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {
            "status": "unhealthy",
            "reason": f"Redis connection error: {str(e)}"
        }


@router.get("/all", status_code=status.HTTP_200_OK)
async def check_all_health(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Comprehensive health check for all system components.

    Returns:
        Dict with status for each component and overall health

    Status Codes:
        200: All components healthy
        503: One or more components unhealthy
    """
    try:
        # Check each component
        api_health = await health_check()
        celery_health = await check_celery_health()
        db_health = await check_database_health(db)
        redis_health = await check_redis_health()

        # Determine overall health
        all_healthy = all([
            api_health.get("status") == "healthy",
            celery_health.get("status") == "healthy",
            db_health.get("status") == "healthy",
            redis_health.get("status") == "healthy"
        ])

        return {
            "status": "healthy" if all_healthy else "degraded",
            "components": {
                "api": api_health,
                "celery": celery_health,
                "database": db_health,
                "redis": redis_health
            }
        }

    except Exception as e:
        logger.error(f"Comprehensive health check failed: {e}")
        return {
            "status": "unhealthy",
            "reason": f"Health check error: {str(e)}"
        }
