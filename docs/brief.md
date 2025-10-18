# Project Brief: Customs Declaration Automation Platform

**Document Version:** 1.0
**Date:** 2025-10-17
**Status:** Draft
**Owner:** Development Team

---

## Executive Summary

The **Customs Declaration Automation Platform** is a cloud-based SaaS solution that automatically generates Vietnamese customs declarations from six input files (4 document PDFs/images + 2 data Excel files) with 95%+ accuracy. The platform combines cutting-edge AI (Google Document AI OCR + GPT-5 LLM extraction + spaCy validation) with Human-in-the-Loop review to ensure customs compliance while reducing manual processing time by 90%.

**Primary Problem:** Logistics companies currently spend 30-60 minutes manually processing each customs declaration, requiring staff to extract data from multiple documents, cross-reference information, apply tariff codes, and calculate taxes - a tedious, error-prone process that creates bottlenecks in customs clearance.

**Target Market:** Logistics and freight forwarding companies in Vietnam processing 500-5,000 customs declarations per month, starting with our first client who handles ~1,000 declarations monthly.

**Key Value Proposition:** Transform a 45-minute manual process into a 2-minute automated workflow with human verification, achieving 95%+ accuracy through AI while continuously learning from user corrections to improve over time.

---

## Problem Statement

### Current State and Pain Points

Logistics companies process customs declarations manually through a complex, multi-step workflow:

1. **Document Gathering:** Staff collect 6 files per declaration from various sources (emails, shared drives, supplier portals)
2. **Data Entry:** Manually type information from PDFs into Excel templates
   - Arrival Notice → shipment details
   - Bill of Lading → container information
   - Certificate of Origin → HS codes and origin
   - Invoice → product descriptions, quantities, values
3. **Reference Lookup:** Cross-reference product descriptions against historical Good List to find correct HS codes
4. **Tariff Application:** Look up tax rates in EXIM-Tariff database
5. **Calculation:** Manually calculate duties and VAT
6. **Validation:** Cross-check totals across documents for consistency
7. **Excel Generation:** Format data according to Vietnamese customs requirements

**Time Investment:** 30-60 minutes per declaration × 1,000 declarations/month = 500-1,000 staff hours monthly

**Error Impact:**
- Incorrect HS codes → customs penalties, delayed clearance, duty overpayment
- Calculation errors → compliance violations, re-submission
- Missing information → rejected declarations, shipment delays
- Manual validation gaps → fraud exposure

### Why Existing Solutions Fall Short

- **Generic OCR tools:** Can't handle complex customs document formats, tables, or mixed languages (Vietnamese/English/Chinese)
- **Manual spreadsheets:** Error-prone, no validation, no learning capability
- **Enterprise customs software:** Expensive ($500-2,000/month), complex implementation (6-12 months), still requires significant manual data entry
- **Offshore data entry:** Quality inconsistent, security concerns with sensitive customs data, communication delays

### Urgency and Importance

**Market Opportunity:**
- Vietnam import/export value: $732B annually (2024)
- Growing e-commerce driving declaration volume growth (15-20% YoY)
- Government digitization push creating demand for automation tools

**Client Pain:**
- Current client processing 1,000 declarations/month (growing to 1,500 by Q2 2026)
- Staff shortage in customs processing roles
- Error rate 3-5% causing costly re-work and penalties
- Competitive pressure to offer faster clearance times

**Strategic Timing:**
- AI capabilities (GPT-5, Google Document AI) now mature enough for production
- First-mover advantage in Vietnam market for AI-powered customs automation
- Build defensible moat through accumulated learning data (corrections → better accuracy)

---

## Proposed Solution

### Core Concept

An **intelligent document processing platform** that combines:

1. **Advanced OCR** (Google Document AI) - Extract text and tables from PDFs/images with 99% accuracy
2. **LLM-powered extraction** (GPT-5 via OpenRouter) - Understand context, handle variations, extract structured data
3. **NLP validation** (spaCy) - Validate formats, fuzzy match to knowledge base, cross-check consistency
4. **Human-in-the-Loop review** - Allow staff to verify and correct AI output with confidence scores
5. **Continuous learning** - Improve accuracy over time by learning from user corrections

