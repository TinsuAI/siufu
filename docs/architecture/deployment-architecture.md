# Deployment Architecture

## Docker Compose Configuration

```yaml
version: '3.8'

services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    restart: unless-stopped

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:${POSTGRES_PASSWORD}@postgres:5432/customs_db
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - uploaded-files:/app/data/uploads
      - exports:/app/data/exports
    secrets:
      - gcp-sa-key
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  celery-worker:
    build: ./backend
    command: celery -A src.workers.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:${POSTGRES_PASSWORD}@postgres:5432/customs_db
      - CELERY_BROKER_URL=redis://redis:6379/0
    volumes:
      - uploaded-files:/app/data/uploads
      - exports:/app/data/exports
    secrets:
      - gcp-sa-key
    depends_on:
      - redis
      - postgres
    restart: unless-stopped

  postgres:
    image: postgres:18.0-alpine
    environment:
      - POSTGRES_DB=customs_db
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7.4.1-alpine
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
    restart: unless-stopped

volumes:
  postgres-data:
  redis-data:
  uploaded-files:
  exports:

secrets:
  gcp-sa-key:
    file: ./secrets/gcp-sa-key.json
```

## CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
name: CI
on: [pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Backend tests
        run: |
          cd backend
          pip install -r requirements.txt
          pytest --cov=src

      - name: Frontend tests
        run: |
          cd frontend
          npm ci
          npm run test

      - name: Lint
        run: |
          cd backend && ruff check .
          cd frontend && npm run lint
```

---
