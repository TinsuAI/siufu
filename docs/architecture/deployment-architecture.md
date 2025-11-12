# Deployment Architecture

## Overview

The application is deployed using Docker Compose with separate configurations for development and production environments. The production deployment uses separate domains for frontend and backend API.

### Production Domains

- **Frontend**: https://siufu.tinsu.ai
- **Backend API**: https://siufu-api.tinsu.ai
- **Infrastructure**: Ubuntu server with Docker, Nginx, Cloudflare SSL

### Architecture Diagram

```
                                    Cloudflare
                                         |
                                    [SSL/TLS]
                                         |
                    +--------------------+--------------------+
                    |                                         |
          https://siufu.tinsu.ai              https://siufu-api.tinsu.ai
                    |                                         |
                    |                                         |
              [Nginx Server]                            [Nginx Server]
            (Frontend Proxy)                           (Backend Proxy)
                    |                                         |
                    |                                         |
            localhost:8779                              localhost:8780
                    |                                         |
                    v                                         v
            +---------------+                         +---------------+
            |   Frontend    |                         |    Backend    |
            |   (Next.js)   |                         |   (FastAPI)   |
            |   Container   |                         |   Container   |
            +---------------+                         +-------+-------+
                                                              |
                                                              |
                        +---------------------+---------------+---------------+
                        |                     |                               |
                        v                     v                               v
                +---------------+     +---------------+             +-------------------+
                |   PostgreSQL  |     |     Redis     |             |  Celery Worker    |
                |   Container   |     |   Container   |             |    Container      |
                +---------------+     +---------------+             +-------------------+
```

## Docker Compose Configurations

The project uses two Docker Compose configurations:

### Development Configuration (docker-compose.yml)

**Purpose**: Local development with live code reloading

**Key Features**:
- Source code mounted as volumes
- Ports exposed for direct access
- Restart policy: `unless-stopped`
- Development environment variables
- No resource limits
- Suitable for Tailscale development domain

**Ports**:
- Frontend: 8779:3000
- Backend: 8780:8000
- PostgreSQL: 8781:5432
- Redis: 8782:6379

### Production Configuration (docker-compose.prod.yml)

**Purpose**: Production deployment with security and performance optimizations

**Key Features**:
- No source code mounts (baked into images)
- Restart policy: `always`
- Health checks with production intervals
- Resource limits (CPU/Memory)
- Log rotation configured
- Production environment variables
- Optimized Celery worker settings
- Redis maxmemory and eviction policy

**Differences from Development**:

| Feature | Development | Production |
|---------|-------------|------------|
| Source Code | Volume mounted | Baked into image |
| Restart Policy | unless-stopped | always |
| Health Checks | Basic | Production intervals (30-60s) |
| Resource Limits | None | CPU & Memory limits configured |
| Logging | Unlimited | JSON file with rotation (max size/files) |
| Celery Workers | Default | Optimized (concurrency=4, max-tasks-per-child=100) |
| Redis | Default config | maxmemory=512mb, eviction=allkeys-lru, AOF enabled |
| Build Args | None | ENVIRONMENT=production |
| Security | Development | Production-grade (read-only mounts, least privilege) |

**Usage**:

```bash
# Development
docker compose up -d
docker compose down

# Production
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml down
```

## CI/CD Pipeline

The deployment pipeline is automated using GitHub Actions.

### Workflow Overview

```
Push to main branch
        ↓
Pre-Deployment Tests (optional)
  - Backend tests (pytest)
  - Frontend tests (vitest)
  - Build verification
        ↓
Deploy to Production
  - SSH to server
  - Sync code via rsync
  - Create production .env
  - Pull base images
  - docker compose -f docker-compose.prod.yml down
  - docker compose -f docker-compose.prod.yml up -d --build
  - Run database migrations
  - Health checks
        ↓
Success/Failure Notification
```

### Key Workflow Features

1. **Pre-deployment Testing**: Runs full test suite before deployment
2. **Secure Secrets Management**: All secrets stored in GitHub Secrets
3. **Zero-downtime Strategy**: Docker health checks ensure services are ready
4. **Automated Migrations**: Database migrations run automatically
5. **Rollback on Failure**: Deployment fails fast if health checks don't pass
6. **Environment Protection**: GitHub environment protection for production
7. **Manual Trigger**: Can be triggered manually with option to skip tests

