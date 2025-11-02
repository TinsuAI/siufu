# Dev Handoff: LLM Test Fixture Loading Issue

**Date**: 2025-11-01
**From**: Quinn (Test Architect)
**To**: Dev Agent
**Priority**: P0 - CRITICAL
**Estimated Complexity**: Medium (2-4 hours)
**STATUS**: ✅ RESOLVED (2025-11-01)

---

## Resolution Summary

**Fixed By**: James (Dev Agent)
**Solution**: Applied proven Google fixtures pattern - converted OpenRouter fixtures to plain functions and wrapped them in conftest.py
**Result**: 14/15 LLM tests now PASS (93% success rate), down from 15 ERROR states

### Changes Made

1. **backend/tests/fixtures/openrouter.py**:
   - Removed all `@pytest.fixture` decorators
   - Converted 8 fixtures to plain Python functions

2. **backend/tests/conftest.py**:
   - Removed non-working `pytest_plugins` configuration
   - Imported plain functions from openrouter.py
   - Created 8 wrapper fixtures using `@pytest.fixture` decorator
   - Matches proven Google fixtures pattern exactly

### Test Results

- ✅ LLM Tests: 14 PASS, 1 FAIL (fixture issue resolved, 1 test has wrong mock data)
- ✅ Story 3.3.1 Tests: 22 PASS, 1 SKIPPED (no regressions)
- ✅ Fixtures now visible in `pytest --fixtures` output

**Files Modified**:
- `backend/tests/fixtures/openrouter.py` (line 8, 83, 133, 153, 201, 211, 231, 242)
- `backend/tests/conftest.py` (lines 13-30, 150-196)

---

## Issue Summary

**Problem**: 15 LLM service tests fail with `fixture 'sample_ocr_result' not found` error, even though the fixtures are defined in `tests/fixtures/openrouter.py`.

**Impact**: Cannot run LLM service tests, blocking verification of LLM extraction functionality.

**Current State**:
- ✅ Story 3.3.1 tests: ALL PASSING (22/22)
- ❌ LLM service tests: 11 ERROR, 4 PASS
- 📊 Overall: 72 failed, 80 passed, 13 skipped, 15 errors

---

## Root Cause Analysis

### Symptoms

1. **Fixtures exist but aren't discovered by pytest**:
   - Fixtures defined in `/backend/tests/fixtures/openrouter.py` with `@pytest.fixture` decorators
   - Direct Python import works: `from tests.fixtures.openrouter import sample_ocr_result` ✅
   - Pytest runtime discovery fails: fixtures not in `pytest --fixtures` output ❌

2. **Error message**:
   ```
   E       fixture 'sample_ocr_result' not found
   >       available fixtures: _session_event_loop, anyio_backend, ...
   ```

3. **Contrast with working Google fixtures**:
   - Google Document AI fixtures ARE discovered
   - They work because they're re-wrapped in conftest.py as new fixtures
   - Example: `conftest.py` defines `google_ocr_invoice_mock()` that calls `mock_ocr_invoice_response()`

### Investigation Performed

**Attempted Fixes (by Quinn - Test Architect)**:

1. ✅ Created `/backend/tests/fixtures/__init__.py` (missing package marker)
2. ✅ Added explicit imports in `conftest.py`:
   ```python
   from tests.fixtures.openrouter import (
       sample_ocr_result,
       mock_openrouter_response_success,
       ...
   )
   ```
3. ✅ Tried `pytest_plugins` configuration:
   ```python
   pytest_plugins = ["tests.fixtures.openrouter"]
   ```
4. ❌ None of these worked - fixtures still not discovered

**Verification**:
- Direct import works: `docker compose exec backend python -c "from tests.fixtures.openrouter import sample_ocr_result"` ✅
- Conftest import works: `from tests.conftest import *` ✅
- Pytest discovery fails: fixtures not available at test runtime ❌

---

## Affected Files

### Modified (Safe to Keep or Revert)
- `/backend/tests/fixtures/__init__.py` - CREATED (empty package marker - safe)
- `/backend/tests/conftest.py` - MODIFIED (added `pytest_plugins`, can revert if needed)

### Need Investigation
- `/backend/tests/fixtures/openrouter.py` - Contains 8 fixtures that aren't being discovered
- `/backend/tests/unit/test_llm_service.py` - 11 tests failing due to missing fixtures

---

## Fixture Definitions

**In `/backend/tests/fixtures/openrouter.py`** (8 fixtures):

