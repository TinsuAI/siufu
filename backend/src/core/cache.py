"""
Redis caching utilities
"""
import hashlib
from typing import Optional

import redis
import structlog

from src.core.config import settings
from src.schemas.ocr import OCRResult

logger = structlog.get_logger()

# Initialize Redis client
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


def get_ocr_cache_key(file_path: str) -> str:
    """
    Generate cache key using MD5 hash of file contents + file path

    Args:
        file_path: Path to file

    Returns:
        Cache key string
    """
    with open(file_path, 'rb') as f:
        file_hash = hashlib.md5(f.read()).hexdigest()
    return f"ocr:result:{file_hash}"


def cache_ocr_result(file_path: str, result: OCRResult) -> None:
    """
    Store OCR result in Redis with 24-hour TTL

    Args:
        file_path: Path to file
        result: OCR result to cache
    """
    cache_key = get_ocr_cache_key(file_path)
    cache_value = result.model_dump_json()

    # Store in Redis with 24-hour TTL (86400 seconds)
    redis_client.setex(cache_key, 86400, cache_value)

    logger.info(
        "OCR result cached",
        cache_key=cache_key,
        file=file_path,
        ttl_seconds=86400
    )


def get_cached_ocr_result(file_path: str) -> Optional[OCRResult]:
    """
    Retrieve cached OCR result from Redis

    Args:
        file_path: Path to file

    Returns:
        Cached OCR result or None if not found
    """
    cache_key = get_ocr_cache_key(file_path)
    cached_value = redis_client.get(cache_key)

    if cached_value:
        logger.info("OCR cache hit", cache_key=cache_key, file=file_path)
        return OCRResult.model_validate_json(cached_value)

    logger.info("OCR cache miss", cache_key=cache_key, file=file_path)
    return None
