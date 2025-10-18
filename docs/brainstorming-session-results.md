# Brainstorming Session Results

**Session Date:** 2025-10-17
**Facilitator:** Business Analyst Mary 📊
**Participant:** Development Team

---

## Executive Summary

### Topic
**Customs Declaration Automation Tool for Logistics Business**

A cloud-based SaaS platform to automatically generate Vietnamese customs declarations from 6 input files (4 document PDFs/images + 2 data Excel files) with Human-in-the-Loop review and continuous learning capabilities.

### Session Goals
- Explore technical approaches for document processing automation
- Design architecture with accuracy as primary goal (optimize cost later)
- Implement learning knowledge base that improves over time
- Create Human-in-the-Loop interface for verification and corrections

### Techniques Used
1. First Principles Thinking (30 min)
2. Architecture Comparison Analysis (45 min)
3. Technology Stack Research & Evaluation (60 min)
4. Cost-Benefit Analysis (20 min)

### Total Ideas Generated
**87 distinct concepts** across architecture, technology, workflow, and implementation strategies

### Key Themes Identified
- **Accuracy First:** Prioritize best-in-class AI/ML tools before cost optimization
- **Learning System:** Platform must improve from user corrections
- **Data Sovereignty:** Client-updatable knowledge base (Good List, Tariff data)
- **Human Oversight:** HITL interface essential for customs compliance
- **Hybrid Intelligence:** Combine LLM (complex reasoning) + spaCy (validation/matching) for optimal results
- **Modern Stack:** Use latest 2025 versions of all technologies
- **Local Deployment:** Docker-based with local storage, no cloud vendor lock-in

---

## Technique Sessions

### Session 1: First Principles Thinking - 30 minutes

**Description:** Deconstructing the customs declaration problem to fundamental components and rebuilding from ground up.

#### Ideas Generated

1. **Core Problem Definition**
   - Input: 6 heterogeneous files (PDFs, images, Excel) per declaration
   - Challenge: Multi-format OCR + data normalization + intelligent matching
   - Output: Structured Excel customs declaration (Vietnamese format)

2. **Fundamental Data Flow**
   - Document Classification → OCR → Extraction → Matching → Validation → Generation

3. **Critical Success Factors**
   - OCR accuracy >95% (invoices often have tables, mixed languages)
   - HS Code matching precision (incorrect codes = customs penalties)
   - Cross-document validation (data consistency across 6 files)
   - Audit trail (compliance requirement)

4. **Essential Data Elements** (from customs research)
   - HS/Tariff codes (8 digits)
   - Goods description (Vietnamese + English)
   - Value of goods (with currency)
   - Country of origin
   - Quantity and units
   - Buyer/Seller information

5. **Data Validation Anchors**
   - HS Code appears in multiple documents (Invoice, Certificate of Origin)
   - Can cross-reference for accuracy
   - Totals must reconcile (Invoice = Certificate of Origin = Bill of Lading)

#### Insights Discovered
- The HS Code is the "data validation anchor" - appears across multiple documents
- Historical data (goodlist1.xls: 1,294 records) provides valuable training data
- Document format variations are predictable (same info, different presentation)
- Problem is actually: **data extraction + normalization + intelligent matching**

#### Notable Connections
- Good List Excel files = living knowledge base, not static reference
- User corrections = training data for future improvements
- OCR errors are predictable (159,800 vs 159.800) - can be pattern-matched

---

### Session 2: Architecture Comparison - 45 minutes

**Description:** Comparing Cloud SaaS vs Local Pipeline vs Hybrid architectures for optimal approach.

#### Ideas Generated

1. **Cloud-based SaaS Architecture**
   - Web app with file upload
   - Cloud AI services (AWS Textract, Google Document AI)
   - Auto-scaling processing
   - Multi-tenant ready
   - **Pros:** Accessibility, scalability, powerful AI
   - **Cons:** Data privacy, ongoing costs, internet dependency

2. **Local Pipeline Architecture**
   - Sequential processing stages
   - On-premise deployment
   - Open-source OCR (Tesseract, PaddleOCR)
   - **Pros:** Data sovereignty, one-time cost, offline capable
   - **Cons:** Limited AI options, manual updates, hardware dependent

3. **Hybrid Approach (Selected)**
   - Cloud AI for OCR (Google Document AI - 99% accuracy)
   - Cloud LLM for extraction (GPT-5 via OpenRouter)
   - Local processing for matching/validation (spaCy)
   - Local storage (Docker volumes)
   - **Best of both worlds:** Accuracy + control

4. **Microservices Architecture Consideration**
   - Separate services: OCR, Extraction, Matching, Generation
   - Benefit: Independently scalable
   - Rejected for MVP: Added complexity, team is small

5. **Event-Driven Architecture**
   - Upload → Queue → Process → Notify
   - Using Celery + Redis for background tasks
   - Allows async processing of 50 declarations/day

