# Backup & Restore Guide

This guide covers backup and restore procedures for the LogAI production server.

## What Gets Backed Up

| Component | Description | Location |
|-----------|-------------|----------|
| PostgreSQL Database | All application data | `./backups/customs_db_*.sql` |
| Uploaded Files | Client-uploaded documents | `./backups/files/uploads_*.tar.gz` |
| Exports | Generated Excel reports | `./backups/files/exports_*.tar.gz` |
| Screenshots | OCR processing images | `./backups/files/screenshots_*.tar.gz` |

## Quick Commands

```bash
# Full backup (DB + files + remote sync)
./scripts/backup-all.sh

# Database only
./scripts/backup-db.sh

# Files only
./scripts/backup-files.sh

# Sync to remote server
./scripts/backup-sync.sh
```

---

## Backup Scripts

### `backup-all.sh` - Master Backup

Runs all backup steps in sequence:
1. Database backup
2. File volumes backup
3. Remote sync (if configured)

```bash
./scripts/backup-all.sh
```

### `backup-db.sh` - Database Backup

Creates a PostgreSQL SQL dump.

```bash
./scripts/backup-db.sh
```

Output: `./backups/customs_db_YYYY-MM-DD_HH-MM-SS.sql`

### `backup-files.sh` - File Volumes Backup

Creates compressed archives of Docker volumes.

```bash
./scripts/backup-files.sh
```

Output:
- `./backups/files/uploads_YYYY-MM-DD_HH-MM-SS.tar.gz`
- `./backups/files/exports_YYYY-MM-DD_HH-MM-SS.tar.gz`
- `./backups/files/screenshots_YYYY-MM-DD_HH-MM-SS.tar.gz`

### `backup-sync.sh` - Remote Sync

Syncs local backups to a remote Tailscale server.

```bash
# Configure the remote server first
export BACKUP_HOST="your-server.tail12345.ts.net"
export BACKUP_USER="your-username"  # Optional, defaults to current user
export BACKUP_PATH="~/logai-backups/"  # Optional

./scripts/backup-sync.sh
```

---

## Restore Scripts

### `restore-db.sh` - Database Restore

Restores the database from a SQL backup file.

```bash
# List available backups
./scripts/restore-db.sh

# Restore specific backup
./scripts/restore-db.sh ./backups/customs_db_2025-12-13_02-00-00.sql
```

**Warning:** This will DROP the existing database and all data!

### `restore-files.sh` - File Volumes Restore

Restores file volumes from backup archives.

```bash
# List available backups
./scripts/restore-files.sh

# Restore specific volume
./scripts/restore-files.sh uploads ./backups/files/uploads_2025-12-13_02-00-00.tar.gz
./scripts/restore-files.sh exports ./backups/files/exports_2025-12-13_02-00-00.tar.gz
./scripts/restore-files.sh screenshots ./backups/files/screenshots_2025-12-13_02-00-00.tar.gz

# Restore all volumes at once
./scripts/restore-files.sh all uploads.tar.gz exports.tar.gz screenshots.tar.gz
```

**Warning:** This will OVERWRITE existing files in the volume!

---

## Automated Backups (Cron)

### Setup

1. SSH into the production server
2. Edit crontab:
   ```bash
   crontab -e
   ```
3. Add the backup schedule:
   ```bash
   # Twice daily backups at 2 AM and 2 PM
   0 2,14 * * * cd ~/logai-production && ./scripts/backup-all.sh >> ./logs/backup.log 2>&1
   ```

### With Remote Sync

If you want to sync to a remote Tailscale server:

```bash
# Set environment variables in crontab
BACKUP_HOST=your-server.tail12345.ts.net
0 2,14 * * * cd ~/logai-production && ./scripts/backup-all.sh >> ./logs/backup.log 2>&1
```

Or add to your shell profile (`~/.bashrc` or `~/.zshrc`):
```bash
export BACKUP_HOST="your-server.tail12345.ts.net"
```

---

## Remote Server Setup

On your Tailscale backup server:

1. Create the backup directory:
   ```bash
   mkdir -p ~/logai-backups
   ```

2. Ensure SSH key authentication is set up:
   ```bash
   # On the production server
   ssh-copy-id your-user@your-server.tail12345.ts.net
   ```

3. Test the connection:
   ```bash
   ssh your-server.tail12345.ts.net "echo 'Connection works'"
   ```

---

## Retention Policy

- Backups older than **30 days** are automatically deleted
- Both database and file backups follow this policy
- Retention is applied during each backup run

To change retention, edit the `RETENTION_DAYS` variable in:
- `scripts/backup-db.sh`
- `scripts/backup-files.sh`

---

## Disaster Recovery

### Complete Restore Procedure

1. **Deploy fresh environment:**
   ```bash
   docker compose down
   docker compose up -d
   ```

2. **Wait for services to start:**
   ```bash
   docker compose ps  # Verify all services are healthy
   ```

3. **Restore database:**
   ```bash
   ./scripts/restore-db.sh ./backups/customs_db_LATEST.sql
   ```

4. **Restore file volumes:**
   ```bash
   ./scripts/restore-files.sh uploads ./backups/files/uploads_LATEST.tar.gz
   ./scripts/restore-files.sh exports ./backups/files/exports_LATEST.tar.gz
   ./scripts/restore-files.sh screenshots ./backups/files/screenshots_LATEST.tar.gz
   ```

5. **Verify:**
   - Access the frontend and check data
   - Upload a test file to verify storage works

---

## Backup Directory Structure

```
./backups/
├── customs_db_2025-12-13_02-00-00.sql
├── customs_db_2025-12-13_14-00-00.sql
├── files/
│   ├── uploads_2025-12-13_02-00-00.tar.gz
│   ├── uploads_2025-12-13_14-00-00.tar.gz
│   ├── exports_2025-12-13_02-00-00.tar.gz
│   ├── exports_2025-12-13_14-00-00.tar.gz
│   ├── screenshots_2025-12-13_02-00-00.tar.gz
│   └── screenshots_2025-12-13_14-00-00.tar.gz
└── logs/
    └── backup.log
```

---

## Troubleshooting

### "Could not determine Docker Compose project name"

Make sure Docker Compose services are running:
```bash
docker compose up -d
```

### Remote sync fails with "Connection refused"

1. Verify Tailscale is running on both servers
2. Check SSH key is authorized on remote server
3. Test connection manually: `ssh your-server.tail12345.ts.net`

### Restore fails with "database is being accessed"

Stop the backend services first:
```bash
docker compose stop backend celery-worker
./scripts/restore-db.sh ./backups/customs_db_LATEST.sql
docker compose up -d
```
