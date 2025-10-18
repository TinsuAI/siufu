# Epic List

## Epic 1: Foundation & Document Processing Pipeline (9 Stories)
**Goal:** Establish project infrastructure and core document processing capabilities, delivering a working end-to-end pipeline that can ingest 6 files, extract data via AI, and output raw JSON results.

**Deliverable:** Developers can upload sample declaration files and receive structured JSON output with extracted data and confidence scores. Foundation enables all subsequent development.

**Stories:** 1.0 (Testing Infrastructure), 1.1 (Project Setup), 1.0.5 (CI/CD Pipeline), 1.2 (Backend API), 1.3 (Google Document AI), 1.4 (GPT-5 Integration), 1.5 (Async Processing), 1.6 (File Upload), 1.7 (End-to-End Processing)

---

## Epic 2: Declaration Generation & Excel Export (6 Stories)
**Goal:** Transform extracted data into properly formatted Vietnamese customs declaration Excel files with tariff rates applied and calculations performed.

**Deliverable:** System generates CD.xlsx files that match Vietnamese customs format requirements with all fields populated, taxes calculated, ready for human review.

**Stories:** 2.1 (Knowledge Base Import), 2.2 (Fuzzy Matching), 2.3 (Cross-Document Validation), 2.4 (Tariff Calculation), 2.5 (Excel Generation), 2.6 (End-to-End Pipeline)

---

## Epic 3: Human-in-the-Loop Review Interface (10 Stories)
**Goal:** Build the web-based review interface where users can verify AI output, make corrections, and approve declarations for submission.

**Deliverable:** Users can log in, upload files, review generated declarations side-by-side with source PDFs, edit fields inline, and export approved Excel files.

**Stories:** 3.1 (Frontend Foundation), 3.2 (User Authentication), 3.3 (File Upload Interface), 3.4 (Processing Status), 3.5 (PDF Viewer), 3.6 (Review Form), 3.7 (Jump Navigation), 3.8 (Approval & Export), 3.9 (Declaration History), 3.10 (Edge Cases)

---

## Epic 4: Learning System & Knowledge Base Management (6 Stories)
**Goal:** Implement correction tracking and knowledge base management features that enable continuous improvement and user empowerment.

**Deliverable:** System captures all user corrections for future learning, allows users to upload updated Good List and EXIM-Tariff files, and provides foundation for Phase 2 AI training.

**Stories:** 4.1 (Correction Tracking), 4.2 (Analytics Dashboard), 4.3 (Knowledge Base Upload), 4.4 (Version History), 4.5 (Confidence Learning), 4.6 (User Documentation)

---
