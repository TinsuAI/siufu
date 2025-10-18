# Testing Strategy

## Testing Pyramid

```
       E2E Tests (Playwright)
      /                      \
  Integration Tests (TestClient)
 /                                \
Frontend Unit (Vitest)    Backend Unit (pytest)
```

## Coverage Targets

- **Backend**: 70%+ for critical paths
- **Frontend**: 60%+ for business logic
- **E2E**: Happy path + critical error scenarios

---