### Key Differentiators

**vs Manual Processing:**
- 95% faster (45 min → 2 min)
- Higher accuracy (AI + human review)
- Consistent quality
- Audit trail included

**vs Generic OCR/RPA:**
- Domain-specific intelligence (understands customs terminology, document relationships)
- Multi-document validation (cross-checks Invoice vs CO vs BOL)
- Learning system (gets smarter with each correction)
- Vietnamese customs format expertise

**vs Enterprise Customs Software:**
- 95% lower cost ($35/month vs $500-2,000/month)
- 90% faster implementation (4 weeks vs 6 months)
- Modern tech stack (AI-powered vs rule-based)
- Flexible deployment (Docker, can run on-premise or cloud)

### Why This Will Succeed

**Technical Advantages:**
- Latest 2025 AI models (GPT-5 released Aug 2025, 45% fewer hallucinations)
- Hybrid approach (cloud AI for hard problems, local processing for speed)
- Smart cost optimization (use GPT-5 Mini/Nano for simple tasks)

**Product Advantages:**
- HITL builds trust (staff verify before submission)
- Living knowledge base (Good List + corrections grow value over time)
- Client-updatable data (tariff changes, new products)

**Market Advantages:**
- First client provides validation + reference
- Vietnam market underserved by modern tech
- Network effects (more users → more corrections → better accuracy)

### High-Level Vision

**Today (MVP):** Process one customs declaration at a time with 85% auto-extraction accuracy, staff review and correct, export Excel file.

**6 Months:** 95% accuracy, processing time under 60 seconds, client managing knowledge base independently, handling 2,000 declarations/month.

**12 Months:** Multi-client SaaS, 98% accuracy with selective auto-approval, predictive HS code suggestions, mobile app for on-the-go review.

**24 Months:** Market leader in Vietnam customs automation, 10+ clients, direct integration with customs e-portal, AI-powered tariff optimization advisory.

---

## Target Users

### Primary User Segment: Customs Processing Specialists

**Demographic/Firmographic Profile:**
- Role: Customs clearance staff, logistics coordinators
- Company: Small to medium freight forwarders (10-100 employees)
- Location: Vietnam (Hanoi, Ho Chi Minh City, Hai Phong)
- Volume: Processing 500-5,000 declarations per month
- Experience: 2-10 years in customs/logistics

**Current Behaviors and Workflows:**
- Receive shipment documents via email/shared drive
- Manually download and organize files (often rename for tracking)
- Type data from PDFs into Excel using templates
- Look up HS codes in historical records or ask senior staff
- Calculate duties using printed tariff booklets or Excel lookups
- Cross-check totals manually (calculator or Excel formulas)
- Submit to customs portal or hand off to customs broker

**Specific Needs and Pain Points:**
- **Speed:** Pressure to clear shipments quickly (clients demand 24-48hr turnaround)
- **Accuracy:** Fear of mistakes (penalties, shipment delays damage client relationships)
- **Reference access:** Constantly searching for "what HS code did we use last time for product X?"
- **Format complexity:** Vietnamese customs Excel format is intricate, easy to make formatting errors
- **Validation burden:** Manually checking if Invoice total = CO total, if weights match, etc.
- **Knowledge retention:** When experienced staff leave, institutional knowledge is lost

**Goals They're Trying to Achieve:**
- Process declarations faster without sacrificing accuracy
- Reduce mental load of constant cross-referencing
- Avoid embarrassment of rejected declarations
- Build reliable processes that new staff can follow
- Focus on exception handling rather than routine data entry

### Secondary User Segment: Logistics Operations Managers

**Demographic/Firmographic Profile:**
- Role: Operations manager, customs department head
- Company: Same as primary segment
- Scope: Oversee 3-15 customs processing staff
- KPIs: Declaration throughput, error rate, processing cost, clearance time

