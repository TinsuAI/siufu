# Wireframes & Mockups

**Primary Design Files:** To be created in Figma (link to be added)

For MVP, we'll use shadcn/ui components with minimal customization, documented below.

## Key Screen Layouts

### Screen 1: Login

**Purpose:** Authenticate users and establish session

**Key Elements:**
- Centered card layout (max-width 400px)
- Logo/app name at top
- Email input field (type=email, autocomplete=username)
- Password input field (type=password, autocomplete=current-password, show/hide toggle)
- "Remember me" checkbox (checked by default)
- "Login" button (primary, full-width, disabled until both fields filled)
- Error message area (hidden unless login fails)

**Interaction Notes:**
- Enter key submits form
- Failed login shows inline error: "Invalid email or password"
- Success redirects to `/upload` or return URL if user was redirected from protected route
- Loading state on button during API call ("Logging in...")

**Design File Reference:** `figma.com/login-screen` (TBD)

---

### Screen 2: Upload Declaration

**Purpose:** Accept 6 required files for new declaration

**Key Elements:**
- Page header: "Upload New Declaration"
- 6 labeled drop zones in 2x3 grid:
  - Row 1: Arrival Notice (PDF) | Bill of Lading (PDF) | Certificate of Origin (PDF)
  - Row 2: Invoice (PDF/Image) | Good List (Excel) | EXIM Tariff (Excel)
- Each drop zone shows:
  - Label with accepted file types
  - Drag-drop target (dashed border when empty, solid when filled)
  - Icon (document icon, changes to checkmark when file added)
  - File name and size when uploaded
  - Remove button (X icon) to clear file
- Visual checklist sidebar (right side):
  - "Required Files (6/6)" with progress circle
  - List of 6 files with checkmark status
- "Process Declaration" button at bottom (disabled until all 6 files uploaded, primary color when enabled)
- Cancel button to return to declarations list

**Interaction Notes:**
- Drag-over highlights drop zone with blue border
- Click drop zone opens file picker
- File type validation shows immediate error: "Expected .pdf, got .docx"
- File size validation shows: "File too large. Maximum 10MB for PDFs"
- All 6 files must be present to enable Process button
- Clicking Process shows loading state, then redirects to Processing Status screen
- Keyboard: Tab through zones, Enter to open file picker

**Design File Reference:** `figma.com/upload-screen` (TBD)

---

### Screen 3: Processing Status

**Purpose:** Show real-time progress of declaration processing

**Key Elements:**
- Page header: "Processing Declaration #12345"
- Vertical stepper showing stages:
  1. Uploading Files (✓ Complete - green)
  2. OCR Processing (In Progress - animated spinner, blue)
  3. AI Extraction (Pending - gray)
  4. Cross-Document Validation (Pending)
  5. Generating Excel (Pending)
  6. Ready for Review (Pending)
- Current stage highlighted with description: "Extracting text from PDFs using Google Document AI..."
- Progress bar (0-100%, updates with each stage)
- Estimated time remaining: "Approximately 60 seconds remaining"
- "You can navigate away - processing continues in background" info message
- "View Declarations List" button to navigate away

**Interaction Notes:**
- Polls `/api/declarations/{id}/status` every 2 seconds
- Progress bar increments smoothly between stages
- When status = READY_FOR_REVIEW: Auto-redirect to Review screen after 2s or show "Review Declaration" button
- When status = FAILED: Show error message with details, "Retry Processing" and "Return to Upload" buttons
- Page refresh/navigation-back preserves processing (can return via Declarations list)

**Design File Reference:** `figma.com/processing-status` (TBD)

---

### Screen 4: Review & Edit Declaration (Primary Workspace)

**Purpose:** Allow users to verify AI output, make corrections, and approve declaration

**Key Elements:**

**Layout: Split View (40% PDF / 60% Form)**

**Left Panel (PDF Viewer):**
- Document selector tabs: AN | BOL | CO | Invoice (current tab highlighted)
- PDF canvas with react-pdf 9.1
- Toolbar:
  - Page navigation: ← → (Previous/Next)
  - Page indicator: "Page 2 of 5"
  - Zoom controls: - | Fit Width | Fit Page | +
  - Search icon (opens search dialog)
- Thumbnail sidebar (collapsible, left edge)
- Highlighted bounding boxes when field clicked (red outline for 3s)

**Right Panel (Declaration Form):**
- Sticky header:
  - Declaration ID and status badge
  - Auto-save indicator: "Saved" (green check) or "Saving..." (spinner)
  - Action buttons: Approve (primary, green) | Reject (secondary, red)
- Form sections (collapsible accordions):
  1. **Company Information**
     - Importer name, address, tax ID (color-coded by confidence)
  2. **Shipment Details**
     - Container numbers, arrival date, port (color-coded)
  3. **Product Line Items** (Table with add/remove rows)
     - Columns: Description, HS Code, Quantity, Unit Price, Total, Origin
     - Each cell color-coded (green/yellow/red)
     - Info icon on fields with validation warnings
  4. **Tax Calculations** (Read-only, calculated fields)
     - Subtotal, Import Duty, VAT, Total Payable
- Validation Warnings Panel (collapsible, between form and actions):
  - Warning icon with count badge: "⚠ 3 Warnings"
  - List of warnings with severity (Error = red, Warning = yellow)
  - Each warning shows: Message | Affected field link | Dismiss button