#### Insights Discovered
- Data privacy is critical for customs data (rejected pure cloud)
- Cloud AI accuracy (95-99%) justifies API costs for first client
- Local storage in Docker provides control without infrastructure complexity
- Hybrid approach provides upgrade path (can replace cloud AI later)

#### Notable Connections
- Choice of architecture directly impacts: cost, scalability, compliance
- Docker deployment allows future migration to any cloud (GCP, AWS, on-premise)
- Pipeline stages map cleanly to microservices (future evolution path)

---

### Session 3: Technology Stack Evaluation - 60 minutes

**Description:** Researching and selecting latest 2025 versions across frontend, backend, AI/ML, database, and deployment technologies.

#### Ideas Generated

**Frontend Technologies (12 options evaluated):**

1. **Next.js 15.5.6** (Selected - Latest stable, App Router, RSC)
2. React 19.2 (Latest with Effect Events)
3. Tailwind CSS 4.0 (Major v4 rewrite, 100x faster builds)
4. shadcn/ui (Latest component library, Radix UI primitives)
5. TypeScript 5.6 (Type safety for complex data structures)
6. Zustand 5.0 (Lightweight state management)
7. Tanstack Query 5.59 (Server state, perfect for HITL interface)
8. React Hook Form 7.53 (Form handling with validation)
9. react-pdf 9.1 (PDF viewing for source document verification)
10. Zod 3.23 (Schema validation)

**Backend Technologies (15 options evaluated):**

11. **Python 3.14.0** (Latest stable, October 2025 release)
12. **FastAPI 0.119.0** (Latest, async-native, auto-docs)
13. **Google Document AI** (pretrained-foundation-model-v1.5.1-2025-08-07)
14. **GPT-5 via OpenRouter.ai** (openai/gpt-5, released August 2025)
15. **spaCy 3.8.7** (Latest NLP library, May 2025)
16. PostgreSQL 18.0 (Latest stable, September 2025)
17. Redis 7.4.1 (Cache + Celery message broker)
18. SQLAlchemy 2.0 (Modern async ORM)
19. Celery 5.4 (Background task processing)
20. Pydantic 2.10 (Data validation with FastAPI)
21. openpyxl 3.1.5 (Excel read/write)
22. rapidfuzz 3.10 (Fast fuzzy string matching)
23. pandas 2.2.3 (Data manipulation)
24. httpx 0.28 (Async HTTP client)
25. Sentry SDK 2.18 (Error monitoring)

**AI Model Selection Strategy:**

26. **GPT-5 Flagship** ($1.25/$10 per M tokens) - Complex invoice extraction
27. **GPT-5 Mini** ($0.25/$2 per M tokens) - Simple field extraction
28. **GPT-5 Nano** ($0.05/$0.40 per M tokens) - Validation tasks
29. Smart model routing based on task complexity
30. OpenRouter BYOK option (1M requests/month free)

**Deployment Technologies (8 options):**

31. Docker 27.x (Containerization)
32. Docker Compose 2.x (Multi-container orchestration)
33. Node.js 22 Alpine (Frontend base image)
34. Python 3.14 Slim (Backend base image)
35. PostgreSQL 18 Alpine (Database image)
36. Redis 7.4 Alpine (Cache image)
37. GCP Cloud Run (Future deployment option)
38. Sentry (Monitoring and error tracking)

#### Insights Discovered
- Latest versions provide significant performance improvements (Tailwind 4.0: 100x faster)
- GPT-5 released August 2025 offers 45% fewer hallucinations than GPT-4o
- Python 3.14 just released October 2025 (bleeding edge)
- Next.js 15.5 stable, Next.js 16 beta available (will upgrade later)
- OpenRouter allows model flexibility (can switch to Claude, Gemini without code changes)

#### Notable Connections
- FastAPI + Pydantic + TypeScript = End-to-end type safety
- Docker Compose = Development = Production environment
- OpenRouter = API abstraction layer (future-proof)
- Latest versions align well (no compatibility issues found)

---

### Session 4: Document Analysis & Data Mapping - 40 minutes

**Description:** Analyzing actual sample files to understand extraction challenges and design data flow.

#### Ideas Generated from Sample Files

**Invoice (INVOICE.jpg) Analysis:**

39. Contains product table with: Description, Brand, Quantity, Unit Price, Amount
40. Mixed formatting: "159,800" vs "159.800" (different number formats)
41. Multiple products per invoice (2 products in sample)
42. Total value calculation validation opportunity
43. Brand names: "Ipaly", "ENJOYQEEN" (entity recognition targets)
44. HS Code mentioned: 961900 (matches Certificate of Origin)

**Certificate of Origin (CO.pdf) Analysis:**

45. Form E (ASEAN-China Free Trade Area)
46. HS Code: 96190014 (8-digit, more specific than invoice)
47. Origin criteria: "PE" (Produced Exclusively)
48. Gross weights per product line
49. Serial numbers and reference numbers (traceability)
50. Official stamps and signatures (authenticity markers)

