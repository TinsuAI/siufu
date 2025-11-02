"""Pytest configuration and shared fixtures."""

import pytest
import pytest_asyncio
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

# Import Base from models
from src.models.base import Base

# Mock fixtures
from tests.fixtures.google_document_ai import (
    mock_ocr_invoice_response,
    mock_ocr_bill_of_lading_response,
    mock_ocr_certificate_of_origin_response,
    mock_ocr_error_response
)

from tests.fixtures.openrouter import (
    mock_openrouter_response_success as _mock_openrouter_response_success,
    mock_openrouter_response_with_markdown as _mock_openrouter_response_with_markdown,
    mock_openrouter_response_invalid_json as _mock_openrouter_response_invalid_json,
    sample_ocr_result as _sample_ocr_result,
    _create_mock_openrouter_client_success,
    _create_mock_openrouter_client_rate_limit,
    _create_mock_openrouter_client_timeout,
    _create_mock_openrouter_client_auth_error,
)


# Database configuration for tests
# Use same Postgres instance but different database for tests
# When running inside Docker, use service name 'postgres' instead of localhost
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:test_password_123@postgres:5432/customs_db_test"


@pytest.fixture(scope="session")
def anyio_backend():
    """Configure anyio backend for async tests."""
    return "asyncio"


@pytest.fixture(scope="session")
def event_loop():
    """
    Create a session-scoped event loop for all async tests.

    This prevents 'Event loop is closed' errors by ensuring all async
    fixtures and tests use the same event loop throughout the test session.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """
    Create test database engine and setup tables.

    Uses session-scoped fixture to create tables once per test session.
    Transaction-based isolation ensures each test gets clean state without
    recreating tables, preventing event loop conflicts.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,  # Disable connection pooling for tests
        echo=False,  # Set to True for SQL debugging
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables after tests complete
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a new database session for each test.

    This fixture:
    - Creates a new connection
    - Begins a transaction
    - Yields a session
    - Rolls back the transaction after the test
    - Closes the connection

    This ensures test isolation - each test gets a clean database state.

    Note: We explicitly manage connection/transaction lifecycle instead of
    using context managers to ensure proper cleanup order in the correct
    event loop context, preventing "Event loop is closed" errors.
    """
    # Explicitly create connection and transaction for better cleanup control
    connection = await test_engine.connect()
    transaction = await connection.begin()

    session_maker = async_sessionmaker(
        bind=connection,
        class_=AsyncSession,
        expire_on_commit=False
    )
    session = session_maker()

    try:
        yield session
    finally:
        # Explicit cleanup in correct order
        await session.close()
        await transaction.rollback()
        await connection.close()


# Google Document AI mock fixtures
@pytest.fixture
def google_ocr_invoice_mock():
    """Fixture for mocked Google Document AI invoice response."""
    return mock_ocr_invoice_response()


@pytest.fixture
def google_ocr_bol_mock():
    """Fixture for mocked Google Document AI Bill of Lading response."""
    return mock_ocr_bill_of_lading_response()


@pytest.fixture
def google_ocr_co_mock():
    """Fixture for mocked Google Document AI Certificate of Origin response."""
    return mock_ocr_certificate_of_origin_response()


@pytest.fixture
def google_ocr_error_mock():
    """Fixture for mocked Google Document AI error response."""
    return mock_ocr_error_response()


# OpenRouter LLM mock fixtures (wrapped pattern matching Google fixtures)
@pytest.fixture
def mock_openrouter_response_success():
    """Fixture for successful OpenRouter API response with ExtractedData JSON."""
    return _mock_openrouter_response_success()


@pytest.fixture
def mock_openrouter_response_with_markdown():
    """Fixture for OpenRouter response where JSON is wrapped in markdown code blocks."""
    return _mock_openrouter_response_with_markdown()


@pytest.fixture
def mock_openrouter_response_invalid_json():
    """Fixture for OpenRouter response with invalid JSON (for testing error handling)."""
    return _mock_openrouter_response_invalid_json()


@pytest.fixture
def sample_ocr_result():
    """Fixture for sample OCR result for LLM testing."""
    return _sample_ocr_result()


@pytest.fixture
def mock_openrouter_client_success(monkeypatch, mock_openrouter_response_success):
    """Fixture for mocked OpenRouterClient with successful API calls."""
    _create_mock_openrouter_client_success(monkeypatch, mock_openrouter_response_success)


@pytest.fixture
def mock_openrouter_client_rate_limit(monkeypatch):
    """Fixture for mocked OpenRouterClient that simulates rate limit error."""
    _create_mock_openrouter_client_rate_limit(monkeypatch)


@pytest.fixture
def mock_openrouter_client_timeout(monkeypatch):
    """Fixture for mocked OpenRouterClient that simulates timeout."""
    _create_mock_openrouter_client_timeout(monkeypatch)


@pytest.fixture
def mock_openrouter_client_auth_error(monkeypatch):
    """Fixture for mocked OpenRouterClient that simulates auth error (401)."""
    _create_mock_openrouter_client_auth_error(monkeypatch)


# HTTP Client fixture for API testing
@pytest_asyncio.fixture(scope="function")
async def async_client():
    """
    Create async HTTP client for testing FastAPI endpoints.

    Uses httpx.AsyncClient with FastAPI app. This fixture ensures proper
    cleanup of HTTP connections and async resources.
    """
    from httpx import AsyncClient, ASGITransport
    from src.main import app

    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test")

    try:
        yield client
    finally:
        await client.aclose()


@pytest_asyncio.fixture(scope="function")
async def test_organization(db_session: AsyncSession):
    """
    Create a test organization for use in tests.

    Returns an Organization instance with a fixed UUID.
    """
    from uuid import UUID
    from src.models.organization import Organization

    org = Organization(
        id=UUID("00000000-0000-0000-0000-000000000001"),
        name="Test Organization"
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession, test_organization):
    """
    Create a test user for authentication testing.

    Returns a User instance with:
    - Fixed UUID: 00000000-0000-0000-0000-000000000002
    - Email: test@example.com
    - Password: test123 (hashed)
    - Role: processor
    """
    from uuid import UUID
    from src.models.user import User, UserRole
    from src.core.security import pwd_context

    user = User(
        id=UUID("00000000-0000-0000-0000-000000000002"),
        email="test@example.com",
        hashed_password=pwd_context.hash("test123"),
        full_name="Test User",
        role=UserRole.processor,
        is_active=True,
        organization_id=test_organization.id
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user
