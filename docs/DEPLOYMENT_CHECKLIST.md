# Deployment Checklist

Use this checklist to ensure all steps are completed for successful deployment.

## Pre-Deployment Setup

### Server Preparation

- [ ] Ubuntu server (20.04+) provisioned and accessible
- [ ] Root/sudo access confirmed
- [ ] Server IP address noted: `___________________`
- [ ] SSH access from local machine working
- [ ] Run server setup script: `bash scripts/server-setup.sh`

### Docker Installation

- [ ] Docker installed: `docker --version`
- [ ] Docker Compose installed: `docker compose version`
- [ ] Current user added to docker group: `sudo usermod -aG docker $USER`
- [ ] Logged out and back in for group changes

### Nginx Installation

- [ ] Nginx installed: `nginx -v`
- [ ] Nginx enabled: `sudo systemctl enable nginx`
- [ ] Nginx running: `sudo systemctl status nginx`

### Firewall Configuration

- [ ] UFW installed: `ufw --version`
- [ ] Port 22 (SSH) allowed: `sudo ufw allow 22/tcp`
- [ ] Port 80 (HTTP) allowed: `sudo ufw allow 80/tcp`
- [ ] Port 443 (HTTPS) allowed: `sudo ufw allow 443/tcp`
- [ ] UFW enabled: `sudo ufw enable`

## Cloudflare Configuration

### DNS Setup

- [ ] Logged into Cloudflare dashboard
- [ ] Domain `tinsu.ai` selected
- [ ] A record created: `siufu` → Server IP (Proxied - orange cloud)
- [ ] A record created: `api.siufu` → Server IP (Proxied - orange cloud)
- [ ] DNS propagation verified: `nslookup siufu.tinsu.ai`
- [ ] DNS propagation verified: `nslookup api.siufu.tinsu.ai`

### SSL Configuration

- [x] SSL/TLS mode: Full (Strict)
- [x] Always Use HTTPS: Enabled
- [x] Minimum TLS Version: 1.2
- [x] Origin Certificate created (15-year validity)
- [x] Origin Certificate downloaded
- [x] Private Key downloaded

### Security Settings

- [ ] Bot Fight Mode: Enabled (recommended)
- [ ] DDoS Protection: Enabled (default)
- [ ] Rate Limiting: Configured (optional)
- [ ] WAF Rules: Reviewed (optional)

## Server Configuration

### SSL Certificates

- [ ] SSL directory created: `sudo mkdir -p /etc/nginx/ssl`
- [ ] Frontend certificate uploaded: `/etc/nginx/ssl/siufu.tinsu.ai.pem`
- [ ] Frontend private key uploaded: `/etc/nginx/ssl/siufu.tinsu.ai.key`
- [ ] Backend API certificate uploaded: `/etc/nginx/ssl/api.siufu.tinsu.ai.pem`
- [ ] Backend API private key uploaded: `/etc/nginx/ssl/api.siufu.tinsu.ai.key`
- [ ] Permissions set: `sudo chmod 600 /etc/nginx/ssl/*.key && sudo chmod 644 /etc/nginx/ssl/*.pem`

### Nginx Configuration

- [ ] Frontend config created: `/etc/nginx/sites-available/siufu.tinsu.ai`
- [ ] Backend API config created: `/etc/nginx/sites-available/api.siufu.tinsu.ai`
- [ ] Configurations pasted from docs/DEPLOYMENT.md
- [ ] Frontend symlink created: `sudo ln -s /etc/nginx/sites-available/siufu.tinsu.ai /etc/nginx/sites-enabled/`
- [ ] Backend API symlink created: `sudo ln -s /etc/nginx/sites-available/api.siufu.tinsu.ai /etc/nginx/sites-enabled/`
- [ ] Default site removed: `sudo rm /etc/nginx/sites-enabled/default`
- [ ] Configuration tested: `sudo nginx -t`
- [ ] Nginx reloaded: `sudo systemctl reload nginx`

### Deployment Directory

- [ ] Directory created: `mkdir -p ~/logai-production`
- [ ] Secrets directory: `mkdir -p ~/logai-production/secrets`
- [ ] Backups directory: `mkdir -p ~/logai-production/backups`
- [ ] Permissions set: `chmod 700 ~/logai-production/secrets`

## GitHub Configuration

### Repository Access

- [ ] GitHub account has admin access to repository
- [ ] Repository URL noted: `___________________`

### SSH Key Generation

- [ ] SSH key generated: `ssh-keygen -t ed25519 -C "github-deploy" -f ~/.ssh/github_deploy`
- [ ] Public key copied to server: `ssh-copy-id -i ~/.ssh/github_deploy.pub user@server-ip`
- [ ] SSH connection tested: `ssh -i ~/.ssh/github_deploy user@server-ip`
- [ ] Private key content copied: `cat ~/.ssh/github_deploy`

