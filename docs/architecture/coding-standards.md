# Coding Standards

## Critical Fullstack Rules

- **Type Sharing:** Define types in `backend/src/schemas/`, generate TypeScript types via OpenAPI
- **API Calls:** Never use direct `fetch()` - use generated API client
- **Environment Variables:** Access via `config.py` (backend) or `process.env.NEXT_PUBLIC_*` (frontend)
- **Error Handling:** All API routes use standard error middleware
- **State Updates:** Never mutate Zustand state directly

## Naming Conventions

| Element | Frontend | Backend | Example |
|---------|----------|---------|---------|
| Components | PascalCase | - | `UserProfile.tsx` |
| Hooks | camelCase with 'use' | - | `useAuth.ts` |
| API Routes | - | kebab-case | `/api/user-profile` |
| Database Tables | - | snake_case | `user_profiles` |

---
