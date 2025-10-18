# Operations Runbook

This document contains operational procedures for maintaining the Customs Declaration Automation Platform.

## Table of Contents
- [Database Backup & Restore](#database-backup--restore)
- [Service Health Checks](#service-health-checks)
- [Troubleshooting](#troubleshooting)

---

## Database Backup & Restore

### Automated Backup Process

**Schedule:** Daily at 2:00 AM (configured by system administrator)

**Location:** `./backups/` directory

**Retention Policy:** 30 days (older backups are automatically deleted)

**Backup File Format:** `customs_db_YYYY-MM-DD_HH-MM-SS.sql`

### Manual Backup Procedure

To trigger an ad-hoc backup before making major changes:

```bash
./scripts/backup-db.sh
```

**Expected Output:**
```
================================================
  PostgreSQL Database Backup
================================================
Timestamp: 2025-10-18_14-30-00
Backup file: ./backups/customs_db_2025-10-18_14-30-00.sql

Starting backup...
✓ Backup successful!
File: ./backups/customs_db_2025-10-18_14-30-00.sql
Size: 20K

Cleaning up backups older than 30 days...
Backups remaining: 5
```

### Database Restoration Procedure

**⚠️ WARNING:** This procedure will **completely replace** the current database. All data since the backup will be lost.

**Prerequisites:**
- Backup file available in `./backups/` directory
- Docker containers running
- System administrator access

**Steps:**

#### 1. Stop Backend and Celery Services

This prevents new database connections during restoration:

```bash
docker-compose stop backend celery-worker
```

**Verify services stopped:**
```bash
docker-compose ps
# backend and celery-worker should show "Exit" status
```

#### 2. Drop and Recreate Database

```bash
docker-compose exec postgres psql -U postgres -c "DROP DATABASE customs_db;"
docker-compose exec postgres psql -U postgres -c "CREATE DATABASE customs_db;"
```

**Expected Output:**
```
DROP DATABASE
CREATE DATABASE
```

#### 3. Restore from Backup File

Replace the timestamp with your actual backup file:

```bash
cat ./backups/customs_db_2025-10-18_02-00-00.sql | docker-compose exec -T postgres psql -U postgres -d customs_db
```

**Expected Output:**
```
SET
SET
CREATE EXTENSION
CREATE EXTENSION
CREATE TABLE
CREATE INDEX
...
(many SQL commands will execute)
```

**⏱️ Estimated Time:** 1-5 minutes depending on database size

#### 4. Verify Restoration

Check that tables were restored:

```bash
docker-compose exec postgres psql -U postgres -d customs_db -c "\dt"
```

**Expected Output:**
```
                    List of tables
 Schema |          Name           | Type  |  Owner
--------+-------------------------+-------+----------
 public | alembic_version         | table | postgres
 public | corrections             | table | postgres
 public | declarations            | table | postgres
 public | good_list_entries       | table | postgres
 public | knowledge_base_versions | table | postgres
 public | organizations           | table | postgres
 public | tariff_rates            | table | postgres
 public | users                   | table | postgres
(8 rows)
```

Check Alembic migration version:

```bash
docker-compose exec backend alembic current
```

**Expected Output:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
e3061fd0812f (head)
```

#### 5. Restart Services

```bash
docker-compose start backend celery-worker
```

**Verify services are healthy:**
```bash
docker-compose ps
# All services should show "Up" status

curl http://localhost:8880/health
# Should return {"status": "healthy", ...}
```

#### 6. Verify Data Integrity

Check record counts match expected values:

```bash
docker-compose exec postgres psql -U postgres -d customs_db -c "
SELECT
    'users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'declarations', COUNT(*) FROM declarations
UNION ALL
SELECT 'organizations', COUNT(*) FROM organizations;
"
```

---

## Troubleshooting

### Common Restoration Errors

#### Error: "database is being accessed by other users"

**Cause:** Backend or Celery services are still running

**Solution:**
```bash
docker-compose stop backend celery-worker
# Wait 5 seconds
docker-compose ps  # Verify they're stopped
# Retry DROP DATABASE command
```

#### Error: "role 'postgres' does not exist"

**Cause:** PostgreSQL container is not running properly

**Solution:**
```bash
docker-compose restart postgres
sleep 5  # Wait for PostgreSQL to start
# Retry restoration procedure
```

#### Error: "permission denied" when running backup script

**Cause:** Script is not executable

**Solution:**
```bash
chmod +x scripts/backup-db.sh
./scripts/backup-db.sh
```

#### Backup file is empty or very small (< 1KB)

**Cause:** Database backup failed but error was suppressed

**Solution:**
1. Check database connectivity:
   ```bash
   docker-compose exec postgres psql -U postgres -d customs_db -c "SELECT 1;"
   ```
2. If database is down, restart PostgreSQL:
   ```bash
   docker-compose restart postgres
   ```
3. Retry backup

---

## Service Health Checks

### Check All Services Status

```bash
docker-compose ps
```

All services should show "Up (healthy)" status.

### Check API Health

```bash
curl http://localhost:8880/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "services": {
    "api": "ok",
    "database": "ok",
    "redis": "ok"
  }
}
```

### Check Database Connectivity

```bash
docker-compose exec postgres psql -U postgres -d customs_db -c "SELECT COUNT(*) FROM users;"
```

Should return a count without errors.

### Check Redis Connectivity

```bash
docker-compose exec redis redis-cli PING
```

**Expected Output:** `PONG`

---

## Scheduling Automated Backups

### Using Cron (Linux/Mac)

1. Open crontab editor:
   ```bash
   crontab -e
   ```

2. Add daily backup at 2:00 AM:
   ```
   0 2 * * * cd /path/to/logai && ./scripts/backup-db.sh >> /var/log/customs-backup.log 2>&1
   ```

3. Save and exit. Verify:
   ```bash
   crontab -l
   ```

### Using systemd Timer (Linux)

1. Create service file `/etc/systemd/system/customs-backup.service`:
   ```ini
   [Unit]
   Description=Customs DB Backup

   [Service]
   Type=oneshot
   WorkingDirectory=/path/to/logai
   ExecStart=/path/to/logai/scripts/backup-db.sh
   User=youruser
   ```

2. Create timer file `/etc/systemd/system/customs-backup.timer`:
   ```ini
   [Unit]
   Description=Customs DB Backup Timer

   [Timer]
   OnCalendar=daily
   OnCalendar=02:00
   Persistent=true

   [Install]
   WantedBy=timers.target
   ```

3. Enable and start:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable customs-backup.timer
   sudo systemctl start customs-backup.timer
   ```

4. Check status:
   ```bash
   sudo systemctl list-timers customs-backup.timer
   ```

---

**Last Updated:** 2025-10-18
**Version:** 1.0
