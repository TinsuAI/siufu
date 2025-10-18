# Security and Performance

## Security Requirements

**Frontend Security:**
- **CSP Headers**: `Content-Security-Policy: default-src 'self'`
- **XSS Prevention**: React auto-escaping, DOMPurify for user content
- **Secure Storage**: JWT in httpOnly cookies (not localStorage)

**Backend Security:**
- **Input Validation**: Pydantic schemas on all endpoints
- **Rate Limiting**: 100 req/min per user (SlowAPI)
- **CORS Policy**: Whitelist production domain only

**Authentication Security:**
- **Token Storage**: httpOnly cookies with Secure, SameSite=Strict
- **Session Management**: 8-hour JWT expiration
- **Password Policy**: Min 8 chars, bcrypt hashing (12 rounds)

## Performance Optimization

**Frontend Performance:**
- **Bundle Size Target**: <500KB initial load (measured: ~380KB)
- **Loading Strategy**: Next.js automatic code splitting
- **Caching Strategy**: TanStack Query 5-minute stale time

**Backend Performance:**
- **Response Time Target**: <100ms GET, <500ms complex queries
- **Database Optimization**: Strategic indexes (see Database Schema)
- **Caching Strategy**: Redis 24hr TTL for OCR, 1hr for tariffs

---