**Bill of Lading (BOL.pdf) Analysis:**

51. Container numbers and seal numbers
52. Container sizes: 40H (High Cube)
53. Vessel name and voyage number
54. Port information: XIAMEN → HAIPHONG
55. Total packages: 2520 (can validate against invoice quantities)
56. Marks: "N/M" (standard notation)

**Arrival Notice (AN.pdf) Analysis:**

57. B/L Number: EGLV146500902564 (cross-reference with BOL)
58. Arrival date and port
59. Freight charges breakdown (not needed for customs declaration)
60. Exchange rate information
61. Vietnamese language instructions (mixed language challenge)

**Good List Excel Files:**

62. 1,294 historical records (goodlist1.xls)
63. Contains: HS codes, product descriptions, prices, weights, tax rates
64. Vietnamese product descriptions (need matching algorithm)
65. Multiple variations of same product
66. Historical pricing data (validation range)

**EXIM Tariff Excel:**

67. Complete Vietnamese tariff database
68. VAT rates, import duties, trade agreement codes
69. HS code descriptions in Vietnamese and English
70. Multiple trade agreements (ACFTA, ATIGA, AJCEP, etc.)

**Customs Declaration Output (CD.xlsx):**

71. Complex multi-page Excel format
72. Header section: Importer details, dates, reference numbers
73. Line item section: Products with HS codes, quantities, values
74. Tax calculation section: VAT, duties, totals
75. Vietnamese regulatory format (must match exactly)

#### Insights Discovered
- HS Code is key linking field: 961900 (6-digit) → 96190014 (8-digit)
- Document interconnections allow validation (BOL containers = AN containers)
- Historical data provides validation ranges (typical prices, weights)
- Mixed languages (Vietnamese, English, Chinese) across documents
- Table extraction is critical (invoice line items)

#### Notable Connections
- Good List = training data for product → HS code matching
- Historical corrections can build fuzzy matching patterns
- OCR confidence varies by document type (printed vs scanned vs photo)
- Excel output format is highly structured (template-based generation)

---

### Session 5: Processing Pipeline Design - 45 minutes

**Description:** Designing the 8-stage processing pipeline with Option A (LLM + spaCy hybrid approach).

#### Ideas Generated

**Stage 1: Document Upload & Classification**

76. Detect document type by filename pattern (AN.pdf, BOL.pdf, etc.)
77. Store in structured folders: `/{declaration_id}/{document_type}`
78. Validate file count (must be exactly 6 files)
79. Check file types (PDF, JPG, XLS, XLSX)
80. Generate unique declaration ID

**Stage 2: OCR - Google Document AI**

81. Use Form Parser for structured documents
82. Extract key-value pairs automatically
83. Table extraction for invoice line items
84. Confidence scores per extracted field
85. Handle multi-language text (Vietnamese, English, Chinese)

**Stage 3: LLM Extraction - GPT-5**

86. **Complex extraction (GPT-5 Flagship):** Invoice products, descriptions, amounts
87. **Simple extraction (GPT-5 Mini):** Dates, reference numbers, names
88. **Validation (GPT-5 Nano):** Format checking, consistency validation
89. Structured JSON output with confidence scores
90. Token usage tracking for cost monitoring

**Stage 4: spaCy Validation & Entity Linking**

91. Named Entity Recognition (NER) for companies, products, codes
92. Fuzzy matching to Good List (rapidfuzz, threshold: 85%)
93. HS code format validation (8 digits, numeric)
94. Price range validation against historical data
95. Entity linking (product description → HS code)

**Stage 5: Cross-Document Validation**

96. Invoice total = Certificate of Origin total
97. BOL containers = Arrival Notice containers
98. HS codes consistent (CO vs Invoice)
99. Supplier name variations matched
100. Logical date sequence validation

**Stage 6: Draft Declaration Generation**

101. Map to Vietnamese customs Excel template
102. Apply tariff rates from EXIM-Tariff.xlsx
103. Calculate VAT (8% for HS 961900)
104. Calculate import duties (0% for ACFTA origin)
105. Format numbers per Vietnamese standards

**Stage 7: HITL Review Interface**

106. Side-by-side view: Source docs vs Generated declaration
107. Color-coded confidence scores (green >90%, yellow 70-90%, red <70%)
108. Click field → jump to source PDF location
109. Inline editing with auto-save
110. Flag corrections for knowledge base update

**Stage 8: Learning & Feedback**

111. Store all user corrections in database
112. Track: original value, corrected value, field name, timestamp
113. Update confidence scores in knowledge base
114. Build correction patterns for future processing
115. Optional: Retrain spaCy NER model with accumulated corrections

#### Insights Discovered
- 8-stage pipeline provides clear separation of concerns
- Each stage has defined inputs/outputs (easy to test)
- Confidence scores flow through entire pipeline
- HITL interface is data source for learning system
- Cost optimization via smart model selection (Flagship vs Mini vs Nano)