### GitHub Secrets Configuration

Navigate to: **GitHub Repository → Settings → Secrets and variables → Actions**

#### SSH Secrets (3)
- [ ] `SSH_HOST` - Server IP or hostname
- [ ] `SSH_USER` - SSH username (e.g., ubuntu, deploy)
- [ ] `SSH_PRIVATE_KEY` - Private key content from `~/.ssh/github_deploy`

#### Database Secrets (1)
- [ ] `POSTGRES_PASSWORD` - Generated with: `openssl rand -base64 32`
      Value: `___________________` (store securely offline)

#### Security Secrets (1)
- [ ] `JWT_SECRET_KEY` - Generated with: `openssl rand -hex 32`
      Value: `___________________` (store securely offline)

#### External API Secrets (4)
- [ ] `OPENROUTER_API_KEY` - From https://openrouter.ai/
- [ ] `GOOGLE_CLOUD_PROJECT_ID` - GCP project ID
- [ ] `GOOGLE_CLOUD_LOCATION` - Usually "us"
- [ ] `GOOGLE_CLOUD_PROCESSOR_ID` - Document AI processor ID

#### Service Account Secret (1)
- [ ] `GCP_SA_KEY_JSON` - Full JSON file content
      File: `cat /path/to/gcp-sa-key.json` (paste entire JSON)

#### Optional Secrets (1)
- [ ] `SENTRY_DSN` - From Sentry.io (optional, can be empty)

**Total: 11 secrets configured**

## Initial Deployment

### Pre-Deployment Verification

- [ ] All GitHub Secrets configured
- [ ] Server accessible via SSH
- [ ] Nginx running and configured
- [ ] SSL certificates in place
- [ ] Cloudflare DNS propagated

### Deployment Method Selection

Choose one:

#### Option A: Automatic (Push to Main)
- [ ] Local repository on main branch: `git checkout main`
- [ ] All changes committed: `git status`
- [ ] Push to trigger deployment: `git push origin main`

#### Option B: Manual (GitHub Actions UI)
- [ ] Navigate to: GitHub Repository → Actions
- [ ] Select workflow: "Deploy to Production"
- [ ] Click: "Run workflow"
- [ ] Select branch: main
- [ ] Skip tests: No (first time)
- [ ] Click: "Run workflow"

### Monitor Deployment

- [ ] Workflow started in GitHub Actions
- [ ] Pre-deployment tests passing (if not skipped)
- [ ] SSH connection successful
- [ ] File synchronization completed
- [ ] Docker images building
- [ ] Containers starting
- [ ] Database migrations running
- [ ] Health checks passing
- [ ] Deployment completed successfully

## Post-Deployment Verification

### Website Access

- [ ] Frontend accessible: https://siufu.tinsu.ai
- [ ] Page loads without errors
- [ ] No SSL certificate warnings

### API Access

- [ ] API docs accessible: https://api.siufu.tinsu.ai/docs
- [ ] ReDoc accessible: https://api.siufu.tinsu.ai/redoc
- [ ] Health endpoint: https://api.siufu.tinsu.ai/health
      Expected response: `{"status": "healthy"}` or similar

### Server Verification

SSH into server and verify:

```bash
cd ~/logai-production
```

- [ ] All containers running: `docker compose -f docker-compose.prod.yml ps`
      Expected: 5 containers (frontend, backend, postgres, redis, celery-worker)

- [ ] Check container status:
  ```
  Name                    State     Health
  siufu-frontend         Up
  siufu-backend          Up
  siufu-postgres         Up        healthy
  siufu-redis            Up        healthy
  siufu-celery-worker    Up        healthy
  ```

- [ ] Backend logs clean: `docker compose logs backend --tail=50`
      No critical errors

- [ ] Frontend logs clean: `docker compose logs frontend --tail=50`
      No critical errors

- [ ] Database migrations current: `docker compose exec backend alembic current`

### Functional Testing

- [ ] User registration works
- [ ] User login works
- [ ] File upload works
- [ ] Document processing works
- [ ] Export generation works
- [ ] All main features functional

### Performance Checks

- [ ] Page load time acceptable (< 3 seconds)
- [ ] API response time acceptable (< 500ms for simple endpoints)
- [ ] No memory leaks: `docker stats`
- [ ] Disk space sufficient: `df -h`

### Log Verification

- [ ] Application logs: `cd ~/logai-production && docker compose logs -f`
- [ ] Deployment log: `tail -f ~/logai-production/deployment.log`
- [ ] Nginx access log: `sudo tail -f /var/log/nginx/siufu.access.log`
- [ ] Nginx error log: `sudo tail -f /var/log/nginx/siufu.error.log`

