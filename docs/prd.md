# Customs Declaration Automation Platform - Product Requirements Document (PRD)

**Document Version:** 1.1
**Date:** 2025-10-17
**Status:** Ready for Architecture Phase
**Owner:** Product Management Team

---

## Goals and Background Context

### Goals

- Successfully process 1,000+ customs declarations per month with 95%+ auto-extraction accuracy by Week 24
- Reduce customs declaration processing time by 90% (from 45 minutes to under 5 minutes including HITL review)
- Achieve first client production deployment within 8 weeks of development start
- Maintain operational cost under $50/month for processing 1,000 declarations
- Build continuous learning system that improves accuracy over time through user corrections
- Enable first client to independently manage knowledge base (Good List, EXIM Tariff updates)
- Establish foundation for multi-client SaaS platform expansion in 2026
- Deliver tangible ROI: $500/month MRR from first client within 3 months of launch

### Background Context

The Customs Declaration Automation Platform addresses a critical bottleneck in logistics operations: manual customs declaration processing. Vietnamese logistics companies currently spend 30-60 minutes per declaration extracting data from source documents (Arrival Notice, Bill of Lading, Certificate of Origin, Invoice) and cross-referencing knowledge base files (Good List, EXIM Tariff) to manually populate complex Excel templates. This tedious process costs our first client 500-1,000 staff hours monthly, creates 3-5% error rates, and limits their ability to scale operations.

Our comprehensive brainstorming session (2025-10-17) analyzed actual sample declaration files and identified that a hybrid AI approach—combining Google Document AI OCR, GPT-5 LLM extraction, and spaCy NLP validation—can achieve 85%+ accuracy immediately with a clear path to 95%+ through continuous learning. By implementing a Human-in-the-Loop review interface, we maintain accuracy while building a learning dataset that improves the system over time. The MVP focuses on delivering a complete end-to-end workflow running on Docker for on-premise deployment, meeting client data sovereignty requirements while leveraging cloud AI APIs for maximum accuracy.

### Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-10-17 | 1.0 | Initial PRD created from Project Brief | John (PM) |
| 2025-10-17 | 1.1 | Added Stories 1.0, 1.0.5, 4.6 per PO validation recommendations | Sarah (PO) |
| 2025-10-30 | 1.2 | Updated Stories 1.6 & 3.3: Good List/EXIM Tariff now knowledge base only (not uploaded per declaration), CO accepts multiple files, all file sizes increased to 20MB | John (PM) |

---

## Requirements

### Functional Requirements

**Document Processing:**

- **FR1:** System shall accept upload of 4 required source documents per declaration (AN.pdf, BOL.pdf, CO.pdf [multiple files accepted], INVOICE.pdf/jpg) via drag-and-drop interface with file type and count validation (max 20MB per file). Good List and EXIM Tariff are managed as knowledge base data, not uploaded per declaration.
- **FR2:** System shall process document PDFs/images using Google Document AI Form Parser to extract text, tables, and key-value pairs with confidence scores
- **FR3:** System shall use GPT-5 to extract structured data from OCR results including product descriptions, quantities, prices, HS codes, company names, and dates, returning JSON with per-field confidence scores
- **FR4:** System shall fuzzy match extracted product descriptions against Good List database using rapidfuzz with 85% threshold to suggest HS codes
- **FR5:** System shall cross-validate data consistency across documents (Invoice total = CO total, BOL containers = AN containers, HS codes match between Invoice and CO, dates follow logical sequence) and flag inconsistencies for user review with low confidence scores

**Declaration Generation:**

- **FR6:** System shall generate Vietnamese customs declaration Excel file (CD.xlsx) with all extracted data mapped to proper fields
- **FR7:** System shall apply tariff rates from EXIM-Tariff database based on extracted HS codes
- **FR8:** System shall automatically calculate VAT and import duties based on applied tariff rates and invoice values
- **FR9:** System shall allow users to download final approved declaration as properly formatted Excel file matching Vietnamese customs CD.xlsx template

**Human-in-the-Loop Review:**

- **FR10:** System shall display side-by-side view showing source documents (with PDF viewer) and generated declaration draft
- **FR11:** System shall color-code fields by confidence level (green >90%, yellow 70-90%, red <70%)
- **FR12:** System shall support inline editing of any field with auto-save functionality
- **FR13:** System shall allow users to click any field to jump to corresponding source location in PDF
- **FR14:** System shall require user to explicitly approve or reject declaration before export

**Learning System:**

- **FR15:** System shall capture all user corrections to database with metadata (original value, corrected value, field name, confidence score, timestamp, user ID)
- **FR16:** System shall flag user corrections for potential knowledge base updates
- **FR17:** System shall allow users to upload updated Good List and EXIM-Tariff files to replace existing knowledge base data

**User Management:**

- **FR18:** System shall provide user authentication with email/password login
- **FR19:** System shall maintain user session for duration of work (configurable timeout)
- **FR20:** System shall track which user processed and approved each declaration for audit purposes

### Non-Functional Requirements

**Performance:**

- **NFR1:** System shall process one declaration from upload to draft ready in under 90 seconds (excluding user review time)
- **NFR2:** System shall render PDF documents within 3 seconds for documents up to 10 pages
- **NFR3:** System shall generate final Excel export within 5 seconds of user approval
- **NFR4:** System shall support 20 concurrent users without performance degradation
- **NFR5:** System shall load web pages within 2 seconds on standard broadband connection

**Reliability:**

- **NFR6:** System shall handle graceful degradation if external APIs (Google Document AI, OpenRouter) experience downtime
- **NFR7:** System shall auto-save user edits every 5 seconds to prevent data loss
- **NFR8:** System shall provide clear error messages when file upload, processing, or export fails
- **NFR9:** System shall maintain 99% uptime during business hours (8am-8pm Vietnam time)

**Security:**

- **NFR10:** System shall encrypt data at rest in PostgreSQL database
- **NFR11:** System shall use HTTPS for all production deployments
- **NFR12:** System shall authenticate API requests using JWT tokens
- **NFR13:** System shall store sensitive credentials (API keys) in environment variables, never in code
- **NFR14:** System shall provide audit trail showing all changes to declarations (who, what, when)

**Usability:**

- **NFR15:** New users shall be able to process their first declaration within 15 minutes without training
- **NFR16:** System UI shall be intuitive for users with basic Excel proficiency
- **NFR17:** System shall provide clear visual indicators for required actions (fields needing review, approval pending)

**Scalability:**

- **NFR18:** System architecture shall support future expansion to multi-tenant SaaS (even though MVP is single-tenant)
- **NFR19:** Database schema shall support 10,000+ declarations without performance degradation
- **NFR20:** System shall process declarations asynchronously to allow users to continue working during processing

**Cost Efficiency:**

- **NFR21:** System shall implement smart model routing (GPT-5 Flagship for complex, Mini for simple, Nano for validation) to minimize LLM costs
- **NFR22:** System shall cache OCR results to avoid redundant API calls if user re-uploads same document
- **NFR23:** System shall target operational cost under $0.05 per declaration for API usage

**Deployment:**

- **NFR24:** System shall run entirely within Docker Compose with all dependencies containerized
- **NFR25:** System shall store all data (database, uploaded files, cache) in Docker volumes for persistence
- **NFR26:** System shall require only Docker installation and API keys for deployment (no complex infrastructure)
- **NFR27:** System shall provide health check endpoints for monitoring service availability

**Maintainability:**

- **NFR28:** System shall use TypeScript for frontend code with strict type checking enabled
- **NFR29:** System shall use Python type hints throughout backend codebase
- **NFR30:** System shall generate API documentation automatically using FastAPI's built-in OpenAPI support

---

## User Interface Design Goals

### Overall UX Vision

The platform UX prioritizes **speed and trust** for customs processing specialists who need to review AI-generated declarations quickly and confidently. The interface follows a **guided workflow paradigm**: upload → process → review → approve → export, with clear visual states at each step. Users should feel in control—the AI assists but never makes final decisions without human approval. The design philosophy is "trust through transparency": show confidence scores, highlight areas needing attention, and make source documents easily accessible for verification. Visual hierarchy guides users to focus on exceptions (low-confidence fields, validation errors) rather than requiring review of every field.

### Key Interaction Paradigms

**Side-by-Side Verification:**
- Primary interaction model shows source PDFs on left, generated declaration on right
- Click any declaration field to jump to corresponding location in source document
- Supports rapid visual verification without context switching

**Confidence-Driven Review:**
- Color-coded fields (green/yellow/red) allow users to prioritize low-confidence areas
- Users can filter view to show only fields requiring attention (yellow/red)
- High-confidence fields (green) can be batch-approved with single click

**Inline Editing:**
- All declaration fields editable directly without modal dialogs
- Auto-save every 5 seconds prevents data loss
- Clear visual indicator when edits are pending save vs saved

**Progressive Disclosure:**
- Default view shows essential fields, advanced details collapsed
- Power users can expand sections for full control
- Validation errors surface prominently, but detailed rules available on hover/click

### Core Screens and Views

**Login Screen:**
- Simple email/password authentication
- "Remember me" option for convenience
- Clear error messages for failed login

