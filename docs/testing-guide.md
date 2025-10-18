# Testing Guide

Comprehensive guide for writing and running tests in the LogAI project.

## Table of Contents

1. [Testing Philosophy](#testing-philosophy)
2. [Backend Testing (Python/pytest)](#backend-testing)
3. [Frontend Testing (TypeScript/Vitest)](#frontend-testing)
4. [E2E Testing (Playwright)](#e2e-testing)
5. [Mocking External APIs](#mocking-external-apis)
6. [Coverage Requirements](#coverage-requirements)
7. [Running Tests](#running-tests)
8. [Troubleshooting](#troubleshooting)

---

## Testing Philosophy

We follow the testing pyramid approach:

```
       E2E Tests (Playwright)
      /                      \
  Integration Tests (TestClient)
 /                                \
Frontend Unit (Vitest)    Backend Unit (pytest)
```

**Principles:**
- **Unit tests** should be fast, isolated, and test single units of logic
- **Integration tests** verify multiple components work together correctly
- **E2E tests** validate complete user workflows from UI to backend

**Coverage Targets:**
- Backend: 70%+ for critical paths (business logic, data processing)
- Frontend: 60%+ for business logic (components, hooks)
- E2E: Happy path + critical error scenarios

---

## Backend Testing

### Setup

Backend tests use **pytest 8.3** with async support.

```bash
cd backend
source venv/bin/activate
pytest
```

### Directory Structure

```
backend/tests/
├── unit/              # Fast, isolated tests
├── integration/       # Tests with DB/external deps
├── fixtures/          # Mock API responses
└── conftest.py        # Shared fixtures
```

### Writing Unit Tests

**Example: Testing a model**

```python
# tests/unit/test_user_model.py
import pytest
from src.models.user import User

@pytest.mark.unit
async def test_user_creation(db_session):
    user = User(
        email="test@example.com",
        hashed_password="hashed_pwd"
    )
    db_session.add(user)
    await db_session.flush()

    assert user.id is not None
    assert user.email == "test@example.com"
```

**Key Points:**
- Use `@pytest.mark.unit` for fast tests
- Use `async def` for async functions
- Use fixtures for database sessions
- Test one behavior per test function

### Writing Integration Tests

**Example: Testing an API endpoint**

```python
# tests/integration/test_auth_endpoint.py
import pytest
from httpx import AsyncClient
from src.main import app

@pytest.mark.integration
async def test_login_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "password"}
        )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
```

### Using Mock Fixtures

Mock external API calls to avoid costs and ensure test reliability:

```python
def test_ocr_processing(google_ocr_invoice_mock):
    # google_ocr_invoice_mock is a fixture from tests/fixtures/google_document_ai.py
    result = process_invoice(google_ocr_invoice_mock)
    assert result.invoice_number == "INV-2024-001"
```

### Database Testing

The `db_session` fixture:
- Creates a new transaction before each test
- Rolls back after test completes (no data persists)
- Ensures test isolation

```python
async def test_with_database(db_session):
    # Add data
    user = User(email="test@example.com")
    db_session.add(user)
    await db_session.flush()

    # Test logic
    assert user.id is not None

    # Automatic rollback after test
```

---

## Frontend Testing

### Setup

Frontend tests use **Vitest 2.1** with React Testing Library.

```bash
cd frontend
npm run test
```

### Directory Structure

```
frontend/src/
├── __tests__/
│   ├── unit/          # Component tests
│   ├── integration/   # Hook/API tests
│   └── setup.ts       # Test setup
├── components/
├── hooks/
├── mocks/             # MSW handlers
└── test-utils.tsx     # Custom render
```

### Writing Component Tests

**Example: Testing a form component**

```typescript
// __tests__/unit/declaration-form.test.tsx
import { render, screen, waitFor } from '@/test-utils'
import userEvent from '@testing-library/user-event'
import { DeclarationForm } from '@/components/declarations/declaration-form'

test('submits form with valid data', async () => {
  const user = userEvent.setup()
  const mockSubmit = vi.fn()

  render(<DeclarationForm onSubmit={mockSubmit} />)

  // Fill form
  await user.type(screen.getByLabelText(/importer name/i), 'ABC Corp')
  await user.type(screen.getByLabelText(/total value/i), '10000')

  // Submit
  await user.click(screen.getByRole('button', { name: /submit/i }))

  // Assert
  await waitFor(() => expect(mockSubmit).toHaveBeenCalled())
})
```

**Best Practices:**
- Use `getByRole` for accessible queries
- Use `userEvent` for realistic interactions
- Test user behavior, not implementation
- Wait for async updates with `waitFor()`

### Writing Hook Tests

**Example: Testing a TanStack Query hook**

```typescript
// __tests__/integration/use-declarations.test.ts
import { renderHook, waitFor } from '@testing-library/react'
import { AllTheProviders } from '@/test-utils'
import { useDeclarations } from '@/hooks/use-declarations'

test('fetches declarations successfully', async () => {
  const { result } = renderHook(() => useDeclarations(), {
    wrapper: AllTheProviders
  })

  await waitFor(() => expect(result.current.isSuccess).toBe(true))

  expect(result.current.data).toHaveLength(2)
})
```

**Key Points:**
- Wrap hooks in `AllTheProviders` for QueryClient access
- MSW automatically mocks API calls
- Test loading, success, and error states

### Mock Service Worker (MSW)

API calls are automatically mocked using MSW:

```typescript
// src/mocks/handlers.ts
import { http, HttpResponse } from 'msw'

export const handlers = [
  http.get('/api/declarations', () => {
    return HttpResponse.json([
      { id: 1, status: 'draft' },
      { id: 2, status: 'submitted' }
    ])
  })
]
```

Override handlers for specific tests:

```typescript
import { server } from '@/mocks/server'
import { http, HttpResponse } from 'msw'

test('handles API error', async () => {
  server.use(
    http.get('/api/declarations', () => {
      return HttpResponse.json({ error: 'Server error' }, { status: 500 })
    })
  )

  // Test error handling...
})
```

---

## E2E Testing

### Setup

E2E tests use **Playwright 1.48** for cross-browser testing.

```bash
# Install browsers (first time only)
npm run playwright:install

# Run tests
npm run test:e2e

# Run with UI
npm run test:e2e:ui
```

### Writing E2E Tests

**Example: Happy path test**

```typescript
// tests/e2e/happy-path.spec.ts
import { test, expect } from '@playwright/test'
import { login } from './helpers/login'

test('complete declaration workflow', async ({ page }) => {
  // Login
  await login(page, { email: 'test@example.com', password: 'pass' })

  // Navigate
  await page.goto('/declarations/new')

  // Fill form
  await page.getByLabel(/importer name/i).fill('ABC Corp')
  await page.getByRole('button', { name: /save/i }).click()

  // Assert
  await expect(page.getByText(/saved/i)).toBeVisible()
})
```

**Best Practices:**
- Use helpers (`login.ts`, `file-upload.ts`) for common actions
- Use `data-testid` for stable selectors
- Wait for elements with `expect().toBeVisible()`
- Test in Chromium, Firefox, and WebKit

### Helper Functions

Reusable helpers for common operations:

```typescript
// tests/e2e/helpers/login.ts
export async function login(page: Page, credentials: LoginCredentials) {
  await page.goto('/login')
  await page.getByLabel(/email/i).fill(credentials.email)
  await page.getByLabel(/password/i).fill(credentials.password)
  await page.getByRole('button', { name: /log in/i }).click()
  await page.waitForURL(/\/dashboard/)
}
```

### File Upload Testing

```typescript
import { uploadFile } from './helpers/file-upload'

test('uploads documents', async ({ page }) => {
  await uploadFile(page, 'invoice.pdf', {
    waitForCompletion: true,
    timeout: 30000
  })

  await expect(page.getByText(/upload.*complete/i)).toBeVisible()
})
```

### Playwright MCP Integration

**Note:** Model Context Protocol (MCP) integration for AI-assisted test generation is planned for future implementation. This will allow:

- Generating E2E tests from user stories
- Querying codebase for component selectors
- Auto-updating tests when UI changes

For now, write tests manually using the patterns above.

---

## Mocking External APIs

### Backend Mocking

Mock Google Document AI and OpenRouter in tests:

```python
# tests/fixtures/google_document_ai.py
def mock_ocr_invoice_response():
    return {
        "document": {
            "text": "INVOICE\\nINV-001...",
            "entities": [
                {"type": "invoice_number", "mentionText": "INV-001"}
            ]
        }
    }

# Use in tests
def test_invoice_processing(google_ocr_invoice_mock):
    result = extract_invoice_data(google_ocr_invoice_mock)
    assert result["invoice_number"] == "INV-001"
```

### Frontend Mocking

MSW automatically intercepts API calls:

```typescript
// src/mocks/handlers.ts
http.post('/api/declarations', () => {
  return HttpResponse.json({ id: 1, status: 'draft' })
})
```

**Why mock external APIs?**
- Avoid API costs during testing
- Ensure test reliability (no network issues)
- Test error scenarios
- Run tests offline

---

## Coverage Requirements

### Backend Coverage

Target: **70%+ for critical paths**

Run coverage report:

```bash
cd backend
source venv/bin/activate
pytest --cov=src --cov-report=html
```

View report: `backend/htmlcov/index.html`

**Focus coverage on:**
- Business logic (data extraction, validation)
- Repository methods (database operations)
- API endpoints (authentication, CRUD)
- Celery tasks (background processing)

**Exclude from coverage:**
- Migrations
- Configuration files
- `__repr__` methods

### Frontend Coverage

Target: **60%+ for business logic**

Run coverage report:

```bash
cd frontend
npm run test:coverage
```

View report: `frontend/coverage/index.html`

**Focus coverage on:**
- Form validation logic
- TanStack Query hooks
- Complex components (multi-step forms)
- Utility functions

**Exclude from coverage:**
- App router files (mostly routing)
- Simple presentational components
- Type definitions

### E2E Coverage

E2E tests focus on **user workflows**, not code coverage:

✅ **Must test:**
- Happy path: Login → Upload → Process → Review → Approve → Download
- Draft saving and resuming
- File upload errors
- Authentication failures

❌ **Don't test with E2E:**
- Edge cases (use unit tests)
- Error message wording
- Internal state

---

## Running Tests

### Local Development

```bash
# Backend tests
npm run test:backend

# Frontend tests
npm run test:frontend

# E2E tests (requires servers running)
npm run test:e2e

# All tests
npm run test:all
```

### Watch Mode

```bash
# Backend watch mode
cd backend && source venv/bin/activate && pytest --watch

# Frontend watch mode
cd frontend && npm run test:watch
```

### Specific Tests

```bash
# Backend: Run single file
pytest backend/tests/unit/test_user_model.py

# Backend: Run single test
pytest backend/tests/unit/test_user_model.py::test_user_creation

# Frontend: Run single file
cd frontend && npx vitest run src/__tests__/unit/declaration-form.test.tsx

# Playwright: Run single test
npx playwright test happy-path.spec.ts
```

### CI/CD

Tests run automatically in Docker on GitHub Actions:

```bash
# Simulate CI environment locally
docker-compose up -d
npm run test:all
docker-compose down
```

---

## Troubleshooting

### Backend Issues

**Problem:** `asyncpg.exceptions.InvalidCatalogNameError: database "logai_test" does not exist`

**Solution:**
```bash
# Create test database
docker-compose up -d postgres
docker exec -it logai_postgres psql -U postgres -c "CREATE DATABASE logai_test;"
```

**Problem:** Tests fail with `ModuleNotFoundError`

**Solution:**
```bash
# Ensure virtual environment is activated
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend Issues

**Problem:** `Cannot find module '@/...'`

**Solution:** Check `tsconfig.json` has correct path mapping:

```json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

**Problem:** MSW handlers not intercepting requests

**Solution:** Verify MSW server is started in `setup.ts`:

```typescript
import { server } from '../mocks/server'

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
```

### Playwright Issues

**Problem:** `browserType.launch: Executable doesn't exist`

**Solution:**
```bash
npm run playwright:install
```

**Problem:** Tests timing out

**Solution:** Increase timeout in test:

```typescript
test('slow operation', async ({ page }) => {
  test.setTimeout(60000)  // 60 seconds
  // ... test code
})
```

**Problem:** Can't find element

**Solution:** Use Playwright Inspector for debugging:

```bash
PWDEBUG=1 npx playwright test
```

---

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [Vitest documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/react)
- [Playwright documentation](https://playwright.dev/)
- [MSW documentation](https://mswjs.io/)

---

**Last Updated:** 2025-10-18
