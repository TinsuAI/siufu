# Core Workflows

## Workflow 1: Complete Declaration Processing (Happy Path)

```mermaid
sequenceDiagram
    actor User as 👤 Customs Processor
    participant Browser as Next.js Frontend
    participant API as FastAPI Backend
    participant Celery as Celery Worker
    participant Redis as Redis Cache
    participant DB as PostgreSQL
    participant DocAI as Google Document AI
    participant GPT5 as OpenRouter GPT-5

    User->>Browser: Upload 6 files
    Browser->>API: POST /api/declarations/upload
    API->>DB: Create Declaration (UPLOADED)
    API-->>Browser: 201 Created {declaration_id}

    Browser->>API: POST /api/declarations/{id}/process
    API->>Redis: Enqueue process_declaration_task
    API-->>Browser: 202 Accepted

    Redis->>Celery: Dequeue task
    Celery->>DB: Update status: PROCESSING

    loop For each PDF (AN, BOL, CO, Invoice)
        Celery->>Redis: Check cache
        alt Cache Miss
            Celery->>DocAI: Process document
            DocAI-->>Celery: OCR results
            Celery->>Redis: Cache (24hr TTL)
        end
    end

    Celery->>GPT5: Extract (Flagship model)
    GPT5-->>Celery: Structured JSON

    Celery->>GPT5: Validate (Nano model)
    GPT5-->>Celery: Validation warnings

    Celery->>DB: Query tariff rates
    Celery->>Celery: Calculate taxes
    Celery->>Celery: Generate Excel

    Celery->>DB: Update status: READY_FOR_REVIEW

    loop Every 2 seconds
        Browser->>API: GET /api/declarations/{id}/status
        API-->>Browser: {status, progress}
    end

    Browser->>Browser: Auto-redirect to review screen
    User->>Browser: Review & edit fields
    Browser->>API: PATCH /api/declarations/{id} (auto-save)

    User->>Browser: Click "Approve"
    Browser->>API: POST /api/declarations/{id}/approve

    User->>Browser: Download Excel
    Browser->>API: GET /api/declarations/{id}/export
    API-->>Browser: CD.xlsx file
```

**Timing Breakdown (Target <90s):**
- Upload: 5-10s
- OCR (4 PDFs): 20-30s
- LLM Extraction: 25-40s
- Validation: 5-10s
- Excel Generation: 3-5s
- **Total**: 58-95s (avg 75s)

---

## Workflow 2: Auto-Save with Correction Tracking

This workflow shows automatic capture of user corrections for learning.

```mermaid
sequenceDiagram
    actor User
    participant Browser
    participant Form as React Hook Form
    participant API
    participant Tracker as Correction Tracker
    participant DB

    User->>Form: Edit field value
    Form->>Form: Wait 5s (debounce)
    Form->>API: PATCH /api/declarations/{id}

    API->>DB: SELECT current draft_data
    API->>API: Compare old vs new
    API->>Tracker: capture_correction(...)
    Tracker->>DB: INSERT INTO corrections
    API->>DB: UPDATE draft_data

    API-->>Browser: 200 OK
    Browser->>Form: Show "Saved" indicator
```

---
