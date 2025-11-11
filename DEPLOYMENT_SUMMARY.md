# GitHub Actions CI/CD Deployment - Summary

This document provides a complete overview of the GitHub Actions CI/CD setup for deploying the Customs Declaration Automation Platform to an Ubuntu server.

## What Was Created

### 1. GitHub Actions Workflows

#### `/home/tinxu-luna/logai-focus-attemp/.github/workflows/deploy.yml`
Complete production deployment workflow that:
- Runs pre-deployment tests (backend + frontend)
- Connects to Ubuntu server via SSH
- Syncs code using rsync
- Deploys using `docker compose down` && `docker compose up -d --build`
- Runs database migrations
- Performs health checks
- Provides deployment notifications
- Supports manual triggers with option to skip tests

**Triggers:**
- Automatic: Push to `main` branch
- Manual: GitHub Actions UI with optional test skipping

#### Existing: `/home/tinxu-luna/logai-focus-attemp/.github/workflows/ci.yml`
CI pipeline for testing (already exists):
- Backend tests with PostgreSQL and Redis
- Frontend tests and build
- Docker image build verification
- Code coverage reporting

### 2. Documentation

#### `/home/tinxu-luna/logai-focus-attemp/docs/DEPLOYMENT.md` (Comprehensive Guide)
Complete 500+ line deployment guide covering:
- Architecture overview
- Prerequisites checklist
- GitHub Secrets configuration (detailed)
- Step-by-step server setup
- Complete Nginx configuration with SSL
- First-time deployment procedures
- Automated deployment workflows
- Troubleshooting guide (comprehensive)
- Rollback procedures
- Security best practices
- Monitoring and maintenance

#### `/home/tinxu-luna/logai-focus-attemp/docs/DEPLOYMENT_QUICKSTART.md` (Quick Start)
Condensed 20-minute setup guide with:
- Prerequisites checklist
- Quick setup commands
- Essential configuration steps
- Quick troubleshooting fixes
- Common commands reference

### 3. Configuration Templates

#### `/home/tinxu-luna/logai-focus-attemp/.env.production.example`
Production environment template showing:
- All required environment variables
- GitHub Secret placeholders
- Internal Docker network configuration
- Production-specific settings
- Detailed inline documentation

### 4. Setup Scripts

#### `/home/tinxu-luna/logai-focus-attemp/scripts/server-setup.sh`
Automated server setup script that:
- Verifies Ubuntu OS
- Updates system packages
- Installs Docker and Docker Compose
- Installs and configures Nginx
- Creates deployment directory structure
- Configures UFW firewall
- Provides next steps guidance

## Codebase Analysis

### Application Stack

**Backend:**
- FastAPI (Python 3.12)
- PostgreSQL 18.0 database
- Redis 7.4.1 for caching and Celery
- Celery workers for async tasks
- SQLAlchemy ORM with Alembic migrations
- Google Cloud Document AI integration

**Frontend:**
- Next.js 15.5.6 with React 19.2
- TypeScript 5.6
- Tailwind CSS 4.0
- Standalone build for production

**Infrastructure:**
- Multi-stage Docker builds
- Docker Compose orchestration
- Health checks for all services
- Volume persistence for data

### Port Mapping

| Service | Container Port | Host Port | Public Access |
|---------|---------------|-----------|---------------|
| Frontend | 3000 | 8779 | Via Nginx (/) |
| Backend | 8000 | 8780 | Via Nginx (/api) |
| PostgreSQL | 5432 | 8781 | Internal only |
| Redis | 6379 | 8782 | Internal only |

### Domain Configuration

- **Production**: https://siufu.tinsu.ai (via Cloudflare with SSL)
- **Development**: tinxudev.airplane-manta.ts.net
- **SSL**: Cloudflare Full (Strict) mode with Origin Certificates

## GitHub Secrets Required

Configure these in: **GitHub Repository → Settings → Secrets and variables → Actions**

### SSH Connection (3 secrets)
```
SSH_HOST                    # Server IP or hostname
SSH_USER                    # SSH username (e.g., ubuntu)
SSH_PRIVATE_KEY            # Private SSH key content
```

### Database (1 secret)
```
POSTGRES_PASSWORD          # PostgreSQL password (openssl rand -base64 32)
```

### Security (1 secret)
```
JWT_SECRET_KEY            # JWT signing secret (openssl rand -hex 32)
```

### External APIs (4 secrets)
```
OPENROUTER_API_KEY        # LLM API key from openrouter.ai
GOOGLE_CLOUD_PROJECT_ID   # GCP project ID
GOOGLE_CLOUD_LOCATION     # GCP region (usually "us")
GOOGLE_CLOUD_PROCESSOR_ID # Document AI processor ID
```

### Service Account (1 secret)
```
GCP_SA_KEY_JSON          # Full JSON content of GCP service account key
```

