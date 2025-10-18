"""Pytest configuration and shared fixtures."""

import pytest
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

# Import Base from models
from src.models.user import Base

# Mock fixtures
from tests.fixtures.google_document_ai import (
    mock_ocr_invoice_response,
    mock_ocr_bill_of_lading_response,
    mock_ocr_certificate_of_origin_response,
    mock_ocr_error_response
)
from tests.fixtures.openrouter import (
    mock_llm_extraction_response,
    mock_llm_hs_code_classification_response,
    mock_llm_validation_response,
    mock_llm_streaming_response,
    mock_llm_error_response
)


# Database configuration for tests
TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost:5432/logai_test"


@pytest.fixture(scope="session")
def anyio_backend():
    """Configure anyio backend for async tests."""
    return "asyncio"


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine and setup tables."""
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


@pytest.fixture(scope="function")
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
    """
    async with test_engine.connect() as connection:
        async with connection.begin() as transaction:
            session_maker = async_sessionmaker(
                bind=connection,
                class_=AsyncSession,
                expire_on_commit=False
            )
            async with session_maker() as session:
                yield session
                await transaction.rollback()


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


# OpenRouter LLM mock fixtures
@pytest.fixture
def llm_extraction_mock():
    """Fixture for mocked OpenRouter extraction response."""
    return mock_llm_extraction_response()


@pytest.fixture
def llm_hs_code_mock():
    """Fixture for mocked OpenRouter HS code classification response."""
    return mock_llm_hs_code_classification_response()


@pytest.fixture
def llm_validation_mock():
    """Fixture for mocked OpenRouter validation response."""
    return mock_llm_validation_response(is_valid=True)


@pytest.fixture
def llm_validation_error_mock():
    """Fixture for mocked OpenRouter validation response with errors."""
    return mock_llm_validation_response(is_valid=False)


@pytest.fixture
def llm_streaming_mock():
    """Fixture for mocked OpenRouter streaming response."""
    return mock_llm_streaming_response()


@pytest.fixture
def llm_error_mock():
    """Fixture for mocked OpenRouter error response."""
    return mock_llm_error_response()
