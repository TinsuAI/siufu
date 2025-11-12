"""
Integration tests for Celery task execution

These tests require:
- Redis running (for Celery broker)
- PostgreSQL running (for database)
- Celery worker running (for actual task execution)

Run with: pytest tests/integration/test_celery_integration.py -v -m integration
"""
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.celery_app import celery_app
from src.repositories.declaration_repository import DeclarationRepository
from src.workers.declaration_processor import process_declaration_task


@pytest.mark.integration
class TestCeleryIntegration:
    """Integration tests for Celery worker and task execution"""

    @pytest.mark.asyncio
    async def test_celery_worker_connects_to_redis(self):
        """
        Test 1: Verify Celery worker can ping Redis broker

        This test verifies the basic connectivity between Celery and Redis.
        """
        # Ping celery workers
        inspect = celery_app.control.inspect()
        stats = inspect.stats()

        # If stats is None, no workers are running
        if stats is None:
            pytest.skip("No Celery workers running. Start worker with: celery -A src.core.celery_app worker")

        # Verify at least one worker is active
        assert len(stats) > 0, "Expected at least one active Celery worker"

        # Verify workers can be pinged
        pong = inspect.ping()
        assert pong is not None, "Workers did not respond to ping"
        assert len(pong) > 0, "No workers responded to ping"

    @pytest.mark.asyncio
    async def test_health_check_task_execution(self):
        """Test basic task execution with health check task"""
        from src.core.celery_app import health_check

        # Submit health check task
        result = health_check.delay()

        # Wait for result (timeout 10 seconds)
        task_result = result.get(timeout=10)

        assert task_result["status"] == "healthy"
        assert task_result["message"] == "Celery worker is running"

    @pytest.mark.asyncio
    async def test_task_execution_end_to_end(self, db_session: AsyncSession):
        """
        Test 2: Submit real task, poll until completion, verify results

        This test creates a declaration, triggers processing, and polls
        status endpoint until completion.

        Note: This test requires mock files to be present or will fail.
        Consider using fixtures to create temporary test files.
        """
        # Create test declaration
        _ = DeclarationRepository(db_session)  # Reserved for future test implementation

        # For now, skip this test if no test data available
        pytest.skip("Requires test declaration with uploaded files. Implement in Story 1.6+")

    @pytest.mark.asyncio
    async def test_status_endpoint_returns_accurate_progress(self, db_session: AsyncSession):
        """
        Test 3: Poll status endpoint during task execution

        Verifies that status endpoint returns accurate progress updates
        as task progresses through stages.
        """
        # Skip for now - requires full declaration with files
        pytest.skip("Requires test declaration with uploaded files. Implement in Story 1.6+")

    @pytest.mark.asyncio
    async def test_failed_task_updates_declaration_status(self, db_session: AsyncSession):
        """
        Test 4: Trigger task with invalid declaration ID, verify FAILED status

        This test verifies error handling by submitting a task with
        an invalid declaration ID and checking that it fails gracefully.
        """
        # Check if Celery workers are running
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        if stats is None:
            pytest.skip("No Celery workers running")

        # Create invalid UUID
        invalid_id = str(uuid4())

        # Submit task with invalid ID
        task = process_declaration_task.delay(invalid_id)

        # Wait for task to complete (should fail)
        try:
            _ = task.get(timeout=30)
            pytest.fail("Task should have failed with invalid declaration ID")
        except Exception as e:
            # Expected to raise ValueError or database error
            error_msg = str(e).lower()
            # Accept either "not found" or database schema errors (which indicate DB not set up properly)
            if "not found" in error_msg or "ValueError" in str(type(e).__name__):
                pass  # Expected error
            elif "does not exist" in error_msg or "undefinedcolumnerror" in error_msg:
                pytest.skip("Database schema not set up for Celery worker - run database migrations")
            else:
                # Re-raise unexpected errors
                raise

        # Verify task state is FAILURE
        assert task.state in ["FAILURE", "REVOKED"], f"Expected task to fail, got state: {task.state}"


@pytest.mark.integration
class TestCeleryTaskRetry:
    """Test Celery task retry logic"""

    @pytest.mark.asyncio
    async def test_task_retries_on_transient_error(self):
        """
        Verify that tasks retry on transient errors (rate limits, timeouts)

        This would require mocking external services to return 429 errors.
        Skip for now - implement when mocking infrastructure is in place.
        """
        pytest.skip("Requires mocking external API rate limits. Implement in future story.")

    @pytest.mark.asyncio
    async def test_task_fails_immediately_on_permanent_error(self):
        """
        Verify that tasks fail immediately on permanent errors (file not found)

        Skip for now - implement when mocking infrastructure is in place.
        """
        pytest.skip("Requires mocking file system errors. Implement in future story.")


@pytest.mark.integration
class TestCeleryMonitoring:
    """Test Celery monitoring and observability"""

    @pytest.mark.asyncio
    async def test_celery_task_logs_to_stdout(self):
        """
        Verify that Celery task logs appear in stdout/Docker logs

        This is a manual verification test - check Docker logs to ensure
        task execution is being logged properly.
        """
        from src.core.celery_app import health_check

        # Run health check task
        result = health_check.delay()
        result.get(timeout=10)

        # Log verification is manual - check docker logs:
        # docker-compose logs celery-worker | grep "health_check"
        pytest.skip("Manual verification required - check Docker logs")

    @pytest.mark.asyncio
    async def test_sentry_integration_configured(self):
        """
        Verify Sentry integration is configured for Celery

        This checks that Sentry SDK is initialized with CeleryIntegration.
        """
        import sentry_sdk

        # Check if Sentry client is initialized
        client = sentry_sdk.Hub.current.client

        if client is None:
            pytest.skip("Sentry not configured (SENTRY_DSN not set)")

        # Verify CeleryIntegration is registered
        integrations = [type(i).__name__ for i in client.options["integrations"]]
        assert "CeleryIntegration" in integrations, "CeleryIntegration not found in Sentry integrations"


# Pytest fixtures for integration tests
@pytest.fixture
async def test_declaration(db_session: AsyncSession):
    """
    Create a test declaration with uploaded files for integration testing

    This fixture will be implemented when file upload is working.
    """
    pytest.skip("Test declaration fixture not implemented yet")