#### Notable Connections
- Stage 4 (spaCy) validates Stage 3 (LLM) outputs
- Stage 5 creates feedback loop to improve Stage 3 accuracy
- Stage 8 learning improves Stage 4 matching over time
- Historical data (Good List) + user corrections = growing knowledge base

---

## Idea Categorization

### Immediate Opportunities
**Ideas ready to implement now**

1. **Docker-based Development Environment**
   - Description: Multi-container setup with frontend, backend, PostgreSQL, Redis
   - Why immediate: Ensures dev/prod parity, easy onboarding, no environment issues
   - Resources needed: Docker Compose configuration, base images (available)

2. **Google Document AI Integration**
   - Description: Form Parser for OCR with 95%+ accuracy
   - Why immediate: Managed service, no ML expertise required, pay-per-use
   - Resources needed: GCP account, service account key, API quota

3. **GPT-5 via OpenRouter Setup**
   - Description: LLM extraction using OpenAI SDK with OpenRouter endpoint
   - Why immediate: Drop-in replacement, BYOK option available, flexible model selection
   - Resources needed: OpenRouter API key OR OpenAI API key for BYOK

4. **Next.js + shadcn/ui Frontend Scaffold**
   - Description: Modern React setup with TypeScript, Tailwind, component library
   - Why immediate: Well-documented, active community, production-ready templates
   - Resources needed: Node.js 22, package dependencies (all stable)

5. **FastAPI Backend Scaffold**
   - Description: Python API with async support, auto-docs, Pydantic validation
   - Why immediate: Minimal boilerplate, excellent DX, type-safe
   - Resources needed: Python 3.14, pip dependencies (all stable)

6. **PostgreSQL Schema Design**
   - Description: Tables for declarations, knowledge base, user corrections, audit trail
   - Why immediate: Well-understood problem domain, clear data model
   - Resources needed: PostgreSQL 18, SQLAlchemy models, Alembic migrations

7. **File Upload & Storage System**
   - Description: Multi-file upload with validation, storage in Docker volumes
   - Why immediate: Standard functionality, libraries available (react-dropzone, FastAPI multipart)
   - Resources needed: Frontend upload component, backend endpoint, volume mounts

8. **Basic HITL Review Interface**
   - Description: Display extracted data with confidence scores, allow inline editing
   - Why immediate: Core UX requirement, React Hook Form + Tanstack Query
   - Resources needed: UI components (shadcn), form handling, API integration

### Future Innovations
**Ideas requiring development/research**

1. **Custom spaCy NER Model Training**
   - Description: Train domain-specific Named Entity Recognition for customs terms
   - Development needed: Data annotation (200-500 samples), model training pipeline, evaluation metrics
   - Timeline estimate: 4-6 weeks after MVP, requires accumulated correction data

2. **Semantic Search with pgvector**
   - Description: Embedding-based product matching instead of fuzzy string matching
   - Development needed: Embedding generation (OpenAI embeddings), vector index, similarity search
   - Timeline estimate: 6-8 weeks, Phase 2 feature

3. **Automated Email Import**
   - Description: Process declarations directly from email attachments
   - Development needed: Email integration (IMAP/Gmail API), attachment extraction, queueing
   - Timeline estimate: 3-4 weeks, client-specific feature

4. **Multi-Tenant Architecture**
   - Description: Support multiple logistics companies with isolated data
   - Development needed: Tenant isolation, authentication, billing, data partitioning
   - Timeline estimate: 8-12 weeks, only if scaling to multiple clients

5. **Mobile App (React Native)**
   - Description: Mobile interface for reviewing declarations on-the-go
   - Development needed: React Native setup, mobile-optimized UI, offline support
   - Timeline estimate: 8-10 weeks, low priority for MVP

6. **Real-time Collaboration**
   - Description: Multiple users reviewing same declaration simultaneously (WebSocket)
   - Development needed: WebSocket infrastructure, conflict resolution, presence indicators
   - Timeline estimate: 4-6 weeks, needed only for larger teams

7. **Advanced Analytics Dashboard**
   - Description: Insights on processing time, accuracy trends, cost per declaration, common errors
   - Development needed: Analytics schema, visualization library (Chart.js/Recharts), aggregation queries
   - Timeline estimate: 3-4 weeks, Phase 2 feature

8. **Export to Customs Portal Integration**
   - Description: Direct submission to Vietnamese customs e-portal
   - Development needed: Customs API integration, authentication, submission workflow
   - Timeline estimate: 6-8 weeks, requires customs portal API access

### Moonshots
**Ambitious, transformative concepts**

1. **Fully Automated Processing (Zero Human Review)**
   - Description: 99.9% accuracy allowing auto-approval for routine declarations
   - Transformative potential: 10x efficiency gain, process 10,000 declarations/month with same team
   - Challenges to overcome: Regulatory acceptance, liability concerns, edge case handling

