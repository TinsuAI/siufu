# Tech Stack

## Technology Stack Table

| Category | Technology | Version | Purpose | Rationale |
|----------|-----------|---------|---------|-----------|
| **Frontend Language** | TypeScript | 5.6 | Type-safe frontend development | Industry standard for React apps, catches 60%+ of bugs at compile time, excellent IDE support |
| **Frontend Framework** | Next.js | 15.5.6 | React-based web application framework | App Router architecture, built-in SSR, automatic code splitting, excellent DX, production-ready |
| **UI Library** | React | 19.2 | Component-based UI rendering | Latest stable, Server Components support, improved performance over v18 |
| **UI Component Library** | shadcn/ui | latest | Pre-built accessible components | Radix UI primitives, Tailwind integration, copyable source code (not npm dep), WCAG AA compliant |
| **State Management** | Zustand | 4.5 | Client-side state management | Lightweight (1KB), simpler than Redux, perfect for modest state needs, hooks-based API |
| **Server State** | TanStack Query | 5.59 | API response caching and synchronization | Industry-leading server state management, auto-refetch, optimistic updates, cache invalidation |
| **Form Handling** | React Hook Form | 7.53 | Form state and validation | Uncontrolled inputs (better performance), integrates with Zod, minimal re-renders |
| **Validation** | Zod | 3.24 | Runtime type validation (shared frontend/backend) | TypeScript-first schema validation, generates types from schemas, runtime safety |
| **CSS Framework** | Tailwind CSS | 4.0 | Utility-first styling | Rapid development, tree-shaking (small bundle), consistent design system, JIT compiler |
| **PDF Rendering** | react-pdf | 9.1 | Display source PDFs in browser | Canvas rendering (best performance), bounding box support (jump-to-source), 2.7M weekly downloads |
| **Backend Language** | Python | 3.14 | Backend API and processing logic | Latest stable, excellent AI/ML ecosystem (spaCy), async/await native, type hints support |
| **Backend Framework** | FastAPI | 0.119 | Async REST API server | Auto-generated OpenAPI docs, async-native (critical for AI API calls), Pydantic validation, fastest Python framework |
| **API Style** | REST | - | HTTP JSON API following REST conventions | Simpler than GraphQL for CRUD operations, excellent browser/tool support, OpenAPI spec generation |
| **ORM** | SQLAlchemy | 2.0 | Database abstraction and migrations | Async support (new in 2.0), battle-tested, complex query support, Alembic migrations |
| **Migration Tool** | Alembic | 1.14 | Database schema versioning | Industry standard for SQLAlchemy, auto-generates migrations from models, rollback support |
| **Task Queue** | Celery | 5.4 | Async background processing | Mature (10+ years), Redis integration, task prioritization, retry logic, monitoring via Flower |
| **Database** | PostgreSQL | 18.0 | Primary relational database | Latest stable, JSONB support (flexible schema), excellent performance, pg_crypto for encryption |
| **Cache & Queue** | Redis | 7.4.1 | Cache layer + Celery message broker | In-memory speed, TTL support, pub/sub for real-time, persistence options, proven reliability |
| **File Storage** | Docker Volume | - | Local filesystem in container | Meets on-premise requirement, simple backup (volume snapshots), no cloud dependencies |
| **Authentication** | JWT (python-jose) | 3.3 | Stateless token-based auth | httpOnly cookies (XSS protection), short-lived tokens (15min), refresh token pattern |
| **Password Hashing** | bcrypt | 4.2 | Secure password storage | Industry standard, slow hashing (OWASP recommended), rainbow table resistant |
| **Excel Processing** | openpyxl | 3.1.5 | Read/write .xlsx files | Pure Python (no Excel dependency), formula support, cell formatting, template-based generation |
| **OCR Service** | Google Document AI | pretrained-foundation-model-v1.5.1 | Extract text/tables from PDFs | Best-in-class accuracy (95%+), form parser, confidence scores, Vietnamese language support |
| **LLM Service** | OpenRouter (GPT-5) | Flagship/Mini/Nano | Intelligent data extraction | Smart routing (cost optimization), unified API for multiple providers, streaming support |
| **NLP Library** | spaCy | 3.8.7 | Text validation and entity extraction | Fast (Cython), pre-trained models (en/zh), custom pipeline support, production-ready |
| **Fuzzy Matching** | rapidfuzz | 3.10 | Product description matching for HS codes | Fastest fuzzy library (C++), Levenshtein distance, 85% threshold tuning (per FR4) |
| **Frontend Testing** | Vitest | 2.1 | Unit/integration tests for React components | Vite-native (fast), Jest-compatible API, ESM support, React Testing Library integration |
| **Backend Testing** | pytest | 8.3 | Unit/integration tests for Python code | Fixtures, async support, parametrization, TestClient for FastAPI, 70% coverage target |
| **E2E Testing** | Playwright | 1.48 | Cross-browser end-to-end tests | Multi-browser (Chrome/Firefox/Safari), auto-wait, screenshot/video, stable selectors |
| **Build Tool (Frontend)** | Next.js Built-in | - | TypeScript compilation, bundling | Zero-config, Turbopack (faster than Webpack), automatic optimizations |
| **Bundler** | Turbopack | Built-in Next.js 15 | Fast module bundling | 700x faster than Webpack (Rust-based), incremental compilation, HMR in <10ms |
| **Linter (Frontend)** | ESLint | 9.14 | JavaScript/TypeScript code quality | Next.js config, auto-fix, pre-commit hooks, TypeScript-aware rules |
| **Linter (Backend)** | Ruff | 0.7 | Python code quality and formatting | 10-100x faster than Flake8, auto-fix, replaces Black+isort+Flake8 |
| **Formatter (Frontend)** | Prettier | 3.3 | Consistent code formatting | Opinionated, integrates with ESLint, supports Tailwind class sorting |
| **Type Checker (Backend)** | mypy | 1.13 | Static type checking for Python | Enforces type hints, catches bugs pre-runtime, gradual typing support |
| **IaC Tool** | Docker Compose | 2.x | Container orchestration and networking | Declarative YAML, multi-container apps, volume management, built-in service discovery |
| **CI/CD** | GitHub Actions | - | Automated testing and deployment | Free for private repos, Docker support, matrix testing, deployment workflows |
| **Monitoring** | Sentry | 2.18 | Error tracking and performance monitoring | Real-time alerts, breadcrumb trails, source map support, performance insights |
| **Logging** | structlog (Python) + pino (Node) | 24.4 / 9.4 | Structured JSON logging | Machine-readable, integration with log aggregators, context preservation, async-safe |
| **API Documentation** | FastAPI OpenAPI | Built-in | Auto-generated API docs | Swagger UI at `/docs`, ReDoc at `/redoc`, OpenAPI 3.1 spec for code generation |

---
