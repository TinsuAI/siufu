# Development Workflow

## Local Development Setup

```bash
# Prerequisites: Docker Desktop 27.x+

# Clone and setup
git clone https://github.com/client/logai.git
cd logai
cp .env.example .env
# Edit .env with actual API keys

# Start all services
docker-compose up -d

# Run migrations
docker-compose exec backend alembic upgrade head

# Seed initial data
docker-compose exec backend python scripts/seed-data.py

# Access application
# Frontend: http://localhost:3000
# Backend: http://localhost:8000/docs
# Login: admin@logistics.vn / admin123
```

## Development Commands

```bash
# Frontend dev (hot reload)
cd frontend && npm run dev

# Backend dev (hot reload)
cd backend && uvicorn src.main:app --reload

# Run tests
npm run test             # Frontend (Vitest)
pytest                   # Backend (pytest)
playwright test          # E2E

# Database operations
alembic revision --autogenerate -m "Add field"
alembic upgrade head
alembic downgrade -1

# Generate API client
npm run generate-client  # OpenAPI TypeScript codegen
```

---
