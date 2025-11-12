# Deployment Quick Start Guide

This is a condensed guide to get your application deployed quickly. For detailed information, see [DEPLOYMENT.md](DEPLOYMENT.md).

## Prerequisites Checklist

- [ ] Ubuntu server (20.04+) with root/sudo access
- [ ] Docker & Docker Compose installed on server
- [ ] GitHub repository admin access
- [ ] Domain configured in Cloudflare (siufu.tinsu.ai)
- [ ] GCP Service Account with Document AI permissions
- [ ] OpenRouter API key

## Step 1: Server Setup (5 minutes)

SSH into your Ubuntu server and run:

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Nginx
sudo apt update
sudo apt install nginx -y

# Create deployment directory
mkdir -p ~/logai-production/secrets
```

Log out and log back in for Docker permissions to take effect.

## Step 2: Generate SSH Keys (2 minutes)

On your local machine:

```bash
# Generate SSH key for GitHub Actions
ssh-keygen -t ed25519 -C "github-deploy" -f ~/.ssh/github_deploy

# Copy public key to server
ssh-copy-id -i ~/.ssh/github_deploy.pub your-user@your-server-ip

# Test connection
ssh -i ~/.ssh/github_deploy your-user@your-server-ip "echo 'Success!'"
```

## Step 3: Configure Cloudflare SSL (3 minutes)

1. Go to Cloudflare Dashboard → Your Domain → SSL/TLS → Origin Server
2. Click **Create Certificate**
3. Copy the certificate and private key

On your server:

```bash
sudo mkdir -p /etc/nginx/ssl
sudo nano /etc/nginx/ssl/siufu.tinsu.ai.pem  # Paste certificate
sudo nano /etc/nginx/ssl/siufu.tinsu.ai.key  # Paste private key
sudo chmod 600 /etc/nginx/ssl/siufu.tinsu.ai.key
```

## Step 4: Configure Nginx (3 minutes)

Create Nginx configuration:

```bash
sudo nano /etc/nginx/sites-available/siufu.tinsu.ai
```

Paste the configuration from [DEPLOYMENT.md Nginx section](DEPLOYMENT.md#nginx-configuration), then:

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/siufu.tinsu.ai /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # Remove default

# Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

## Step 5: Configure GitHub Secrets (5 minutes)

Go to GitHub repo → Settings → Secrets and variables → Actions

Add these secrets (click **New repository secret** for each):

### Required Secrets:

```bash
# SSH Connection
SSH_HOST                    # Your server IP (e.g., 203.0.113.42)
SSH_USER                    # Your server username (e.g., ubuntu)
SSH_PRIVATE_KEY            # Content of ~/.ssh/github_deploy (private key)

# Database
POSTGRES_PASSWORD          # Generate: openssl rand -base64 32

# Security
JWT_SECRET_KEY            # Generate: openssl rand -hex 32

# External APIs
OPENROUTER_API_KEY        # From https://openrouter.ai/
GOOGLE_CLOUD_PROJECT_ID   # Your GCP project ID
GOOGLE_CLOUD_LOCATION     # Usually "us"
GOOGLE_CLOUD_PROCESSOR_ID # Document AI processor ID
GCP_SA_KEY_JSON          # Full JSON content of your service account key
```

### Optional Secrets:

```bash
SENTRY_DSN               # From Sentry.io (leave blank to skip)
```

## Step 6: Deploy (1 minute)

### Option A: Automatic Deployment

Push to main branch:

```bash
git push origin main
```

Watch deployment in GitHub Actions tab.

### Option B: Manual Deployment

1. Go to GitHub → Actions tab
2. Select **Deploy to Production** workflow
3. Click **Run workflow**
4. Click **Run workflow** button

## Step 7: Verify Deployment (2 minutes)

Once deployment completes:

1. **Check website**: https://siufu.tinsu.ai
2. **Check API docs**: https://siufu-api.tinsu.ai/docs
3. **Check health**: https://siufu-api.tinsu.ai/health

On server:

```bash
cd ~/logai-production
docker compose -f docker-compose.prod.yml ps  # All services should be "Up"
docker compose -f docker-compose.prod.yml logs -f  # View logs
```

## Troubleshooting Quick Fixes

### Deployment fails with SSH error

```bash
# Verify SSH key is correct
cat ~/.ssh/github_deploy  # Copy this to SSH_PRIVATE_KEY secret

# Test SSH connection
ssh -i ~/.ssh/github_deploy $SSH_USER@$SSH_HOST
```

### Services won't start

```bash
cd ~/logai-production

# Check logs
docker compose logs

# Rebuild and restart
docker compose down
docker compose up -d --build
```

### Nginx shows error

```bash
# Check Nginx logs
sudo tail -f /var/log/nginx/siufu.error.log

# Test configuration
sudo nginx -t

# Verify SSL certificates exist
ls -l /etc/nginx/ssl/
```

### Health check fails

```bash
cd ~/logai-production

# Check container status
docker compose ps

# Check backend logs
docker compose logs backend

# Try accessing health endpoint directly
curl http://localhost:8780/health
```

## Common Commands

```bash
# View all logs
cd ~/logai-production && docker compose logs -f

# Restart service
docker compose restart backend

# Full rebuild
docker compose down && docker compose up -d --build

# Run migrations
docker compose exec backend alembic upgrade head

# Check Nginx
sudo nginx -t
sudo systemctl reload nginx
```

## What's Next?

- [ ] Set up monitoring (optional)
- [ ] Configure backups (recommended)
- [ ] Review security settings
- [ ] Test all features

For detailed information, see:
- [Full Deployment Guide](DEPLOYMENT.md)
- [Troubleshooting Section](DEPLOYMENT.md#troubleshooting)
- [Security Best Practices](DEPLOYMENT.md#security-best-practices)

## Getting Help

- **Check logs**: `docker compose logs -f`
- **View deployment log**: `tail -f ~/logai-production/deployment.log`
- **GitHub Actions logs**: Check workflow runs in GitHub
- **Full documentation**: [DEPLOYMENT.md](DEPLOYMENT.md)

## Time Estimate

- Server setup: 5 minutes
- SSH keys: 2 minutes
- Cloudflare SSL: 3 minutes
- Nginx setup: 3 minutes
- GitHub secrets: 5 minutes
- Deploy: 1 minute
- Verify: 2 minutes

**Total: ~20 minutes** for first-time setup
