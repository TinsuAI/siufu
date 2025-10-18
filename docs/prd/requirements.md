# Requirements

## Functional Requirements

**Document Processing:**

- **FR1:** System shall accept upload of 6 files per declaration (AN.pdf, BOL.pdf, CO.pdf, INVOICE.pdf/jpg, goodlist.xls, tariff.xlsx) via drag-and-drop interface with file type and count validation
- **FR2:** System shall process document PDFs/images using Google Document AI Form Parser to extract text, tables, and key-value pairs with confidence scores
- **FR3:** System shall use GPT-5 to extract structured data from OCR results including product descriptions, quantities, prices, HS codes, company names, and dates, returning JSON with per-field confidence scores
- **FR4:** System shall fuzzy match extracted product descriptions against Good List database using rapidfuzz with 85% threshold to suggest HS codes
- **FR5:** System shall cross-validate data consistency across documents (Invoice total = CO total, BOL containers = AN containers, HS codes match between Invoice and CO, dates follow logical sequence) and flag inconsistencies for user review with low confidence scores

**Declaration Generation:**

- **FR6:** System shall generate Vietnamese customs declaration Excel file (CD.xlsx) with all extracted data mapped to proper fields
- **FR7:** System shall apply tariff rates from EXIM-Tariff database based on extracted HS codes
- **FR8:** System shall automatically calculate VAT and import duties based on applied tariff rates and invoice values
- **FR9:** System shall allow users to download final approved declaration as properly formatted Excel file matching Vietnamese customs CD.xlsx template

**Human-in-the-Loop Review:**

- **FR10:** System shall display side-by-side view showing source documents (with PDF viewer) and generated declaration draft
- **FR11:** System shall color-code fields by confidence level (green >90%, yellow 70-90%, red <70%)
- **FR12:** System shall support inline editing of any field with auto-save functionality
- **FR13:** System shall allow users to click any field to jump to corresponding source location in PDF
- **FR14:** System shall require user to explicitly approve or reject declaration before export

**Learning System:**

- **FR15:** System shall capture all user corrections to database with metadata (original value, corrected value, field name, confidence score, timestamp, user ID)
- **FR16:** System shall flag user corrections for potential knowledge base updates
- **FR17:** System shall allow users to upload updated Good List and EXIM-Tariff files to replace existing knowledge base data

**User Management:**

- **FR18:** System shall provide user authentication with email/password login
- **FR19:** System shall maintain user session for duration of work (configurable timeout)
- **FR20:** System shall track which user processed and approved each declaration for audit purposes

## Non-Functional Requirements

**Performance:**

- **NFR1:** System shall process one declaration from upload to draft ready in under 90 seconds (excluding user review time)
- **NFR2:** System shall render PDF documents within 3 seconds for documents up to 10 pages
- **NFR3:** System shall generate final Excel export within 5 seconds of user approval
- **NFR4:** System shall support 20 concurrent users without performance degradation
- **NFR5:** System shall load web pages within 2 seconds on standard broadband connection

**Reliability:**

- **NFR6:** System shall handle graceful degradation if external APIs (Google Document AI, OpenRouter) experience downtime
- **NFR7:** System shall auto-save user edits every 5 seconds to prevent data loss
- **NFR8:** System shall provide clear error messages when file upload, processing, or export fails
- **NFR9:** System shall maintain 99% uptime during business hours (8am-8pm Vietnam time)

**Security:**

- **NFR10:** System shall encrypt data at rest in PostgreSQL database
- **NFR11:** System shall use HTTPS for all production deployments
- **NFR12:** System shall authenticate API requests using JWT tokens
- **NFR13:** System shall store sensitive credentials (API keys) in environment variables, never in code
- **NFR14:** System shall provide audit trail showing all changes to declarations (who, what, when)

**Usability:**

- **NFR15:** New users shall be able to process their first declaration within 15 minutes without training
- **NFR16:** System UI shall be intuitive for users with basic Excel proficiency
- **NFR17:** System shall provide clear visual indicators for required actions (fields needing review, approval pending)

**Scalability:**

- **NFR18:** System architecture shall support future expansion to multi-tenant SaaS (even though MVP is single-tenant)
- **NFR19:** Database schema shall support 10,000+ declarations without performance degradation
- **NFR20:** System shall process declarations asynchronously to allow users to continue working during processing

**Cost Efficiency:**

- **NFR21:** System shall implement smart model routing (GPT-5 Flagship for complex, Mini for simple, Nano for validation) to minimize LLM costs
- **NFR22:** System shall cache OCR results to avoid redundant API calls if user re-uploads same document
- **NFR23:** System shall target operational cost under $0.05 per declaration for API usage

**Deployment:**

- **NFR24:** System shall run entirely within Docker Compose with all dependencies containerized
- **NFR25:** System shall store all data (database, uploaded files, cache) in Docker volumes for persistence
- **NFR26:** System shall require only Docker installation and API keys for deployment (no complex infrastructure)
- **NFR27:** System shall provide health check endpoints for monitoring service availability

**Maintainability:**

- **NFR28:** System shall use TypeScript for frontend code with strict type checking enabled
- **NFR29:** System shall use Python type hints throughout backend codebase
- **NFR30:** System shall generate API documentation automatically using FastAPI's built-in OpenAPI support

---
