# External APIs

## Google Cloud Document AI API

**Purpose:** Extract text, tables, and key-value pairs from PDF documents with high accuracy OCR including Vietnamese text support.

**Documentation:** https://cloud.google.com/document-ai/docs

**Base URL:** `https://documentai.googleapis.com/v1`

**Authentication:** Service Account Key (JSON file) mounted as Docker secret

**Rate Limits:**
- 60 requests/minute (default quota)
- Max 20MB per document, max 15 pages per API call
- 10 concurrent requests per project

**Key Endpoints:**
- `POST /v1/projects/{project}/locations/{location}/processors/{processor}:process`

**Integration Strategy:**
- Cache OCR results in Redis (24hr TTL) to avoid redundant API calls
- Retry logic with exponential backoff for transient failures
- Cost tracking: Log every API call to Sentry

**Cost Estimation:**
- Each declaration = 4 PDFs × 3 pages avg = 12 pages
- 1,000 declarations/month × 12 pages = 12,000 pages/month
- **Estimated cost**: $480-$1,440/month (with caching: 50-70% reduction)

---

## OpenRouter GPT-5 API

**Purpose:** Intelligent structured data extraction from OCR results. Handles format variations, provides per-field confidence scores.

**Documentation:** https://openrouter.ai/docs

**Base URL:** `https://openrouter.ai/api/v1`

**Authentication:** API Key (Bearer token)

**Smart Model Routing Strategy:**

| Task Type | Model | Cost/1M Tokens | Use Case |
|-----------|-------|----------------|----------|
| **Complex Multi-Doc Extraction** | `openai/gpt-5` (Flagship) | ~$15 input, ~$60 output | Correlating Invoice + CO + BOL, resolving conflicts |
| **Simple Field Extraction** | `openai/gpt-5-mini` (Mini) | ~$0.15 input, ~$0.60 output | Extracting dates, company names, container numbers |
| **Validation Tasks** | `openai/gpt-5-nano` (Nano) | ~$0.05 input, ~$0.20 output | Format checking, consistency validation |

**Estimated Cost per Declaration:**
- Complex extraction: ~$0.025
- Simple extraction: ~$0.005
- Validation: ~$0.001
- **Total**: ~$0.026/declaration (well under $0.05 target)

---