2. **AI-Powered Tariff Classification Assistant**
   - Description: AI suggests optimal HS codes considering duty minimization strategies
   - Transformative potential: Save clients 5-15% on import duties through better classification
   - Challenges to overcome: Legal compliance, customs audits, expert validation required

3. **Blockchain-based Document Verification**
   - Description: Immutable audit trail on blockchain for customs transparency
   - Transformative potential: Eliminate document fraud, trusted by customs automatically
   - Challenges to overcome: Blockchain infrastructure cost, regulatory adoption, privacy concerns

4. **Computer Vision for Damaged Goods Detection**
   - Description: Analyze shipping photos to flag discrepancies with invoice
   - Transformative potential: Reduce fraud, automate insurance claims, quality control
   - Challenges to overcome: Image quality requirements, CV model training, false positives

5. **Predictive Customs Clearance Time**
   - Description: ML model predicting clearance time based on historical patterns
   - Transformative potential: Better supply chain planning, customer satisfaction
   - Challenges to overcome: Access to customs clearance data, model accuracy, external factors

### Insights & Learnings
**Key realizations from the session**

- **Accuracy vs Cost Trade-off:** For first client, accuracy justifies higher API costs. Can optimize later with cached results, cheaper models, or local processing as volume grows.

- **Knowledge Base is Core Asset:** The accumulated corrections and Good List data become more valuable over time. This is defensible IP that competitors can't easily replicate.

- **Hybrid Approach Wins:** Pure cloud or pure local both have significant drawbacks. Hybrid (cloud AI for hard problems, local processing for routine tasks) provides best ROI.

- **HITL is Feature, Not Bug:** Human-in-the-Loop isn't a limitation - it's a trust-building feature for compliance-critical workflows. Auto-approval can be phased in gradually.

- **Latest Tech = Less Debt:** Using 2025 latest versions (Next.js 15, Python 3.14, PostgreSQL 18) means longer runway before major upgrades needed.

- **OpenRouter = Flexibility:** Using OpenRouter.ai instead of direct provider APIs allows easy model switching (GPT-5 → Claude → Gemini) without code changes.

- **Docker = Portability:** Local Docker deployment means client can run on-premise, migrate to any cloud, or hybrid setup without architecture changes.

- **spaCy Complements LLM:** LLMs are great at extraction, spaCy is great at validation and entity linking. Together they catch each other's errors.

- **Excel is Actually Hard:** Generating correctly formatted Vietnamese customs Excel files is non-trivial. Template-based approach with openpyxl required.

- **Progressive Enhancement:** Start with 70-80% automation, improve to 90-95% over 3-6 months as learning system accumulates data.

---

## Action Planning

### Top 3 Priority Ideas

#### #1 Priority: MVP Development (Weeks 1-8)

**Rationale:**
Deliver working prototype to first client quickly. Prove value, gather real-world data, establish feedback loop.

**Next steps:**
1. Week 1-2: Project setup
   - Initialize Next.js frontend + FastAPI backend repositories
   - Configure Docker Compose with all services
   - Setup PostgreSQL schema and migrations
   - Integrate Sentry monitoring

2. Week 3-4: Core Processing Pipeline
   - Implement Google Document AI integration
   - Implement GPT-5 via OpenRouter integration
   - Build file upload and storage system
   - Create background job processing with Celery

3. Week 5-6: HITL Interface
   - Build declaration review screen
   - Implement PDF viewer for source documents
   - Create inline editing with validation
   - Build approval/rejection workflow

4. Week 7-8: Testing & Refinement
   - Process 10-20 sample declarations
   - Measure accuracy and identify failure patterns
   - Optimize prompts and processing logic
   - User acceptance testing with client

**Resources needed:**
- 2 full-stack developers (Python + TypeScript)
- GCP account with Document AI enabled
- OpenRouter account or OpenAI API key
- Staging environment for testing

**Timeline:** 8 weeks to MVP

---

#### #2 Priority: Learning System Implementation (Weeks 9-12)

**Rationale:**
Transform user corrections into continuous improvement. This is the key differentiator that makes the platform smarter over time.

**Next steps:**
1. Week 9: Correction Tracking
   - Build database schema for corrections
   - Implement correction capture in HITL interface
   - Create correction review and approval workflow

2. Week 10: Knowledge Base Updates
   - Implement automatic Good List updates from corrections
   - Build fuzzy matching improvement system
   - Create confidence score adjustment logic

3. Week 11: Pattern Recognition
   - Analyze correction patterns
   - Build extraction pattern library
   - Implement pattern-based validation rules

4. Week 12: Analytics & Insights
   - Create accuracy dashboard
   - Build cost tracking (API usage)
   - Generate weekly improvement reports

**Resources needed:**
- 1 backend developer
- Data analyst (part-time)
- Access to production correction data

**Timeline:** 4 weeks after MVP

---

#### #3 Priority: spaCy Integration & Custom Training (Weeks 13-18)

**Rationale:**
Reduce API costs by 40-60% while maintaining accuracy. Custom NER model trained on client's specific domain.