**Current Behaviors and Workflows:**
- Review staff work for quality control (spot checks)
- Handle escalations (difficult classifications, regulatory questions)
- Train new staff on customs procedures
- Monitor processing backlogs and assign work
- Report metrics to executive team
- Evaluate and procure tools/software

**Specific Needs and Pain Points:**
- **Visibility:** Hard to track who processed what, identify bottlenecks
- **Quality control:** Inconsistent quality between junior and senior staff
- **Training burden:** Takes 3-6 months to train new staff to proficiency
- **Capacity planning:** Difficult to predict staffing needs during peak seasons
- **Cost pressure:** Executive team wants to reduce processing costs
- **Technology gap:** Current tools are outdated, spreadsheet-based

**Goals They're Trying to Achieve:**
- Standardize quality across all staff levels
- Reduce training time for new hires
- Gain visibility into processing metrics
- Scale operations without proportional headcount growth
- Demonstrate ROI on technology investments

---

## Goals & Success Metrics

### Business Objectives

- **Revenue:** Generate $500/month MRR from first client within 3 months of launch
- **Efficiency:** Reduce declaration processing time by 90% (45 min → 4.5 min average)
- **Quality:** Achieve 95%+ accuracy on auto-extracted fields by Week 12
- **Scalability:** Support 1,000 declarations/month by end of Q1 2026
- **Cost efficiency:** Maintain operational cost under $50/month for first 1,000 declarations
- **Client satisfaction:** Net Promoter Score (NPS) > 50 within 6 months

### User Success Metrics

- **Time to first declaration:** New user processes their first declaration within 15 minutes of account creation
- **Daily usage:** Active users process average 20+ declarations per day
- **Correction rate:** Users correct fewer than 3 fields per declaration on average
- **User retention:** 90%+ of trained users continue using platform after 30 days
- **Feature adoption:** 80%+ of users actively use knowledge base management features
- **User satisfaction:** Average rating 4.2+ stars on post-declaration survey

### Key Performance Indicators (KPIs)

- **Processing Accuracy:** Percentage of fields auto-extracted correctly without user correction
  - Week 4: 85%
  - Week 12: 92%
  - Week 24: 95%

- **Throughput:** Declarations processed per month
  - Month 1: 100-200
  - Month 3: 500-800
  - Month 6: 1,000-1,500

- **Processing Time:** Average time from upload to export (including HITL review)
  - Week 4: 5 minutes
  - Week 12: 3 minutes
  - Week 24: 2 minutes

- **Error Rate:** Percentage of declarations rejected by customs due to platform errors
  - Target: < 0.5% (industry standard: 3-5%)

- **API Cost per Declaration:** Cost of Google Document AI + GPT-5 calls
  - Week 4: $0.05 (baseline, unoptimized)
  - Week 12: $0.035 (smart model routing)
  - Week 18: $0.020 (spaCy integration reduces LLM calls)

- **Learning System Performance:** Accuracy improvement from user corrections
  - Track: Corrections per field over time (should trend downward)
  - Measure: Accuracy on previously corrected product types (should trend upward)

---

## MVP Scope

### Core Features (Must Have)

- **Multi-file Upload:** Drag-and-drop interface to upload 6 files per declaration (AN.pdf, BOL.pdf, CO.pdf, INVOICE.pdf/jpg, goodlist.xls, tariff.xlsx). Validate file types and count before processing.

- **Automated OCR & Extraction:** Process all 4 document PDFs/images using Google Document AI Form Parser. Extract key-value pairs, tables, and text blocks with confidence scores.

- **Intelligent Data Extraction:** Use GPT-5 to extract structured data from OCR results (product descriptions, quantities, prices, HS codes, company names, dates). Return JSON output with confidence scores per field.

- **Knowledge Base Matching:** Fuzzy match extracted product descriptions against Good List database (1,294+ historical records) to suggest HS codes. Use rapidfuzz with 85% threshold for auto-suggestions.

- **Cross-Document Validation:** Automatically validate consistency across documents (Invoice total = CO total, BOL containers = AN containers, HS codes match between Invoice and CO, dates are logical sequence).

