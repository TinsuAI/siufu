# Technical Assumptions

## Repository Structure: Monorepo

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

## Service Architecture

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

## Testing Requirements

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

## Additional Technical Assumptions and Requests

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
