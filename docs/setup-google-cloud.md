# Google Cloud Setup Guide

This guide walks through setting up Google Cloud Document AI for OCR functionality.

## Prerequisites

- Google Cloud account
- Project billing enabled (~$0.04/page for Document AI)

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a Project" → "New Project"
3. Enter project name (e.g., `logai-production`)
4. Note the **Project ID** (e.g., `logai-production-12345`)

## Step 2: Enable Document AI API

1. Navigate to [APIs & Services → Library](https://console.cloud.google.com/apis/library)
2. Search for "Document AI API"
3. Click "Enable"
4. Wait for API to be enabled (~30 seconds)

## Step 3: Create Document AI Processor

1. Navigate to [Document AI → Processors](https://console.cloud.google.com/ai/document-ai/processors)
2. Click "Create Processor"
3. Select **"Form Parser"**
4. Choose version: **pretrained-foundation-model-v1.5.1-2025-08-07**
5. Select processor location:
   - **us** (United States) - recommended for lowest latency
   - **eu** (Europe)
   - **asia-northeast1** (Tokyo)
6. Click "Create"
7. Note the following from the processor details page:
   - **Processor ID** (long alphanumeric string)
   - **Location** (e.g., `us`, `eu`)
   - **Project ID** (from Step 1)

## Step 4: Create Service Account

1. Navigate to [IAM & Admin → Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. Click "Create Service Account"
3. Enter service account details:
   - **Name**: `logai-document-ai`
   - **Description**: `Service account for LogAI Document AI OCR`
4. Click "Create and Continue"
5. Grant **"Document AI API User"** role:
   - Click "Select a role"
   - Search for "Document AI API User"
   - Select role
   - Click "Continue"
6. Click "Done"

## Step 5: Download Service Account JSON Key

1. In the Service Accounts list, find `logai-document-ai`
2. Click the three dots (⋮) → "Manage keys"
3. Click "Add Key" → "Create new key"
4. Select **JSON** format
5. Click "Create"
6. Save the downloaded JSON file securely (e.g., `gcp-sa-key.json`)

**⚠️ Security Warning**: This key file grants full access to Document AI. Keep it secure and never commit to version control.

## Step 6: Place JSON Key in Secrets Directory

1. Copy the downloaded JSON file to your project:
   ```bash
   cp ~/Downloads/logai-production-*.json ./secrets/gcp-sa-key.json
   ```

2. Verify file permissions (should be readable only by you):
   ```bash
   chmod 600 ./secrets/gcp-sa-key.json
   ```

3. Verify `.gitignore` excludes secrets directory:
   ```bash
   grep "secrets/" .gitignore
   ```

## Step 7: Update Environment Variables

1. Open `.env` file (create from `.env.example` if needed):
   ```bash
   cp .env.example .env
   ```

2. Update Google Cloud configuration variables:
   ```env
   # Google Cloud Project ID (from Step 1)
   GOOGLE_CLOUD_PROJECT_ID=logai-production-12345

   # Google Cloud Location (from Step 3)
   GOOGLE_CLOUD_LOCATION=us

   # Google Cloud Processor ID (from Step 3)
   GOOGLE_CLOUD_PROCESSOR_ID=abc123def456ghi789
   ```

## Step 8: Restart Backend Service

Restart the backend to load new credentials:

```bash
docker-compose restart backend celery-worker
```

Verify credentials loaded successfully by checking logs:

```bash
docker-compose logs backend | grep -i "google"
```

You should see no errors about missing credentials.

## Step 9: Test OCR Functionality

Run the OCR test script to verify setup:

```bash
docker-compose exec backend python scripts/test-ocr.py
```

Expected output:
```
Processing AN.pdf...
✓ Extracted 1250 characters
✓ Confidence score: 0.94
✓ Processing time: 1850ms

Processing BOL.pdf...
✓ Extracted 2100 characters
✓ Confidence score: 0.96
✓ Processing time: 2200ms

...

All tests passed! Document AI is configured correctly.
```

## Troubleshooting

### Error: "GCP service account key not found"

**Solution**: Verify the JSON key file exists at `./secrets/gcp-sa-key.json` and is mounted in Docker:
```bash
ls -la ./secrets/gcp-sa-key.json
docker-compose exec backend ls -la /app/secrets/gcp-sa-key.json
```

### Error: "Document AI API has not been enabled"

**Solution**: Enable the API in Google Cloud Console:
1. Go to [APIs & Services → Library](https://console.cloud.google.com/apis/library)
2. Search for "Document AI API"
3. Click "Enable"

### Error: "Permission denied: Document AI API User role required"

**Solution**: Grant the service account the correct role:
1. Go to [IAM & Admin → IAM](https://console.cloud.google.com/iam-admin/iam)
2. Find your service account
3. Click "Edit" (pencil icon)
4. Add role: "Document AI API User"
5. Save changes

### Error: "Quota exceeded: 60 requests/minute"

**Solution**: Implement rate limiting or request quota increase:
1. Navigate to [APIs & Services → Quotas](https://console.cloud.google.com/iam-admin/quotas)
2. Filter for "Document AI API"
3. Click "Edit Quotas"
4. Request increase (explain use case)

### Error: "Invalid processor ID"

**Solution**: Verify processor ID in Google Cloud Console:
1. Go to [Document AI → Processors](https://console.cloud.google.com/ai/document-ai/processors)
2. Click on your processor
3. Copy the processor ID from the URL or details page
4. Update `GOOGLE_CLOUD_PROCESSOR_ID` in `.env`

## Cost Estimation

Document AI pricing: **~$0.04 per page**

**Example monthly costs**:
- 1,000 declarations × 4 documents × 3 pages avg = 12,000 pages
- 12,000 pages × $0.04 = **$480/month**
- With 70% cache hit rate: **$144/month**

**Recommendations**:
- Enable Redis caching (24-hour TTL) to reduce costs
- Monitor usage via Sentry logs (page counts tracked automatically)
- Set up budget alerts in Google Cloud Console:
  1. Go to [Billing → Budgets & alerts](https://console.cloud.google.com/billing/budgets)
  2. Create budget with threshold alerts at 50%, 80%, 100%

## Additional Resources

- [Document AI Documentation](https://cloud.google.com/document-ai/docs)
- [Form Parser Model Details](https://cloud.google.com/document-ai/docs/processors-list#processor_form-parser)
- [Pricing Calculator](https://cloud.google.com/products/calculator)
- [Best Practices Guide](https://cloud.google.com/document-ai/docs/best-practices)
