# Declaration Processing Stuck Issue - Investigation Report

**Date:** 2025-11-04
**Issue:** All declarations stuck at "Processing LLM" status

## Summary

Three critical issues causing declarations to appear stuck:
1. **Celery soft timeout (270s)** - LLM processing takes longer than timeout
2. **Status enum mismatch** - Backend uses `PROCESSING_LLM`, frontend doesn't recognize it
3. **Empty processing logs** - Worker doesn't populate `processing_log` field

## Investigation Details

### Test Declaration
- **ID:** e3a8eca9-05fc-4fd9-9af9-87a81f146908
- **Database Status:** PROCESSING_LLM
- **Progress:** 0.4 (40%)
- **Celery Task ID:** 6fc73fb7-5604-4420-9b43-dc691abc0462
- **Processing Log:** Empty `[]`

### UI Symptoms
- Progress shows "NaN%" (calculation error)
- Status displays "Uploading" instead of actual status
- Activity log shows "Processing has not started yet..."
- Elapsed time continues ticking (6:44 when checked)

### Root Cause Analysis

#### 1. Celery Soft Time Limit Exceeded

**File:** `backend/src/core/celery_app.py:46-47`

```python
task_time_limit=300,  # 5 minutes hard limit
task_soft_time_limit=270,  # 4.5 minutes soft limit (warning)
```

**Timeline from Logs:**
```
08:21:33 - Task received
08:21:34 - OCR processing complete (cache hits)
08:21:34 - LLM extraction started
08:21:35 - HTTP request to OpenRouter started
08:26:03 - SOFT TIMEOUT (270s exceeded)
```

**Error:**
```
billiard.exceptions.SoftTimeLimitExceeded: SoftTimeLimitExceeded()
```

**Issue:** LLM extraction via OpenRouter takes >4.5 minutes, exceeding soft limit. Task is killed but database status remains `PROCESSING_LLM`.

#### 2. Status Enum Mismatch

**Backend** (`backend/src/schemas/declaration.py:11-21`):
```python
class DeclarationStatus(str, Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    PROCESSING_OCR = "PROCESSING_OCR"  # ← Backend only
    PROCESSING_LLM = "PROCESSING_LLM"  # ← Backend only
    VALIDATING = "VALIDATING"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"
```

**Frontend** (`frontend/src/types/declaration.ts:5-13`):
```typescript
export enum DeclarationStatus {
  UPLOADED = 'UPLOADED',
  PROCESSING = 'PROCESSING',
  VALIDATING = 'VALIDATING',
  READY_FOR_REVIEW = 'READY_FOR_REVIEW',
  APPROVED = 'APPROVED',
  REJECTED = 'REJECTED',
  FAILED = 'FAILED',
}
```

**Issue:** Frontend doesn't have `PROCESSING_OCR` or `PROCESSING_LLM`, causing:
- Status mapping to fail
- Progress calculation to return NaN
- UI displaying wrong stage

#### 3. Empty Processing Logs

**Database Check:**
```sql
processing_log length: 2  -- which is '[]' in JSONB
```

**Issue:** Worker doesn't write log entries during processing stages. The `processing_log` field exists but is never populated.

## Solutions Required

### 1. Increase Celery Timeout

**File:** `backend/src/core/celery_app.py`

**Change:**
```python
# Current (too short)
task_time_limit=300,  # 5 minutes hard limit
task_soft_time_limit=270,  # 4.5 minutes soft limit

# Recommended (for LLM processing)
task_time_limit=1800,  # 30 minutes hard limit
task_soft_time_limit=1500,  # 25 minutes soft limit (warning)
```

**Rationale:** OpenRouter LLM calls can take 5-10 minutes depending on model and complexity.

### 2. Fix Status Enum Mismatch

**Option A - Remove Backend Substatus** (Recommended):
Remove `PROCESSING_OCR` and `PROCESSING_LLM` from backend, use only `PROCESSING`.

**File Changes:**
- `backend/src/schemas/declaration.py` - Remove substatus from enum
- `backend/src/workers/declaration_processor.py` - Use `PROCESSING` instead

**Option B - Add to Frontend:**
Add `PROCESSING_OCR` and `PROCESSING_LLM` to frontend enum.

**File:** `frontend/src/types/declaration.ts`

**Recommendation:** Option A is better - simpler and matches original design.

### 3. Implement Processing Log Entries

**File:** `backend/src/workers/declaration_processor.py`

**Add log entries at each stage:**
```python
async def _log_entry(db: AsyncSession, declaration_id: UUID, level: str, message: str, details: dict = None):
    """Add entry to processing_log"""
    await db.execute(
        update(Declaration)
        .where(Declaration.id == declaration_id)
        .values(processing_log=func.jsonb_insert(
            Declaration.processing_log,
            '{-1}',
            {
                'timestamp': datetime.utcnow().isoformat(),
                'level': level,
                'message': message,
                'details': details
            }
        ))
    )
    await db.commit()
```

**Add calls:**
- OCR start/complete per file
- LLM extraction start/complete
- Validation start/complete
- Excel generation start/complete

### 4. Better Timeout Handling

**Current behavior:** Task killed, status stays `PROCESSING_LLM`, no error message.

**Improved behavior:**
- Catch `SoftTimeLimitExceeded`
- Set status to `FAILED`
- Set `processing_error` message
- Log timeout event

## Affected Declarations

All three declarations in system are affected:
1. `e3a8eca9-05fc-4fd9-9af9-87a81f146908` (checked)
2. `2a5b04a6-36a1-466a-bebf-a9a67b9cbd99`
3. `6ad7eca2-750a-4559-98e4-4cdd5b35ea28`

All show:
- Status: PROCESSING_LLM (database)
- Progress: 0.4 (40%)
- Empty processing logs
- Celery timeout errors in worker logs

## Recommended Fix Priority

1. **CRITICAL:** Increase Celery timeout (immediate fix to unblock processing)
2. **HIGH:** Remove status enum mismatch (fixes UI display)
3. **HIGH:** Implement processing log entries (improves monitoring)
4. **MEDIUM:** Better timeout error handling (improves debugging)

## Files to Modify

1. `backend/src/core/celery_app.py` - Increase timeouts
2. `backend/src/schemas/declaration.py` - Remove substatus enum values
3. `backend/src/workers/declaration_processor.py` - Use PROCESSING status, add logging
4. `frontend/src/types/declaration.ts` - (No change needed if Option A chosen)