**Upload Screen:**
- Drag-and-drop zone for all 4 required source documents (AN, BOL, CO [multiple], INVOICE)
- Visual checklist showing which files uploaded (AN ✓, BOL ✓, CO ✓×2, INVOICE ✓)
- File type validation with helpful error messages ("Expected .pdf, got .docx")
- "Process Declaration" button disabled until all 4 required file types uploaded (at least 1 CO required)

**Processing Status Screen:**
- Real-time progress indicator showing current step (OCR → Extraction → Validation → Generation)
- Estimated time remaining
- Option to navigate away and return (background processing)

**Review & Edit Screen (Primary Workspace):**
- Split view: Source documents (left 40%), Declaration form (right 60%)
- PDF viewer with zoom, page navigation, search
- Declaration form with color-coded fields and inline editing
- Validation warnings panel showing cross-document inconsistencies
- Sticky header with "Approve" and "Reject" action buttons

**History/Dashboard Screen (Post-MVP consideration):**
- List of processed declarations with status, date, user
- Search and filter capabilities
- Quick re-export for previously approved declarations

### Accessibility: WCAG AA

- Keyboard navigation for all core workflows (upload, review, approve)
- Screen reader support for confidence scores and validation warnings
- Color coding supplemented with icons (not color-only indicators)
- Minimum contrast ratio 4.5:1 for text
- Focus indicators clearly visible for keyboard users
- Form labels properly associated with inputs

### Branding

**Minimal, professional design with customs/logistics aesthetic:**
- Color palette: Navy blue (trust, official), green (approved/success), amber (caution), red (error)
- Typography: Clean sans-serif (Inter or similar), optimized for readability of dense tabular data
- Use shadcn/ui components with minimal customization for rapid development
- Logo placeholder (client can provide, or simple text-based branding for MVP)
- No heavy animations or decorative elements—focus on data clarity and speed

### Target Device and Platforms: Web Responsive

**Primary:** Desktop browsers (1920x1080 and above)
- Chrome 120+, Firefox 120+, Safari 17+ (last 2 major versions)
- Optimized for large screens where users can see source docs + declaration simultaneously