- **Draft Declaration Generation:** Generate Vietnamese customs declaration Excel file (CD.xlsx) with all extracted data mapped to proper fields, tariff rates applied from EXIM-Tariff database, VAT and duties calculated.

- **Human-in-the-Loop Review Interface:** Side-by-side view showing source documents (with PDF viewer) and generated declaration. Color-code fields by confidence (green >90%, yellow 70-90%, red <70%). Allow inline editing with auto-save. Click any field to jump to source location in PDF.

- **Correction Tracking:** Capture all user corrections to database with metadata (original value, corrected value, field name, confidence score, timestamp, user ID). Flag corrections for knowledge base update.

- **Excel Export:** Download final approved declaration as properly formatted Excel file matching Vietnamese customs requirements (CD.xlsx template).

- **Basic Authentication:** User login with email/password. Single-tenant initially (one client account).

### Out of Scope for MVP

- Multi-tenant architecture (multiple client accounts with data isolation)
- Mobile app (React Native)
- Automated email import (process declarations from email attachments)
- Direct customs portal integration (auto-submit to Vietnamese e-customs)
- Advanced analytics dashboard (trends, cost tracking, accuracy over time)
- Real-time collaboration (multiple users editing same declaration)
- Bulk processing (upload 10+ declarations at once)
- API for third-party integrations
- Custom branding/white-labeling
- Role-based permissions (admin, reviewer, viewer)
- Audit log export (compliance reporting)
- spaCy custom NER model (using GPT-5 only for MVP)
- Semantic search with pgvector (using fuzzy matching only)

### MVP Success Criteria

**MVP is considered successful when:**

1. **Functional completeness:** All 9 core features working end-to-end
2. **Accuracy threshold:** 85%+ auto-extraction accuracy on test set of 20 diverse declarations
3. **Performance:** Process one declaration in under 5 minutes (upload to export)
4. **Reliability:** Successfully process 50 consecutive declarations without crashes
5. **Client validation:** First client completes 100 real declarations and confirms willingness to pay
6. **Cost target:** Operating cost under $50/month for 100 declarations processed
7. **Usability:** New user can process first declaration without assistance in under 15 minutes

**Timeline:** 8 weeks from project start to MVP ready for client testing.

---

## Post-MVP Vision

### Phase 2 Features (Weeks 9-18)

**Learning System Enhancement:**
- Automatic knowledge base updates from corrections
- Confidence score adjustment based on historical accuracy
- Pattern recognition for common extraction errors
- Weekly accuracy improvement reports

**Cost Optimization:**
- Custom spaCy NER model trained on client's domain
- Smart routing: spaCy for simple extractions, GPT-5 for complex
- Target: 50% reduction in LLM API costs while maintaining accuracy

**User Experience Improvements:**
- Bulk upload (process 5-10 declarations at once)
- Declaration history with search and filters
- Duplicate detection (warn if declaration already processed)
- Quick-edit mode (edit single field without full review)

**Knowledge Base Management:**
- Web interface to upload/update Good List
- Web interface to upload/update EXIM-Tariff
- Visual diff showing what changed between versions
- Rollback capability for incorrect updates

### Long-term Vision (12-24 Months)

**Multi-Client SaaS Platform:**
- Support 10+ logistics companies with isolated data
- Subscription tiers: Starter (100/mo), Professional (500/mo), Enterprise (2000+/mo)
- Centralized admin dashboard for platform monitoring

**AI-Powered Advisory:**
- Suggest optimal HS codes for duty minimization (within legal compliance)
- Predict customs clearance time based on historical patterns
- Flag suspicious data (fraud detection)
- Auto-classify new products based on description similarity

**Ecosystem Integration:**
- Email integration (forward shipment docs → auto-process)
- Direct submission to Vietnamese customs e-portal (VNACCS/VCIS)
- ERP integration (SAP, Oracle, local Vietnamese systems)
- Notification system (SMS/email when declaration ready)