**Next steps:**
1. Week 13-14: Data Annotation
   - Annotate 200-300 sample declarations
   - Create training/dev/test splits
   - Define entity labels (PRODUCT, HS_CODE, BRAND, QUANTITY, etc.)

2. Week 15-16: Model Training
   - Train custom spaCy NER model
   - Evaluate on test set (target: 90%+ F1 score)
   - Fine-tune hyperparameters

3. Week 17: Integration
   - Integrate custom model into pipeline
   - A/B test: LLM vs spaCy for simple extractions
   - Measure accuracy and cost savings

4. Week 18: Optimization
   - Route simple tasks to spaCy (free)
   - Route complex tasks to GPT-5 (paid)
   - Target: 50% reduction in LLM API calls

**Resources needed:**
- 1 ML engineer with spaCy experience
- Annotation budget ($500-1000 if outsourced)
- GPU for training (can use Colab free tier)

**Timeline:** 6 weeks, starting after 3 months of operation

---

## Reflection & Follow-up

### What Worked Well

- **Document Analysis First:** Examining real sample files provided concrete understanding of extraction challenges
- **Architecture Comparison:** Systematic evaluation of cloud vs local vs hybrid led to informed decision
- **Latest Tech Research:** Web search for 2025 versions ensured modern, future-proof stack
- **Cost Estimation:** Calculating per-declaration costs ($0.033) provides clear ROI for client
- **Phased Approach:** Identifying MVP vs Future vs Moonshot ideas creates realistic roadmap
- **Hybrid LLM + spaCy:** Combining strengths of both approaches for optimal accuracy/cost balance

### Areas for Further Exploration

- **Vietnamese Customs Regulations:** Deep dive into specific compliance requirements, required fields, validation rules
- **Excel Template Complexity:** Detailed analysis of CD.xlsx structure, formulas, formatting requirements
- **Error Handling Strategies:** How to handle OCR failures, ambiguous data, missing fields
- **Scaling Considerations:** Performance at 5,000-10,000 declarations/month, database optimization, caching strategies
- **Security & Authentication:** User roles, permissions, API authentication, data encryption
- **Backup & Disaster Recovery:** Data backup strategy, declaration versioning, rollback procedures

### Recommended Follow-up Techniques

- **User Journey Mapping:** Map detailed workflow from upload to final export for UX optimization
- **Risk Analysis (Pre-Mortem):** "What could go wrong?" exercise to identify potential failure modes
- **Technical Spike:** Build proof-of-concept for most uncertain component (Excel generation)
- **Cost Modeling:** Detailed financial model with pricing tiers, break-even analysis, profitability projections
- **Competitive Analysis:** Research existing customs automation solutions, identify differentiation opportunities

### Questions That Emerged

1. **What is acceptable error rate for auto-approval?** (95%? 98%? 99%?)
2. **How often do tariff rates change?** (impacts knowledge base update frequency)
3. **Are there seasonal patterns in declarations?** (e.g., holiday shopping seasons)
4. **What is client's tolerance for processing time?** (real-time vs batch overnight)
5. **Will client need multi-user access?** (impacts authentication, audit trail)
6. **Are there specific Vietnamese customs software integrations required?** (e.g., VNACCS, VCIS)
7. **How long must declarations be retained?** (impacts storage costs, data lifecycle)
8. **Is there regulatory approval process for automated customs tools?** (compliance requirements)

### Next Session Planning

**Suggested topics:**
- Database schema design workshop
- HITL interface UX design session
- Error handling and edge case brainstorming
- Security and compliance deep-dive

**Recommended timeframe:** 1-2 weeks after project initiation

**Preparation needed:**
- Review Vietnamese customs documentation
- Gather 10-20 more sample declarations (diverse examples)
- Document current manual process (time study)
- Define success metrics with client

---

## Technical Specifications Summary

### Complete Technology Stack (2025 Latest Versions)

#### Frontend
```yaml
Framework: Next.js 15.5.6 (App Router)
UI Library: React 19.2.0
Styling: Tailwind CSS 4.0.0
Components: shadcn/ui (latest)
Language: TypeScript 5.6.0
State Management:
  - Client: Zustand 5.0.2
  - Server: Tanstack Query 5.59.20
Forms: React Hook Form 7.53.2
Validation: Zod 3.23.8
PDF Viewer: react-pdf 9.1.1
File Upload: react-dropzone 14.3.5
HTTP Client: axios 1.7.7
Icons: lucide-react (latest)
```

