# Operations Runbook

This document contains operational procedures for maintaining the Customs Declaration Automation Platform.

## Table of Contents
- [End-to-End Declaration Processing Workflow](#end-to-end-declaration-processing-workflow)
- [Database Backup & Restore](#database-backup--restore)
- [Service Health Checks](#service-health-checks)
- [Troubleshooting](#troubleshooting)

---

## End-to-End Declaration Processing Workflow

This section documents the complete processing pipeline for customs declarations from file upload through AI extraction to review-ready status.

### Processing Stages

The system processes declarations through the following stages:

```
UPLOADED → PENDING_PROCESSING → PROCESSING_OCR → PROCESSING_LLM → READY_FOR_REVIEW
```

**Status Progression:**
1. **UPLOADED**: Files successfully uploaded, awaiting processing trigger
2. **PENDING_PROCESSING**: Processing task queued in Celery
3. **PROCESSING_OCR**: Google Document AI extracting text from 4 PDF documents
4. **PROCESSING_LLM**: GPT-5 extracting structured data from OCR results
5. **READY_FOR_REVIEW**: Extraction complete, data stored in database
6. **FAILED**: Processing encountered an error (see error handling section)

### Target Performance Metrics

**NFR1 Processing Time Target:** < 240 seconds (end-to-end)
- **Revised:** 2025-10-22 from original 90s target based on actual LLM performance
- **Rationale:** Quality prioritized over speed for MVP; 3-4 minute processing acceptable for complex customs declarations

**Actual Performance (as of 2025-10-22):**
- OCR Processing: 7-11 seconds (4 documents in parallel)
- LLM Extraction: 189-225 seconds (GPT-5 Flagship model)
- Data Storage: < 1 second
- **Total: 200-232 seconds**

✅ **Status:** Meets revised NFR1 target. Performance optimization deferred to future story.

### Processing Workflow Details

#### Stage 1: File Upload

**Endpoint:** `POST /api/v1/declarations/upload`

**Files Required (4 documents):**
- `AN.pdf` - Arrival Notice
- `BOL.pdf` - Bill of Lading
- `CO.pdf` - Certificate of Origin
- `INVOICE.pdf` or `INVOICE.jpg` - Commercial Invoice

**Optional Files:**
- `CD.xlsx` - Good List (for HS code matching)
- `TARIFF.xlsx` - Tariff rates reference

**Example Upload:**
```bash
curl -X POST http://localhost:8880/api/v1/declarations/upload \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -F "files=@resources/sample/1/AN.pdf" \
  -F "files=@resources/sample/1/BOL.pdf" \
  -F "files=@resources/sample/1/CO.pdf" \
  -F "files=@resources/sample/1/INVOICE.jpg"
```

**Response:**
```json
{
  "id": "uuid-here",
  "status": "UPLOADED",
  "uploaded_files": [
    {"filename": "AN.pdf", "file_type": "AN", "size": 461372},
    {"filename": "BOL.pdf", "file_type": "BOL", "size": 599112},
    {"filename": "CO.pdf", "file_type": "CO", "size": 989716},
    {"filename": "INVOICE.jpg", "file_type": "INVOICE", "size": 215057}
  ],
  "created_at": "2025-10-22T10:30:00Z"
}
```

#### Stage 2: Trigger Processing

**Endpoint:** `POST /api/v1/declarations/{id}/process`

**Example:**
```bash
curl -X POST http://localhost:8880/api/v1/declarations/{declaration_id}/process \
  -H "Authorization: Bearer $JWT_TOKEN"
```

**Response (202 Accepted):**
```json
{
  "declaration_id": "uuid-here",
  "status": "PENDING_PROCESSING",
  "celery_task_id": "task-uuid",
  "message": "Processing started. Poll /api/declarations/{id}/status for updates."
}
```

#### Stage 3: OCR Processing (20-30 seconds)

**What Happens:**
- Celery worker retrieves declaration and file paths from database
- All 4 documents processed in parallel using `asyncio.gather()`
- Google Document AI extracts text, tables, and key-value pairs
- OCR results cached in Redis (24-hour TTL)
- Status updated to `PROCESSING_OCR`, progress: 0.2

**OCR Cache Strategy:**
- Cache key: `ocr:result:{file_hash_sha256}`
- TTL: 86400 seconds (24 hours)
- Benefit: Reprocessing same files is 5-10x faster

**Performance:**
- Average: 7-11 seconds for 4 documents
- Cost: ~$0.52 per declaration (without caching)
- Cost: ~$0.25 per declaration (with 50% cache hit rate)

#### Stage 4: LLM Extraction (189-225 seconds)

**What Happens:**
- All 4 OCR results sent to GPT-5 with comprehensive extraction prompt
- LLM extracts all 77 fields required for Vietnamese customs declaration
- Per-field confidence scores calculated
- Status updated to `PROCESSING_LLM`, progress: 0.6

**Extracted Data Structure (77 fields across 12 categories):**
- Declaration header (6 fields)
- Importer information (5 fields)
- Exporter information (5 fields)
- Shipping & transport (10 fields)
- Package & container (6 fields)
- Invoice information (8 fields)
- Certificate of Origin (3 fields)
- Product line items (18 fields per product)
- Import duty (4 fields)
- VAT (6 fields)
- Tax summary (4 fields)
- Metadata (2 fields)

**Complete field mapping:** See `docs/stories/1.7-field-mapping.md`

**LLM Configuration:**
- Model: `openai/gpt-5` (Flagship)
- Temperature: 0.1 (deterministic extraction)
- Max tokens: 8192
- Timeout: 240 seconds

**Retry Logic:**
- Transient errors (429, 503): Exponential backoff (60s, 120s, 300s)
- Permanent errors (400, 401): Fail immediately

#### Stage 5: Data Storage (< 1 second)

**What Happens:**
- Extracted data saved to `declaration.extracted_data` JSONB field
- Confidence scores saved to `declaration.confidence_scores` JSONB field
- Performance metrics logged to Sentry
- Status updated to `READY_FOR_REVIEW`, progress: 1.0

**Database Transaction:**
- All updates wrapped in async transaction
- Rollback on any error
- NullPool used for Celery workers (avoids connection pooling issues)

#### Stage 6: Status Polling

**Endpoint:** `GET /api/v1/declarations/{id}/status`

**Example:**
```bash
curl http://localhost:8880/api/v1/declarations/{declaration_id}/status \
  -H "Authorization: Bearer $JWT_TOKEN"
```

**Response:**
```json
{
  "id": "uuid-here",
  "status": "PROCESSING_LLM",
  "processing_progress": 0.6,
  "celery_task_id": "task-uuid",
  "created_at": "2025-10-22T10:30:00Z",
  "updated_at": "2025-10-22T10:32:45Z"
}
```

**Poll Interval Recommendation:** 2-5 seconds

#### Stage 7: Retrieve Results

**Endpoint:** `GET /api/v1/declarations/{id}`

**Example:**
```bash
curl http://localhost:8880/api/v1/declarations/{declaration_id} \
  -H "Authorization: Bearer $JWT_TOKEN"
```

**Response:**
```json
{
  "id": "uuid-here",
  "status": "READY_FOR_REVIEW",
  "uploaded_files": [...],
  "extracted_data": {
    "importer": {
      "tax_code": "0104118221",
      "name": "CONG TY TNHH...",
      ...
    },
    "invoice": {
      "invoice_number": "LA2025-068",
      "invoice_total": 23385.2,
      ...
    },
    "products": [
      {
        "hs_code": "96190000",
        "quantity_1": 307700.0,
        ...
      }
    ],
    ...
  },
  "confidence_scores": {
    "importer.tax_code": 0.99,
    "invoice.invoice_number": 0.99,
    "products.0.hs_code": 0.88,
    ...
  },
  "processing_progress": 1.0,
  "created_at": "2025-10-22T10:30:00Z",
  "updated_at": "2025-10-22T10:33:52Z"
}
```

### Error Handling

#### Common Processing Failures

**1. OCR Failure**

**Status:** `FAILED`
**Error Example:** `"OCR processing failed for INVOICE.jpg: Invalid PDF format"`

**Causes:**
- Corrupted PDF file
- Unsupported file format
- Google Document AI quota exceeded
- Network timeout to Document AI API

**Resolution:**
```bash
# Check file validity
file resources/sample/1/INVOICE.jpg

# Check Document AI quota
# Navigate to: https://console.cloud.google.com/apis/api/documentai.googleapis.com/quotas

# Check Celery worker logs
docker logs logai-focus-celery-worker 2>&1 | grep -A 10 "OCR processing failed"

# Reupload with valid file
curl -X POST http://localhost:8880/api/v1/declarations/upload \
  -F "files=@corrected_INVOICE.pdf" \
  ...
```

**2. LLM Extraction Failure**

**Status:** `FAILED`
**Error Example:** `"OpenRouter API returned invalid JSON"`

**Causes:**
- OpenRouter API timeout (> 240s)
- Invalid API key or quota exceeded
- LLM returned malformed JSON
- Network connectivity issues

**Resolution:**
```bash
# Check OpenRouter API key
echo $OPENROUTER_API_KEY

# Check OpenRouter status
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"

# Check Celery worker logs for LLM errors
docker logs logai-focus-celery-worker 2>&1 | grep -A 20 "LLM extraction"

# Retry processing (OCR cached, only LLM re-runs)
curl -X POST http://localhost:8880/api/v1/declarations/{id}/process \
  -H "Authorization: Bearer $JWT_TOKEN"
```

**3. Celery Worker Not Available**

**Status:** `PENDING_PROCESSING` (stuck, never progresses)
**Error:** Task submitted but never processed

**Causes:**
- Celery worker not running
- Celery worker not connected to Redis broker
- Worker crashed or restarting

**Resolution:**
```bash
# Check Celery worker health
curl http://localhost:8880/api/v1/health/celery

# Expected healthy response:
# {"status": "healthy", "workers": 1, "worker_names": ["celery@..."]}

# If unhealthy, restart Celery worker
docker-compose restart celery-worker

# Wait 10 seconds for worker to connect
sleep 10

# Verify worker is ready
curl http://localhost:8880/api/v1/health/celery

# Retry processing
curl -X POST http://localhost:8880/api/v1/declarations/{id}/process
```

### Performance Monitoring

**Sentry Instrumentation:**

All processing stages log performance metrics to Sentry:

- `ocr_duration`: Time for OCR processing (all 4 documents)
- `llm_duration`: Time for LLM extraction
- `storage_duration`: Time for database storage
- `total_duration`: End-to-end processing time

**Sentry Alert:**
- Alert triggered if `total_duration` > 90 seconds
- Alert level: Warning

**View Metrics:**
```bash
# Check recent processing times
docker logs logai-focus-celery-worker 2>&1 | grep "succeeded in" | tail -10
```

**Example Output:**
```
Task process_declaration_task[uuid] succeeded in 200.75s:
  {'status': 'READY_FOR_REVIEW', 'ocr_duration': 10.96, 'llm_duration': 189.35, ...}
```

### Cache Strategy

**OCR Results (Redis):**
- Cache key: `ocr:result:{sha256(file_content)}`
- TTL: 86400 seconds (24 hours)
- Benefit: Reprocessing declarations with same files is 5-10x faster
- Cost savings: ~50-70% reduction in Document AI API costs

**How to Clear Cache (if needed):**
```bash
# Clear all OCR cache
docker-compose exec redis redis-cli KEYS "ocr:result:*" | xargs docker-compose exec redis redis-cli DEL

# Clear specific file cache (get hash from logs)
docker-compose exec redis redis-cli DEL "ocr:result:86e641314b5314514a0cff68fdcb74ff"
```

### Troubleshooting Guide

#### Issue: Processing Stuck at PROCESSING_OCR

**Symptoms:**
- Status remains `PROCESSING_OCR` for > 5 minutes
- Progress stuck at 0.2

**Diagnosis:**
```bash
# Check Celery worker logs
docker logs logai-focus-celery-worker 2>&1 | tail -50

# Look for Google Document AI errors
docker logs logai-focus-celery-worker 2>&1 | grep "Document AI"
```

**Common Causes:**
1. Network timeout to Google Cloud
2. Invalid GCP service account credentials
3. Document AI quota exceeded

**Resolution:**
```bash
# Verify GCP credentials mounted
docker-compose exec backend ls -la /app/secrets/gcp-service-account.json

# Test Document AI connectivity manually
# (Add test script if needed)

# Check quota in GCP Console
# https://console.cloud.google.com/apis/api/documentai.googleapis.com/quotas
```

#### Issue: Processing Stuck at PROCESSING_LLM

**Symptoms:**
- Status remains `PROCESSING_LLM` for > 5 minutes
- Progress stuck at 0.6

**Diagnosis:**
```bash
# Check Celery worker logs for LLM activity
docker logs logai-focus-celery-worker 2>&1 | grep "LLM extraction"

# Check for OpenRouter errors
docker logs logai-focus-celery-worker 2>&1 | grep "OpenRouter"
```

**Common Causes:**
1. OpenRouter API slow response (GPT-5 can take 3-4 minutes)
2. OpenRouter timeout (> 240s)
3. Invalid API key
4. Rate limit exceeded

**Resolution:**
```bash
# Verify OpenRouter API key is set
docker-compose exec backend printenv | grep OPENROUTER_API_KEY

# Check OpenRouter account status
# https://openrouter.ai/account

# If timeout, wait for Celery retry (exponential backoff)
# Retries at 60s, 120s, 300s intervals
```

#### Issue: Low Extraction Accuracy

**Symptoms:**
- Fields extracted with low confidence (< 0.70)
- Critical fields missing or incorrect
- Overall confidence score < 0.85

**Diagnosis:**
```bash
# Retrieve extracted data and check confidence scores
curl http://localhost:8880/api/v1/declarations/{id} | jq '.confidence_scores'

# Check which fields have low confidence
curl http://localhost:8880/api/v1/declarations/{id} | \
  jq '.confidence_scores | to_entries | map(select(.value < 0.7))'
```

**Common Causes:**
1. Poor quality scanned documents (blurry, rotated)
2. Handwritten text in documents
3. Non-standard document formats
4. Missing information in source documents

**Resolution:**
- For poor quality scans: Re-scan documents at higher resolution
- For handwritten text: Manually enter critical fields
- For missing data: Contact importer/exporter for complete documents
- For non-standard formats: Update LLM extraction prompt (developer task)

### API Usage Examples

**Complete workflow example:**
```bash
#!/bin/bash
# Example: Process declaration from upload to results

# 1. Upload files
RESPONSE=$(curl -s -X POST http://localhost:8880/api/v1/declarations/upload \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -F "files=@resources/sample/1/AN.pdf" \
  -F "files=@resources/sample/1/BOL.pdf" \
  -F "files=@resources/sample/1/CO.pdf" \
  -F "files=@resources/sample/1/INVOICE.jpg")

DECLARATION_ID=$(echo $RESPONSE | jq -r '.id')
echo "Declaration ID: $DECLARATION_ID"

# 2. Trigger processing
curl -s -X POST http://localhost:8880/api/v1/declarations/$DECLARATION_ID/process \
  -H "Authorization: Bearer $JWT_TOKEN"

echo "Processing started. Polling status..."

# 3. Poll status until complete
while true; do
  STATUS_RESPONSE=$(curl -s http://localhost:8880/api/v1/declarations/$DECLARATION_ID/status \
    -H "Authorization: Bearer $JWT_TOKEN")

  STATUS=$(echo $STATUS_RESPONSE | jq -r '.status')
  PROGRESS=$(echo $STATUS_RESPONSE | jq -r '.processing_progress')

  echo "Status: $STATUS | Progress: $(echo "$PROGRESS * 100" | bc)%"

  if [ "$STATUS" = "READY_FOR_REVIEW" ]; then
    echo "✓ Processing complete!"
    break
  elif [ "$STATUS" = "FAILED" ]; then
    echo "✗ Processing failed"
    echo $STATUS_RESPONSE | jq '.processing_error'
    exit 1
  fi

  sleep 5
done

# 4. Retrieve results
curl -s http://localhost:8880/api/v1/declarations/$DECLARATION_ID \
  -H "Authorization: Bearer $JWT_TOKEN" | jq '.'
```

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
