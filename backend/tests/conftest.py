"""Pytest configuration and shared fixtures."""

import asyncio
import os
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

# Set test database URL and Redis URL BEFORE importing any src modules
# This ensures src.core.config loads the test configuration
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:test_password_123@localhost:8781/customs_db_test"
TEST_REDIS_URL = "redis://localhost:8782/0"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["REDIS_URL"] = TEST_REDIS_URL
os.environ["CELERY_BROKER_URL"] = TEST_REDIS_URL

# Import Base from models
from src.models.base import Base

# Mock fixtures
from tests.fixtures.google_document_ai import (
    mock_ocr_bill_of_lading_response,
    mock_ocr_certificate_of_origin_response,
    mock_ocr_error_response,
    mock_ocr_invoice_response,
)
from tests.fixtures.openrouter import (
    _create_mock_openrouter_client_auth_error,
    _create_mock_openrouter_client_rate_limit,
    _create_mock_openrouter_client_success,
    _create_mock_openrouter_client_timeout,
)
from tests.fixtures.openrouter import (
    mock_openrouter_response_invalid_json as _mock_openrouter_response_invalid_json,
)
from tests.fixtures.openrouter import (
    mock_openrouter_response_success as _mock_openrouter_response_success,
)
from tests.fixtures.openrouter import (
    mock_openrouter_response_with_markdown as _mock_openrouter_response_with_markdown,
)
from tests.fixtures.openrouter import (
    sample_ocr_result as _sample_ocr_result,
)

# TEST_DATABASE_URL is set at the top of the file before any imports


@pytest.fixture(scope="session")
def anyio_backend():
    """Configure anyio backend for async tests."""
    return "asyncio"


@pytest.fixture(scope="function")
def event_loop():
    """
    Create a function-scoped event loop for each async test.

    This prevents 'attached to a different loop' errors by ensuring each
    test gets its own event loop, avoiding conflicts with asyncpg connections.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """
    Create test database engine for each test function.

    Creates a fresh engine per test to avoid event loop conflicts.
    Tables are created once per test run via metadata.create_all.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,  # Disable connection pooling for tests
        echo=False,  # Set to True for SQL debugging
    )

    # Create all tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

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
async def async_client(db_session: AsyncSession):
    """
    Create async HTTP client for testing FastAPI endpoints.

    Uses httpx.AsyncClient with FastAPI app. This fixture ensures proper
    cleanup of HTTP connections and async resources.

    Overrides app dependencies to use test database session.
    """
    from contextlib import asynccontextmanager

    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient

    from src.core.database import get_db

    # Mock Celery app before importing routers
    mock_celery = MagicMock()
    mock_celery.send_task = MagicMock()
    mock_celery.conf.update = MagicMock()

    # Mock Redis before importing routers
    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock(return_value=True)
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.setex = AsyncMock()

    async def mock_get_redis():
        return mock_redis

    # Create a test lifespan that does nothing (skip database connection test)
    @asynccontextmanager
    async def test_lifespan(app: FastAPI):
        """Test lifespan - skip startup/shutdown events"""
        yield

    # Create a fresh app instance for testing with test lifespan
    test_app = FastAPI(
        title="Test API",
        lifespan=test_lifespan
    )

    # Mock external dependencies before importing routers
    with patch('src.core.celery_app.celery_app', mock_celery), \
         patch('src.core.redis.get_redis', mock_get_redis):

        # Import and copy routes from main app
        from src.api.v1 import api_router
        test_app.include_router(api_router, prefix="/api/v1")

        # Add a simple root endpoint
        @test_app.get("/")
        async def root():
            return {"message": "Test API"}

        # Override database dependency to use test session
        async def override_get_db():
            yield db_session

        test_app.dependency_overrides[get_db] = override_get_db

        # Create client
        transport = ASGITransport(app=test_app)
        client = AsyncClient(transport=transport, base_url="http://test")

        try:
            yield client
        finally:
            # Clean up
            test_app.dependency_overrides.clear()
            await client.aclose()


@pytest_asyncio.fixture(scope="function")
async def test_organization(db_session: AsyncSession):
    """
    Create a test organization for use in tests.

    Returns an Organization instance with a fixed UUID.
    """
    from uuid import UUID

    from sqlalchemy import select

    from src.models.organization import Organization

    org_id = UUID("00000000-0000-0000-0000-000000000001")

    # Check if organization already exists
    result = await db_session.execute(
        select(Organization).where(Organization.id == org_id)
    )
    org = result.scalar_one_or_none()

    if org is None:
        org = Organization(
            id=org_id,
            name="Test Organization"
        )
        db_session.add(org)
        await db_session.flush()

    return org