**Secondary:** Tablets (iPad 10"+, landscape orientation)
- Responsive layout: Source docs and declaration stack vertically or use tabs
- Touch-friendly tap targets (44x44px minimum)

**Out of Scope for MVP:** Mobile phones
- Screen size insufficient for side-by-side PDF + form review
- Mobile app planned for Phase 2 (manager approval workflow)

**Platform Support:**
- Windows 10+, macOS 13+, Linux (Ubuntu 22.04+)
- No browser plugins required (pure web application)
- Minimum screen resolution: 1366x768 (acceptable but suboptimal experience)

---

## Technical Assumptions

### Repository Structure: Monorepo

The project will use a **monorepo structure** with separate `frontend/` and `backend/` directories within a single Git repository. This approach provides:

- **Unified versioning:** Single source of truth for releases, tags, and deployment coordination
- **Simplified dependency management:** Shared Docker Compose configuration, unified CI/CD pipeline
- **Atomic changes:** Frontend and backend changes for a feature can be committed together
- **Developer efficiency:** Single clone, single IDE workspace, easier refactoring across boundaries

**Structure:**
```
logai/
├── frontend/          # Next.js application
├── backend/           # FastAPI application
├── docker-compose.yml # All 5 services defined
├── .env.example       # Environment variable template
└── docs/              # Shared documentation
```

**Rationale:** With only 2 developers for 8 weeks, monorepo reduces coordination overhead compared to polyrepo. Future multi-tenant SaaS can still modularize within monorepo using workspace tooling.

### Service Architecture

**Hybrid: Monolithic application with external cloud AI services**

The system follows a **pragmatic monolith** architecture for MVP with strategic use of cloud AI APIs:

**Core Services (Dockerized):**
- **Frontend Service:** Next.js 15.5.6 server (port 3000) serving React 19.2 application
- **Backend Service:** FastAPI 0.119 API server (port 8000) handling all business logic
- **Celery Worker:** Background task processor for async declaration processing
- **PostgreSQL 18.0:** Primary database (port 5432) for all persistent data
- **Redis 7.4.1:** Message broker for Celery + caching layer (port 6379)

**External Cloud APIs (called from Backend/Celery):**
- **Google Document AI:** OCR and form parsing (pretrained-foundation-model-v1.5.1-2025-08-07)
- **OpenRouter (GPT-5):** LLM-powered extraction and validation

**Rationale:**
- Monolithic backend simplifies deployment for single-client MVP (avoid microservices complexity)
- Celery worker enables async processing (NFR20) without over-engineering
- Cloud AI APIs provide best-in-class accuracy without GPU infrastructure
- All services containerized for portability and consistent development/production environments
- Architecture supports future extraction of services (e.g., separate processing-service) when scaling to multi-tenant

**Not using:** Serverless functions, Kubernetes, microservices (YAGNI for MVP)

### Testing Requirements

**Unit + Integration Testing** with pragmatic coverage goals:

**Backend (Python/FastAPI):**
- **Unit tests:** pytest for business logic, data validation, utility functions
- **Integration tests:** Test full API endpoints with test database (pytest + TestClient)
- **Coverage target:** 70%+ for critical paths (extraction logic, validation, Excel generation)
- **Mocking strategy:** Mock external APIs (Google Document AI, OpenRouter) to avoid cost and flakiness

**Frontend (TypeScript/Next.js):**
- **Component tests:** Vitest + React Testing Library for UI components
- **Integration tests:** Playwright for critical user workflows (upload → review → export)
- **Coverage target:** 60%+ for business logic, skip pure presentational components
- **Visual regression:** Not in MVP (manual QA sufficient for single-client)

**E2E Testing:**
- **Playwright tests:** Cover happy path (successful declaration processing end-to-end)
- **Test data:** Use anonymized versions of sample declarations from `resources/sample/`
- **Run frequency:** Pre-deployment and on-demand (not every commit due to API costs)

**Manual Testing:**
- **Client UAT:** Client will perform acceptance testing with real declarations (Week 9-10)
- **Exploratory testing:** Developers manually test edge cases before client handoff

**Not included in MVP:**
- Load testing (single-client, 20 concurrent users max)
- Security penetration testing (post-MVP)
- Automated performance regression testing

**Rationale:** Balance test coverage with 8-week timeline. Focus on critical paths (data extraction accuracy, Excel generation correctness) rather than 100% coverage. Client UAT is the ultimate validation for MVP.

### Additional Technical Assumptions and Requests

**Language & Framework Versions:**
- **Frontend:** TypeScript 5.6, Next.js 15.5.6 (App Router), React 19.2, Tailwind CSS 4.0, shadcn/ui
- **Backend:** Python 3.14, FastAPI 0.119 (async-native)
- **Database:** PostgreSQL 18.0, Redis 7.4.1
- **State Management:** Zustand (client state), Tanstack Query (server state/caching)
- **Form Handling:** React Hook Form + Zod validation
- **PDF Rendering:** react-pdf 9.1
- **Excel Processing:** openpyxl 3.1.5
- **NLP:** spaCy 3.8.7 (en_core_web_trf, zh_core_web_trf models for English/Chinese text)
- **Fuzzy Matching:** rapidfuzz 3.10
- **ORM:** SQLAlchemy 2.0 (async support), Alembic 1.14 (migrations)
- **Task Queue:** Celery 5.4

**All versions are latest stable as of October 2025** to avoid technical debt and ensure long-term maintainability.

**Deployment & Infrastructure:**
- **Containerization:** Docker 27.x + Docker Compose 2.x
- **Initial Deployment:** On-premise (client's Windows/Linux server or laptop)
- **Data Storage:** All data in Docker volumes (PostgreSQL data, Redis persistence, uploaded files)
- **No cloud storage:** No AWS S3, Google Cloud Storage, etc. (client data sovereignty requirement)
- **Future Cloud Option:** GCP Cloud Run for hosted SaaS offering (post-MVP)
- **Monitoring:** Sentry 2.18 for error tracking and performance monitoring

**API Integrations:**
- **Google Cloud:** Document AI API requires service account key (JSON) mounted as Docker secret
- **OpenRouter:** API key for GPT-5 access (or BYOK option with OpenAI key directly)
- **No other third-party integrations required for MVP**

**Security:**
- **Authentication:** JWT tokens (httpOnly cookies for web, Bearer tokens for future API)
- **Password hashing:** bcrypt or Argon2
- **Secrets management:** Environment variables (Docker Compose .env file, never committed to Git)
- **HTTPS:** Required for production, configured via reverse proxy (nginx or Traefik)
- **Data encryption:** PostgreSQL encryption at rest (pg_crypto extension)

**Database Schema Design Principles:**
- **Audit trail:** All tables include created_at, updated_at, created_by, updated_by columns
- **Soft deletes:** Use deleted_at for important entities (declarations, users) rather than hard deletes
- **JSON flexibility:** Use JSONB columns for storing flexible data (OCR raw output, LLM responses, correction metadata)
- **Future multi-tenancy:** Include organization_id in all tables (initially single org, prepares for SaaS)

**Code Quality Standards:**
- **Type safety:** TypeScript strict mode enabled, Python type hints enforced with mypy
- **Linting:** ESLint (frontend), Ruff (backend)
- **Formatting:** Prettier (frontend), Black (backend)
- **Pre-commit hooks:** Run linters and formatters before commit
- **API documentation:** Auto-generated via FastAPI OpenAPI/Swagger UI

**Performance Optimization:**
- **Caching strategy:** Redis for OCR results (avoid re-processing same document), Tanstack Query for frontend API response caching
- **Smart model routing:** GPT-5 Flagship for complex extraction, GPT-5 Mini for simple fields, GPT-5 Nano for validation (minimize cost per NFR21)
- **Database indexes:** Index on frequently queried fields (user_id, created_at, hs_code)
- **Lazy loading:** Load PDFs and large datasets incrementally to reduce initial page load

**Accessibility Requirements:**
- Follow WCAG AA standards (4.5:1 contrast, keyboard navigation, screen reader support)
- Use semantic HTML and ARIA labels where needed
- Test with keyboard-only navigation for core workflows

**Localization (Post-MVP):**
- English UI for MVP
- Vietnamese localization planned for Phase 2
- Design API responses to support i18n from start (separate presentation from data)

**Documentation Requirements:**
- **User guide:** How to process a declaration (with screenshots)
- **Setup guide:** Docker installation and configuration steps
- **API documentation:** Auto-generated FastAPI docs accessible at /docs endpoint
- **Architecture diagram:** High-level system overview for developers
- **Runbook:** Common issues and troubleshooting steps

---

## Epic List

### Epic 1: Foundation & Document Processing Pipeline (9 Stories)
**Goal:** Establish project infrastructure and core document processing capabilities, delivering a working end-to-end pipeline that can ingest source documents (AN, BOL, CO, INVOICE), extract data via AI, and output raw JSON results.

**Deliverable:** Developers can upload sample declaration files and receive structured JSON output with extracted data and confidence scores. Foundation enables all subsequent development.

**Stories:** 1.0 (Testing Infrastructure), 1.1 (Project Setup), 1.0.5 (CI/CD Pipeline), 1.2 (Backend API), 1.3 (Google Document AI), 1.4 (GPT-5 Integration), 1.5 (Async Processing), 1.6 (File Upload), 1.7 (End-to-End Processing)

---

### Epic 2: Declaration Generation & Excel Export (6 Stories)
**Goal:** Transform extracted data into properly formatted Vietnamese customs declaration Excel files with tariff rates applied and calculations performed.

**Deliverable:** System generates CD.xlsx files that match Vietnamese customs format requirements with all fields populated, taxes calculated, ready for human review.

**Stories:** 2.1 (Knowledge Base Import), 2.2 (Fuzzy Matching), 2.3 (Cross-Document Validation), 2.4 (Tariff Calculation), 2.5 (Excel Generation), 2.6 (End-to-End Pipeline)

---

### Epic 3: Human-in-the-Loop Review Interface (10 Stories)
**Goal:** Build the web-based review interface where users can verify AI output, make corrections, and approve declarations for submission.

**Deliverable:** Users can log in, upload files, review generated declarations side-by-side with source PDFs, edit fields inline, and export approved Excel files.

**Stories:** 3.1 (Frontend Foundation), 3.2 (User Authentication), 3.3 (File Upload Interface), 3.4 (Processing Status), 3.5 (PDF Viewer), 3.6 (Review Form), 3.7 (Jump Navigation), 3.8 (Approval & Export), 3.9 (Declaration History), 3.10 (Edge Cases)

---

### Epic 4: Learning System & Knowledge Base Management (6 Stories)
**Goal:** Implement correction tracking and knowledge base management features that enable continuous improvement and user empowerment.

**Deliverable:** System captures all user corrections for future learning, allows users to upload updated Good List and EXIM-Tariff files, and provides foundation for Phase 2 AI training.

**Stories:** 4.1 (Correction Tracking), 4.2 (Analytics Dashboard), 4.3 (Knowledge Base Upload), 4.4 (Version History), 4.5 (Confidence Learning), 4.6 (User Documentation)

---

## Epic Details

### Epic 1: Foundation & Document Processing Pipeline (9 Stories)

**Epic Goal:** Establish project infrastructure and core document processing capabilities, delivering a working end-to-end pipeline that can ingest source documents (AN, BOL, CO, INVOICE), extract data via AI, and output raw JSON results. This epic lays the technical foundation while delivering the most critical capability—automated data extraction from customs documents.

---

#### Story 1.0: Comprehensive Testing Infrastructure Setup

As a **developer**,
I want **a complete testing infrastructure with unit, integration, E2E, and MCP-enabled Playwright tests configured across frontend and backend**,
so that **I can write and run tests confidently throughout development with consistent tooling and best practices**.

**Acceptance Criteria:**

**Backend Testing (Python):**
1. pytest 8.3 installed and configured with `pytest.ini` defining test paths, coverage settings, and async support
2. pytest-asyncio 0.23 configured for async test support (FastAPI TestClient)
3. pytest-cov configured for coverage reporting with 70%+ target for critical paths
4. Test directory structure created: `backend/tests/unit/`, `backend/tests/integration/`, `backend/tests/fixtures/`
5. Mock fixtures created for external APIs (Google Document AI, OpenRouter) to avoid test costs
6. Test database configuration (separate PostgreSQL test DB with automatic cleanup)
7. Sample unit test passes: `test_user_model.py` validates User model creation
8. Sample integration test passes: `test_auth_endpoint.py` validates login endpoint with TestClient
9. Coverage report generated with `pytest --cov=src --cov-report=html`

**Frontend Testing (TypeScript):**
10. Vitest 2.1 installed and configured with `vitest.config.ts`
11. React Testing Library 16.1 installed for component testing
12. `@testing-library/jest-dom` matchers configured for assertions
13. Test directory structure created: `frontend/src/__tests__/unit/`, `frontend/src/__tests__/integration/`
14. Mock Service Worker (msw 2.4) configured for API mocking in tests
15. Sample component test passes: `declaration-form.test.tsx` validates form rendering
16. Sample hook test passes: `use-declaration.test.ts` validates TanStack Query hook
17. Coverage report generated with `vitest --coverage` (60%+ target)

**End-to-End Testing (Playwright):**
18. Playwright 1.48 installed with TypeScript support
19. Playwright configuration (`playwright.config.ts`) defines: Chrome, Firefox, Safari browsers, base URL (http://localhost:3000), video recording on failure, screenshot on failure
20. **Playwright MCP (Model Context Protocol) integration configured** for AI-assisted test generation and maintenance
21. MCP server configured to access codebase context and generate context-aware Playwright tests
22. Test directory created: `tests/e2e/` with helper utilities (login helper, file upload helper)
23. Sample E2E test passes: `happy-path.spec.ts` validates complete declaration workflow (Login → Upload → Process → Review → Approve → Download)
24. Test data fixtures created: Anonymized versions of `resources/sample/1/` files for E2E tests
25. Playwright HTML reporter configured for visual test results

**Integration and Documentation:**
26. Pre-commit hooks configured (husky) to run linters before commit (ESLint, Ruff, Prettier)
27. Test scripts added to root `package.json`: `npm run test:backend`, `npm run test:frontend`, `npm run test:e2e`, `npm run test:all`
28. Test environment variables documented in `.env.test.example`
29. Testing best practices documented in `docs/testing-guide.md` including: How to write unit tests, How to mock external APIs, How to use Playwright MCP for test generation, Coverage requirements per component type
30. CI readiness validated: All test commands run successfully in Docker containers (prerequisite for Story 1.0.5)

**Playwright MCP Specific Features:**
31. MCP configuration enables Playwright to query codebase for component selectors, API endpoints, and user flows
32. MCP-generated tests validated against manual test baseline for accuracy
33. Developer documentation includes examples of using MCP to generate E2E tests from user stories

---

#### Story 1.1: Project Setup & Development Environment

As a **developer**,
I want **a fully configured development environment with all services running in Docker Compose**,
so that **I can start building features immediately without environment configuration issues**.

**Acceptance Criteria:**
1. Monorepo structure created with `frontend/`, `backend/`, `docker-compose.yml`, and `docs/` directories
2. Docker Compose defines 5 services: frontend (Next.js), backend (FastAPI), celery-worker, postgres, redis
3. All services start successfully with `docker-compose up` and health checks pass
4. PostgreSQL 18.0 database is initialized with empty schema and migrations framework (Alembic) configured
5. Redis 7.4.1 is accessible from both backend and celery-worker services
6. Environment variable template (`.env.example`) documents all required configuration
7. README.md includes setup instructions for new developers (Docker installation, first-time setup, common commands)
8. Git repository initialized with `.gitignore` configured to exclude `.env`, `node_modules/`, `__pycache__/`, etc.
9. All frontend dependencies install successfully with `npm install` in `frontend/` directory
10. All backend dependencies install successfully with `pip install -r requirements.txt` in `backend/` directory
11. No dependency version conflicts detected during installation

---

#### Story 1.0.5: CI/CD Pipeline Setup with GitHub Actions

As a **developer**,
I want **an automated CI/CD pipeline using GitHub Actions that runs all tests on pull requests and automates deployment on merge to main**,
so that **code quality is enforced, bugs are caught early, and deployment is consistent and reliable**.

**Acceptance Criteria:**

**Continuous Integration Workflow:**
1. GitHub Actions workflow file created: `.github/workflows/ci.yml`
2. CI workflow triggers on: Pull request creation/update to any branch, Push to main branch
3. CI workflow job "Backend Tests" runs: `cd backend && pip install -r requirements.txt`, `pytest --cov=src --cov-report=xml`, `ruff check .`, `mypy src/`
4. CI workflow job "Frontend Tests" runs: `cd frontend && npm ci`, `npm run test`, `npm run lint`, `npm run build` (validates TypeScript compilation)
5. CI workflow job "E2E Tests" runs: `docker-compose up -d`, Wait for health checks, `npx playwright test`, `docker-compose down`
6. CI workflow uploads coverage reports to GitHub Actions artifacts
7. Branch protection rule configured: Pull requests require CI workflow to pass before merge
8. CI workflow displays status badge in README.md (shows passing/failing status)

**Continuous Deployment Workflow:**
9. GitHub Actions workflow file created: `.github/workflows/deploy.yml`
10. CD workflow triggers on: Push to main branch (after merge)
11. CD workflow builds Docker images: `docker build -t logai-frontend ./frontend`, `docker build -t logai-backend ./backend`
12. CD workflow tags images with commit SHA and `latest`
13. CD workflow saves images to tar files (for on-premise deployment, no Docker registry needed for MVP)
14. CD workflow creates GitHub release with: Docker image tar files as artifacts, Deployment instructions, Database migration commands (`alembic upgrade head`)
15. CD workflow sends notification to Slack/email on deployment success or failure (webhook configured)

**Secrets and Environment Management:**
16. GitHub repository secrets configured: `GOOGLE_CLOUD_KEY` (base64-encoded service account JSON), `OPENROUTER_API_KEY`, `POSTGRES_PASSWORD`, `JWT_SECRET_KEY`, `SENTRY_DSN`
17. GitHub secrets documentation in `docs/deployment.md` with instructions for rotating keys
18. Environment variable injection into Docker containers during CI (test environment)
19. Production environment variables managed separately (documented in deployment guide, not in CI)

**Quality Gates:**
20. CI fails if backend test coverage < 60% (quality gate enforced by pytest-cov)
21. CI fails if frontend test coverage < 50% (quality gate enforced by vitest)
22. CI fails if any linter errors detected (Ruff, ESLint, mypy)
23. CI fails if E2E tests fail (Playwright)
24. PR status checks visible in GitHub UI with clickable links to detailed logs

**Performance and Optimization:**
25. CI workflow uses caching for: npm dependencies (`actions/cache` for `node_modules`), pip dependencies (`actions/cache` for pip cache), Docker layer caching
26. CI workflow runs frontend and backend tests in parallel (separate jobs) for faster feedback
27. E2E tests run only on main branch pushes (not on every PR) to save resources (configurable)

**Documentation and Developer Experience:**
28. CI/CD pipeline documented in `docs/ci-cd-guide.md` with: Workflow architecture diagram, How to run CI locally (act tool), How to debug failed CI runs, How to add new test jobs
29. Developer onboarding includes CI/CD setup: Clone repo → Configure GitHub secrets (admin) → Create PR → Verify CI passes
30. Troubleshooting guide includes common CI failures and solutions

**Post-Deployment Validation:**
31. CD workflow includes smoke test: `curl http://localhost:8000/health` (validates backend is running)
32. CD workflow validates database migration succeeded before marking deployment as successful
33. Rollback procedure documented: How to revert to previous Docker image tag, How to rollback database migration (`alembic downgrade -1`)

---

#### Story 1.2: Backend API Foundation

As a **developer**,
I want **a FastAPI backend with database models, API routing structure, and basic health checks**,
so that **I have a solid foundation for building business logic and API endpoints**.

**Acceptance Criteria:**
1. FastAPI 0.119 application runs on port 8000 with auto-generated OpenAPI documentation at `/docs`
2. SQLAlchemy 2.0 configured with async support and connection to PostgreSQL
3. Database models created for core entities: `User`, `Declaration`, `KnowledgeBase`, `Correction`, `AuditLog`
4. All models include audit fields: `id`, `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at`, `organization_id`
5. Alembic migrations created for initial schema and successfully applied to database
6. Health check endpoint (`GET /health`) returns service status and database connectivity
7. CORS configured to allow requests from frontend (localhost:3000 in dev)
8. Error handling middleware configured with Sentry 2.18 integration for error tracking
9. PostgreSQL automated backup configured (pg_dump cron job or Docker volume snapshot script) running daily
10. Backup restoration procedure documented in runbook with step-by-step instructions

---

#### Story 1.3: Google Document AI Integration

As a **developer**,
I want **integration with Google Document AI to perform OCR on PDF and image files**,
so that **the system can extract text and tables from customs documents**.

**Acceptance Criteria:**
0. **USER RESPONSIBILITY:** User creates Google Cloud project, enables Document AI API (form-parser-v1.5.1-2025-08-07), creates service account with Document AI User role, and downloads JSON key file before development begins
1. Google Cloud service account key (JSON) mounted as Docker secret and loaded by backend
2. Document AI client configured with pretrained-foundation-model-v1.5.1-2025-08-07 (form parser)
3. Function `process_document_ocr(file_path: str) -> OCRResult` extracts text, key-value pairs, and tables from PDF/image
4. OCR results include confidence scores for each extracted element
5. Results cached in Redis with 24-hour TTL to avoid redundant API calls for same document (per NFR22)
6. Graceful error handling if Document AI API is unavailable (per NFR6) with clear error messages
7. Unit tests mock Document AI API responses to avoid test costs
8. Successfully processes sample files from `resources/sample/1/` (AN.pdf, BOL.pdf, CO.pdf, INVOICE.jpg)

---

#### Story 1.4: GPT-5 LLM Integration via OpenRouter

As a **developer**,
I want **integration with GPT-5 via OpenRouter for intelligent data extraction from OCR results**,
so that **the system can understand and extract structured customs data regardless of document format variations**.

**Acceptance Criteria:**
1. OpenRouter API client configured with API key from environment variables
2. Service supports three model tiers: `openai/gpt-5` (Flagship), `openai/gpt-5-mini` (Mini), `openai/gpt-5-nano` (Nano)
3. Function `extract_structured_data(ocr_result: OCRResult, model: str) -> ExtractedData` sends OCR text to GPT-5 with extraction prompt
4. Extraction prompt instructs GPT-5 to extract: product descriptions, quantities, prices, HS codes, company names, dates, container numbers, weights
5. LLM response parsed as JSON with per-field confidence scores
6. Temperature set to 0.1 for deterministic extraction
7. Retry logic with exponential backoff for transient API failures
8. Unit tests mock OpenRouter API to avoid costs and ensure deterministic testing

---

#### Story 1.5: Async Processing with Celery

As a **user**,
I want **declaration processing to happen in the background**,
so that **I can continue working while the system processes documents without the browser hanging**.

**Acceptance Criteria:**
1. Celery 5.4 worker configured with Redis as message broker
2. Celery worker starts successfully in Docker Compose and connects to Redis
3. Background task `process_declaration_task(declaration_id: int)` orchestrates full processing pipeline
4. Task progresses through states: PENDING → PROCESSING_OCR → PROCESSING_LLM → VALIDATING → COMPLETED or FAILED
5. Task status and progress stored in database and queryable via API endpoint `GET /api/declarations/{id}/status`
6. Task results (extracted data JSON) stored in Declaration model upon completion
7. Failed tasks log errors to Sentry and update Declaration status to FAILED with error message
8. Frontend can poll status endpoint to show real-time processing progress (per NFR1: <90 sec processing time)

---

#### Story 1.6: File Upload and Storage

As a **user**,
I want **to upload all required source documents for a customs declaration**,
so that **the system can begin processing my declaration**.

**Acceptance Criteria:**
1. API endpoint `POST /api/declarations/upload` accepts multipart form data with required files: AN (single), BOL (single), CO (multiple), INVOICE (single)
2. Validates file types: AN.pdf, BOL.pdf, CO*.pdf (must be PDF), INVOICE (PDF or JPG/PNG)
3. Validates all 4 required file types are present (at least 1 CO file required)
4. Files stored in Docker volume at `./data/uploads/{declaration_id}/` with original filenames preserved
5. Multiple CO files stored with indexed filenames (e.g., CO_1.pdf, CO_2.pdf, CO_3.pdf)
6. Declaration record created in database with status UPLOADED and references to file paths (including CO file count)
7. Returns declaration ID, status, and uploaded file list to frontend for tracking
8. File size limits enforced: All files max 20MB with clear error messages if exceeded
9. Clear error messages returned if validation fails (missing files, wrong types, size exceeded)

**Notes:**
- Good List and EXIM Tariff are NOT uploaded via this endpoint—they are managed as knowledge base data in Epic 2 (Story 2.1)
- Maximum CO files per declaration: 10 (reasonable business limit)

---

#### Story 1.7: Process Complete Declaration End-to-End

As a **developer**,
I want **to trigger end-to-end processing that calls OCR, LLM extraction, and stores results**,
so that **I can verify the complete AI extraction pipeline works with real sample data**.

**Acceptance Criteria:**
1. API endpoint `POST /api/declarations/{id}/process` triggers Celery task for given declaration
2. Task processes all 4 document files (AN, BOL, CO, INVOICE) through Google Document AI OCR
3. OCR results for all 4 documents passed to GPT-5 extraction with comprehensive prompt
4. Extracted data (JSON) includes: shipper/consignee details, products array, container details, dates, totals
5. Each extracted field includes confidence score from LLM
6. Processing completes within 90 seconds for sample declarations (per NFR1)
7. Results stored in database and accessible via `GET /api/declarations/{id}` endpoint
8. Successfully processes all 3 sample declarations from `resources/sample/1/`, `resources/sample/2/`, `resources/sample/3/`
9. Extracted data matches expected values from manual review of sample files (accuracy validation)

---

### Epic 2: Declaration Generation & Excel Export

**Epic Goal:** Transform extracted data into properly formatted Vietnamese customs declaration Excel files with tariff rates applied and calculations performed. This epic delivers the core output artifact—the CD.xlsx file ready for customs submission.

---

#### Story 2.1: Knowledge Base Data Import

As a **developer**,
I want **to import Good List and EXIM-Tariff data into the database**,
so that **the system can reference historical HS codes and tariff rates during declaration generation**.

**Acceptance Criteria:**
1. Database schema includes tables: `good_list_entries` (columns: id, product_description, hs_code, price, weight, supplier, metadata) and `tariff_rates` (hs_code, vat_rate, import_duty, trade_agreement, description_vi, description_en)
2. Import script reads `resources/goodlist1.xls` and `resources/goodlist2.xls` and populates `good_list_entries` table
3. Import script reads `resources/EXIM-Tarrif.xlsx` and populates `tariff_rates` table
4. Total records imported: 1,294+ from Good Lists, complete tariff database from EXIM-Tarrif
5. Duplicate detection: If same HS code appears multiple times in Good List, keep all variations for fuzzy matching
6. Data validation: Reject entries with missing required fields (HS code, description)
7. Import operation is idempotent (can run multiple times without creating duplicates)
8. API endpoint `GET /api/knowledge-base/stats` returns counts of entries in both tables

---

#### Story 2.2: Fuzzy Matching for HS Code Suggestions

As a **system**,
I want **to match extracted product descriptions against historical Good List entries**,
so that **I can suggest the most likely HS code for each product based on past declarations**.

**Acceptance Criteria:**
1. Function `suggest_hs_code(product_description: str) -> List[HSCodeSuggestion]` uses rapidfuzz 3.10 for fuzzy string matching
2. Searches product description against all `good_list_entries.product_description` fields
3. Returns top 5 matches with similarity scores (0-100 scale)
4. Filters results to only include matches with similarity ≥ 85% (per FR4)
5. If extracted data already includes HS code from OCR/LLM, compares it against fuzzy match suggestions
6. Confidence score adjusted: High if fuzzy match confirms LLM extraction, Low if mismatch detected
7. Unit tests verify matching behavior with Vietnamese product descriptions from sample data
8. Performance: Fuzzy matching completes within 2 seconds for 20 products against 1,294 entry database

---

#### Story 2.3: Cross-Document Validation

As a **system**,
I want **to validate consistency across the 4 source documents**,
so that **I can flag potential errors or inconsistencies for user review** (per FR5).

**Acceptance Criteria:**
1. Validation function runs after extraction and checks: Invoice total = Certificate of Origin total (within 1% tolerance), BOL container count = Arrival Notice container count, HS codes in Invoice match HS codes in Certificate of Origin, Dates follow logical sequence (Invoice date ≤ BOL date ≤ Arrival date)
2. Each validation produces result: PASS, WARNING, or FAIL with specific message
3. Validation warnings stored in database with reference to specific fields
4. Fields failing validation have confidence scores automatically reduced to <70% (red flag for review)
5. Validation results included in API response for `GET /api/declarations/{id}`
6. Successfully identifies intentional mismatches in test data (e.g., manually create declaration with Invoice total ≠ CO total)

---

#### Story 2.4: Tariff Rate Lookup and Tax Calculation

As a **system**,
I want **to look up tariff rates for each HS code and calculate VAT and import duties**,
so that **the declaration includes accurate tax calculations** (per FR7, FR8).

**Acceptance Criteria:**
1. For each product with HS code, query `tariff_rates` table to retrieve VAT rate and import duty rate
2. If exact 8-digit HS code not found, fall back to 6-digit, then 4-digit, then 2-digit lookup
3. Calculate taxes: `import_duty = invoice_value × import_duty_rate`, `vat = (invoice_value + import_duty) × vat_rate`
4. Store calculated values in Declaration model: `total_invoice_value`, `total_import_duty`, `total_vat`, `total_payable`
5. Handle special cases: Multiple trade agreements (ACFTA, ATIGA) - use lowest applicable rate for first client (Vietnam context)
6. Tariff lookup failures flagged with low confidence score and placeholder rate (default VAT 8%)
7. Unit tests verify calculations against manually computed examples from `resources/sample/2/CD.xlsx`
8. Tax calculation completes within 1 second for 20-product declaration

---

#### Story 2.5: Excel Template Generation

As a **system**,
I want **to generate a Vietnamese customs declaration Excel file (CD.xlsx) matching the official format**,
so that **users can submit the file directly to customs without reformatting** (per FR6, FR9).

**Acceptance Criteria:**
1. Excel generator uses openpyxl 3.1.5 to create .xlsx file based on template structure from `resources/sample/2/CD.xlsx`
2. Template includes: Header section (importer name, address, tax ID, declaration date), Product line items table (product description, HS code, quantity, unit price, total value, origin), Tax summary (subtotal, import duty, VAT, total payable)
3. All extracted data fields mapped to correct Excel cells
4. Number formatting matches customs requirements (currency with 2 decimals, dates as DD/MM/YYYY)
5. Vietnamese language headers and labels preserved from template
6. Generated file saved to `./data/exports/{declaration_id}/CD.xlsx`
7. File downloadable via API endpoint `GET /api/declarations/{id}/export`
8. Generated Excel file opens correctly in Microsoft Excel and LibreOffice Calc without errors
9. Manual comparison: Generated file for `sample/2/` matches structure of original `resources/sample/2/CD.xlsx`

---

#### Story 2.6: End-to-End Declaration Generation Pipeline

As a **developer**,
I want **to trigger complete declaration generation from extracted data to final Excel export**,
so that **I can verify the system produces customs-ready Excel files from uploaded documents**.

**Acceptance Criteria:**
1. API workflow: Upload files → Process (OCR + LLM) → Generate Excel, all automated
2. Celery task extended to include: Knowledge base matching (Story 2.2), Cross-document validation (Story 2.3), Tariff lookup and calculation (Story 2.4), Excel generation (Story 2.5)
3. Declaration status progresses: UPLOADED → PROCESSING → VALIDATING → GENERATING_EXCEL → READY_FOR_REVIEW
4. Processing time from upload to Excel ready: <90 seconds (per NFR1)
5. Generated Excel files for all 3 sample declarations verified manually against expected outputs
6. Accuracy check: 80%+ of fields correctly extracted and formatted for sample declarations (acknowledging MVP 85% target, allowing early iteration)
7. Error handling: If Excel generation fails, Declaration status set to FAILED with error details
8. Developer documentation updated with end-to-end API workflow examples

---

### Epic 3: Human-in-the-Loop Review Interface

**Epic Goal:** Build the web-based review interface where users can verify AI output, make corrections, and approve declarations for submission. This epic delivers the primary user-facing application and completes the core MVP workflow.

---

#### Story 3.1: Frontend Foundation & Routing

As a **developer**,
I want **a Next.js 15 frontend application with routing, layout, and UI component library configured**,
so that **I have a foundation for building user-facing screens**.

**Acceptance Criteria:**
1. Next.js 15.5.6 application created with App Router architecture
2. TypeScript 5.6 configured with strict mode enabled
3. Tailwind CSS 4.0 configured with shadcn/ui component library installed
4. Application layout created with responsive navigation header
5. Routes defined: `/login`, `/upload`, `/declarations`, `/declarations/[id]/review`
6. Zustand store configured for client state management
7. Tanstack Query configured for server state/API caching
8. ESLint and Prettier configured with pre-commit hooks
9. Frontend runs on port 3000 and successfully connects to backend API on port 8000
10. Health check: Frontend displays backend API status from `/health` endpoint

---

#### Story 3.2: User Authentication

As a **user**,
I want **to log in with email and password**,
so that **my declarations are secure and tracked to my account** (per FR18, FR19).

**Acceptance Criteria:**
1. Login screen with email and password input fields, "Remember me" checkbox, "Login" button
2. Backend endpoint `POST /api/auth/login` validates credentials and returns JWT token
3. JWT token stored in httpOnly cookie with configurable expiration (default 8 hours per NFR19)
4. Protected routes redirect to login if user not authenticated
5. Backend middleware validates JWT on protected endpoints and attaches user context
6. User registration endpoint `POST /api/auth/register` creates new user with bcrypt password hashing
7. Session persists across browser refreshes via cookie
8. Logout endpoint `POST /api/auth/logout` clears cookie and invalidates session
9. Clear error messages for failed login ("Invalid email or password")
10. For MVP: Single user account seeded in database (client's primary user)

---

#### Story 3.3: File Upload Interface

As a **user**,
I want **a drag-and-drop interface to upload all required source documents**,
so that **I can easily submit documents for processing** (per FR1).

**Acceptance Criteria:**
1. Upload screen (`/upload`) displays 4 labeled drop zones: Arrival Notice (PDF), Bill of Lading (PDF), Certificate of Origin (PDF, multiple files accepted), Invoice (PDF/Image)
2. Drag-and-drop functionality works for all drop zones with visual feedback (highlight on drag-over)
3. Certificate of Origin drop zone accepts multiple files (show list of uploaded files with remove option)
4. Alternative: Click to open file browser for each zone
5. Visual checklist shows which required files uploaded (✓ green checkmark when file added)
6. File type validation on frontend before upload (show error if wrong type)
7. File size validation: All files max 20MB with clear error messages if exceeded
8. "Process Declaration" button enabled only when all 4 required files uploaded (AN, BOL, at least 1 CO, INVOICE)
9. Clicking "Process Declaration" uploads files to `POST /api/declarations/upload` and triggers processing
10. After upload, user redirected to processing status screen showing declaration ID
11. Error handling: Display clear messages if upload fails (network error, validation error)

**Notes:**
- Good List and EXIM Tariff are NOT uploaded—they are managed as knowledge base data
- CO files may include multiple certificates (e.g., Form E, Form D, general CO)

---

#### Story 3.4: Processing Status Display

As a **user**,
I want **to see real-time progress while my declaration is being processed**,
so that **I know the system is working and how long it will take**.

**Acceptance Criteria:**
1. Processing status screen (`/declarations/[id]`) polls `GET /api/declarations/{id}/status` every 2 seconds
2. Progress indicator shows current stage: Uploading → OCR Processing → AI Extraction → Validation → Generating Excel → Ready for Review
3. Visual progress bar or stepper component indicates completion percentage
4. Estimated time remaining displayed (based on average processing time, initially ~90 seconds)
5. Status updates in real-time as backend progresses through Celery task states
6. When status changes to READY_FOR_REVIEW, auto-redirect to review screen or show "Review Declaration" button
7. If status changes to FAILED, display error message and option to re-upload or contact support
8. User can navigate away and return; processing continues in background (per NFR20)
9. If status = FAILED, user can click "Retry Processing" button to re-queue declaration for processing
10. After 3 consecutive failed processing attempts, system displays "Contact Support" message with error ID for troubleshooting

---

#### Story 3.5: PDF Viewer Component

As a **user**,
I want **to view source PDF documents within the review interface**,
so that **I can verify extracted data against original documents** (per FR10).

**Acceptance Criteria:**
1. PDF viewer component built with react-pdf 9.1 library
2. Displays PDF with page navigation (previous/next buttons, page number indicator)
3. Zoom controls: Zoom in, zoom out, fit to width, fit to page
4. Search functionality to find text within PDF
5. Thumbnail sidebar showing all pages (collapsible)
6. Renders 10-page PDF within 3 seconds (per NFR2)
7. Supports viewing all 4 document PDFs: AN, BOL, CO, INVOICE
8. Tab or dropdown selector to switch between different source documents
9. Highlights or scrolls to specific location when user clicks field in declaration (Story 3.7 dependency)
10. Works in Chrome 120+, Firefox 120+, Safari 17+

---

#### Story 3.6: Declaration Review Form

As a **user**,
I want **to see all extracted declaration data in an editable form with confidence indicators**,
so that **I can review and correct any errors before approval** (per FR10, FR11, FR12).

**Acceptance Criteria:**
1. Review screen (`/declarations/[id]/review`) displays extracted data in structured form sections: Company Information, Shipment Details, Product Line Items, Tax Calculations
2. Each field color-coded by confidence: Green (>90%), Yellow (70-90%), Red (<70%) per FR11
3. All fields editable inline using React Hook Form with Zod validation
4. Auto-save functionality: Save changes to backend every 5 seconds (per NFR7)
5. Visual indicator showing "Saving..." vs "Saved" status
6. Validation errors display inline (e.g., "HS Code must be 8 digits")
7. Product line items displayed in table format with add/remove row functionality
8. Cross-document validation warnings displayed prominently (e.g., "Warning: Invoice total ($23,208) does not match CO total ($23,200)")
9. Form data fetched from `GET /api/declarations/{id}` on page load
10. Updates sent to `PATCH /api/declarations/{id}` on auto-save or manual save

---

#### Story 3.7: Source Document Jump Navigation

As a **user**,
I want **to click any field and see the corresponding location in the source PDF**,
so that **I can quickly verify extracted data without manually searching documents** (per FR13).

**Acceptance Criteria:**
1. Each form field annotated with metadata indicating source document and location (page number, bounding box coordinates)
2. Backend includes source location in extraction response (e.g., `{field: "invoice_total", value: "$23,208.80", source: "INVOICE.pdf", page: 1, bbox: [x, y, w, h]}`)
3. Clicking field label or "View Source" icon highlights corresponding area in PDF viewer
4. PDF viewer automatically switches to correct document tab and page
5. Highlighted area outlined in red rectangle for 3 seconds
6. If source location unavailable (e.g., calculated field like total tax), show tooltip "Calculated field - no source"
7. Jump navigation works for all extracted fields with source metadata
8. Smooth scroll/animation when jumping to source location

---

#### Story 3.8: Declaration Approval & Export

As a **user**,
I want **to approve the reviewed declaration and download the final Excel file**,
so that **I can submit it to customs** (per FR14, FR9).

**Acceptance Criteria:**
1. Review screen header contains sticky "Approve" and "Reject" buttons visible while scrolling
2. "Approve" button disabled if unsaved changes exist (show tooltip: "Please wait for auto-save to complete")
3. Clicking "Approve" sends `POST /api/declarations/{id}/approve` request
4. Backend updates Declaration status to APPROVED and records approving user ID and timestamp (per FR20)
5. On approval success, "Download Excel" button appears
6. Clicking "Download Excel" triggers download of `CD.xlsx` file from `GET /api/declarations/{id}/export`
7. Excel file downloads within 5 seconds (per NFR3)
8. After download, confirmation message: "Declaration approved and exported successfully"
9. "Reject" button marks Declaration as REJECTED and prompts user for rejection reason
10. Rejected declarations moved to "Rejected" list, can be re-opened and re-processed

---

#### Story 3.9: Declaration History List

As a **user**,
I want **to see a list of all my processed declarations**,
so that **I can track my work and re-download previous exports**.

**Acceptance Criteria:**
1. Declarations list screen (`/declarations`) displays table of all declarations for authenticated user
2. Table columns: Declaration ID, Upload Date, Status (Uploaded/Processing/Ready/Approved/Rejected), Products Count, Actions
3. Status badge color-coded: Gray (Uploaded), Blue (Processing), Green (Approved), Red (Rejected)
4. Sortable by Upload Date (default: newest first) and Status
5. Searchable by Declaration ID
6. Actions column includes: "Review" button (for Ready/Approved), "Download" button (for Approved), "Delete" button (soft delete)
7. Pagination: 20 declarations per page
8. Clicking "Review" navigates to `/declarations/[id]/review`
9. Clicking "Download" re-downloads Excel file (no re-processing needed)
10. API endpoint `GET /api/declarations` returns paginated, filtered list

---

#### Story 3.10: Edge Case Handling

As a **user**,
I want **the system to detect and warn me about edge cases and unusual data**,
so that **I can handle special situations appropriately before submitting to customs**.

**Acceptance Criteria:**
1. Multi-currency detection: If invoice contains multiple currencies (e.g., USD and EUR), display warning: "Multi-currency invoice detected. Please verify exchange rates and totals."
2. Partial shipment detection: If BOL containers < Invoice total containers, flag as potential partial shipment with message: "Container count mismatch. Is this a partial shipment?"
3. Missing required field prompts: If extraction fails to populate required customs fields (importer tax ID, HS code, origin country), block approval and display: "Required field missing: [field name]. Please fill manually."
4. Unusually large/small values: Flag products with unit price >$10,000 or <$0.01 as "Unusual unit price detected. Please verify."
5. Date sequence validation: If Invoice date > BOL date or BOL date > Arrival date, display warning: "Dates appear out of sequence. Please verify."
6. Duplicate HS code check: If same HS code appears >5 times with different descriptions, warn: "Same HS code used for multiple distinct products. Please verify classification."
7. All warnings displayed in dedicated "Validation Warnings" panel on review screen with severity levels (Error blocks approval, Warning allows proceed with confirmation)
8. User can dismiss warnings after review with "I have verified this is correct" confirmation
9. Dismissed warnings logged in audit trail with user ID and timestamp
10. Backend validation rules configurable (thresholds adjustable without code changes)

---

### Epic 4: Learning System & Knowledge Base Management (6 Stories)

**Epic Goal:** Implement correction tracking and knowledge base management features that enable continuous improvement and user empowerment. This epic completes the MVP by adding learning capabilities and user control over platform knowledge.

---

#### Story 4.1: Correction Tracking

As a **system**,
I want **to capture all user edits to AI-generated declarations**,
so that **I can build a learning dataset for future accuracy improvements** (per FR15).

**Acceptance Criteria:**
1. Backend middleware intercepts all `PATCH /api/declarations/{id}` requests and compares new values against original extracted values
2. For each changed field, create record in `corrections` table: `declaration_id`, `field_name`, `original_value`, `corrected_value`, `original_confidence`, `user_id`, `timestamp`, `metadata` (per FR15)
3. Metadata includes: Source document (which PDF the field came from), Correction type (typo, wrong extraction, wrong HS code, etc.) inferred from field name
4. Corrections linked to specific products (if editing product table) or declaration-level fields
5. API endpoint `GET /api/corrections/stats` returns summary: Total corrections, corrections by field name, corrections by confidence level
6. Corrections automatically flagged if confidence was high (>90%) but user still corrected (indicates systematic LLM error vs random)
7. Database indexes on `field_name` and `timestamp` for efficient querying
8. Unit tests verify correction records created when user edits any field

---

#### Story 4.2: Correction Analytics Dashboard

As a **operations manager**,
I want **to see analytics on what fields users frequently correct**,
so that **I can understand where the AI needs improvement and track accuracy trends over time**.

**Acceptance Criteria:**
1. Analytics screen (`/analytics`) displays correction insights (accessible to admin users only for MVP)
2. Charts showing: Corrections over time (line chart by week), Top 10 most-corrected fields (bar chart), Corrections by confidence level (pie chart: high/medium/low confidence)
3. Table showing recent corrections with drill-down to specific declarations
4. Metrics displayed: Total declarations processed, Average corrections per declaration, Accuracy improvement trend (calculated as reduction in corrections over time)
5. Date range filter (last 7 days, 30 days, 90 days, all time)
6. Export corrections data as CSV for deeper analysis
7. Backend endpoint `GET /api/analytics/corrections` returns aggregated data
8. Dashboard displays daily/weekly API costs (Google Document AI + OpenRouter) with budget threshold warnings (yellow at 80%, red at 100% of monthly budget)
9. Dashboard updates automatically as new declarations processed

---

#### Story 4.3: Knowledge Base Upload Interface

As a **user**,
I want **to upload updated Good List and EXIM-Tariff files**,
so that **the platform uses my latest product and tariff data for future declarations** (per FR17).

**Acceptance Criteria:**
1. Knowledge Base Management screen (`/knowledge-base`) with two upload sections: Good List, EXIM Tariff
2. Each section shows: Current file version (upload date, record count), "Upload New Version" button
3. Upload validates file format (must be .xls or .xlsx) and structure (required columns present)
4. Preview: After upload, show first 10 rows and total row count before confirming import
5. Confirmation dialog: "This will replace X existing Good List entries. Continue?"
6. Import process: Replace existing data with new data (versioned - old data archived, not deleted)
7. Backend endpoints: `POST /api/knowledge-base/good-list/upload`, `POST /api/knowledge-base/tariff/upload`
8. Import runs as Celery background task to avoid timeout on large files
9. Success notification: "Good List updated successfully. 1,532 entries imported."
10. Error handling: If import fails (malformed Excel, missing required columns), show specific error and allow user to fix and re-upload

---

#### Story 4.4: Knowledge Base Version History

As a **operations manager**,
I want **to see version history of Good List and Tariff uploads**,
so that **I can track changes and rollback if incorrect data was uploaded**.

**Acceptance Criteria:**
1. Knowledge Base screen includes "Version History" tab
2. Table showing: Version Number, Upload Date, Uploaded By User, Record Count, Status (Active/Archived)
3. Each version row has "View Details" and "Rollback" actions
4. "View Details" shows sample of data from that version (first 20 rows)
5. "Rollback" replaces current active data with selected historical version (with confirmation dialog)
6. Backend maintains `knowledge_base_versions` table: `id`, `type` (good_list/tariff), `version_number`, `uploaded_at`, `uploaded_by`, `record_count`, `status`, `file_path`
7. All declaration processing uses "Active" version of knowledge base
8. Rollback operation is audited: Creates audit log entry with reason (user provides reason in dialog)
9. Version history pagination: 50 versions per page
10. Filtering by type (Good List vs Tariff)

---

#### Story 4.5: Confidence Score Learning (Foundation)

As a **system**,
I want **to adjust confidence scores based on historical correction patterns**,
so that **fields frequently corrected are flagged with lower confidence in future declarations**.

**Acceptance Criteria:**
1. Nightly batch job (Celery periodic task) analyzes last 30 days of corrections
2. For each field name, calculate correction rate: `corrections / total_extractions`
3. If field has >20% correction rate, reduce confidence multiplier for that field by 0.1 (e.g., LLM confidence 0.95 → adjusted 0.85)
4. Confidence adjustment factors stored in database table: `field_name`, `adjustment_factor`, `last_updated`
5. During extraction (Story 1.4), apply adjustment factors to LLM confidence scores before storing
6. High correction rate fields automatically flagged as yellow/red for user review
7. Adjustment factors reset if correction rate improves (adaptive learning)
8. Admin interface shows current adjustment factors for transparency
9. Unit tests verify confidence adjustment logic with mock correction data
10. This is foundation for Phase 2 full model retraining; MVP uses simple statistical adjustment

---

#### Story 4.6: User Documentation and Training Materials

As an **operations manager**,
I want **comprehensive user documentation with screenshots and step-by-step guides**,
so that **new customs processors can learn the system independently and existing users have a reference for advanced features**.

**Acceptance Criteria:**

**Core User Guide:**
1. User guide created as `docs/user-guide.md` (Markdown format with embedded screenshots)
2. User guide section "Getting Started": System login, First-time setup, Navigation overview, User roles (processor vs admin)
3. User guide section "Processing a Declaration": Step-by-step workflow with screenshots for each screen: Upload screen (drag-drop 4 required documents, multiple CO files accepted), Processing status screen (progress bar), Review screen (PDF viewer + form), Approval and export
4. User guide section "Review Interface": How to interpret confidence colors (green/yellow/red), How to edit fields inline, How to use PDF jump navigation (click field → see source), How to handle validation warnings
5. User guide section "Knowledge Base Management" (Admin only): How to upload updated Good List, How to upload updated EXIM Tariff, How to view version history, How to rollback to previous version
6. User guide section "Analytics Dashboard" (Admin only): How to read correction statistics, How to identify frequently-corrected fields, How to export corrections data as CSV

**Troubleshooting and FAQs:**
7. Troubleshooting section covers: File upload errors ("Expected .pdf, got .docx"), Processing failures ("API timeout - retry processing"), Validation warnings ("Invoice total doesn't match CO total"), Excel export issues ("Generated file won't open in Excel")
8. FAQ section answers: "What file types are supported?", "How long does processing take?", "Can I edit a declaration after approval?", "What if I upload the wrong file?", "How do I know if AI extraction is accurate?"
9. Error code reference table: Maps backend error codes to user-friendly explanations and solutions

**Quick Reference Materials:**
10. Quick reference card (1-page PDF) created: `docs/quick-reference.pdf` with: File upload checklist (6 required files), Keyboard shortcuts (Save: Ctrl+S, Approve: Ctrl+Enter), Confidence color legend, Common error solutions
11. Visual cheat sheet (infographic): Declaration processing workflow diagram, Review screen anatomy (labeled screenshot)

**Screenshots and Visual Aids:**
12. High-quality screenshots captured for all core screens (1920x1080 resolution)
13. Screenshots annotated with numbered callouts explaining key features
14. GIF animations created for key workflows: Drag-drop file upload, Inline field editing with auto-save, PDF jump navigation (click field → highlight source)

**In-App Help Integration:**
15. Help link added to navigation header (all screens): Opens user guide in new tab or in-app help panel
16. Contextual help tooltips on key UI elements: File drop zones ("Drag PDF file here or click to browse"), Confidence color indicators ("Red = Low confidence, please verify carefully"), Validation warnings ("This value conflicts with another document")
17. Empty state guidance: Upload screen shows helpful instructions when no files uploaded, Declarations list shows "Get Started" guide when no declarations exist

**Knowledge Base Upload Instructions:**
18. Excel template examples provided: `docs/templates/goodlist-template.xlsx` with sample data showing required columns, `docs/templates/tariff-template.xlsx` with sample data showing required columns
19. Data preparation guide: How to format product descriptions for fuzzy matching, How to structure HS codes (8-digit format), How to handle special characters in Vietnamese text
20. Upload validation errors documented: "Missing required column: hs_code" → Solution, "Invalid HS code format" → Solution

**Localization Preparation:**
21. User guide structured for easy translation (clear section headers, simple language)
22. Screenshot file naming convention supports localization: `screenshot-upload-en.png`, `screenshot-upload-vi.png` (placeholder for Phase 2)
23. Vietnamese translation status noted: "English MVP - Vietnamese localization planned for Phase 2"

**Accessibility Documentation:**
24. Accessibility features documented: Keyboard navigation shortcuts, Screen reader compatibility notes, High-contrast mode (if implemented), Font size adjustment
25. Accessibility guide for users with disabilities: How to navigate with keyboard only, How to use screen reader with PDF viewer

**Training Materials:**
26. Video tutorial script created (for future video production): 5-minute walkthrough of complete declaration processing workflow
27. Onboarding checklist for new users: 1. Read Getting Started section, 2. Process sample declaration (provided in training environment), 3. Review troubleshooting guide, 4. Complete first real declaration with supervisor
28. Certification quiz (optional for client): 10 questions covering key workflows, passing score 80%

**Documentation Maintenance:**
29. Documentation version control: User guide version matches application version (v1.0 for MVP)
30. Documentation update process defined: When UI changes, update screenshots within 1 sprint, When new features added, update user guide before release
31. Feedback mechanism: "Was this helpful?" button on each user guide page with link to submit documentation improvement suggestions

**Deployment and Access:**
32. User guide accessible at `/docs/user-guide` route within application (embedded view)
33. User guide also available as downloadable PDF: `CustomsDeclarationPlatform-UserGuide-v1.0.pdf`
34. Quick reference card printed and provided to all users (client responsibility, PDF template provided)

---

## Checklist Results Report

**Analysis Date:** 2025-10-17
**PRD Version:** 1.1 (Final + PO Validation Updates)
**Analyst:** Sarah (PO)

### Executive Summary

**Overall PRD Completeness:** 100% (all critical gaps addressed)

**MVP Scope Appropriateness:** Optimal

**Readiness for Development:** ✅ Ready to Begin

**Key Strengths:**
- Comprehensive requirements (60 total: 30 FR + 30 NFR)
- Well-structured epics with clear sequential dependencies (4 epics, 31 stories)
- Strong technical assumptions grounded in latest 2025 tech stack
- Explicit out-of-scope items prevent scope creep
- Learning system differentiates from commodity tools
- **NEW:** Comprehensive testing infrastructure with Playwright MCP integration
- **NEW:** Automated CI/CD pipeline ensures code quality
- **NEW:** User documentation ensures successful client onboarding

**Critical Actions for Architect (Week 1):**
1. **HIGH PRIORITY:** Analyze `resources/sample/2/CD.xlsx` template structure (formulas, merged cells, formatting complexity)
2. Design database schema with versioning for knowledge base
3. Create API abstraction layer for LLM provider flexibility
4. Validate Google Document AI OCR accuracy on Vietnamese text

### Category Statuses

| Category                         | Status | Critical Issues |
| -------------------------------- | ------ | --------------- |
| 1. Problem Definition & Context  | PASS   | None |
| 2. MVP Scope Definition          | PASS   | None |
| 3. User Experience Requirements  | PASS   | None |
| 4. Functional Requirements       | PASS   | None |
| 5. Non-Functional Requirements   | PASS   | None |
| 6. Epic & Story Structure        | PASS   | None |
| 7. Technical Guidance            | PASS   | None |
| 8. Cross-Functional Requirements | PASS   | None (backup strategy added to Story 1.2) |
| 9. Clarity & Communication       | PASS   | None |

**Overall:** 9/9 PASS

### Updates Applied (V1.1 - PO Validation)

1. ✅ **Story 1.0:** NEW - Comprehensive testing infrastructure setup (pytest, Vitest, Playwright MCP)
2. ✅ **Story 1.0.5:** NEW - CI/CD pipeline with GitHub Actions for automated testing and deployment
3. ✅ **Story 1.1:** Added AC9-11 for dependency installation validation
4. ✅ **Story 1.3:** Added AC0 clarifying user responsibility for Google Cloud project setup
5. ✅ **Story 3.4:** Added AC9-10 for failed processing retry workflow
6. ✅ **Story 4.6:** NEW - User documentation and training materials for client onboarding
7. ✅ **Epic summaries:** Updated all epic headers with story counts

### Final Decision

✅ **READY FOR DEVELOPMENT**

The PRD is comprehensive, properly structured, and ready for development execution. All PO validation recommendations have been implemented, including critical infrastructure stories for testing and CI/CD. The updated plan now includes 31 stories across 4 epics with a revised 8.5-week timeline.

**Updated Project Statistics:**
- **Total Stories:** 31 (was 28)
- **Epic 1:** 9 stories (was 7)
- **Epic 2:** 6 stories (unchanged)
- **Epic 3:** 10 stories (unchanged)
- **Epic 4:** 6 stories (was 5)
- **Estimated Timeline:** 8.5 weeks (was 8 weeks)
- **Overall Readiness:** 100% (was 78%)

---

## Next Steps

### UX Expert Prompt

```
You are the UX Expert for the Customs Declaration Automation Platform.

Please review the Product Requirements Document (docs/prd.md) and create a detailed
UX/UI architecture document that includes:

1. Detailed user flow diagrams for all core workflows (Upload → Review → Approve)
2. Wireframes or component specifications for each core screen:
   - Login Screen
   - Upload Screen
   - Processing Status Screen
   - Review & Edit Screen (with PDF viewer and form layout)
   - Declaration History List
   - Analytics Dashboard
   - Knowledge Base Management Screen

3. Information architecture and navigation structure
4. Component library specification (leveraging shadcn/ui)
5. Accessibility implementation guidelines (WCAG AA compliance)
6. Responsive design breakpoints and mobile considerations
7. Visual design system (colors, typography, spacing, icons)
8. Interaction patterns (drag-drop, inline editing, confidence color-coding)
9. Error state designs and messaging patterns
10. Performance optimization recommendations for PDF rendering and large forms

Key constraints from PRD:
- Desktop-first (1920x1080 primary, 1366x768 minimum)
- Side-by-side PDF + form layout is core UX paradigm
- Confidence-driven review (green/yellow/red color coding)
- Trust through transparency (show sources, confidence scores)
- Speed and efficiency for power users processing 20+ declarations/day

Please create comprehensive UX documentation that enables developers to implement
the interface with minimal design ambiguity.
```

---

### Architect Prompt

```
You are the Technical Architect for the Customs Declaration Automation Platform.

Please review the Product Requirements Document (docs/prd.md) and create a detailed
technical architecture document that includes:

1. **System Architecture:**
   - High-level architecture diagram (5 Docker services + external APIs)
   - Service interaction flows and API contracts
   - Data flow from upload → OCR → LLM → validation → Excel export
   - Background processing architecture (Celery task queues)

2. **Database Design:**
   - Complete PostgreSQL schema for all entities (User, Declaration, KnowledgeBase,
     Correction, AuditLog, GoodListEntry, TariffRate)
   - Relationships, indexes, constraints
   - Migration strategy (Alembic)
   - Versioning strategy for knowledge base updates

3. **API Design:**
   - RESTful API endpoint specifications (all routes for frontend-backend)
   - Request/response schemas (JSON)
   - Authentication flow (JWT)
   - Error response standards

4. **External Integration Architecture:**
   - Google Document AI integration (authentication, request/response handling, caching)
   - OpenRouter/GPT-5 integration (model selection logic, prompt engineering, fallback)
   - LLM abstraction layer (provider-agnostic interface)

5. **Processing Pipeline Architecture:**
   - Detailed flow for declaration processing (8 stages)
   - Smart model routing logic (when to use Flagship/Mini/Nano)
   - Cross-document validation rules
   - Fuzzy matching algorithm and performance optimization

6. **Excel Generation Architecture:**
   - **CRITICAL: Analyze resources/sample/2/CD.xlsx template structure**
   - Document formulas, merged cells, formatting complexity
   - openpyxl implementation strategy or alternative library recommendation
   - Template versioning strategy

7. **Security Architecture:**
   - Authentication and authorization (JWT implementation)
   - Data encryption (at rest and in transit)
   - Secret management (Docker secrets, environment variables)
   - API rate limiting and abuse prevention

8. **Performance & Scalability:**
   - Caching strategy (Redis for OCR results, API responses)
   - Database query optimization (indexes, pagination)
   - PDF rendering optimization
   - Concurrent user handling

9. **Deployment Architecture:**
   - Docker Compose configuration details
   - Volume mount strategy for persistence
   - Environment configuration management
   - Health checks and monitoring

10. **Testing Strategy:**
    - Unit test architecture (mocking external APIs)
    - Integration test setup (test database)
    - E2E test framework (Playwright)
    - Test data management

Key technical constraints from PRD:
- Monorepo with frontend/ and backend/ directories
- Latest 2025 tech stack (Next.js 15.5.6, Python 3.14, PostgreSQL 18)
- On-premise deployment (no cloud storage, all data in Docker volumes)
- Smart cost optimization (target <$0.05 per declaration)
- 8-week timeline (pragmatic choices over perfect architecture)

High-priority architectural investigations:
1. CD.xlsx template complexity analysis (Week 1)
2. PostgreSQL 18.0 stability validation
3. Google Document AI Vietnamese text OCR accuracy testing
4. React-pdf performance validation for 10-page PDFs

Please create comprehensive technical architecture that enables the development
team to begin implementation immediately.
```

---

**END OF PRODUCT REQUIREMENTS DOCUMENT**

*This PRD was created using the BMAD-METHOD™ framework.*
