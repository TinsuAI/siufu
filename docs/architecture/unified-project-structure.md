# Unified Project Structure

```
logai/                                    # Root monorepo
├── .github/workflows/
│   ├── ci.yml                            # Run tests on PR
│   └── deploy.yml                        # Deploy to production
├── frontend/                             # Next.js 15 application
│   ├── src/
│   │   ├── app/                          # App Router pages
│   │   ├── components/                   # React components
│   │   ├── hooks/                        # Custom hooks
│   │   ├── lib/                          # Utils, API client
│   │   └── stores/                       # Zustand stores
│   ├── package.json
│   └── tsconfig.json
├── backend/                              # FastAPI application
│   ├── alembic/                          # Database migrations
│   ├── src/
│   │   ├── api/v1/                       # API routes
│   │   ├── core/                         # Config, security, database
│   │   ├── models/                       # SQLAlchemy models
│   │   ├── repositories/                 # Repository pattern
│   │   ├── schemas/                      # Pydantic schemas
│   │   ├── services/                     # Business logic
│   │   ├── workers/                      # Celery tasks
│   │   └── main.py                       # FastAPI app entry
│   ├── tests/
│   ├── requirements.txt
│   └── pyproject.toml
├── docs/
│   ├── prd.md
│   ├── front-end-spec.md
│   ├── architecture.md                   # THIS DOCUMENT
│   └── runbook.md
├── scripts/
│   ├── backup-db.sh
│   └── seed-data.py
├── docker-compose.yml                    # All 5 services
├── .env.example
├── .gitignore
└── README.md
```

---
