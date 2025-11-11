# Deployment Architecture Diagram

## Production Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              INTERNET                                    │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                           CLOUDFLARE                                     │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  - SSL/TLS Termination (Visitor to Cloudflare)                   │  │
│  │  - DDoS Protection                                               │  │
│  │  - CDN & Caching                                                 │  │
│  │  - Bot Protection                                                │  │
│  │  - WAF (Web Application Firewall)                                │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  Domain: siufu.tinsu.ai → Server IP (Proxied)                          │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │ HTTPS (Full Strict Mode)
                               ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                       UBUNTU SERVER                                      │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                          NGINX                                      │ │
│  │  Port 443 (HTTPS) with Cloudflare Origin Certificate              │ │
│  │                                                                     │ │
│  │  Routing:                                                          │ │
│  │    /         → Frontend (localhost:8779)                           │ │
│  │    /api/*    → Backend  (localhost:8780)                           │ │
│  │    /docs     → Backend  (localhost:8780)                           │ │
│  │    /redoc    → Backend  (localhost:8780)                           │ │
│  └─────────────────────────┬──────────────────┬───────────────────────┘ │
│                            │                  │                          │
│                            ↓                  ↓                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    DOCKER NETWORK (siufu-network)                │   │
│  │                                                                   │   │
│  │  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐ │   │
│  │  │   FRONTEND      │  │     BACKEND      │  │  CELERY WORKER │ │   │
│  │  │   (Next.js)     │  │    (FastAPI)     │  │   (Celery)     │ │   │
│  │  │                 │  │                  │  │                │ │   │
│  │  │  Container      │  │  Container       │  │  Container     │ │   │
│  │  │  Port: 3000     │  │  Port: 8000      │  │  (No HTTP)     │ │   │
│  │  │  Host: 8779     │  │  Host: 8780      │  │                │ │   │
│  │  └────────┬────────┘  └────────┬─────────┘  └───────┬────────┘ │   │
│  │           │                    │                     │          │   │
│  │           │                    ↓                     ↓          │   │
│  │           │         ┌──────────────────┐   ┌────────────────┐  │   │
│  │           │         │   POSTGRESQL     │   │     REDIS      │  │   │
│  │           │         │   (Database)     │   │  (Cache/Queue) │  │   │
│  │           │         │                  │   │                │  │   │
│  │           │         │  Container       │   │  Container     │  │   │
│  │           │         │  Port: 5432      │   │  Port: 6379    │  │   │
│  │           │         │  Host: 8781      │   │  Host: 8782    │  │   │
│  │           │         └──────────────────┘   └────────────────┘  │   │
│  │           │                    ↑                     ↑          │   │
│  │           └────────────────────┴─────────────────────┘          │   │
│  │                                                                  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │                    DOCKER VOLUMES                               │    │
│  │  - postgres-data    (Database files)                            │    │
│  │  - redis-data       (Cache data)                                │    │
│  │  - uploaded-files   (User uploads)                              │    │
│  │  - exports          (Generated files)                           │    │
│  │  - screenshots      (Test screenshots)                          │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │                    HOST FILESYSTEM                              │    │
│  │  ~/logai-production/                                            │    │
│  │    ├── .env                  (Environment variables)            │    │
│  │    ├── docker-compose.yml    (Container orchestration)          │    │
│  │    ├── backend/              (FastAPI code)                     │    │
│  │    ├── frontend/             (Next.js code)                     │    │
│  │    ├── secrets/              (GCP service account key)          │    │
│  │    ├── backups/              (.env backups)                     │    │
│  │    └── deployment.log        (Deployment history)               │    │
│  └────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────┘
```

## CI/CD Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        DEVELOPER WORKFLOW                                │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                      git push origin main
                               │
                               ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                         GITHUB REPOSITORY                                │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                      GitHub Actions                                 │ │
│  │                                                                     │ │
│  │  Workflow: deploy.yml                                              │ │
│  │                                                                     │ │
│  │  Step 1: Pre-Deployment Tests                                      │ │
│  │    ├─ Backend Tests (pytest)                                       │ │
│  │    ├─ Frontend Tests (vitest)                                      │ │
│  │    └─ Build Verification                                           │ │
│  │                                                                     │ │
│  │  Step 2: SSH Connection                                            │ │
│  │    ├─ Setup SSH key from secrets                                   │ │
│  │    ├─ Test connection to server                                    │ │
│  │    └─ Verify access                                                │ │
│  │                                                                     │ │
│  │  Step 3: File Synchronization                                      │ │
│  │    ├─ Create deployment directories                                │ │
│  │    ├─ Upload GCP service account key                              │ │
│  │    ├─ Generate production .env                                     │ │
│  │    └─ Rsync code to server                                         │ │
│  │                                                                     │ │
│  │  Step 4: Docker Deployment                                         │ │
│  │    ├─ docker compose down                                          │ │
│  │    ├─ docker compose up -d --build                                │ │
│  │    └─ Wait for services to start                                   │ │
│  │                                                                     │ │
│  │  Step 5: Database Migration                                        │ │
│  │    └─ alembic upgrade head                                         │ │
│  │                                                                     │ │
│  │  Step 6: Health Checks                                             │ │
│  │    ├─ Backend health endpoint                                      │ │
│  │    ├─ Container status verification                                │ │
│  │    └─ Service availability checks                                  │ │
│  │                                                                     │ │
│  │  Step 7: Notification                                              │ │
│  │    └─ Success/Failure notification                                 │ │
│  │                                                                     │ │
│  └────────────────────────────┬───────────────────────────────────────┘ │
└────────────────────────────────┼───────────────────────────────────────┘
                                 │ SSH over port 22
                                 ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                        UBUNTU SERVER                                     │
│                                                                          │
│  Deployment triggered by GitHub Actions                                 │
│  Services automatically updated via Docker Compose                      │
└──────────────────────────────────────────────────────────────────────────┘
```

## Request Flow (Production)

```
User Browser
      │
      │ HTTPS Request
      │ (e.g., GET https://siufu.tinsu.ai)
      ↓
Cloudflare Edge Network
      │
      │ - DDoS Protection
      │ - SSL Termination (Visitor ↔ Cloudflare)
      │ - Caching
      │ - Bot Detection
      ↓
      │ HTTPS (Full Strict)
      │ (Cloudflare ↔ Origin)
      ↓
Ubuntu Server - Nginx (Port 443)
      │
      │ Route: / (Frontend)
      ↓
Next.js Frontend Container (Port 8779)
      │
      │ API Request
      │ (e.g., POST /api/declarations)
      ↓
Nginx (Proxy pass to backend)
      │
      │ Route: /api/* → Backend
      ↓
FastAPI Backend Container (Port 8780)
      ├─────────────┬──────────────┐
      ↓             ↓              ↓
  PostgreSQL    Redis        Celery Worker
  (Port 8781)  (Port 8782)   (Background)
      │             │              │
      │             │              │
      ↓             ↓              ↓
  Database      Cache/Queue    Async Tasks
  Queries       Operations     (OCR, AI)
      │             │              │
      └─────────────┴──────────────┘
                    │
                    ↓
              Response Data
                    │
                    ↓
            FastAPI Backend
                    │
                    ↓
             Next.js Frontend
                    │
                    ↓
               Cloudflare
                    │
                    ↓
              User Browser
```

## Service Dependencies

```
┌─────────────────────────────────────────────────────────────┐
│                     Service Startup Order                    │
└─────────────────────────────────────────────────────────────┘

1. PostgreSQL (postgres)
   └─ Health: pg_isready
      └─ Status: healthy

2. Redis (redis)
   └─ Health: redis-cli ping
      └─ Status: healthy

3. Backend (backend)
   └─ Depends on: postgres (healthy), redis (healthy)
      └─ Status: started

4. Celery Worker (celery-worker)
   └─ Depends on: postgres (healthy), redis (healthy), backend (started)
      └─ Health: celery inspect ping
         └─ Status: healthy

5. Frontend (frontend)
   └─ Depends on: backend (started)
      └─ Status: started

All services connected via: siufu-network (Docker bridge network)
```

## Data Flow for Document Processing

```
User Uploads PDF/Excel
      │
      ↓
Frontend (Next.js)
      │ POST /api/documents
      ↓
Backend API (FastAPI)
      │
      ├─ Save file to volume: uploaded-files
      │
      ├─ Store metadata in PostgreSQL
      │
      └─ Queue processing task to Celery (via Redis)
            │
            ↓
      Celery Worker picks up task
            │
            ├─ Read file from uploaded-files volume
            │
            ├─ Call Google Cloud Document AI
            │  (Using GCP service account key)
            │
            ├─ Process with OpenRouter LLM
            │  (Data extraction & validation)
            │
            ├─ Store results in PostgreSQL
            │
            ├─ Cache results in Redis
            │
            └─ Generate export file to exports volume
                  │
                  ↓
      Task complete notification
            │
            ↓
      Frontend polls for status
            │
            ↓
      Display results to user
```

## Network Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     siufu-network (Bridge)                   │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │  frontend    │  │   backend    │  │  celery-worker  │  │
│  │  (3000)      │  │   (8000)     │  │   (no ports)    │  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬────────┘  │
│         │                 │                    │            │
│         │                 │                    │            │
│         └─────────────────┼────────────────────┘            │
│                           │                                 │
│                  ┌────────┴────────┐                        │
│                  │                 │                        │
│           ┌──────┴──────┐   ┌─────┴──────┐                │
│           │  postgres   │   │   redis    │                │
│           │  (5432)     │   │   (6379)   │                │
│           └─────────────┘   └────────────┘                │
│                                                              │
│  All containers communicate via service names:              │
│    - backend → postgres:5432                                │
│    - backend → redis:6379                                   │
│    - frontend → backend:8000 (internal)                     │
│    - celery-worker → redis:6379                             │
│    - celery-worker → postgres:5432                          │
└─────────────────────────────────────────────────────────────┘

Host Network (Ubuntu Server)
  ├─ Port 443  → Nginx (HTTPS)
  ├─ Port 80   → Nginx (HTTP → HTTPS redirect)
  ├─ Port 8779 → Frontend container (for Nginx proxy)
  ├─ Port 8780 → Backend container (for Nginx proxy)
  ├─ Port 8781 → PostgreSQL (optional, for direct access)
  └─ Port 8782 → Redis (optional, for direct access)
```

## Security Layers

```
┌─────────────────────────────────────────────────────────────┐
│                        Security Layers                       │
└─────────────────────────────────────────────────────────────┘

Layer 1: Cloudflare
  ├─ DDoS Protection
  ├─ Bot Detection & Challenge
  ├─ WAF (Web Application Firewall)
  ├─ Rate Limiting
  └─ SSL/TLS Encryption (Visitor → Cloudflare)

Layer 2: Nginx (Ubuntu Server)
  ├─ SSL/TLS with Origin Certificate (Cloudflare → Server)
  ├─ Request filtering
  ├─ Rate limiting (optional)
  └─ Security headers (X-Frame-Options, X-Content-Type-Options, etc.)

Layer 3: Application (Docker Containers)
  ├─ JWT Authentication (Backend)
  ├─ CORS restrictions
  ├─ Input validation
  ├─ SQL injection prevention (SQLAlchemy ORM)
  └─ XSS protection

Layer 4: Infrastructure
  ├─ SSH key authentication (no passwords)
  ├─ UFW Firewall (ports 22, 80, 443 only)
  ├─ Non-root Docker containers
  ├─ Secrets management (GitHub Secrets)
  └─ Environment isolation (.env files)

Layer 5: Network
  ├─ Docker bridge network isolation
  ├─ No direct database/redis access from internet
  ├─ Internal service-to-service communication only
  └─ Volume permissions and isolation
```

## Backup Strategy (Recommended)

```
┌─────────────────────────────────────────────────────────────┐
│                       Backup Points                          │
└─────────────────────────────────────────────────────────────┘

1. Database (PostgreSQL)
   └─ Daily automated dumps
      └─ pg_dump customs_db > backup_$(date +%Y%m%d).sql

2. Docker Volumes
   └─ Weekly snapshots
      ├─ postgres-data
      ├─ uploaded-files
      └─ exports

3. Configuration Files
   └─ Continuous backup (on change)
      ├─ .env (encrypted)
      ├─ nginx config
      └─ docker-compose.yml

4. Code Repository
   └─ Automatic (Git)
      └─ GitHub with full history

5. SSL Certificates
   └─ Store securely (15-year validity)
      └─ Cloudflare Origin Certificates
```

## Monitoring Points

```
┌─────────────────────────────────────────────────────────────┐
│                     Monitoring Strategy                      │
└─────────────────────────────────────────────────────────────┘

Application Level:
  ├─ Health endpoints (/health, /api/health)
  ├─ Response times
  ├─ Error rates (Sentry integration)
  └─ API request/response logs

Infrastructure Level:
  ├─ Container status (docker compose ps)
  ├─ Container resources (docker stats)
  ├─ Disk space usage (df -h)
  └─ Network connectivity

Service Level:
  ├─ PostgreSQL: Connection pool, query times
  ├─ Redis: Memory usage, hit rate
  ├─ Celery: Task queue length, success rate
  └─ Nginx: Access logs, error logs

External Level:
  ├─ Uptime monitoring (UptimeRobot, Pingdom)
  ├─ SSL certificate expiration
  ├─ Domain DNS resolution
  └─ Cloudflare analytics
```

This architecture provides:
- High availability with health checks
- Scalability via container orchestration
- Security through multiple layers
- Easy deployment via GitHub Actions
- Monitoring and observability
- Disaster recovery through backups
