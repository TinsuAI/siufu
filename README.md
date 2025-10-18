# Customs Declaration Automation Platform

Automated customs declaration processing platform for logistics operations, built with Next.js, FastAPI, and PostgreSQL.

## Overview

This platform automates the processing of customs declarations by extracting data from PDFs and Excel files, using OCR and AI to populate customs declaration forms accurately and efficiently.

## Tech Stack

- **Frontend:** Next.js 15.5.6, React 19.2, TypeScript 5.6, Tailwind CSS 4.0
- **Backend:** FastAPI 0.119, Python 3.12, SQLAlchemy 2.0
- **Database:** PostgreSQL 18.0
- **Cache/Queue:** Redis 7.4.1, Celery 5.4
- **Containerization:** Docker Compose 2.x

## Prerequisites

Before you begin, ensure you have the following installed:

- **Docker Desktop** 27.x or higher ([Download](https://www.docker.com/products/docker-desktop))
- **Git** ([Download](https://git-scm.com/downloads))

That's it! Docker Compose will handle all other dependencies.

## First-Time Setup

### 1. Clone the Repository

```bash
git clone https://github.com/client/logai.git
cd logai
```

### 2. Configure Environment Variables

Copy the environment template and configure with your actual values:

```bash
cp .env.example .env
```

Edit `.env` and update the following required variables:

- `POSTGRES_PASSWORD` - Set a secure database password
- `JWT_SECRET_KEY` - Generate with `openssl rand -hex 32`
- `OPENROUTER_API_KEY` - Your OpenRouter API key (for LLM access)
- `GOOGLE_CLOUD_PROJECT_ID` - Your Google Cloud project ID

### 3. Add Google Cloud Service Account Key

Place your Google Cloud service account JSON key file at:

```bash
mkdir -p secrets
# Copy your gcp-sa-key.json file to the secrets/ directory
cp /path/to/your/gcp-sa-key.json secrets/gcp-sa-key.json
```

> **Note:** The service account needs Document AI API permissions.

### 4. Start All Services

```bash
docker-compose up -d
```

This will start 5 services:
- `postgres` - PostgreSQL database (port 8881)
- `redis` - Redis cache/message broker (port 8882)
- `backend` - FastAPI backend (port 8880)
- `celery-worker` - Celery background task worker
- `frontend` - Next.js frontend (port 8879)

### 5. Run Database Migrations

```bash
docker-compose exec backend alembic upgrade head
```

### 6. Access the Application

**Local access:**
- **Frontend:** http://localhost:8879
- **Backend API Docs:** http://localhost:8880/docs
- **Backend ReDoc:** http://localhost:8880/redoc

**Tailscale network access:**
- **Frontend:** http://tinxudev.airplane-manta.ts.net:8879
- **Backend API Docs:** http://tinxudev.airplane-manta.ts.net:8880/docs
- **Backend ReDoc:** http://tinxudev.airplane-manta.ts.net:8880/redoc

## Common Commands

### Start Services

```bash
docker-compose up -d
```

### Stop Services

```bash
docker-compose down
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f celery-worker
```

### Restart a Service

```bash
docker-compose restart backend
```

### Run Tests

```bash
# Backend tests
docker-compose exec backend pytest

# Frontend tests
docker-compose exec frontend npm run test
```

### Access Database CLI

```bash
docker-compose exec postgres psql -U postgres -d customs_db
```

### Run Migrations

```bash
# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "Description"

# Apply migrations
docker-compose exec backend alembic upgrade head

# Rollback one migration
docker-compose exec backend alembic downgrade -1
```

### Rebuild Services

```bash
# Rebuild all services
docker-compose build

# Rebuild specific service
docker-compose build backend
```

## Development Workflow

### Local Development (Without Docker)

If you prefer to develop without Docker:

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

Access at http://localhost:3000 (or http://localhost:8879 / http://tinxudev.airplane-manta.ts.net:8879 when using Docker)

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn src.main:app --reload
```

Access at http://localhost:8000 (or http://localhost:8880 / http://tinxudev.airplane-manta.ts.net:8880 when using Docker)

### Code Quality

```bash
# Backend linting
docker-compose exec backend ruff check src/

# Backend type checking
docker-compose exec backend mypy src/

# Frontend linting
docker-compose exec frontend npm run lint
```

## Troubleshooting

### Port Already in Use

If you see errors about ports already in use:

```bash
# Check what's using the port
lsof -i :8879  # or :8880, :8881, :8882

# Kill the process or change the port in docker-compose.yml
```

### Docker Not Running

Ensure Docker Desktop is running:

```bash
docker --version
docker-compose --version
```

### Permission Errors

On Linux, you may need to add your user to the docker group:

```bash
sudo usermod -aG docker $USER
# Log out and log back in for changes to take effect
```

### Database Connection Issues

Verify the database is healthy:

```bash
docker-compose ps
# postgres should show "healthy" status

# Check database logs
docker-compose logs postgres
```

### Services Won't Start

Clean up and rebuild:

```bash
docker-compose down -v  # Warning: This removes volumes (data will be lost)
docker-compose build --no-cache
docker-compose up -d
```

### Missing Dependencies

Rebuild the containers after updating `requirements.txt` or `package.json`:

```bash
docker-compose build
docker-compose up -d
```

## Project Structure

```
logai/
├── frontend/              # Next.js application
│   ├── src/
│   │   ├── app/          # App Router pages
│   │   ├── components/   # React components
│   │   ├── hooks/        # Custom hooks
│   │   ├── lib/          # Utilities, API client
│   │   └── stores/       # Zustand stores
│   ├── Dockerfile
│   └── package.json
├── backend/              # FastAPI application
│   ├── alembic/         # Database migrations
│   ├── src/
│   │   ├── api/v1/      # API routes
│   │   ├── core/        # Config, security
│   │   ├── models/      # SQLAlchemy models
│   │   ├── repositories/# Repository pattern
│   │   ├── schemas/     # Pydantic schemas
│   │   ├── services/    # Business logic
│   │   ├── workers/     # Celery tasks
│   │   └── main.py      # App entry point
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── docs/                # Documentation
├── scripts/             # Utility scripts
├── secrets/             # Service account keys
├── docker-compose.yml   # Container orchestration
├── .env.example         # Environment template
└── README.md           # This file
```

## Support

For issues or questions:

- Check the [Troubleshooting](#troubleshooting) section
- Review Docker logs: `docker-compose logs`
- Ensure all environment variables are properly configured

## License

Proprietary - All rights reserved