**Interaction Notes:**
- Color coding: Green (#10B981) >90%, Yellow (#F59E0B) 70-90%, Red (#EF4444) <70%
- Click any form field label or "View Source" icon → PDF jumps to source location
- Inline editing: Click field to edit, Tab to next field
- Auto-save triggers every 5 seconds if changes detected
- Approve button disabled if: Unsaved changes OR errors present (only warnings can be dismissed)
- Validation warnings can be dismissed with "I have verified this is correct" confirmation
- Keyboard shortcuts:
  - Ctrl+S: Manual save
  - Ctrl+Enter: Approve (if ready)
  - Ctrl+F: Search in PDF
  - Tab: Navigate fields
  - Escape: Close modals/dialogs

**Design File Reference:** `figma.com/review-edit-screen` (TBD)

---

### Screen 5: Declarations List (History)

**Purpose:** View all processed declarations, filter, search, and access past declarations

**Key Elements:**
- Page header: "Declarations" with "Upload New" button (primary, top-right)
- Filter/Search bar:
  - Search by Declaration ID (text input with search icon)
  - Status filter dropdown: All | Processing | Ready for Review | Approved | Rejected
  - Date range picker
- Data table (sortable columns):
  - Declaration ID (link to review screen)
  - Upload Date (sortable, default descending)
  - Status (badge with color: Gray/Blue/Green/Red)
  - Products Count
  - Uploaded By (user name)
  - Actions (icon buttons: Review | Download | Delete)
- Pagination: "Showing 1-20 of 247" with Previous/Next buttons
- Empty state (if no declarations): "No declarations found. Upload a new one to get started."

**Interaction Notes:**
- Click Declaration ID or Review icon → Navigate to Review screen
- Click Download icon → Download Excel file (only for Approved status)
- Click Delete icon → Confirm dialog "Are you sure? This cannot be undone." → Soft delete
- Sort by clicking column headers (ascending/descending toggles)
- Pagination shows max 20 per page
- Search debounces 300ms
- Filters update URL query params (shareable links)

**Design File Reference:** `figma.com/declarations-list` (TBD)

---

### Screen 6: Analytics Dashboard

**Purpose:** Show correction insights and API cost tracking (Operations Manager)

**Key Elements:**
- Page header: "Analytics" with date range selector (Last 7 days | 30 days | 90 days | All time)
- KPI Cards (top row, 4 cards):
  1. Total Declarations Processed
  2. Average Corrections per Declaration
  3. Accuracy Trend (↑ 5.2% improvement)
  4. Monthly API Cost ($27.43 / $50 budget)
- Charts (2-column grid):
  - **Corrections Over Time** (Line chart by week)
  - **Top 10 Most Corrected Fields** (Horizontal bar chart)
  - **Corrections by Confidence Level** (Pie chart: High/Medium/Low)
  - **API Cost Breakdown** (Stacked area: Document AI vs OpenRouter)
- Recent Corrections Table:
  - Declaration ID | Field Name | Original Value | Corrected Value | User | Timestamp
  - Click row to view declaration
- Export button: "Export to CSV"

**Interaction Notes:**
- Date range filter updates all charts/metrics
- Charts are interactive (hover for tooltips with exact values)
- API Cost card shows yellow warning at 80% budget, red at 100%
- Export CSV includes all corrections data for selected date range
- Access restricted to admin users (redirect non-admins with permission error)

**Design File Reference:** `figma.com/analytics-dashboard` (TBD)

---

### Screen 7: Knowledge Base Management

**Purpose:** Upload and manage Good List and EXIM Tariff versions

**Key Elements:**
- Page header: "Knowledge Base Management"
- Two sections (2-column layout):

**Good List Section:**
- Current version info:
  - "Good List - Version 3"
  - "Uploaded: 2025-09-15 by Linh"
  - "Records: 1,532 entries"
- "Upload New Version" button (primary)
- "View Version History" button (secondary)

**EXIM Tariff Section:**
- Current version info:
  - "EXIM Tariff - Version 2"
  - "Uploaded: 2025-10-01 by Linh"
  - "Records: Complete tariff database"
- "Upload New Version" button (primary)
- "View Version History" button (secondary)

**Upload Modal (appears when Upload clicked):**
- "Upload [Good List / EXIM Tariff]" title
- File drop zone (accepts .xls, .xlsx)
- Preview table (first 10 rows) after file selected
- Total row count: "1,642 entries detected"
- Validation warnings (if any): "47 duplicate HS codes will be kept"
- Confirm button: "Replace X existing entries" (primary, requires confirmation)
- Cancel button

**Version History Modal:**
- Table: Version # | Upload Date | Uploaded By | Record Count | Status | Actions
- Status: Active (green badge) or Archived (gray)
- Actions: View Details | Rollback (for archived only)
- Rollback confirms: "Rollback to Version 2? Current version will be archived. Reason: [text input]"

**Interaction Notes:**
- Upload triggers background Celery task, shows progress toast
- Success toast: "Good List updated successfully. 1,532 entries imported."
- Error shows specific issue: "Missing column: hs_code. Please check template."
- Rollback requires reason (logged in audit trail)
- Version history paginated (50 per page)

**Design File Reference:** `figma.com/knowledge-base-mgmt` (TBD)

---