### Deployment File: `.github/workflows/deploy.yml`

Key sections:
- Uses `docker-compose.prod.yml` for production deployments
- Creates production `.env` file with correct domain configuration
- Health checks verify backend responds at `/health` endpoint
- Validates all 5 containers are running
- Logs deployment progress to `deployment.log`

## Nginx Configuration

Two separate Nginx server blocks handle the frontend and backend domains.

### Frontend Server Block (siufu.tinsu.ai)

```nginx
# Upstream definition
upstream frontend_upstream {
    server localhost:8779;
    keepalive 32;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name siufu.tinsu.ai;

    # SSL certificates
    ssl_certificate /etc/nginx/ssl/siufu.tinsu.ai.pem;
    ssl_certificate_key /etc/nginx/ssl/siufu.tinsu.ai.key;

    # Proxy to frontend
    location / {
        proxy_pass http://frontend_upstream;
        # ... proxy headers
    }
}
```

### Backend Server Block (siufu-api.tinsu.ai)

```nginx
# Upstream definition
upstream backend_upstream {
    server localhost:8780;
    keepalive 32;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name siufu-api.tinsu.ai;

    # SSL certificates
    ssl_certificate /etc/nginx/ssl/siufu-api.tinsu.ai.pem;
    ssl_certificate_key /etc/nginx/ssl/siufu-api.tinsu.ai.key;

    # Max upload size
    client_max_body_size 50M;

    # Proxy to backend
    location / {
        proxy_pass http://backend_upstream;
        # ... proxy headers and timeouts
    }
}
```

## Security

### SSL/TLS
- Cloudflare SSL (Full Strict mode)
- Cloudflare Origin Certificates
- TLS 1.2+ only
- Strong cipher suites

### Secrets Management
- GitHub Secrets for CI/CD
- Environment variables in `.env` (not committed)
- GCP service account key stored securely
- Read-only mounts for sensitive files

### CORS Configuration
```
CORS_ORIGINS=https://siufu.tinsu.ai,https://siufu-api.tinsu.ai,http://tinxudev.airplane-manta.ts.net:8779
```

### Cloudflare Protection
- DDoS protection
- Bot fight mode
- Rate limiting (recommended for API)
- WAF rules (optional)

## Monitoring & Health Checks

### Container Health Checks

- **PostgreSQL**: `pg_isready` (10s interval)
- **Redis**: `redis-cli ping` (10s interval)
- **Backend**: HTTP GET `/health` (30s interval in prod)
- **Celery Worker**: `celery inspect ping` (60s interval in prod)
- **Frontend**: HTTP GET `/` (30s interval in prod)

### Health Endpoints

- Backend Health: https://siufu-api.tinsu.ai/health
- Backend Docs: https://siufu-api.tinsu.ai/docs
- Frontend: https://siufu.tinsu.ai/

### Logging

Production logging configuration:
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "50m"  # Max 50MB per file
    max-file: "5"    # Keep 5 files
```

## Resource Management

### Production Resource Limits

**Backend**:
- Memory: 2GB limit, 512MB reserved
- CPU: 2 cores limit, 0.5 cores reserved

**Celery Worker**:
- Memory: 3GB limit, 512MB reserved
- CPU: 2 cores limit, 0.5 cores reserved

**Frontend**:
- Memory: 1GB limit, 256MB reserved
- CPU: 1 core limit, 0.25 cores reserved

**PostgreSQL**:
- Memory: 2GB limit, 512MB reserved

**Redis**:
- Memory: 512MB limit, 128MB reserved
- maxmemory: 512MB with allkeys-lru eviction

## Deployment Best Practices

1. **Always use production compose file**: `docker-compose.prod.yml`
2. **Monitor logs**: Check `deployment.log` and container logs
3. **Health checks**: Verify all endpoints respond
4. **Database backups**: Regular PostgreSQL dumps
5. **Environment backups**: `.env` files backed up before deployment
6. **Zero-downtime**: Health checks ensure services ready before routing traffic
7. **Rollback plan**: Keep previous Docker images for quick rollback

## Related Documentation

- [Full Deployment Guide](../DEPLOYMENT.md)
- [Deployment Quickstart](../DEPLOYMENT_QUICKSTART.md)
- [Deployment Checklist](../DEPLOYMENT_CHECKLIST.md)

---
