"""Pytest plugin to mock external dependencies before module imports."""

from unittest.mock import MagicMock, patch


def pytest_configure(config):
    """
    Hook called after command line options have been parsed.

    This runs BEFORE any test collection, so we can mock modules
    before they're imported by the test suite.
    """
    # Mock the Celery class itself to prevent connection attempts
    mock_celery_class = MagicMock()
    mock_celery_instance = MagicMock()
    mock_celery_instance.conf.update = MagicMock()
    mock_celery_instance.send_task = MagicMock()
    mock_celery_instance.autodiscover_tasks = MagicMock()
    mock_celery_class.return_value = mock_celery_instance

    # Patch celery.Celery before it's imported
    celery_patcher = patch('celery.Celery', mock_celery_class)
    celery_patcher.start()

    # Also mock Redis connection
    redis_patcher = patch('redis.asyncio.from_url', MagicMock())
    redis_patcher.start()
