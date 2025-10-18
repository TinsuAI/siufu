# Components

Based on architectural patterns, tech stack, and data models, the system is organized into 8 major components spanning frontend, backend, and worker layers.

## Frontend Components

### 1. Review Interface Component

**Responsibility:** Provides the side-by-side PDF viewer and editable declaration form for human-in-the-loop review.

**Key Interfaces:**
- `DeclarationReviewPage` - Main page at `/declarations/[id]/review`
- `PDFViewer` - Canvas-based PDF rendering with zoom, navigation, source highlighting
- `DeclarationForm` - React Hook Form with auto-save, confidence color-coding
- `ValidationWarningsPanel` - Collapsible panel showing cross-document issues

**Dependencies:**
- FastAPI backend via `/api/declarations/{id}`
- TanStack Query for server state management
- react-pdf library for PDF rendering
- Zod schemas for form validation

**Technology Stack:**
- React 19 Server Components for shell
- Client Components for interactive form/PDF
- Zustand for UI state (PDF zoom level, active tab)
- React Hook Form + Zod for form management

---

### 2. Upload & Processing Component

**Responsibility:** Handles file upload workflow (drag-drop validation) and displays real-time processing status.

**Key Interfaces:**
- `UploadPage` - Drag-drop interface for 6 files
- `FileDropZone` - Individual drop zone with validation
- `ProcessingStatusPage` - Stepper UI showing OCR → LLM → Validation stages

**Dependencies:**
- FastAPI backend via `/api/declarations/upload`
- `/api/declarations/{id}/status` (polling every 2s)

---

### 3. Declarations Dashboard Component

**Responsibility:** Lists all declarations with filtering, search, and pagination.

**Key Interfaces:**
- `DeclarationsListPage` - Main dashboard at `/declarations`
- `DeclarationTable` - Sortable table with status badges
- `SearchFilters` - Status dropdown, date range, search input

---

### 4. Analytics & Knowledge Base Component

**Responsibility:** Admin interface for correction analytics and knowledge base version management.

**Key Interfaces:**
- `AnalyticsPage` - Dashboard with charts and KPIs
- `KnowledgeBasePage` - Upload interface
- `VersionHistoryModal` - Rollback UI

---

## Backend Components

### 5. API Gateway & Auth Component

**Responsibility:** FastAPI application entry point. Handles routing, authentication, request validation, and error handling.

**Key Interfaces:**
- `POST /api/auth/login` - JWT token generation
- `AuthMiddleware` - JWT validation on protected routes
- `ErrorHandler` - RFC 7807 Problem Details formatter
- `RateLimiter` - 100 req/min per user

**Dependencies:**
- PostgreSQL via SQLAlchemy ORM
- Redis for rate limit counters
- python-jose for JWT encode/decode
- bcrypt for password verification

---

### 6. Declaration Processing Service

**Responsibility:** Orchestrates AI processing pipeline. Manages OCR, LLM extraction, fuzzy matching, validation, and Excel generation.

**Key Interfaces:**
- `process_declaration_task(declaration_id)` - Main Celery task
- `OCRService.process_document(pdf_path)` - Google Document AI integration
- `ExtractionService.extract_structured_data(ocr_result)` - GPT-5 integration
- `ValidationService.cross_validate(extracted_data)` - Consistency checks
- `ExcelService.generate_cd_file(declaration_data)` - openpyxl export

**Dependencies:**
- Google Document AI Python client
- OpenRouter HTTP client (httpx async)
- spaCy for NLP validation
- rapidfuzz for Good List matching
- openpyxl for Excel generation
- PostgreSQL for data persistence
- Redis for caching OCR results (24hr TTL)

**Technology Stack:**
- Celery 5.4 for task queue
- Async Python (asyncio) for concurrent AI API calls
- Smart model routing logic (Flagship/Mini/Nano selection)

---

### 7. Knowledge Base Repository

**Responsibility:** Manages Good List and Tariff data with versioning. Provides fuzzy matching and tariff lookup services.

**Key Interfaces:**
- `GoodListRepository.search_products(description, threshold=0.85)` - Fuzzy match
- `TariffRepository.lookup_rate(hs_code, trade_agreement)` - Rate lookup with fallback
- `KnowledgeBaseImporter.import_excel(file_path, type)` - Async Celery task

---

### 8. Correction Tracking Service

**Responsibility:** Captures user edits as corrections for learning. Compares original vs corrected values when declaration is updated.

**Key Interfaces:**
- `CorrectionTracker.capture_correction(...)` - Creates Correction record
- `CorrectionAnalytics.get_stats(start_date, end_date)` - Aggregates for dashboard
- `ConfidenceAdjuster.apply_adjustments(field_name)` - Reduces confidence for frequently-corrected fields

---