**Advanced Features:**
- Mobile app for on-the-go review and approval
- Real-time collaboration with presence indicators
- Advanced analytics (processing trends, cost tracking, accuracy by product type)
- Blockchain-based audit trail for customs transparency

### Expansion Opportunities

**Geographic Expansion:**
- Thailand, Malaysia, Indonesia (ASEAN customs procedures)
- Adapt AI models for local languages and regulations
- Partner with regional freight forwarders

**Vertical Expansion:**
- Export declarations (currently import-focused)
- Specialized industries (pharmaceuticals, food, electronics with specific regulatory requirements)
- Free trade zone declarations

**Horizontal Expansion:**
- Bill of lading generation (reverse workflow: create shipping docs from order data)
- Shipping label automation
- Freight cost calculation and optimization

---

## Technical Considerations

### Platform Requirements

- **Target Platforms:** Web application (desktop browsers primary, tablet secondary)
- **Browser/OS Support:**
  - Chrome 120+, Firefox 120+, Safari 17+ (last 2 major versions)
  - Windows 10+, macOS 13+, Linux (Ubuntu 22.04+)
  - Minimum resolution: 1366x768 (optimized for 1920x1080)
- **Performance Requirements:**
  - Page load: < 2 seconds
  - Declaration processing: < 90 seconds (upload to draft ready)
  - PDF rendering: < 3 seconds for 10-page document
  - Excel export: < 5 seconds
  - Support 20 concurrent users without degradation

### Technology Preferences

- **Frontend:**
  - Framework: Next.js 15.5.6 (App Router, React Server Components)
  - UI: React 19.2 + shadcn/ui + Tailwind CSS 4.0
  - Language: TypeScript 5.6
  - State: Zustand (client) + Tanstack Query (server)
  - Forms: React Hook Form + Zod validation
  - PDF Viewer: react-pdf 9.1

- **Backend:**
  - Language: Python 3.14
  - Framework: FastAPI 0.119 (async-native, auto-docs)
  - OCR: Google Document AI (pretrained-foundation-model-v1.5.1-2025-08-07)
  - LLM: GPT-5 via OpenRouter.ai (openai/gpt-5, gpt-5-mini, gpt-5-nano)
  - NLP: spaCy 3.8.7 (en_core_web_trf, zh_core_web_trf models)
  - Task Queue: Celery 5.4 + Redis 7.4.1
  - Excel: openpyxl 3.1.5
  - Fuzzy Matching: rapidfuzz 3.10

- **Database:**
  - Primary: PostgreSQL 18.0 (latest stable, Sept 2025 release)
  - Cache: Redis 7.4.1 (task queue broker + caching)
  - ORM: SQLAlchemy 2.0 (async support)
  - Migrations: Alembic 1.14

