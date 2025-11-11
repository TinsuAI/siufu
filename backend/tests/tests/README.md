# Backend Testing Documentation

## Overview

This directory contains the test suite for the backend application. Tests are organized by type: unit, integration, and security tests. All tests use pytest with pytest-asyncio for async support.

## Table of Contents

- [Test Organization](#test-organization)
- [Running Tests](#running-tests)
- [Fixture Architecture & Event Loop Management](#fixture-architecture--event-loop-management)
- [Writing Async Tests](#writing-async-tests)
- [Best Practices](#best-practices)
- [Common Patterns](#common-patterns)

---

## Test Organization

```
tests/
├── conftest.py                          # Shared fixtures and configuration
├── fixtures/                            # Mock fixtures for external services
│   ├── google_document_ai.py           # OCR mock responses
│   └── openrouter.py                   # LLM mock responses
├── integration/                         # Integration tests
│   ├── test_auth_endpoints.py
│   ├── test_file_upload_integration.py
│   └── ...
├── security/                            # Security tests
│   └── test_upload_security.py
└── unit/                                # Unit tests
    └── test_declaration_processor.py
```

### Test Types

- **Unit Tests** (`tests/unit/`): Fast tests with no external dependencies, testing individual functions/classes
- **Integration Tests** (`tests/integration/`): Tests that interact with database, API endpoints, or multiple components
- **Security Tests** (`tests/security/`): Security-focused tests for authentication, authorization, and input validation

---

## Running Tests

### All Tests
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing
```

### Specific Test Suites
```bash
# Run security tests
pytest tests/security/ -v

# Run unit tests
pytest tests/unit/ -v

# Run integration tests
pytest tests/integration/ -v
```

### Individual Tests
```bash
# Run a specific test file
pytest tests/security/test_upload_security.py -v

# Run a specific test
pytest tests/security/test_upload_security.py::TestFileUploadSecurity::test_rejects_path_traversal_in_filename -v
```

### Debug Output
```bash
# Verbose output with print statements
pytest tests/ -vvs

# Show local variables on failure
pytest tests/ -l
```

---

## Fixture Architecture & Event Loop Management

### The Problem: Event Loop Conflicts

When testing async code with pytest-asyncio, event loop management is critical. Improper fixture scoping can cause `RuntimeError: Event loop is closed` errors when:

1. Session-scoped fixtures create async connections tied to the first test's event loop
2. pytest-asyncio creates new event loops for each function-scoped test
3. Subsequent tests run in different event loops
4. Cleanup attempts to use closed event loops from previous tests

### The Solution: Session-Scoped Event Loop + Transaction Isolation

Our test infrastructure uses a **session-scoped event loop** combined with **transaction-based test isolation**:

```python
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
```

**Key Benefits:**
- All async fixtures and tests share the same event loop
- No event loop closure errors during cleanup
- Proper async resource management across tests

### Database Test Fixtures

#### Session-Scoped Engine

The `test_engine` fixture creates tables once per test session:

```python
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
        echo=False,
    )

    # Create all tables once
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables after test session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()
```

#### Function-Scoped Database Sessions

The `db_session` fixture provides isolated database sessions using **transaction rollback**:

```python
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
    """
    # Explicitly create connection and transaction
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
```

**Why This Works:**
1. Tables created once (fast)
2. Each test runs in its own transaction
3. Transaction rollback provides clean state for next test
4. No event loop conflicts because explicit cleanup happens in current loop context
5. Industry-standard pattern (FastAPI, SQLAlchemy docs)

### HTTP Client Fixture

The `async_client` fixture provides an HTTP client for API testing:

```python
@pytest_asyncio.fixture(scope="function")
async def async_client():
    """
    Create async HTTP client for testing FastAPI endpoints.
    """
    from httpx import AsyncClient, ASGITransport
    from src.main import app

    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test")

    try:
        yield client
    finally:
        await client.aclose()
```

### Test Data Fixtures

Common test data fixtures use transaction-based isolation:

```python
@pytest_asyncio.fixture(scope="function")
async def test_organization(db_session: AsyncSession):
    """Create a test organization."""
    org = Organization(
        id=UUID("00000000-0000-0000-0000-000000000001"),
        name="Test Organization"
    )
    db_session.add(org)
    await db_session.commit()  # Commits within transaction
    await db_session.refresh(org)
    return org  # Will be rolled back after test

@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession, test_organization):
    """Create a test user."""
    user = User(
        id=UUID("00000000-0000-0000-0000-000000000002"),
        email="test@example.com",
        hashed_password=pwd_context.hash("test123"),
        organization_id=test_organization.id
    )
    db_session.add(user)
    await db_session.commit()  # Commits within transaction
    await db_session.refresh(user)
    return user  # Will be rolled back after test
```

---

## Writing Async Tests

### Basic Async Test

```python
import pytest

@pytest.mark.asyncio
async def test_example(db_session: AsyncSession):
    """Example async test."""
    org = Organization(name="Test Org")
    db_session.add(org)
    await db_session.commit()

    result = await db_session.execute(
        select(Organization).where(Organization.name == "Test Org")
    )
    found_org = result.scalar_one()

    assert found_org.name == "Test Org"
```

### API Endpoint Testing

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_api_endpoint(async_client: AsyncClient, test_user, auth_headers):
    """Test an API endpoint."""
    response = await async_client.get(
        "/api/v1/declarations",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
```

### Using Mock Fixtures

```python
import pytest

@pytest.mark.asyncio
async def test_with_mocks(db_session, google_ocr_invoice_mock, openrouter_extract_mock):
    """Test with external service mocks."""
    # google_ocr_invoice_mock and openrouter_extract_mock are automatically applied
    # by pytest fixtures in tests/fixtures/

    result = await process_invoice(invoice_path)
    assert result.status == "success"
```

---

## Best Practices

### DO ✅

1. **Use pytest_asyncio.fixture for async fixtures**
   ```python
   @pytest_asyncio.fixture(scope="function")
   async def my_fixture():
       yield value
   ```

2. **Use explicit cleanup with try/finally**
   ```python
   @pytest_asyncio.fixture
   async def my_resource():
       resource = await create_resource()
       try:
           yield resource
       finally:
           await resource.cleanup()
   ```

3. **Let transaction rollback handle database cleanup**
   ```python
   async def test_example(db_session):
       org = Organization(name="Test")
       db_session.add(org)
       await db_session.commit()
       # No manual cleanup needed - transaction will rollback
   ```

4. **Use function scope for test-specific fixtures**
   ```python
   @pytest_asyncio.fixture(scope="function")  # Isolated per test
   async def test_data(db_session):
       # Create test data
       yield data
   ```

### DON'T ❌

1. **Don't create session-scoped fixtures without session-scoped event loop**
   ```python
   # ❌ BAD - Will cause event loop errors
   @pytest_asyncio.fixture(scope="session")
   async def bad_fixture():
       # This will use different event loops
       pass
   ```

2. **Don't use nested context managers for db_session-like fixtures**
   ```python
   # ❌ BAD - Less control over cleanup order
   async with connection.begin() as transaction:
       async with session_maker() as session:
           yield session
           await transaction.rollback()  # Problematic cleanup order
   ```

3. **Don't manually create/drop tables in tests**
   ```python
   # ❌ BAD - Slow and unnecessary
   async def test_example(test_engine):
       await create_all_tables(test_engine)  # Don't do this
       # ... test code ...
       await drop_all_tables(test_engine)  # Don't do this
   ```

4. **Don't close event loops in fixtures**
   ```python
   # ❌ BAD - Let pytest-asyncio manage event loop lifecycle
   @pytest.fixture
   def event_loop():
       loop = asyncio.new_event_loop()
       yield loop
       loop.close()  # Handled by framework
   ```

---

## Common Patterns

### Testing with Authentication

```python
@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers for API requests."""
    from src.core.security import create_access_token
    token = create_access_token(subject=str(test_user.id))
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_protected_endpoint(async_client, test_user, auth_headers):
    response = await async_client.get("/api/v1/profile", headers=auth_headers)
    assert response.status_code == 200
```

### Testing File Uploads

```python
@pytest.mark.asyncio
async def test_file_upload(async_client, test_user, auth_headers):
    """Test file upload endpoint."""
    files = {
        'invoice': ('test.pdf', b'PDF content', 'application/pdf'),
    }

    response = await async_client.post(
        '/api/v1/declarations/upload',
        files=files,
        headers=auth_headers
    )

    assert response.status_code == 201
```

### Testing Async Background Tasks

```python
@pytest.mark.asyncio
async def test_background_task(db_session):
    """Test Celery task directly."""
    from src.workers.declaration_processor import process_declaration_task

    declaration = Declaration(status=DeclarationStatus.pending)
    db_session.add(declaration)
    await db_session.commit()

    # Call task directly (not via Celery)
    result = await process_declaration_task(str(declaration.id))

    await db_session.refresh(declaration)
    assert declaration.status == DeclarationStatus.completed
```

### Parametrized Tests

```python
@pytest.mark.asyncio
@pytest.mark.parametrize("email,valid", [
    ("valid@example.com", True),
    ("invalid.email", False),
    ("@example.com", False),
])
async def test_email_validation(async_client, email, valid):
    """Test email validation with multiple inputs."""
    response = await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "test123"}
    )

    if valid:
        assert response.status_code == 201
    else:
        assert response.status_code == 422
```

---

## Troubleshooting

### Event Loop Errors

**Error**: `RuntimeError: Event loop is closed`

**Solution**: Ensure you're using the session-scoped `event_loop` fixture (defined in conftest.py) and `pytest_asyncio.fixture` for all async fixtures.

### Transaction Isolation Issues

**Error**: Test data persists between tests

**Solution**: Verify your test is using the `db_session` fixture, which automatically rolls back after each test. Don't create your own session directly from `test_engine`.

### Slow Tests

**Issue**: Tests are running slowly

**Diagnosis**:
- Check if tables are being created/dropped per test (should only happen once per session)
- Check if you're using database connections efficiently
- Consider using `--cov` only when needed (coverage adds overhead)

---

## Configuration

### pytest.ini

```ini
[pytest]
asyncio_mode = auto  # Enable automatic async test detection
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

### Coverage Target

Per `docs/architecture/testing-strategy.md`:
- **Target**: 70%+ coverage for critical paths
- **Focus**: Business logic, security, data processing
- **Exclude**: Boilerplate, configuration files, migrations

---

## Resources

### Internal Documentation
- `docs/architecture/testing-strategy.md` - Coverage targets and testing pyramid
- `docs/architecture/backend-architecture.md` - Repository pattern and async patterns

### External Documentation
- [pytest-asyncio docs](https://pytest-asyncio.readthedocs.io/)
- [SQLAlchemy async testing](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [FastAPI testing guide](https://fastapi.tiangolo.com/advanced/async-tests/)

---

## Maintenance Notes

**Story 3.3.2**: Test infrastructure refactored to use session-scoped event loop + transaction-based isolation to fix "Event loop is closed" errors. This pattern should be maintained for all future async fixtures.

**Key Principle**: Session-scoped event loop + function-scoped transaction rollback = fast, isolated, reliable tests.