```python
@pytest.fixture
def mock_openrouter_response_success() -> Dict[str, Any]:
    """Mock successful OpenRouter API response with ExtractedData JSON"""
    ...

@pytest.fixture
def mock_openrouter_response_with_markdown() -> Dict[str, Any]:
    ...

@pytest.fixture
def mock_openrouter_response_invalid_json() -> Dict[str, Any]:
    ...

@pytest.fixture
def sample_ocr_result():
    """Sample OCR result for testing"""
    from src.schemas.ocr import OCRResult, KeyValuePair, Table
    return OCRResult(...)

@pytest.fixture
def mock_openrouter_client_success(monkeypatch, mock_openrouter_response_success):
    ...

@pytest.fixture
def mock_openrouter_client_rate_limit(monkeypatch):
    ...

@pytest.fixture
def mock_openrouter_client_timeout(monkeypatch):
    ...

@pytest.fixture
def mock_openrouter_client_auth_error(monkeypatch):
    ...
```

---

## Recommended Solution Approaches

### Option 1: Wrap Fixtures in conftest.py (Like Google Fixtures)

**Pattern from working Google fixtures**:

```python
# In conftest.py
from tests.fixtures.google_document_ai import mock_ocr_invoice_response

@pytest.fixture
def google_ocr_invoice_mock():
    """Fixture for mocked Google Document AI Invoice response."""
    return mock_ocr_invoice_response()
```

**Apply same pattern for OpenRouter fixtures**:

```python
# In conftest.py
from tests.fixtures.openrouter import (
    mock_openrouter_response_success as _mock_openrouter_response_success,
    sample_ocr_result as _sample_ocr_result,
)

@pytest.fixture
def mock_openrouter_response_success():
    return _mock_openrouter_response_success()

@pytest.fixture
def sample_ocr_result():
    return _sample_ocr_result()
```

**Pros**: Proven to work (Google fixtures use this pattern)
**Cons**: Code duplication, need to wrap all 8 fixtures

---

### Option 2: Fix pytest_plugins Configuration

**Current attempt in conftest.py**:
```python
pytest_plugins = ["tests.fixtures.openrouter"]
```

**Investigate**:
- Check pytest-asyncio compatibility with plugin loading
- Verify session-scoped event loop doesn't interfere
- Try different plugin path formats:
  - `"tests.fixtures.openrouter"`
  - `"fixtures.openrouter"`
  - Direct fixture imports

**Debugging commands**:
```bash
# List available fixtures
docker compose exec backend pytest --fixtures tests/unit/test_llm_service.py | grep -E "sample_ocr|mock_openrouter"

# Verbose pytest output
docker compose exec backend pytest tests/unit/test_llm_service.py::test_extract_structured_data_success -v --setup-show

# Check conftest loading
docker compose exec backend pytest --collect-only tests/unit/test_llm_service.py
```

---

### Option 3: Move Fixtures to conftest.py Directly

**Simplest solution**: Move all fixture definitions from `openrouter.py` into `conftest.py`

**Pros**: Guaranteed to work
**Cons**: Makes conftest.py larger, less modular

---

## Test Commands

**Verify fix works**:
```bash
# Test single LLM test
docker compose exec backend pytest tests/unit/test_llm_service.py::test_extract_structured_data_success -v

# Test all LLM tests
docker compose exec backend pytest tests/unit/test_llm_service.py -v

# Verify no regressions
docker compose exec backend pytest tests/security/test_upload_security.py tests/unit/test_declaration_processor.py -v
```

**Success criteria**:
- ✅ All 15 LLM service tests should show status (PASS/FAIL, not ERROR)
- ✅ Fixtures should appear in `pytest --fixtures` output
- ✅ Story 3.3.1 tests remain passing (22/22)

---

## Context: Why This Matters

**Story 3.3.1**: ✅ PASS (production ready)
**LLM Tests**: ❌ Blocked by fixture loading

**Impact on broader test suite**:
- Current: 80 passing, 72 failing, 15 errors
- After LLM fix: Estimated +11 tests discoverable (may pass or fail, but at least runnable)

**Related issues**:
- P1: Async event loop isolation (affects ~40 integration tests)
- P2: Test isolation / shared state (affects ~17 tests)

This P0 fix unblocks LLM service testing and may reveal additional issues once tests can actually run.

---

## Files to Review

1. `/backend/tests/fixtures/openrouter.py` - Source of fixtures
2. `/backend/tests/conftest.py` - Pytest configuration
3. `/backend/tests/fixtures/google_document_ai.py` - Working fixture pattern example
4. `/backend/tests/unit/test_llm_service.py` - Tests that need these fixtures

---

## Success Handoff Checklist

After fixing:
- [ ] All 15 LLM service tests run (not ERROR)
- [ ] Fixtures visible in `pytest --fixtures` output
- [ ] Story 3.3.1 tests still pass (regression check)
- [ ] Document solution in `backend/tests/README.md`
- [ ] Update this handoff with "RESOLVED" status

---

**Quinn's Note**: I've done my due diligence as Test Architect - identified the issue, attempted standard fixes, and documented thoroughly. This needs dev-level pytest expertise to resolve properly. Good luck! 🧪