- **Hosting/Infrastructure:**
  - Containerization: Docker 27.x + Docker Compose 2.x
  - Initial Deployment: Local (client's server/laptop)
  - Future: GCP Cloud Run (auto-scaling, pay-per-use)
  - Monitoring: Sentry 2.18 (error tracking)

### Architecture Considerations

- **Repository Structure:**
  - Monorepo with separate frontend/ and backend/ directories
  - Shared Docker Compose for development environment
  - Unified version control and CI/CD

- **Service Architecture:**
  - Frontend: Next.js server (port 3000)
  - Backend: FastAPI server (port 8000)
  - Celery Worker: Background task processing
  - PostgreSQL: Database (port 5432)
  - Redis: Cache + message broker (port 6379)
  - All services in Docker network

- **Integration Requirements:**
  - Google Cloud: Document AI API (requires service account key)
  - OpenRouter: API key (or bring your own OpenAI key for BYOK)
  - No external integrations required for MVP

- **Security/Compliance:**
  - Data encryption at rest (PostgreSQL encryption)
  - HTTPS required for production
  - API authentication via JWT tokens
  - Sensitive data (API keys) in environment variables
  - GDPR consideration: Data retention policy (configurable, default 90 days)
  - Customs compliance: Audit trail for all changes
  - No PII storage beyond business requirements

---

## Constraints & Assumptions

### Constraints

- **Budget:**
  - Development: Internal team (2 developers for 8 weeks)
  - Operating costs: Target < $100/month for first 1,000 declarations
  - API costs: ~$33-35/month (Google Document AI + GPT-5)
  - Infrastructure: $0 (local Docker deployment)

- **Timeline:**
  - MVP delivery: 8 weeks from project start
  - Client testing: Week 9-10
  - Production launch: Week 11-12
  - Hard deadline: Q4 2025 (client needs by year-end)

- **Resources:**
  - Development team: 2 full-stack developers (Python + TypeScript)
  - Design: No dedicated designer (use shadcn/ui components)
  - QA: Developers handle testing, client performs UAT
  - DevOps: Minimal (Docker Compose, manual deployment initially)

- **Technical:**
  - Must run on-premise initially (client requirement for data sovereignty)
  - Internet required for API calls (Google Document AI, OpenRouter)
  - Client has Windows/Linux servers available
  - No GPU required (using cloud APIs for ML)

### Key Assumptions

- **Client has organized file structure:** Files are consistently named (AN.pdf, BOL.pdf, etc.) or client will adapt to our naming convention
- **Document quality is good:** PDFs are searchable (not scanned images), photos are readable. If quality is poor, accuracy will degrade.
- **Historical data is accurate:** Good List (1,294 records) contains correct HS code mappings. Client will verify and correct if needed.
- **Tariff data is up-to-date:** Client will update EXIM-Tariff.xlsx when rates change (usually quarterly)
- **User has basic Excel skills:** Can review and edit Excel file if needed
- **Internet connection is reliable:** Required for API calls during processing
- **Vietnamese customs format is stable:** CD.xlsx template won't change significantly
- **Client will provide feedback:** Active participation in testing and correction workflow
- **One declaration at a time initially:** Parallel processing not required for MVP
- **English proficiency:** User can read English UI (Vietnamese localization is post-MVP)

---

## Risks & Open Questions

### Key Risks

- **OCR Accuracy Risk:** If document quality is poor (low-res scans, handwritten notes, heavily stamped), OCR accuracy may drop below 95%. **Mitigation:** Set quality guidelines for client, implement image preprocessing, use highest quality OCR (Google Document AI).

- **LLM Hallucination Risk:** GPT-5 may confidently extract incorrect data, especially for ambiguous or unusual cases. **Mitigation:** Always show confidence scores, require human review for low-confidence fields, cross-validate with spaCy rules.

- **Cost Overrun Risk:** If API usage exceeds projections (more complex documents requiring multiple GPT-5 calls), monthly cost could grow faster than revenue. **Mitigation:** Implement caching, smart model selection (use Mini/Nano when possible), monitor costs daily.

- **Format Variation Risk:** Suppliers may change invoice formats, breaking extraction patterns. **Mitigation:** Make extraction prompts robust to format variations, build fallback logic, collect diverse training examples.

- **Knowledge Base Quality Risk:** If Good List contains errors, platform will learn incorrect patterns. **Mitigation:** Implement confidence thresholds, flag conflicts for human review, allow easy correction.

- **Dependency Risk:** Heavy reliance on Google and OpenAI APIs creates vendor lock-in and downtime exposure. **Mitigation:** Use OpenRouter for LLM flexibility (can switch to Claude/Gemini), implement graceful degradation, cache results.

- **Regulatory Change Risk:** Vietnamese customs requirements may change, requiring template updates. **Mitigation:** Make Excel generation template-based (easy to update), maintain relationships with customs experts.

- **Data Privacy Risk:** Client may be uncomfortable with documents sent to cloud APIs. **Mitigation:** Provide on-premise deployment option, anonymize data in API calls if possible, ensure compliance with data protection regulations.

### Open Questions

- What is the client's acceptable error rate for auto-approval (zero human review)? Is 95%, 98%, or 99% required?
- How often do tariff rates change? Do we need automated tariff update notifications?
- Are there seasonal patterns in declaration volume (e.g., pre-Lunar New Year surge)?
- What is client's maximum acceptable processing time per declaration? (Real-time vs batch overnight)
- Will multiple users need concurrent access to the same declaration for collaboration?
- Are there specific Vietnamese customs software integrations required (VNACCS, VCIS, other)?
- How long must declarations be retained for audit purposes? (Impacts storage costs and data lifecycle)
- Is there a regulatory approval process for automated customs tools in Vietnam?
- What backup/disaster recovery requirements exist for customs data?
- Does client need detailed audit logs for compliance reporting?

### Areas Needing Further Research

- **Vietnamese Customs Regulations:** Deep dive into CD.xlsx format requirements, required fields, validation rules, acceptable value ranges
- **Excel Template Complexity:** Detailed analysis of formulas, conditional formatting, linked sheets in CD.xlsx template
- **Edge Case Handling:** How to handle missing fields, ambiguous data, multi-currency invoices, partial shipments
- **Tariff Classification Rules:** Understand customs broker expertise in HS code selection, when to be conservative vs aggressive
- **Competitive Landscape:** Research existing customs automation solutions in Vietnam market, pricing, features
- **User Workflow:** Shadow customs staff for a day to observe actual process, pain points, workarounds
- **Performance at Scale:** Database optimization needed for 5,000-10,000 declarations/month
- **Security Compliance:** Specific requirements for handling sensitive customs data, encryption standards

---

## Appendices

### A. Research Summary

**Brainstorming Session (2025-10-17):**
- Generated 87 distinct ideas across architecture, technology, workflow
- Analyzed actual sample declaration files (6 input files, 1 output Excel)
- Evaluated 3 architecture approaches (Cloud SaaS, Local Pipeline, Hybrid)
- Selected Option A: LLM + spaCy hybrid approach for optimal accuracy/cost balance
- Researched latest 2025 technology versions (Next.js 15.5.6, Python 3.14, PostgreSQL 18, etc.)
- Key finding: HS Code appears in multiple documents and serves as validation anchor

**Document Analysis Findings:**
- Invoice format: Product table with descriptions, brands, quantities, prices, totals
- Certificate of Origin: HS codes (8-digit), origin criteria, weights, official stamps
- Bill of Lading: Container details, vessel info, port routing, total packages
- Arrival Notice: B/L reference, arrival date, freight charges, Vietnamese instructions
- Good List: 1,294 historical records with HS codes, descriptions, prices, weights
- EXIM Tariff: Complete Vietnamese tariff database with VAT, duties, trade agreements

**Cost Research:**
- Google Document AI: $1.50 per 1,000 pages
- GPT-5 via OpenRouter: $1.25/$10 per M tokens (Flagship), $0.25/$2 (Mini), $0.05/$0.40 (Nano)
- Calculated cost per declaration: $0.033 (optimized model selection)
- Monthly cost for 1,000 declarations: $33-35/month

**Technology Validation:**
- Confirmed latest stable versions available (Oct 2025)
- Verified OpenRouter supports GPT-5 (released Aug 2025)
- Tested compatibility of selected stack (no blocking issues found)
- Identified Docker as ideal deployment model for portability

### B. Stakeholder Input

**First Client (Logistics Company - Vietnam):**
- Processes ~1,000 customs declarations per month (growing to 1,500 by Q2 2026)
- Current process: 30-60 minutes per declaration, manual Excel data entry
- Pain points: Staff shortage, error rate 3-5%, knowledge retention when staff leave
- Requirements: High accuracy (>95%), on-premise deployment for data sovereignty, user-friendly interface
- Willingness to pay: $300-500/month for proven solution
- Timeline pressure: Needs solution by end of Q4 2025

**Development Team:**
- 2 full-stack developers available (Python + TypeScript experience)
- 8-week timeline is aggressive but achievable for MVP
- Preference for modern tech stack (Next.js 15, FastAPI, PostgreSQL)
- Concern: LLM cost scaling, mitigation through smart model routing

### C. References

**Project Documentation:**
- Brainstorming Session Results: `docs/brainstorming-session-results.md`
- Sample Files: `resources/sample/1/`, `resources/sample/2/`, `resources/sample/3/`
- Good List: `resources/goodlist1.xls`, `resources/goodlist2.xls`
- Tariff Database: `resources/EXIM-Tarrif.xlsx`

**External Resources:**
- Vietnamese Customs Documentation: https://www.customs.gov.vn/
- ASEAN-China FTA (Form E): Certificate of Origin requirements
- Google Document AI Docs: https://cloud.google.com/document-ai/docs
- OpenRouter API Docs: https://openrouter.ai/docs
- GPT-5 Release Notes: https://openai.com/index/introducing-gpt-5/
- spaCy Documentation: https://spacy.io/usage

**Technical References:**
- Next.js 15 Documentation: https://nextjs.org/docs
- FastAPI Documentation: https://fastapi.tiangolo.com/
- PostgreSQL 18 Release Notes: https://www.postgresql.org/docs/18/release-18.html
- shadcn/ui Components: https://ui.shadcn.com/

---

## Next Steps

### Immediate Actions

1. **Project Setup (Week 1):**
   - Create Git repositories (frontend + backend)
   - Setup Docker Compose with all 5 services (frontend, backend, celery-worker, postgres, redis)
   - Configure development environment
   - Setup Sentry monitoring
   - Document setup instructions

2. **API Accounts (Week 1):**
   - Create Google Cloud account, enable Document AI API
   - Generate service account key for Google Document AI
   - Create OpenRouter account OR prepare OpenAI API key for BYOK
   - Test API connectivity and quota limits

3. **Database Schema Design (Week 1):**
   - Design PostgreSQL schema (declarations, knowledge_base, users, corrections, audit_log)
   - Create SQLAlchemy models
   - Write Alembic migrations
   - Seed database with sample data

4. **Core Processing Pipeline (Week 2-4):**
   - Implement Google Document AI integration
   - Implement GPT-5 via OpenRouter integration
   - Build file upload and storage system
   - Create Celery background tasks for async processing
   - Implement basic Excel generation

5. **HITL Interface (Week 5-6):**
   - Build declaration review screen (Next.js)
   - Implement PDF viewer component
   - Create inline editing with React Hook Form
   - Build approval/rejection workflow
   - Add confidence score visualization

6. **Testing & Refinement (Week 7-8):**
   - Process 20 diverse sample declarations
   - Measure accuracy and identify failure patterns
   - Optimize prompts and processing logic
   - User acceptance testing with client
   - Fix critical bugs and performance issues

7. **Documentation (Week 7-8):**
   - Write user guide (how to process declaration)
   - Document API endpoints (FastAPI auto-docs)
   - Create troubleshooting guide
   - Prepare deployment instructions

8. **Client Onboarding (Week 9):**
   - Deploy to client environment
   - Train staff on platform usage
   - Process first 10 real declarations together
   - Collect feedback and prioritize improvements

### PM Handoff

This Project Brief provides the full context for the **Customs Declaration Automation Platform**.

**For Product Management:** Please review this brief thoroughly and work with the development team to create a detailed Product Requirements Document (PRD) that expands on the MVP features, defines acceptance criteria, and outlines the technical implementation details.

**For Development Team:** Use this brief as the north star for MVP development. All 9 core features listed in MVP Scope are must-haves. Out-of-scope items should not be built until after MVP validation.

**Key Success Criteria to Track:**
- ✅ 85%+ auto-extraction accuracy by Week 8
- ✅ < 5 minute processing time per declaration
- ✅ Client completes 100 real declarations successfully
- ✅ Operating cost < $50/month for 100 declarations
- ✅ Client confirms willingness to pay for ongoing service

**Next Document:** PRD (Product Requirements Document) detailing user stories, acceptance criteria, API specifications, and technical architecture.

---

**Questions or need clarification?** Contact the project team or schedule a review meeting.

*This Project Brief was created using the BMAD-METHOD™ framework based on a comprehensive brainstorming session conducted on 2025-10-17.*