@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession, test_organization):
    """
    Create a test user for authentication testing.

    Returns a User instance with:
    - Fixed UUID: 00000000-0000-0000-0000-000000000002
    - Email: test@example.com
    - Password: test12345 (hashed)
    - Role: processor
    """
    from uuid import UUID

    from sqlalchemy import select

    from src.core.security import pwd_context
    from src.models.user import User, UserRole

    user_id = UUID("00000000-0000-0000-0000-000000000002")

    # Check if user already exists
    result = await db_session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            id=user_id,
            email="test@example.com",
            hashed_password=pwd_context.hash("test12345"),
            full_name="Test User",
            role=UserRole.processor,
            is_active=True,
            organization_id=test_organization.id
        )
        db_session.add(user)
        await db_session.flush()

    return user


# E2E Test Fixtures for External API Mocking
@pytest.fixture
def mock_google_doc_ai(monkeypatch):
    """Mock Google Document AI service for E2E tests."""
    from src.schemas.ocr import KeyValuePair, OCRResult

    async def mock_process_document(*args, **kwargs):
        """Mock OCR processing that returns a basic OCR result."""
        file_path = kwargs.get('file_path', '')
        file_name = str(file_path).split('/')[-1] if file_path else 'test.pdf'

        # Return a basic OCR result
        return OCRResult(
            text=f"Mock OCR text from {file_name}",
            key_value_pairs=[
                KeyValuePair(key="invoice_number", value="TEST-001", confidence=0.95)
            ],
            tables=[],
            confidence_scores={"invoice_number": 0.95},
            page_count=1,
            file_name=file_name,
            processing_time_ms=100
        )

    # Patch the OCR service
    monkeypatch.setattr('src.services.ocr_service.OCRService.process_document_ocr', mock_process_document)
    return mock_process_document


@pytest.fixture
def mock_openrouter_vietnamese_extraction(monkeypatch):
    """Mock OpenRouter Vietnamese extraction for E2E tests."""
    from src.schemas.vietnamese_declaration import (
        VAT,
        CertificateOfOrigin,
        DeclarationHeader,
        Exporter,
        ImportDuty,
        Importer,
        Invoice,
        Metadata,
        PackageContainer,
        ShippingTransport,
        TaxSummary,
        VietnameseDeclarationData,
    )

    async def mock_extract_from_multiple_documents(*args, **kwargs):
        """Mock LLM extraction that returns Vietnamese declaration data."""
        return VietnameseDeclarationData(
            declaration_header=DeclarationHeader(
                declaration_type_code="A11 2 [4]",
                customs_office_code="HQHOALAC",
                processing_division_code="00"
            ),
            importer=Importer(
                tax_code="0123456789",
                name="Test Company Ltd",
                address="123 Test Street, Hanoi, Vietnam"
            ),
            exporter=Exporter(
                name="Test Exporter Co",
                country_code="CN"
            ),
            shipping_transport=ShippingTransport(
                bill_of_lading_number="BOL-TEST-001"
            ),
            package_container=PackageContainer(
                total_packages=100.0,
                package_unit="PK",
                gross_weight_kg=1000.0,
                gross_weight_unit="KGM"
            ),
            invoice=Invoice(
                invoice_number="INV-TEST-001",
                invoice_total=10000.0,
                invoice_currency="USD",
                invoice_incoterm="FOB"
            ),
            certificate_of_origin=CertificateOfOrigin(),
            products=[],
            import_duty=ImportDuty(
                rate=0.0,
                rate_type="C",
                amount=0.0
            ),
            vat=VAT(
                name="Thuế GTGT",
                rate=10.0,
                amount=0.0
            ),
            tax_summary=TaxSummary(
                total_tax_amount_vnd=0.0
            ),
            metadata=Metadata(
                total_pages=1,
                total_line_items=0
            ),
            confidence_scores={},
            overall_confidence=0.85
        )

    # Patch the LLM service
    monkeypatch.setattr('src.services.llm_service.LLMService.extract_from_multiple_documents', mock_extract_from_multiple_documents)
    return mock_extract_from_multiple_documents
