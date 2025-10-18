# API Specification

The API follows RESTful conventions with JSON request/response bodies. All endpoints use FastAPI's automatic OpenAPI 3.1 generation, accessible at `/docs` (Swagger UI) and `/redoc` (ReDoc).

## REST API Specification

```yaml
openapi: 3.1.0
info:
  title: Customs Declaration Automation Platform API
  version: 1.0.0
  description: |
    Backend API for customs declaration processing with AI-powered extraction,
    human-in-the-loop review, and continuous learning.

    **Authentication**: All endpoints except /auth/* require JWT Bearer token
    in Authorization header or httpOnly cookie.

    **Rate Limiting**: 100 requests/minute per user (soft limit for MVP)

    **Error Format**: All errors follow RFC 7807 Problem Details format

servers:
  - url: http://localhost:8000
    description: Local development
  - url: https://customs-api.client.com
    description: Production (client's domain)
```

## Key Endpoints

**Authentication:**
- `POST /api/auth/login` - User login, returns JWT token
- `POST /api/auth/logout` - Invalidate session
- `GET /api/auth/me` - Get current user profile

**Declarations:**
- `GET /api/declarations` - List all declarations (paginated)
- `POST /api/declarations/upload` - Upload 6 files for new declaration
- `POST /api/declarations/{id}/process` - Trigger async processing
- `GET /api/declarations/{id}/status` - Get processing status (polling endpoint)
- `GET /api/declarations/{id}` - Get declaration details
- `PATCH /api/declarations/{id}` - Update draft data (auto-save)
- `POST /api/declarations/{id}/approve` - Approve declaration
- `POST /api/declarations/{id}/reject` - Reject with reason
- `GET /api/declarations/{id}/export` - Download Excel file

**Knowledge Base:**
- `POST /api/knowledge-base/good-list/upload` - Upload new Good List version
- `POST /api/knowledge-base/tariff/upload` - Upload new EXIM Tariff version
- `GET /api/knowledge-base/versions` - List version history

**Analytics (Admin only):**
- `GET /api/analytics/corrections` - Correction statistics

**Utility:**
- `GET /health` - Health check

---
