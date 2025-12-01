"""
Rate limiting configuration
"""
import os

from slowapi import Limiter
from slowapi.util import get_remote_address


def _get_rate_limit_key(request):
    """Get rate limit key - returns None (disabled) in test environment."""
    if os.environ.get("ENVIRONMENT") == "test":
        return None  # Disable rate limiting in tests
    return get_remote_address(request)


# Rate limiter instance - used by auth endpoints
# Disabled in test environment by returning None key
limiter = Limiter(key_func=_get_rate_limit_key)