#### Backend
```yaml
Language: Python 3.14.0
Framework: FastAPI 0.119.0
Server: uvicorn 0.32.1
Validation: pydantic 2.10.0

OCR:
  google-cloud-documentai: 2.35.0
  Model: pretrained-foundation-model-v1.5.1-2025-08-07

LLM:
  openai: 1.58.1 (for OpenRouter integration)
  Endpoint: https://openrouter.ai/api/v1
  Models:
    - openai/gpt-5 ($1.25/$10 per M tokens)
    - openai/gpt-5-mini ($0.25/$2 per M tokens)
    - openai/gpt-5-nano ($0.05/$0.40 per M tokens)

NLP:
  spacy: 3.8.7
  spacy-transformers: 1.3.5
  Models: en_core_web_trf, zh_core_web_trf

Data Processing:
  pandas: 2.2.3
  numpy: 2.1.3
  rapidfuzz: 3.10.1
  openpyxl: 3.1.5
  pdfplumber: 0.11.4
  PyMuPDF: 1.25.1
  Pillow: 11.0.0

Database:
  sqlalchemy: 2.0.36
  alembic: 1.14.0
  asyncpg: 0.30.0

Task Queue:
  celery: 5.4.0
  redis: 5.2.1

Utilities:
  python-dotenv: 1.0.1
  python-multipart: 0.0.20
  httpx: 0.28.1
  sentry-sdk: 2.18.0
```

#### Database & Infrastructure
```yaml
Database: PostgreSQL 18.0 (postgres:18-alpine)
Cache: Redis 7.4.1 (redis:7.4-alpine)
Container: Docker 27.x
Orchestration: Docker Compose 2.x
Monitoring: Sentry (latest SDK)

Base Images:
  Frontend: node:22-alpine
  Backend: python:3.14-slim
```

### Cost Analysis (1000 declarations/month)

```yaml
API Costs:
  Google Document AI:
    - 1000 declarations × 4 PDFs × 3 pages = 12,000 pages
    - Rate: $1.50 per 1,000 pages
    - Cost: $18.00/month

  GPT-5 via OpenRouter (optimized model selection):
    - Invoice (GPT-5 Flagship): $0.01175 per declaration
    - CO (GPT-5 Mini): $0.001 per declaration
    - BOL (GPT-5 Mini): $0.00125 per declaration
    - AN (GPT-5 Mini): $0.0008 per declaration
    - Validation (GPT-5 Nano): $0.0001 per declaration
    - Total LLM: ~$0.015 per declaration
    - 1000 declarations: $15.00/month

  Total API Costs: $33.00/month

  With OpenRouter 5.5% fee: $34.82/month

  OR with BYOK (Bring Your Own OpenAI Key):
    - OpenRouter fee: $0 (first 1M requests free)
    - Pay Google + OpenAI directly: $33.00/month

Infrastructure Costs (Local Docker):
  - Storage: $0 (local volumes)
  - Database: $0 (local PostgreSQL)
  - Compute: $0 (runs on client's server/laptop)

Total Monthly Cost: ~$33-35/month
Cost per Declaration: $0.033-0.035
```

### Processing Pipeline Architecture

```yaml
Stage 1: Document Upload & Classification
  Input: 6 files (AN, BOL, CO, INVOICE, goodlist, tariff)
  Process: Filename detection, storage, validation
  Output: Organized file structure, declaration ID

Stage 2: OCR - Google Document AI
  Input: PDF/image files
  Process: Form Parser, table extraction
  Output: Structured text + tables + confidence scores

Stage 3: LLM Extraction - GPT-5
  Input: OCR results
  Process:
    - Complex (GPT-5): Invoice products, amounts
    - Simple (GPT-5 Mini): Dates, names, codes
    - Validation (GPT-5 Nano): Format checks
  Output: Structured JSON with confidence scores

Stage 4: spaCy Validation & Matching
  Input: Extracted JSON
  Process:
    - NER (entities)
    - Fuzzy matching to Good List
    - HS code validation
    - Price range checks
  Output: Validated data + match confidence

Stage 5: Cross-Document Validation
  Input: All extracted data
  Process:
    - Invoice total = CO total
    - BOL containers = AN containers
    - HS code consistency
    - Date logic checks
  Output: Validation report + flagged discrepancies

Stage 6: Draft Declaration Generation
  Input: Validated data
  Process:
    - Map to customs Excel template
    - Apply tariff rates
    - Calculate taxes (VAT, duties)
    - Format per Vietnamese standards
  Output: CD.xlsx (draft)

Stage 7: HITL Review Interface
  Input: Draft declaration + source documents
  Process:
    - Side-by-side comparison
    - Confidence-based highlighting
    - Inline editing
    - User approval/corrections
  Output: Approved declaration + corrections

Stage 8: Learning & Feedback
  Input: User corrections
  Process:
    - Store corrections in database
    - Update confidence scores
    - Build patterns
    - Improve future accuracy
  Output: Updated knowledge base
```

### Project Structure

