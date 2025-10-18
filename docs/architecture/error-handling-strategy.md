# Error Handling Strategy

## Error Response Format (RFC 7807)

```json
{
  "type": "/errors/validation-error",
  "title": "Validation Error",
  "status": 422,
  "detail": "HS Code must be 8 digits",
  "errors": {
    "products.0.hs_code": ["Must be exactly 8 digits"]
  }
}
```

## Error Handling Flow

**Frontend:**
- TanStack Query captures all API errors
- Toast notifications for user-facing errors
- Sentry for unhandled exceptions

**Backend:**
- FastAPI exception handlers for all error types
- Structured logging (JSON format)
- Sentry integration

---
