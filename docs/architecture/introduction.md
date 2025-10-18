# Introduction

This document outlines the complete fullstack architecture for **Customs Declaration Automation Platform**, including backend systems, frontend implementation, and their integration. It serves as the single source of truth for AI-driven development, ensuring consistency across the entire technology stack.

This unified approach combines what would traditionally be separate backend and frontend architecture documents, streamlining the development process for modern fullstack applications where these concerns are increasingly intertwined.

## Starter Template or Existing Project

**Status:** Greenfield project (no starter template)

This is a greenfield development project with no existing codebase or starter template. The monorepo structure will be built from scratch with the following technology choices:

- **Monorepo Tooling**: Simple monorepo with separate `frontend/` and `backend/` directories (no Nx/Turborepo needed for 2-package structure)
- **Deployment**: Docker Compose for all services
- **Rationale**: For an 8-week MVP with 2 developers, avoiding the complexity of monorepo tooling is pragmatic. The project structure is simple enough that npm workspaces + Docker Compose provide sufficient orchestration.

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-10-17 | 1.0 | Initial architecture document created | Winston (Architect) |

---
