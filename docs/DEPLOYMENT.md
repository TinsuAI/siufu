# Production Deployment Guide

This guide covers deploying the Customs Declaration Automation Platform to an Ubuntu server using GitHub Actions CI/CD.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [GitHub Secrets Configuration](#github-secrets-configuration)
- [Server Setup](#server-setup)
- [Nginx Configuration](#nginx-configuration)
- [First-Time Deployment](#first-time-deployment)
- [Automated Deployments](#automated-deployments)
- [Troubleshooting](#troubleshooting)
- [Rollback Procedures](#rollback-procedures)

## Architecture Overview

The application is deployed using Docker Compose on an Ubuntu server with the following components:

- **Frontend**: Next.js application (port 8779)
- **Backend**: FastAPI application (port 8780)
- **Database**: PostgreSQL 18.0 (port 8781)
- **Cache**: Redis 7.4.1 (port 8782)
- **Worker**: Celery worker for background tasks
- **Nginx**: Reverse proxy handling SSL termination and routing
- **Frontend Domain**: https://siufu.tinsu.ai (SSL via Cloudflare)
- **Backend API Domain**: https://api.siufu.tinsu.ai (SSL via Cloudflare)

### Service Mapping

| Service | Internal Port | Public Domain |
|---------|--------------|---------------|
| Frontend | 8779 | https://siufu.tinsu.ai |
| Backend API | 8780 | https://api.siufu.tinsu.ai |
| Backend Docs | 8780 | https://api.siufu.tinsu.ai/docs, https://api.siufu.tinsu.ai/redoc |

## Prerequisites

### On Your Local Machine

1. GitHub repository with admin access
2. SSH access to the Ubuntu server
3. GCP Service Account key with Document AI permissions

### On the Ubuntu Server

1. Ubuntu 20.04 LTS or higher
2. Docker Engine 27.x or higher
3. Docker Compose 2.x or higher
4. Nginx installed and configured
5. SSH server running
6. User account with sudo privileges
7. Sufficient disk space (minimum 10GB recommended)

## GitHub Secrets Configuration

Navigate to your GitHub repository settings: **Settings → Secrets and variables → Actions → New repository secret**

Add the following secrets:

### SSH Connection Secrets

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `SSH_HOST` | Server IP address or hostname | `203.0.113.42` or `server.example.com` |
| `SSH_USER` | SSH username for deployment | `deploy` or `ubuntu` |
| `SSH_PRIVATE_KEY` | Private SSH key for authentication | Contents of `~/.ssh/id_rsa` |

**Generating SSH Key Pair:**

```bash
# On your local machine
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_deploy_key

# Copy the public key to your server
ssh-copy-id -i ~/.ssh/github_deploy_key.pub your-user@your-server-ip

# Copy the private key content for GitHub Secret
cat ~/.ssh/github_deploy_key
```

### Database Secrets

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `POSTGRES_PASSWORD` | PostgreSQL database password | `SecureDBPassword123!` |

**Generating a secure password:**

```bash
openssl rand -base64 32
```

### Authentication Secrets

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `JWT_SECRET_KEY` | JWT token signing secret | Generate with: `openssl rand -hex 32` |

### External API Keys

| Secret Name | Description | Where to Get |
|-------------|-------------|--------------|
| `OPENROUTER_API_KEY` | OpenRouter API key for LLM access | https://openrouter.ai/ |
| `GOOGLE_CLOUD_PROJECT_ID` | GCP project ID | Google Cloud Console → Project Settings |
| `GOOGLE_CLOUD_LOCATION` | GCP region (e.g., `us`, `eu`) | Usually `us` for Document AI |
| `GOOGLE_CLOUD_PROCESSOR_ID` | Document AI processor ID | Google Cloud Console → Document AI |
| `GCP_SA_KEY_JSON` | Full GCP service account JSON key | Contents of `gcp-sa-key.json` file |

**For `GCP_SA_KEY_JSON`:**

```bash
# Copy the entire JSON file content
cat /path/to/gcp-sa-key.json
# Paste the entire JSON into the GitHub Secret (including { and })
```

### Optional Secrets

| Secret Name | Description | Required |
|-------------|-------------|----------|
| `SENTRY_DSN` | Sentry error tracking DSN | Optional |

## Server Setup

### 1. Initial Server Configuration

SSH into your Ubuntu server and run the following commands:

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose (if not included with Docker)
sudo apt install docker-compose-plugin -y

# Verify installation
docker --version
docker compose version

# Install Nginx
sudo apt install nginx -y

# Enable Nginx to start on boot
sudo systemctl enable nginx
```

### 2. Create Deployment Directory

```bash
# Create directory structure
mkdir -p ~/logai-production/secrets
mkdir -p ~/logai-production/backups

# Set proper permissions
chmod 700 ~/logai-production/secrets
```

### 3. Configure Firewall (if using UFW)

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

## Nginx Configuration

The application uses TWO separate domains:
- **Frontend**: https://siufu.tinsu.ai
- **Backend API**: https://api.siufu.tinsu.ai

This separation provides:
- Better security through domain isolation
- Independent SSL certificate management
- Clearer API versioning and endpoint management
- Simplified CORS configuration

### 1. Create Nginx Configuration Files

#### 1.1 Frontend Configuration (siufu.tinsu.ai)

Create the frontend configuration file:

```bash
sudo nano /etc/nginx/sites-available/siufu.tinsu.ai
```

Add the following configuration:

```nginx
# Upstream definition for frontend
upstream frontend_upstream {
    server localhost:8779;
    keepalive 32;
}

# HTTP to HTTPS redirect for frontend
server {
    listen 80;
    listen [::]:80;
    server_name siufu.tinsu.ai;

    # Allow Cloudflare SSL verification
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # Redirect all other HTTP to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server for frontend
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name siufu.tinsu.ai;

    # SSL Configuration (Cloudflare Origin Certificate)
    ssl_certificate /etc/nginx/ssl/siufu.tinsu.ai.pem;
    ssl_certificate_key /etc/nginx/ssl/siufu.tinsu.ai.key;

    # SSL Security Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    # Cloudflare Real IP Configuration
    set_real_ip_from 173.245.48.0/20;
    set_real_ip_from 103.21.244.0/22;
    set_real_ip_from 103.22.200.0/22;
    set_real_ip_from 103.31.4.0/22;
    set_real_ip_from 141.101.64.0/18;
    set_real_ip_from 108.162.192.0/18;
    set_real_ip_from 190.93.240.0/20;
    set_real_ip_from 188.114.96.0/20;
    set_real_ip_from 197.234.240.0/22;
    set_real_ip_from 198.41.128.0/17;
    set_real_ip_from 162.158.0.0/15;
    set_real_ip_from 104.16.0.0/13;
    set_real_ip_from 104.24.0.0/14;
    set_real_ip_from 172.64.0.0/13;
    set_real_ip_from 131.0.72.0/22;
    set_real_ip_from 2400:cb00::/32;
    set_real_ip_from 2606:4700::/32;
    set_real_ip_from 2803:f800::/32;
    set_real_ip_from 2405:b500::/32;
    set_real_ip_from 2405:8100::/32;
    set_real_ip_from 2a06:98c0::/29;
    set_real_ip_from 2c0f:f248::/32;
    real_ip_header CF-Connecting-IP;

    # Logging
    access_log /var/log/nginx/siufu.frontend.access.log;
    error_log /var/log/nginx/siufu.frontend.error.log;

    # Frontend (Next.js) - All requests
    location / {
        proxy_pass http://frontend_upstream;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # Next.js specific
        proxy_buffering off;
    }

    # Static files caching
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {
        proxy_pass http://frontend_upstream;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

#### 1.2 Backend API Configuration (api.siufu.tinsu.ai)

Create the backend API configuration file:

```bash
sudo nano /etc/nginx/sites-available/api.siufu.tinsu.ai
```

Add the following configuration:

```nginx
# Upstream definition for backend API
upstream backend_upstream {
    server localhost:8780;
    keepalive 32;
}

# HTTP to HTTPS redirect for API
server {
    listen 80;
    listen [::]:80;
    server_name api.siufu.tinsu.ai;

    # Allow Cloudflare SSL verification
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # Redirect all other HTTP to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server for backend API
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.siufu.tinsu.ai;

    # SSL Configuration (Cloudflare Origin Certificate)
    ssl_certificate /etc/nginx/ssl/siufu.tinsu.ai.pem;
    ssl_certificate_key /etc/nginx/ssl/siufu.tinsu.ai.key;

    # SSL Security Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    # Cloudflare Real IP Configuration
    set_real_ip_from 173.245.48.0/20;
    set_real_ip_from 103.21.244.0/22;
    set_real_ip_from 103.22.200.0/22;
    set_real_ip_from 103.31.4.0/22;
    set_real_ip_from 141.101.64.0/18;
    set_real_ip_from 108.162.192.0/18;
    set_real_ip_from 190.93.240.0/20;
    set_real_ip_from 188.114.96.0/20;
    set_real_ip_from 197.234.240.0/22;
    set_real_ip_from 198.41.128.0/17;
    set_real_ip_from 162.158.0.0/15;
    set_real_ip_from 104.16.0.0/13;
    set_real_ip_from 104.24.0.0/14;
    set_real_ip_from 172.64.0.0/13;
    set_real_ip_from 131.0.72.0/22;
    set_real_ip_from 2400:cb00::/32;
    set_real_ip_from 2606:4700::/32;
    set_real_ip_from 2803:f800::/32;
    set_real_ip_from 2405:b500::/32;
    set_real_ip_from 2405:8100::/32;
    set_real_ip_from 2a06:98c0::/29;
    set_real_ip_from 2c0f:f248::/32;
    real_ip_header CF-Connecting-IP;

    # Max upload size (for file uploads)
    client_max_body_size 50M;

    # Logging
    access_log /var/log/nginx/siufu.api.access.log;
    error_log /var/log/nginx/siufu.api.error.log;

    # Backend API - All routes
    location / {
        proxy_pass http://backend_upstream;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # Timeouts for long-running requests
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
```

### 2. Set Up SSL Certificates (Cloudflare Origin)

Since you're using Cloudflare, you'll need to set up Cloudflare Origin Certificates for **BOTH domains**.

#### 2.1 Generate Origin Certificates in Cloudflare

You can use a single wildcard certificate for both domains:

1. **Create Wildcard Certificate:**
   - Go to your domain in Cloudflare Dashboard
   - Navigate to **SSL/TLS → Origin Server**
   - Click **Create Certificate**
   - Choose "Generate private key and CSR with Cloudflare"
   - Add hostnames:
     - `siufu.tinsu.ai`
     - `api.siufu.tinsu.ai`
     - Or use wildcard: `*.tinsu.ai` and `tinsu.ai`
   - Select validity period (15 years recommended)
   - Click **Create**

#### 2.2 Install Certificates on Server

```bash
# Create SSL directory
sudo mkdir -p /etc/nginx/ssl

# Install Frontend Certificate
sudo nano /etc/nginx/ssl/siufu.tinsu.ai.pem
# Paste the Origin Certificate

sudo nano /etc/nginx/ssl/siufu.tinsu.ai.key
# Paste the Private Key

# Install Backend API Certificate (can use same cert if wildcard)
sudo nano /etc/nginx/ssl/api.siufu.tinsu.ai.pem
# Paste the Origin Certificate

sudo nano /etc/nginx/ssl/api.siufu.tinsu.ai.key
# Paste the Private Key

# Set proper permissions
sudo chmod 600 /etc/nginx/ssl/*.key
sudo chmod 644 /etc/nginx/ssl/*.pem
```

**Note**: If using a wildcard certificate, you can symlink the API certificates:

```bash
sudo ln -s /etc/nginx/ssl/siufu.tinsu.ai.pem /etc/nginx/ssl/api.siufu.tinsu.ai.pem
sudo ln -s /etc/nginx/ssl/siufu.tinsu.ai.key /etc/nginx/ssl/api.siufu.tinsu.ai.key
```

### 3. Enable Both Sites

```bash
# Create symlinks to enable both sites
sudo ln -s /etc/nginx/sites-available/siufu.tinsu.ai /etc/nginx/sites-enabled/
sudo ln -s /etc/nginx/sites-available/api.siufu.tinsu.ai /etc/nginx/sites-enabled/

# Remove default site (optional)
sudo rm /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# If test passes, reload Nginx
sudo systemctl reload nginx

# Verify both sites are enabled
ls -l /etc/nginx/sites-enabled/
```

### 4. Configure Cloudflare

In your Cloudflare dashboard for `tinsu.ai`:

1. **DNS Settings:**
   - Add A record: `siufu` → Your server IP address (Enable proxy - orange cloud)
   - Add A record: `api.siufu` → Your server IP address (Enable proxy - orange cloud)

2. **SSL/TLS Settings:**
   - SSL/TLS encryption mode: **Full (strict)**
   - Always Use HTTPS: **On**
   - Minimum TLS Version: **TLS 1.2**

3. **Firewall Rules (Optional):**
   - You can restrict access to only Cloudflare IPs for added security
   - Consider setting up rate limiting for the API domain

## Docker Compose Files: Development vs Production

This project uses two separate Docker Compose configurations:

### docker-compose.yml (Development)
- Source code mounted as volumes for live reloading
- Restart policy: `unless-stopped` (manual control)
- Ports exposed for direct access
- Development environment variables
- No resource limits
- Suitable for local development with Tailscale domain

### docker-compose.prod.yml (Production)
- No source code mounts (baked into images)
- Restart policy: `always` (automatic recovery)
- Health checks with appropriate intervals
- Production environment variables
- Resource limits (CPU/Memory)
- Log rotation configured
- Optimized for production deployment
- Uses production-grade settings for all services

**Key Differences:**

| Feature | Development | Production |
|---------|-------------|------------|
| Source Code | Volume mounted | Baked into image |
| Restart Policy | unless-stopped | always |
| Health Checks | Basic | Production intervals |
| Resource Limits | None | CPU & Memory limits |
| Logging | Unlimited | Rotated (max size/files) |
| Celery Workers | Standard | Optimized (concurrency, task limits) |
| Redis | Default | Configured with maxmemory & eviction |

**Usage:**

```bash
# Development
docker compose up -d
docker compose down

# Production
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml down
```

## First-Time Deployment

### Option 1: Manual First Deployment

1. **Clone repository on server:**

```bash
cd ~/logai-production
git clone https://github.com/your-username/logai.git .
```

2. **Create .env file:**

```bash
cp .env.example .env
nano .env  # Edit with production values
```

3. **Add GCP service account key:**

```bash
# Copy your GCP SA key to secrets directory
nano secrets/gcp-sa-key.json  # Paste JSON content
chmod 600 secrets/gcp-sa-key.json
```

4. **Start services:**

```bash
# For development
docker compose down
docker compose up -d --build

# For production (recommended)
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d --build
```

5. **Run migrations:**

```bash
docker compose exec backend alembic upgrade head
```

6. **Verify deployment:**

```bash
docker compose ps
curl http://localhost:8780/health
curl http://localhost:8779
```

### Option 2: Use GitHub Actions

After configuring all GitHub Secrets:

1. Push to the `main` branch, or
2. Manually trigger deployment:
   - Go to **Actions** tab in GitHub
   - Select **Deploy to Production** workflow
   - Click **Run workflow**
   - Choose to skip tests if needed

## Automated Deployments

### Automatic Deployment

Every push to the `main` branch automatically triggers deployment:

1. Runs tests (backend and frontend)
2. Deploys to the Ubuntu server
3. Runs database migrations
4. Performs health checks
5. Notifies on success/failure

### Manual Deployment

You can manually trigger deployment with option to skip tests:

1. Go to GitHub **Actions** tab
2. Select **Deploy to Production**
3. Click **Run workflow**
4. Select branch (usually `main`)
5. Choose whether to skip tests
6. Click **Run workflow**

### Deployment Flow

```
Push to main
    ↓
Pre-Deployment Tests (optional)
    ↓
SSH to Server
    ↓
Sync Files via rsync
    ↓
docker compose down
    ↓
docker compose up -d --build
    ↓
Run Migrations
    ↓
Health Checks
    ↓
Success/Failure Notification
```

## Troubleshooting

### View Application Logs

```bash
cd ~/logai-production

# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f celery-worker

# Last 100 lines
docker compose logs --tail=100
```

### View Deployment Log

```bash
cd ~/logai-production
tail -f deployment.log
```

### Check Container Status

```bash
docker compose ps
docker compose top
```

### Restart Services

```bash
# Restart specific service
docker compose restart backend

# Restart all services
docker compose restart

# Full rebuild
docker compose down
docker compose up -d --build
```

### Database Issues

```bash
# Connect to database
docker compose exec postgres psql -U postgres -d customs_db

# Check migrations status
docker compose exec backend alembic current

# View migration history
docker compose exec backend alembic history
```

### Nginx Issues

```bash
# Check Nginx status
sudo systemctl status nginx

# Test configuration
sudo nginx -t

# View error logs
sudo tail -f /var/log/nginx/siufu.error.log

# View access logs
sudo tail -f /var/log/nginx/siufu.access.log
```

### SSL Certificate Issues

```bash
# Verify certificate
openssl x509 -in /etc/nginx/ssl/siufu.tinsu.ai.pem -text -noout

# Check certificate expiration
openssl x509 -in /etc/nginx/ssl/siufu.tinsu.ai.pem -noout -enddate
```

### Health Check Failed

```bash
# Check backend health endpoint
curl http://localhost:8780/health

# Check if containers are running
docker compose ps

# Check backend logs for errors
docker compose logs backend --tail=50

# Check if database is ready
docker compose exec postgres pg_isready
```

### Deployment Failed in GitHub Actions

1. Check the workflow logs in GitHub Actions tab
2. Look for SSH connection errors (check SSH_HOST, SSH_USER, SSH_PRIVATE_KEY)
3. Verify all secrets are correctly configured
4. SSH into server manually and check logs
5. Ensure server has enough disk space: `df -h`
6. Check Docker daemon is running: `sudo systemctl status docker`

## Rollback Procedures

### Automatic Rollback (Not Implemented Yet)

Currently, rollback must be done manually. Future improvements could include:
- Automated rollback on health check failure
- Keep previous Docker images
- Blue-green deployment strategy

### Manual Rollback

#### Method 1: Rollback to Previous Git Commit

```bash
cd ~/logai-production

# View recent commits
git log --oneline -10

# Checkout previous commit
git checkout <previous-commit-hash>

# Redeploy
docker compose down
docker compose up -d --build

# Rollback migrations if needed
docker compose exec backend alembic downgrade -1
```

#### Method 2: Restore from Backup

```bash
cd ~/logai-production

# View available backups
ls -lh backups/

# Restore .env from backup
cp backups/.env.backup.YYYYMMDD_HHMMSS .env

# Restart services
docker compose down
docker compose up -d --build
```

#### Method 3: Redeploy from Specific Commit

Use GitHub Actions to deploy a specific commit:

1. Go to **Actions** tab
2. Select **Deploy to Production**
3. Click **Run workflow**
4. Select the branch/commit you want to deploy
5. Run the workflow

### Database Rollback

```bash
# Rollback one migration
docker compose exec backend alembic downgrade -1

# Rollback to specific revision
docker compose exec backend alembic downgrade <revision>

# View migration history
docker compose exec backend alembic history
```

## Monitoring

### Health Endpoints

- **Backend Health**: https://api.siufu.tinsu.ai/health
- **Backend API Documentation**: https://api.siufu.tinsu.ai/docs
- **Frontend**: https://siufu.tinsu.ai/

### Container Monitoring

```bash
# Container resource usage
docker stats

# Container health status
docker compose ps
```

### Log Monitoring

Set up log rotation to prevent disk space issues:

```bash
# Create logrotate config
sudo nano /etc/logrotate.d/docker-compose

# Add this configuration:
/var/lib/docker/containers/*/*.log {
    rotate 7
    daily
    compress
    missingok
    delaycompress
    copytruncate
}
```

### Disk Space Monitoring

```bash
# Check disk usage
df -h

# Clean up old Docker resources
docker system prune -a --volumes -f
```

## Security Best Practices

1. **Keep secrets secure:**
   - Never commit `.env` files
   - Rotate secrets regularly
   - Use GitHub Secrets for CI/CD

2. **Server security:**
   - Keep system updated: `sudo apt update && sudo apt upgrade`
   - Use SSH keys instead of passwords
   - Configure firewall (UFW)
   - Disable root login
   - Use fail2ban for brute-force protection

3. **Application security:**
   - Use strong JWT secrets
   - Enable CORS only for trusted domains
   - Keep dependencies updated
   - Monitor Sentry for errors (if configured)

4. **Cloudflare security:**
   - Enable Bot Fight Mode
   - Set up rate limiting
   - Use WAF rules if needed
   - Enable DDoS protection

## Support and Maintenance

### Regular Maintenance Tasks

1. **Weekly:**
   - Check application logs
   - Monitor disk space
   - Review error rates

2. **Monthly:**
   - Update Docker images: `docker compose pull`
   - Rotate secrets if needed
   - Review and clean old backups

3. **Quarterly:**
   - Update system packages
   - Review and update dependencies
   - Security audit

### Getting Help

- **Application logs**: `docker compose logs`
- **Deployment logs**: `~/logai-production/deployment.log`
- **Nginx logs**: `/var/log/nginx/siufu.*.log`
- **GitHub Actions logs**: Check workflow runs in GitHub

## Appendix

### Environment Variables Reference

See `.env.example` for full list of environment variables.

### Port Mapping

| Service | Container Port | Host Port | Public Access |
|---------|---------------|-----------|---------------|
| Frontend | 3000 | 8779 | Via Nginx (/) |
| Backend | 8000 | 8780 | Via Nginx (/api) |
| PostgreSQL | 5432 | 8781 | Internal only |
| Redis | 6379 | 8782 | Internal only |

### Useful Commands Cheat Sheet

```bash
# Deployment
cd ~/logai-production
docker compose down && docker compose up -d --build

# View logs
docker compose logs -f backend

# Run migrations
docker compose exec backend alembic upgrade head

# Access database
docker compose exec postgres psql -U postgres -d customs_db

# Check status
docker compose ps

# Restart service
docker compose restart backend

# Clean up
docker system prune -a --volumes -f

# Nginx
sudo nginx -t
sudo systemctl reload nginx
sudo tail -f /var/log/nginx/siufu.error.log
```