### Optional (1 secret)
```
SENTRY_DSN               # Sentry error tracking (optional)
```

**Total: 11 secrets (10 required + 1 optional)**

## Server Setup Requirements

### 1. System Requirements
- Ubuntu 20.04 LTS or higher
- Minimum 2 CPU cores
- Minimum 4GB RAM
- Minimum 10GB disk space
- Root or sudo access

### 2. Software Installation
```bash
# Run the automated setup script
bash scripts/server-setup.sh
```

Or manually:
```bash
# Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Nginx
sudo apt install nginx -y

# Utilities
sudo apt install curl wget git rsync -y
```

### 3. Nginx Configuration
- Create site config: `/etc/nginx/sites-available/siufu.tinsu.ai`
- Install SSL certificates: `/etc/nginx/ssl/siufu.tinsu.ai.{pem,key}`
- Enable site and reload Nginx

### 4. Cloudflare Configuration
- DNS: A record `siufu` → Server IP (proxied)
- SSL/TLS: Full (Strict) mode
- Create Origin Certificate for Nginx

## Deployment Workflow

### Automated Deployment (Push to Main)

```
git push origin main
    ↓
GitHub Actions Triggered
    ↓
Run Tests (Backend + Frontend)
    ↓
SSH to Server
    ↓
Create/Update .env File
    ↓
Upload GCP SA Key
    ↓
Sync Code via rsync
    ↓
docker compose down
    ↓
docker compose up -d --build
    ↓
Run Database Migrations
    ↓
Health Checks
    ↓
Deployment Complete
    ↓
Notification (Success/Failure)
```

**Estimated Time: 5-8 minutes**

### Manual Deployment

1. Go to GitHub → Actions tab
2. Select "Deploy to Production"
3. Click "Run workflow"
4. Choose to skip tests (optional)
5. Click "Run workflow"

## Nginx Routing

```
https://siufu.tinsu.ai
    ↓
Cloudflare (SSL + DDoS Protection)
    ↓
Server Nginx (Port 443)
    ↓
┌─────────────────┬──────────────────┐
│ / → Frontend    │ /api → Backend   │
│ (Port 8779)     │ (Port 8780)      │
└─────────────────┴──────────────────┘
    ↓                   ↓
Frontend Container  Backend Container
    ↓                   ↓
Backend API         PostgreSQL + Redis
```

## Health Checks

The deployment includes automated health checks:

1. **PostgreSQL**: `pg_isready` command (10s interval)
2. **Redis**: `redis-cli ping` command (10s interval)
3. **Backend**: HTTP GET `/health` endpoint (after deployment)
4. **Celery**: `celery inspect ping` command (30s interval)
5. **Container Status**: All 5 containers must be running

If any health check fails, deployment is marked as failed.

## Rollback Procedures

### Option 1: Redeploy Previous Commit
```bash
# Via GitHub Actions
1. Go to Actions → Deploy to Production
2. Run workflow from previous commit/tag
```

### Option 2: Manual Rollback on Server
```bash
cd ~/logai-production
git log --oneline -10  # Find previous commit
git checkout <previous-commit-hash>
docker compose down
docker compose up -d --build
```

### Option 3: Database Rollback
```bash
docker compose exec backend alembic downgrade -1  # Rollback one migration
docker compose exec backend alembic downgrade <revision>  # Rollback to specific
```

## Security Features

### Built-in Security
- SSH key authentication (no passwords)
- JWT token-based API authentication
- CORS restricted to production domain
- Cloudflare DDoS protection
- SSL/TLS encryption (Full Strict)
- Origin certificates for Nginx
- Secrets stored in GitHub Secrets
- Non-root Docker containers
- Environment variable isolation

### Recommendations
- Enable Cloudflare Bot Fight Mode
- Set up rate limiting in Cloudflare
- Rotate secrets quarterly
- Monitor logs for suspicious activity
- Keep system and dependencies updated
- Enable automatic security updates

## Monitoring & Logs

### Application Logs
```bash
cd ~/logai-production
docker compose logs -f              # All services
docker compose logs -f backend      # Backend only
docker compose logs -f frontend     # Frontend only
docker compose logs -f celery-worker
```

### Deployment Logs
```bash
tail -f ~/logai-production/deployment.log
```

### Nginx Logs
```bash
sudo tail -f /var/log/nginx/siufu.access.log
sudo tail -f /var/log/nginx/siufu.error.log
```

### Container Status
```bash
docker compose ps
docker stats
```

## Common Operations

### Restart Application
```bash
cd ~/logai-production
docker compose restart
```

### Rebuild and Deploy
```bash
cd ~/logai-production
docker compose down
docker compose up -d --build
```

### Run Migrations
```bash
docker compose exec backend alembic upgrade head
```

### Access Database
```bash
docker compose exec postgres psql -U postgres -d customs_db
```