```
customs-declaration-platform/
├── frontend/                           # Next.js 15 frontend
│   ├── app/                           # App Router
│   │   ├── (auth)/                   # Auth routes
│   │   ├── (dashboard)/              # Main dashboard
│   │   ├── declarations/
│   │   │   ├── [id]/review/         # HITL interface
│   │   │   └── new/                 # Upload interface
│   │   ├── knowledge-base/          # Good List management
│   │   └── layout.tsx
│   ├── components/
│   │   ├── ui/                      # shadcn components
│   │   ├── declaration/             # Custom components
│   │   └── pdf-viewer/              # PDF display
│   ├── lib/
│   │   ├── api.ts                   # API client
│   │   └── utils.ts
│   ├── package.json
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── Dockerfile
│
├── backend/                            # FastAPI backend
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── declarations.py
│   │   │       ├── knowledge_base.py
│   │   │       └── auth.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── celery_app.py
│   │   ├── models/                   # SQLAlchemy models
│   │   │   ├── declaration.py
│   │   │   ├── knowledge_base.py
│   │   │   └── user.py
│   │   ├── schemas/                  # Pydantic schemas
│   │   ├── services/
│   │   │   ├── ocr_service.py       # Google Doc AI
│   │   │   ├── llm_service.py       # GPT-5 OpenRouter
│   │   │   ├── spacy_service.py     # NLP processing
│   │   │   ├── matching_service.py  # Fuzzy matching
│   │   │   └── excel_service.py     # Excel generation
│   │   ├── tasks/                    # Celery tasks
│   │   │   └── process_declaration.py
│   │   ├── db/
│   │   │   ├── base.py
│   │   │   └── session.py
│   │   └── main.py
│   ├── tests/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── init.sql
│
├── data/                               # Docker volumes
│   ├── uploads/                       # Input files
│   ├── outputs/                       # Generated Excel
│   ├── postgres/                      # Database data
│   └── redis/                         # Cache data
│
├── secrets/                            # API keys (gitignored)
│   ├── gcp-key.json
│   └── .env
│
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## Implementation Roadmap

### Phase 1: MVP (Weeks 1-8)

**Goal:** Working prototype processing 10-20 declarations with 85%+ accuracy

**Week 1-2: Project Setup**
- Initialize repositories (frontend + backend)
- Configure Docker Compose (5 services)
- Setup PostgreSQL schema
- Configure Sentry monitoring
- Create basic CI/CD pipeline

**Week 3-4: Core Processing**
- Google Document AI integration
- GPT-5 via OpenRouter integration
- File upload system
- Celery background jobs
- Basic Excel generation

**Week 5-6: HITL Interface**
- Declaration review screen
- PDF viewer
- Inline editing
- Approval workflow
- Confidence visualization

**Week 7-8: Testing & Launch**
- Process 20 sample declarations
- Measure accuracy
- Client UAT
- Fix critical bugs
- Production deployment

**Deliverables:**
- ✅ Working platform
- ✅ Docker deployment
- ✅ Documentation
- ✅ 85%+ accuracy on test set

---

### Phase 2: Learning System (Weeks 9-12)

**Goal:** Platform learns from corrections, accuracy improves to 92%+

**Week 9: Correction Tracking**
- Correction database schema
- Capture corrections in UI
- Approval workflow

**Week 10: Knowledge Base**
- Auto-update Good List
- Improve fuzzy matching
- Confidence adjustment

**Week 11: Pattern Recognition**
- Analyze correction patterns
- Build pattern library
- Validation rules

**Week 12: Analytics**
- Accuracy dashboard
- Cost tracking
- Weekly reports

**Deliverables:**
- ✅ Learning system active
- ✅ Accuracy improvement visible
- ✅ Analytics dashboard
- ✅ 92%+ accuracy

---

### Phase 3: Cost Optimization (Weeks 13-18)

**Goal:** Reduce API costs by 50% while maintaining accuracy

**Week 13-14: Data Annotation**
- Annotate 300 declarations
- Create training dataset
- Define entity labels

**Week 15-16: spaCy Training**
- Train custom NER model
- Evaluate performance
- Fine-tune model

**Week 17: Integration**
- Integrate custom spaCy model
- A/B testing
- Measure cost savings

**Week 18: Optimization**
- Smart routing (spaCy vs GPT-5)
- Caching strategies
- Performance tuning

**Deliverables:**
- ✅ Custom spaCy model
- ✅ 50% cost reduction
- ✅ Maintained accuracy (92%+)
- ✅ ~$16-18/month operating cost

---

### Phase 4: Scale & Polish (Weeks 19-24)

**Goal:** Production-ready for 1000+ declarations/month

**Week 19-20: Performance**
- Database optimization
- Caching layer (Redis)
- Batch processing
- Load testing

**Week 21-22: Features**
- Advanced search
- Bulk operations
- Export templates
- Reporting

**Week 23: Security**
- Authentication hardening
- Authorization rules
- Audit logging
- Penetration testing

**Week 24: Documentation**
- User guide
- API documentation
- Admin manual
- Troubleshooting guide

**Deliverables:**
- ✅ Handle 1000+ declarations/month
- ✅ <10s processing time per declaration
- ✅ Enterprise-grade security
- ✅ Complete documentation

---

*Session facilitated using the BMAD-METHOD™ brainstorming framework*