## Security Hardening (Recommended)

### Server Security

- [ ] SSH password authentication disabled
- [ ] Root login disabled: `sudo nano /etc/ssh/sshd_config`
      Set: `PermitRootLogin no`
- [ ] fail2ban installed: `sudo apt install fail2ban`
- [ ] fail2ban configured for SSH
- [ ] Automatic security updates enabled:
      `sudo apt install unattended-upgrades`

### Application Security

- [ ] Secrets rotated if needed
- [ ] .env file permissions: `chmod 600 ~/logai-production/.env`
- [ ] GCP key permissions: `chmod 600 ~/logai-production/secrets/gcp-sa-key.json`
- [ ] CORS origins verified in .env

### Monitoring Setup

- [ ] Uptime monitoring configured (UptimeRobot, Pingdom, etc.)
- [ ] Sentry configured (if using)
- [ ] Log rotation configured: `/etc/logrotate.d/docker-compose`
- [ ] Disk space monitoring set up

## Backup Configuration (Recommended)

### Database Backup

- [ ] Database backup script created
- [ ] Cron job for daily backups:
      `0 2 * * * /path/to/backup-script.sh`
- [ ] Backup retention policy defined (e.g., keep 30 days)
- [ ] Off-site backup configured (optional)

### Configuration Backup

- [ ] .env file backed up (encrypted)
- [ ] Nginx config backed up
- [ ] SSL certificates backed up (securely stored)

### Test Restore

- [ ] Database restore tested
- [ ] Full recovery procedure documented
- [ ] Restore time estimated: `_____` minutes

## Documentation

- [ ] Server access credentials documented (securely)
- [ ] Deployment procedure documented (DEPLOYMENT.md)
- [ ] Runbook created for common issues
- [ ] Team members trained on deployment process
- [ ] Emergency contacts list created

## Ongoing Maintenance

### Weekly Tasks

- [ ] Check application logs for errors
- [ ] Monitor disk space usage
- [ ] Review Cloudflare analytics
- [ ] Check for failed deployments

### Monthly Tasks

- [ ] Update Docker base images: `cd ~/logai-production && docker compose pull`
- [ ] Rebuild containers: `docker compose up -d --build`
- [ ] Review and rotate secrets (if needed)
- [ ] Clean old Docker resources: `docker system prune`
- [ ] Review backup retention

### Quarterly Tasks

- [ ] Update system packages: `sudo apt update && sudo apt upgrade`
- [ ] Security audit
- [ ] Review and update dependencies
- [ ] Test disaster recovery procedure
- [ ] Review and update documentation

## Rollback Plan

In case of deployment failure:

### Immediate Rollback
- [ ] Document rollback procedure tested
- [ ] Previous commit hash noted: `___________________`
- [ ] Rollback command prepared:
      - Via GitHub Actions: Run workflow from previous commit
      - Via Server: `cd ~/logai-production && git checkout <hash> && docker compose down && docker compose up -d --build`

### Database Rollback
- [ ] Migration rollback tested: `docker compose exec backend alembic downgrade -1`
- [ ] Database backup before deployment verified

## Sign-off

### Deployment Team

| Role | Name | Signature | Date |
|------|------|-----------|------|
| DevOps Engineer | _____________ | _____________ | ___/___/____ |
| Backend Developer | _____________ | _____________ | ___/___/____ |
| Frontend Developer | _____________ | _____________ | ___/___/____ |
| QA Engineer | _____________ | _____________ | ___/___/____ |

### Deployment Information

- **Deployment Date**: ___/___/____
- **Deployment Time**: __:__ (timezone: ____)
- **Commit Hash**: _______________________________
- **Deployed By**: _______________________________
- **Deployment Duration**: _____ minutes
- **Issues Encountered**: _______________________________
- **Resolution Notes**: _______________________________

## Emergency Contacts

| Name | Role | Phone | Email |
|------|------|-------|-------|
| _____________ | DevOps Lead | _____________ | _____________ |
| _____________ | Backend Lead | _____________ | _____________ |
| _____________ | Frontend Lead | _____________ | _____________ |
| _____________ | System Admin | _____________ | _____________ |

## Additional Resources

- Full Deployment Guide: `docs/DEPLOYMENT.md`
- Quick Start Guide: `docs/DEPLOYMENT_QUICKSTART.md`
- Architecture Diagrams: `docs/ARCHITECTURE_DIAGRAM.md`
- Deployment Summary: `DEPLOYMENT_SUMMARY.md`
- Environment Template: `.env.production.example`
- Server Setup Script: `scripts/server-setup.sh`

---

**Checklist Version**: 1.0
**Last Updated**: 2025-11-10
**Next Review Date**: ___/___/____