### Clean Up Docker
```bash
docker system prune -a --volumes -f
```

## Troubleshooting Quick Reference

| Issue | Solution |
|-------|----------|
| SSH connection failed | Verify SSH_HOST, SSH_USER, SSH_PRIVATE_KEY secrets |
| Docker build failed | Check Dockerfile syntax, internet connection |
| Health check failed | Check logs: `docker compose logs backend` |
| Nginx 502 error | Verify backend is running: `docker compose ps` |
| Database connection failed | Check POSTGRES_PASSWORD secret |
| Migration failed | Check migration files, database state |
| Disk space full | Run: `docker system prune -a --volumes -f` |
| Port already in use | Stop conflicting service or change port |

## File Locations

### On Server
```
~/logai-production/                  # Main deployment directory
  ├── .env                          # Production environment variables
  ├── docker-compose.yml            # Compose configuration
  ├── deployment.log                # Deployment history
  ├── backend/                      # Backend code
  ├── frontend/                     # Frontend code
  ├── secrets/
  │   └── gcp-sa-key.json          # GCP service account key
  └── backups/                      # .env backups

/etc/nginx/
  ├── sites-available/siufu.tinsu.ai  # Nginx config
  ├── sites-enabled/siufu.tinsu.ai    # Enabled site symlink
  └── ssl/
      ├── siufu.tinsu.ai.pem          # SSL certificate
      └── siufu.tinsu.ai.key          # SSL private key
```

### In Repository
```
/home/tinxu-luna/logai-focus-attemp/
  ├── .github/workflows/
  │   ├── ci.yml                    # CI testing workflow
  │   └── deploy.yml                # Production deployment workflow
  ├── docs/
  │   ├── DEPLOYMENT.md             # Comprehensive deployment guide
  │   └── DEPLOYMENT_QUICKSTART.md  # Quick start guide
  ├── scripts/
  │   └── server-setup.sh           # Server setup automation
  ├── .env.example                  # Development environment template
  ├── .env.production.example       # Production environment template
  └── DEPLOYMENT_SUMMARY.md         # This file
```

## Additional Resources

1. **Full Deployment Guide**: `/home/tinxu-luna/logai-focus-attemp/docs/DEPLOYMENT.md`
2. **Quick Start Guide**: `/home/tinxu-luna/logai-focus-attemp/docs/DEPLOYMENT_QUICKSTART.md`
3. **Server Setup Script**: `/home/tinxu-luna/logai-focus-attemp/scripts/server-setup.sh`
4. **Environment Template**: `/home/tinxu-luna/logai-focus-attemp/.env.production.example`
5. **Docker Compose**: `/home/tinxu-luna/logai-focus-attemp/docker-compose.yml`

## Estimated Setup Time

| Task | Time |
|------|------|
| Server setup | 10 min |
| SSL certificates | 5 min |
| Nginx configuration | 5 min |
| GitHub Secrets | 10 min |
| First deployment | 8 min |
| Verification | 2 min |
| **Total** | **~40 min** |

## Best Practices Implemented

1. **Infrastructure as Code**: All configuration in version control
2. **Secrets Management**: Sensitive data in GitHub Secrets
3. **Automated Testing**: Tests run before deployment
4. **Health Checks**: Verify services after deployment
5. **Rollback Strategy**: Easy rollback to previous versions
6. **Logging**: Comprehensive logging at all levels
7. **Security**: Multi-layer security (Cloudflare, SSL, SSH keys)
8. **Documentation**: Detailed guides for all scenarios
9. **Automation**: Minimal manual intervention required
10. **Monitoring**: Built-in health checks and logging

## Next Steps After Setup

1. **Test the deployment**:
   - Access https://siufu.tinsu.ai
   - Test API endpoints at https://siufu.tinsu.ai/api
   - Upload test files and verify processing

2. **Set up monitoring** (optional):
   - Configure Sentry for error tracking
   - Set up uptime monitoring (UptimeRobot, Pingdom)
   - Configure log aggregation (if needed)

3. **Configure backups**:
   - Set up automated database backups
   - Configure volume snapshots
   - Test restore procedures

4. **Performance optimization**:
   - Monitor resource usage
   - Adjust container resources if needed
   - Configure CDN for static assets (via Cloudflare)

5. **Security hardening**:
   - Review Cloudflare security settings
   - Enable fail2ban on server
   - Set up automated security updates
   - Configure backup retention policy

## Support

For issues or questions:
- Review troubleshooting sections in documentation
- Check application logs: `docker compose logs`
- Check deployment logs: `~/logai-production/deployment.log`
- Check Nginx logs: `/var/log/nginx/siufu.*.log`
- Review GitHub Actions logs in repository

---

**Deployment Setup Completed**: All files created and ready for use.
**Last Updated**: 2025-11-10
