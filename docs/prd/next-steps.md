# Next Steps

## UX Expert Prompt

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

## Architect Prompt

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
