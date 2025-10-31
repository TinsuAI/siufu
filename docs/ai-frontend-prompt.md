# CUSTOMS DECLARATION AUTOMATION PLATFORM - COMPLETE FRONTEND APPLICATION

> **Last Updated:** 2025-10-30
> **Version:** 1.2 - Updated for Story 1.6 & 3.3 changes (4 required files: AN, BOL, CO [multiple], INVOICE; Good List/EXIM Tariff now knowledge base only; all files max 20MB)

## HIGH-LEVEL GOAL

Create a complete, production-ready Next.js 15.5.6 frontend application for a Customs Declaration Automation Platform. This is a professional B2B SaaS tool for Vietnamese logistics companies to process customs declarations using AI-powered document extraction. The application enables users to upload customs documents, review AI-extracted data side-by-side with source PDFs, make corrections, and export finalized Excel declarations.

---

## PROJECT CONTEXT & TECH STACK

**Core Purpose:** AI-assisted customs declaration processing system that reduces 45-minute manual data entry to 5-minute review workflows.

**Target Users:** Customs processing specialists at logistics companies who handle 20+ declarations daily.

**Tech Stack:**
- **Framework:** Next.js 15.5.6 with App Router (TypeScript 5.6, strict mode)
- **Styling:** Tailwind CSS 4.0 + shadcn/ui component library
- **State Management:** Zustand (client state) + TanStack Query (server state/caching)
- **Forms:** React Hook Form + Zod validation
- **PDF Rendering:** react-pdf 9.1
- **Backend API:** FastAPI (REST) at `http://localhost:8000/api`
- **Authentication:** JWT tokens in httpOnly cookies

**Design System:**
- **Theme:** Professional light theme with shadcn/ui default palette
- **Primary Colors:**
  - Navy Blue (slate-700): Trust, professional, headers
  - Green (emerald-500): Success, high confidence (>90%)
  - Amber (amber-500): Warning, medium confidence (70-90%)
  - Red (rose-500): Error, low confidence (<70%)
- **Typography:** Clean sans-serif (Inter or system font stack)
- **Layout:** Desktop-first (1920x1080 primary, minimum 1366x768)
- **Components:** Use shadcn/ui components exclusively (Button, Card, Input, Table, Badge, etc.)

---

## DETAILED STEP-BY-STEP INSTRUCTIONS

### PHASE 1: Project Foundation & Layout

1. **Create Next.js 15.5.6 application structure** using App Router with the following directory layout:
   ```
   frontend/
   ├── src/
   │   ├── app/
   │   │   ├── layout.tsx           # Root layout with navigation
   │   │   ├── page.tsx              # Redirect to /login or /declarations
   │   │   ├── login/page.tsx        # Story 3.2: Login screen
   │   │   ├── upload/page.tsx       # Story 3.3: File upload
   │   │   ├── declarations/
   │   │   │   ├── page.tsx          # Story 3.9: History list
   │   │   │   └── [id]/
   │   │   │       ├── page.tsx      # Story 3.4: Processing status
   │   │   │       └── review/page.tsx # Story 3.6: Review form
   │   │   └── analytics/page.tsx    # Story 4.2: Analytics (bonus)
   │   ├── components/
   │   │   ├── ui/                   # shadcn/ui components
   │   │   ├── layout/
   │   │   │   ├── header.tsx        # Navigation header
   │   │   │   └── sidebar.tsx       # Optional side nav
   │   │   ├── upload/
   │   │   │   ├── file-drop-zone.tsx
   │   │   │   └── file-checklist.tsx
   │   │   ├── review/
   │   │   │   ├── pdf-viewer.tsx    # Story 3.5: PDF component
   │   │   │   ├── declaration-form.tsx
   │   │   │   ├── confidence-badge.tsx
   │   │   │   └── validation-warnings.tsx
   │   │   └── declarations/
   │   │       └── declarations-table.tsx
   │   ├── lib/
   │   │   ├── api.ts                # API client with axios/fetch
   │   │   ├── auth.ts               # JWT token management
   │   │   └── utils.ts              # Utility functions
   │   ├── hooks/
   │   │   ├── use-auth.ts           # Authentication hook
   │   │   ├── use-declarations.ts   # TanStack Query hooks
   │   │   └── use-auto-save.ts      # Auto-save functionality
   │   ├── stores/
   │   │   └── auth-store.ts         # Zustand auth state
   │   └── types/
   │       └── index.ts              # TypeScript types
   ```

2. **Configure Tailwind CSS 4.0** with shadcn/ui:
   - Install shadcn/ui components: `npx shadcn-ui@latest init`
   - Configure `tailwind.config.ts` with professional light theme colors
   - Set up CSS variables for semantic colors (--primary, --secondary, etc.)
   - Add custom utilities for confidence colors:
     ```css
     .confidence-high { @apply bg-emerald-100 border-emerald-500 text-emerald-900; }
     .confidence-medium { @apply bg-amber-100 border-amber-500 text-amber-900; }
     .confidence-low { @apply bg-rose-100 border-rose-500 text-rose-900; }
     ```

3. **Create root layout** (`src/app/layout.tsx`) with:
   - Global navigation header (sticky top, white background, shadow)
   - Header includes: Logo/brand, navigation links (Declarations, Upload, Analytics), user avatar with dropdown (Profile, Logout)
   - TanStack Query Provider wrapper
   - Toast notification system (using shadcn/ui Toaster)
   - Loading states and error boundaries

### PHASE 2: Authentication (Story 3.2)

4. **Create Login Screen** (`src/app/login/page.tsx`):
   - Center-aligned card (max-width 400px) on light gray background
   - Card contains:
     - Logo/heading: "Customs Declaration Platform"
     - Email input (type="email", required, with validation)
     - Password input (type="password", required, with show/hide toggle icon)
     - "Remember me" checkbox
     - "Login" button (full-width, primary blue, loading state)
     - Clear error message display below button (red text)
   - Form validation using React Hook Form + Zod
   - On submit: POST to `/api/auth/login`, store JWT in cookie, redirect to `/declarations`
   - Error handling: Display "Invalid email or password" for 401 responses

5. **Implement authentication hook** (`src/hooks/use-auth.ts`):
   - Check authentication status from cookie
   - Provide login/logout functions
   - Automatic redirect to `/login` for unauthenticated users on protected routes

6. **Create protected route wrapper** for all authenticated pages

### PHASE 3: File Upload Interface (Story 3.3)

7. **Create Upload Screen** (`src/app/upload/page.tsx`):
   - Page heading: "Upload Declaration Documents"
   - Subheading: "Upload all 4 required source documents to begin processing"
   - Info banner (light blue background): "Note: Good List and EXIM Tariff are managed as knowledge base data and do not need to be uploaded per declaration."
   - Grid layout (2 columns on desktop, 1 on tablet) with 4 file drop zones:
     1. **Arrival Notice (AN.pdf)** - Required: PDF only, single file, max 20MB
     2. **Bill of Lading (BOL.pdf)** - Required: PDF only, single file, max 20MB
     3. **Certificate of Origin (CO.pdf)** - Required: PDF only, **MULTIPLE FILES ACCEPTED**, max 20MB each
     4. **Invoice** - Required: PDF or JPG/PNG, single file, max 20MB
   - Each drop zone is a `FileDropZone` component with:
     - Dashed border (blue-300) with hover state (blue-500)
     - Icon: Upload cloud icon or document icon
     - Label: Document name (bold)
     - Status indicator: Empty (gray), Uploaded (green checkmark), Error (red X)
     - File name display when uploaded
     - "Remove" button to clear uploaded file
     - Click to open file browser or drag-and-drop
     - Client-side validation: file type, size limits (all files max 20MB)
   - **Special handling for Certificate of Origin zone:**
     - Accept multiple files (up to 10 CO files)
     - Display list of uploaded CO files with individual remove buttons
     - Show count: "3 CO files uploaded" with green checkmark
     - Visual list showing each CO filename (e.g., "CO_Form_E.pdf", "CO_Form_D.pdf")
     - "Add Another CO" button to upload additional certificates
   - Visual checklist below grid showing overall progress (e.g., "All 4 required file types uploaded (5 total files: AN, BOL, 3×CO, INVOICE)")
   - "Process Declaration" button:
     - Bottom-right, large, primary blue
     - Disabled (gray) until all 4 required file types uploaded (AN, BOL, at least 1 CO, INVOICE)
     - Tooltip on hover when disabled: "Please upload all 4 required document types"
     - Shows loading spinner when processing upload
   - On click: Upload files to `POST /api/declarations/upload`, then redirect to `/declarations/[id]` (processing status)

8. **Create FileDropZone component** (`src/components/upload/file-drop-zone.tsx`):
   - Accepts: label, fileType (pdf/image), maxSize (default 20MB), allowMultiple (boolean), onFileSelect callback
   - Implements drag-and-drop with visual feedback
   - File validation with clear error messages (show file size in MB if exceeds limit)
   - Accessible keyboard support
   - When `allowMultiple=true`: maintain array of files and show list view with remove buttons

### PHASE 4: Processing Status Display (Story 3.4)

9. **Create Processing Status Screen** (`src/app/declarations/[id]/page.tsx`):
   - Center-aligned card (max-width 600px)
   - Heading: "Processing Declaration #{id}"
   - Progress stepper showing stages (use shadcn/ui Steps or custom component):
     1. Uploading (completed checkmark)
     2. OCR Processing (current - blue spinner)
     3. AI Extraction (pending - gray)
     4. Validation (pending - gray)
     5. Generating Excel (pending - gray)
     6. Ready for Review (pending - gray)
   - Progress bar (0-100%) with animated fill
   - Status text: "Currently processing: OCR on documents..." (updates in real-time)
   - Estimated time remaining: "Approximately 60 seconds remaining"
   - Poll `GET /api/declarations/{id}/status` every 2 seconds using TanStack Query
   - When status = "READY_FOR_REVIEW": Show "Review Declaration" button (navigate to `/declarations/{id}/review`)
   - When status = "FAILED":
     - Show error message in red alert box
     - "Retry Processing" button (POST `/api/declarations/{id}/process`)
     - After 3 failed attempts: "Contact Support" message with error ID
   - "Back to Declarations" link to return to list view

10. **Implement status polling hook** (`src/hooks/use-declaration-status.ts`) using TanStack Query with automatic refetching

### PHASE 5: PDF Viewer Component (Story 3.5)

11. **Create PDF Viewer Component** (`src/components/review/pdf-viewer.tsx`):
   - Uses react-pdf 9.1 library
   - Props: `pdfUrl`, `currentPage`, `highlightBox` (for jump navigation)
   - Layout:
     - Top toolbar (sticky, white background, border-bottom):
       - Document selector dropdown (AN.pdf, BOL.pdf, CO.pdf, INVOICE)
       - Page navigation: "< Previous | Page X of Y | Next >"
       - Zoom controls: "Zoom Out | Fit Width | Fit Page | Zoom In"
       - Search input with magnifying glass icon
     - Main PDF canvas area (scrollable, centered)
     - Optional: Thumbnail sidebar (collapsible, left side, 100px wide thumbnails)
   - Features:
     - Render PDF pages with canvas
     - Zoom levels: 50%, 75%, 100%, 125%, 150%, 200%
     - Search functionality (highlight matching text)
     - Highlight specific areas (red rectangle overlay) when `highlightBox` prop provided
     - Smooth scroll to highlighted area
     - Loading skeleton while PDF loads
   - Performance: Lazy load pages (only render visible + 1 above/below)
   - Keyboard shortcuts: Arrow keys for navigation, +/- for zoom

### PHASE 6: Declaration Review Form (Story 3.6 + 3.7)

12. **Create Review & Edit Screen** (`src/app/declarations/[id]/review/page.tsx`):
   - **Layout:** Split-view (40% PDF viewer left, 60% form right on desktop)
   - **Sticky Header** (top of page, white background, shadow):
     - Breadcrumb: "Declarations > Declaration #{id}"
     - Status badge (e.g., "READY FOR REVIEW" in blue)
     - Action buttons (right side):
       - "Reject" button (outline, red)
       - "Approve" button (solid, green, disabled if unsaved changes)
     - Auto-save indicator: "Saving..." (spinner) or "All changes saved" (green checkmark)
   - **Left Panel: PDF Viewer** (using component from Step 11)
   - **Right Panel: Declaration Form** (scrollable):
     - Fetch data from `GET /api/declarations/{id}` on mount
     - Form sections (collapsible accordions using shadcn/ui Accordion):
       1. **Company Information**
          - Importer name, address, tax ID
          - Exporter name, address, country
       2. **Shipment Details**
          - Bill of Lading number, container numbers
          - Arrival date, invoice date
          - Total invoice value
       3. **Product Line Items** (table with editable rows)
          - Columns: Product Description, HS Code, Quantity, Unit Price, Total, Origin, Confidence
          - Each field has confidence badge (green/yellow/red pill)
          - Click confidence badge to toggle between showing/hiding low-confidence fields
          - "Add Product" button to insert new row
          - "Remove" button (trash icon) on each row
       4. **Tax Calculations**
          - Subtotal, Import Duty, VAT, Total Payable (calculated fields)
     - **Confidence Badges:** Color-coded pill badges next to each field:
       - Green: >90% confidence
       - Yellow: 70-90% confidence
       - Red: <70% confidence
     - **Inline Editing:** All fields editable using React Hook Form
     - **Field Click → PDF Jump:** Each field label has small "eye" icon. Click to:
       - Switch PDF viewer to correct document
       - Navigate to correct page
       - Highlight source location with red rectangle overlay for 3 seconds
     - **Validation Warnings Panel** (below form, collapsible):
       - Warning icon + message (e.g., "Invoice total ($23,208) does not match CO total ($23,200)")
       - Severity indicator: Error (red, blocks approval) vs Warning (yellow, allows proceed with confirmation)
       - Dismissible with "I have verified this is correct" checkbox
     - **Auto-save:** Use debounced PATCH to `/api/declarations/{id}` every 5 seconds when form is dirty
     - Form validation: Zod schema with inline error messages

13. **Create Confidence Badge Component** (`src/components/review/confidence-badge.tsx`):
   - Props: `confidence` (0-100), `size` (sm/md/lg)
   - Returns colored badge with percentage
   - Tooltip on hover: "High/Medium/Low confidence based on AI extraction"

14. **Create Validation Warnings Component** (`src/components/review/validation-warnings.tsx`):
   - Props: `warnings` array
   - Collapsible panel using shadcn/ui Collapsible
   - List of warning cards with icon, message, severity

15. **Implement PDF jump navigation:**
   - When field icon clicked, emit event with source metadata
   - PDF viewer receives event and updates `highlightBox` state
   - Highlight rectangle rendered as absolute-positioned overlay on PDF canvas

16. **Implement auto-save hook** (`src/hooks/use-auto-save.ts`):
   - Debounce form changes (5 second delay)
   - PATCH to `/api/declarations/{id}` with changed fields only
   - Show toast notification on save success/failure
   - Track save status in UI (saving/saved indicator)

### PHASE 7: Approval & Export (Story 3.8)

17. **Implement approval workflow** in Review screen:
   - "Approve" button click:
     - Disable button, show loading spinner
     - POST to `/api/declarations/{id}/approve`
     - On success:
       - Show success toast: "Declaration approved successfully!"
       - Display "Download Excel" button (replaces "Approve" button)
       - Update status badge to "APPROVED" (green)
   - "Download Excel" button click:
     - GET `/api/declarations/{id}/export` (file download)
     - Browser automatically downloads `CD.xlsx`
     - Show confirmation message
   - "Reject" button click:
     - Open dialog (shadcn/ui Dialog) prompting for rejection reason
     - Textarea for reason (required)
     - POST to `/api/declarations/{id}/reject` with reason
     - Redirect to `/declarations` with toast: "Declaration rejected"

### PHASE 8: Declaration History List (Story 3.9)

18. **Create Declarations List Screen** (`src/app/declarations/page.tsx`):
   - Page heading: "Declaration History"
   - "New Declaration" button (top-right, primary blue, navigates to `/upload`)
   - Search bar (top, full-width): "Search by Declaration ID..."
   - Filters (horizontal tabs or dropdown):
     - All, Uploaded, Processing, Ready for Review, Approved, Rejected
   - **Declarations Table** (using shadcn/ui Table):
     - Columns:
       - ID (clickable link)
       - Upload Date (formatted: "Oct 27, 2025 2:30 PM")
       - Status (colored badge: gray/blue/green/red)
       - Products Count
       - Actions (button group)
     - Sortable columns (click header to sort)
     - Actions per row:
       - "Review" button (if status = Ready/Approved)
       - "Download" button (if status = Approved)
       - "Delete" button (trash icon, soft delete with confirmation)
     - Pagination at bottom: "< Previous | Page 1 of 5 | Next >" (20 per page)
     - Empty state (when no declarations):
       - Empty illustration or icon
       - "No declarations yet"
       - "Get Started" button (navigates to `/upload`)
   - Fetch data from `GET /api/declarations?page=1&limit=20&status=all&search=` using TanStack Query
   - Implement client-side sorting and filtering

19. **Create Declarations Table Component** (`src/components/declarations/declarations-table.tsx`):
   - Reusable table with sorting, pagination, and actions
   - Status badge component with color mapping
   - Row click navigates to detail view

### PHASE 9: Analytics Dashboard (Bonus - Story 4.2)

20. **Create Analytics Screen** (`src/app/analytics/page.tsx`) - OPTIONAL:
   - Page heading: "Correction Analytics"
   - Admin-only guard (redirect if not admin)
   - Metrics cards (grid 3 columns):
     - Total Declarations Processed
     - Average Corrections per Declaration
     - Total Corrections This Month
   - Charts (use recharts or similar):
     - Line chart: Corrections over time (last 30 days)
     - Bar chart: Top 10 most-corrected fields
     - Pie chart: Corrections by confidence level
   - Recent corrections table (last 20)
   - "Export CSV" button (downloads corrections data)
   - Date range picker (Last 7/30/90 days, All Time)
   - Fetch data from `GET /api/analytics/corrections` using TanStack Query

### PHASE 10: Global Features & Polish

21. **Implement global loading states:**
   - Page-level loading skeletons using shadcn/ui Skeleton
   - Button loading spinners
   - TanStack Query loading/error states

22. **Implement error handling:**
   - API error interceptor in `lib/api.ts`
   - Global error boundary component
   - User-friendly error messages (avoid technical jargon)
   - 404 page for invalid routes
   - Network error handling (offline detection)

23. **Implement toast notifications:**
   - Success: Green toast with checkmark icon
   - Error: Red toast with X icon
   - Info: Blue toast with info icon
   - Position: Top-right corner
   - Auto-dismiss after 5 seconds (error stays until dismissed)

24. **Add keyboard shortcuts:**
   - Ctrl+S: Manual save on review form
   - Ctrl+Enter: Approve declaration (when on review screen)
   - Esc: Close dialogs/modals

25. **Responsive design:**
   - Desktop (≥1920px): Full split-view layout
   - Laptop (1366px-1919px): Adjust panel widths (50/50 split)
   - Tablet (768px-1365px): Stack PDF and form vertically or use tabs
   - Mobile (<768px): Show message "Please use desktop browser for optimal experience"

26. **Accessibility (WCAG AA):**
   - All interactive elements keyboard-accessible (tab navigation)
   - Focus indicators (blue outline ring)
   - ARIA labels on icons and buttons
   - Semantic HTML (nav, main, section, etc.)
   - Color coding supplemented with icons (not color-only)
   - Minimum contrast ratio 4.5:1
   - Screen reader support (alt text, aria-live regions for status updates)

27. **Performance optimizations:**
   - Next.js Image component for all images
   - React.lazy() for heavy components (PDF viewer)
   - TanStack Query caching (5-minute stale time for declarations list)
   - Debounced search inputs
   - Virtual scrolling for large tables (if >100 rows)

---

## CODE EXAMPLES & DATA STRUCTURES

### API Contracts (TypeScript Types)

```typescript
// src/types/index.ts

export interface User {
  id: string;
  email: string;
  name: string;
  role: 'processor' | 'admin';
}

export interface Declaration {
  id: string;
  status: 'UPLOADED' | 'PROCESSING' | 'READY_FOR_REVIEW' | 'APPROVED' | 'REJECTED' | 'FAILED';
  upload_date: string; // ISO 8601
  products_count: number;
  created_by: string; // User ID
  uploaded_files: {
    an: string; // AN.pdf filename
    bol: string; // BOL.pdf filename
    co: string[]; // Array of CO filenames (e.g., ["CO_1.pdf", "CO_2.pdf"])
    invoice: string; // INVOICE.pdf filename
  };
  extracted_data?: ExtractedData;
  validation_warnings?: ValidationWarning[];
}

export interface ExtractedData {
  // Company Information
  importer: {
    name: { value: string; confidence: number; source?: SourceLocation };
    address: { value: string; confidence: number; source?: SourceLocation };
    tax_id: { value: string; confidence: number; source?: SourceLocation };
  };
  exporter: {
    name: { value: string; confidence: number; source?: SourceLocation };
    address: { value: string; confidence: number; source?: SourceLocation };
    country: { value: string; confidence: number; source?: SourceLocation };
  };

  // Shipment Details
  shipment: {
    bill_of_lading_number: { value: string; confidence: number; source?: SourceLocation };
    container_numbers: { value: string[]; confidence: number; source?: SourceLocation };
    arrival_date: { value: string; confidence: number; source?: SourceLocation };
    invoice_date: { value: string; confidence: number; source?: SourceLocation };
    invoice_total: { value: number; confidence: number; source?: SourceLocation };
  };

  // Products
  products: Array<{
    description: { value: string; confidence: number; source?: SourceLocation };
    hs_code: { value: string; confidence: number; source?: SourceLocation };
    quantity: { value: number; confidence: number; source?: SourceLocation };
    unit_price: { value: number; confidence: number; source?: SourceLocation };
    total: { value: number; confidence: number; source?: SourceLocation };
    origin: { value: string; confidence: number; source?: SourceLocation };
  }>;

  // Tax Calculations
  taxes: {
    subtotal: number;
    import_duty: number;
    vat: number;
    total_payable: number;
  };
}

export interface SourceLocation {
  document: 'AN.pdf' | 'BOL.pdf' | 'INVOICE.pdf' | string; // string allows CO_1.pdf, CO_2.pdf, etc.
  page: number;
  bbox?: { x: number; y: number; width: number; height: number };
}

export interface ValidationWarning {
  id: string;
  severity: 'error' | 'warning';
  message: string;
  field?: string;
  dismissed: boolean;
}

export interface ProcessingStatus {
  declaration_id: string;
  status: Declaration['status'];
  current_stage: string;
  progress_percentage: number;
  estimated_time_remaining: number; // seconds
  error_message?: string;
  retry_count?: number;
}
```

### API Endpoint Examples

```typescript
// src/lib/api.ts

import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE,
  withCredentials: true, // Include cookies
});

// Authentication
export const login = (email: string, password: string) =>
  api.post<{ user: User }>('/auth/login', { email, password });

export const logout = () => api.post('/auth/logout');

// Declarations
export const uploadDeclaration = (files: FormData) =>
  api.post<{ declaration_id: string; uploaded_files: Declaration['uploaded_files'] }>('/declarations/upload', files);

// Usage example for upload with multiple CO files:
// const formData = new FormData();
// formData.append('an', anFile);  // Single File object
// formData.append('bol', bolFile);  // Single File object
// formData.append('co', coFile1);  // Multiple File objects with same key
// formData.append('co', coFile2);
// formData.append('co', coFile3);
// formData.append('invoice', invoiceFile);  // Single File object
// const result = await uploadDeclaration(formData);

export const getDeclarations = (params: { page: number; limit: number; status?: string; search?: string }) =>
  api.get<{ declarations: Declaration[]; total: number }>('/declarations', { params });

export const getDeclaration = (id: string) =>
  api.get<Declaration>(`/declarations/${id}`);

export const getDeclarationStatus = (id: string) =>
  api.get<ProcessingStatus>(`/declarations/${id}/status`);

export const updateDeclaration = (id: string, data: Partial<ExtractedData>) =>
  api.patch<Declaration>(`/declarations/${id}`, data);

export const approveDeclaration = (id: string) =>
  api.post(`/declarations/${id}/approve`);

export const rejectDeclaration = (id: string, reason: string) =>
  api.post(`/declarations/${id}/reject`, { reason });

export const downloadExcel = (id: string) =>
  api.get(`/declarations/${id}/export`, { responseType: 'blob' });
```

### Form Validation Schema Example

```typescript
// Example Zod schema for declaration form
import { z } from 'zod';

export const declarationFormSchema = z.object({
  importer: z.object({
    name: z.string().min(1, 'Importer name is required'),
    address: z.string().min(1, 'Address is required'),
    tax_id: z.string().regex(/^\d{10,13}$/, 'Tax ID must be 10-13 digits'),
  }),
  products: z.array(
    z.object({
      description: z.string().min(1, 'Product description is required'),
      hs_code: z.string().regex(/^\d{8}$/, 'HS Code must be 8 digits'),
      quantity: z.number().positive('Quantity must be positive'),
      unit_price: z.number().positive('Unit price must be positive'),
    })
  ).min(1, 'At least one product is required'),
});
```

### shadcn/ui Components to Install

```bash
# Install these shadcn/ui components:
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add input
npx shadcn-ui@latest add label
npx shadcn-ui@latest add table
npx shadcn-ui@latest add badge
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add dropdown-menu
npx shadcn-ui@latest add toast
npx shadcn-ui@latest add accordion
npx shadcn-ui@latest add checkbox
npx shadcn-ui@latest add select
npx shadcn-ui@latest add skeleton
npx shadcn-ui@latest add alert
npx shadcn-ui@latest add progress
npx shadcn-ui@latest add tabs
npx shadcn-ui@latest add collapsible
```

---

## CONSTRAINTS & WHAT NOT TO DO

**DO NOT:**
1. ❌ Use any CSS framework other than Tailwind CSS 4.0
2. ❌ Use any component library other than shadcn/ui
3. ❌ Use Redux or other complex state management (use Zustand + TanStack Query only)
4. ❌ Store JWT tokens in localStorage (use httpOnly cookies only)
5. ❌ Implement authentication backend (assume API endpoints exist)
6. ❌ Make the UI mobile-first (this is desktop-first B2B tool)
7. ❌ Add animations or transitions that slow down power users
8. ❌ Use color-only indicators (always pair with icons for accessibility)
9. ❌ Hard-code API URLs (use environment variables)
10. ❌ Skip TypeScript types (strict mode required)
11. ❌ Create custom form validation logic (use React Hook Form + Zod)
12. ❌ Build custom PDF rendering (use react-pdf library)
13. ❌ Implement file upload backend logic (just send to API endpoint)
14. ❌ Add unnecessary features beyond the specified stories

**DO:**
1. ✅ Use Next.js 15.5.6 App Router (not Pages Router)
2. ✅ Use TypeScript strict mode for all files
3. ✅ Use shadcn/ui components styled with Tailwind CSS
4. ✅ Implement proper loading states for all async operations
5. ✅ Add comprehensive error handling with user-friendly messages
6. ✅ Make all interactive elements keyboard-accessible
7. ✅ Add proper ARIA labels and semantic HTML
8. ✅ Use TanStack Query for all API data fetching
9. ✅ Implement auto-save with debouncing (5 second delay)
10. ✅ Show confidence scores with color-coded badges
11. ✅ Support PDF viewing with zoom, navigation, and search
12. ✅ Implement the split-view layout (PDF left, form right)
13. ✅ Use proper TypeScript interfaces for all API responses
14. ✅ Add toast notifications for user actions (save, approve, reject)

---

## STRICT SCOPE DEFINITION

**FILES YOU SHOULD CREATE:**

This is a complete frontend application. Generate ALL files needed for the following:

1. **All page routes** in `src/app/`:
   - `layout.tsx` (root layout with navigation)
   - `page.tsx` (home/redirect)
   - `login/page.tsx`
   - `upload/page.tsx`
   - `declarations/page.tsx`
   - `declarations/[id]/page.tsx`
   - `declarations/[id]/review/page.tsx`
   - `analytics/page.tsx` (bonus)

2. **All components** in `src/components/`:
   - All shadcn/ui components in `ui/` folder
   - Layout components (header, navigation)
   - Upload components (file-drop-zone, file-checklist)
   - Review components (pdf-viewer, declaration-form, confidence-badge, validation-warnings)
   - Declarations components (declarations-table)

3. **All utilities and hooks** in `src/lib/`, `src/hooks/`, `src/stores/`:
   - API client (`lib/api.ts`)
   - Auth utilities (`lib/auth.ts`)
   - Custom hooks (use-auth, use-declarations, use-auto-save, use-declaration-status)
   - Zustand store (`stores/auth-store.ts`)
   - TypeScript types (`types/index.ts`)

4. **Configuration files**:
   - `tailwind.config.ts`
   - `next.config.js`
   - `tsconfig.json`
   - `package.json` (with all dependencies)
   - `.env.example` (environment variable template)

**FILES YOU SHOULD NOT MODIFY:**
- DO NOT create backend API code (assume it exists)
- DO NOT create Docker configuration
- DO NOT create database migrations
- DO NOT create CI/CD configuration

---

## MOBILE-FIRST DESIGN INSTRUCTION OVERRIDE

**IMPORTANT:** This application is **desktop-first**, NOT mobile-first. Design for large screens first:

1. **Primary viewport:** 1920x1080 (full split-view layout)
2. **Minimum supported:** 1366x768 (adjust panel widths)
3. **Tablet (768-1365px):** Stack panels vertically or use tabs
4. **Mobile (<768px):** Show message: "Please use a desktop browser for optimal experience. This application requires a larger screen."

Do NOT optimize for mobile touch interactions or small screens beyond showing the desktop-only message.

---

## DELIVERABLE CHECKLIST

Before considering this prompt complete, ensure the generated code includes:

- [ ] ✅ All 6 page routes created (login, upload, processing, review, history, analytics)
- [ ] ✅ Navigation header with user authentication state
- [ ] ✅ Login form with validation and error handling
- [ ] ✅ File upload interface with 4 drop zones (AN, BOL, CO with multiple file support, INVOICE) and validation (max 20MB per file)
- [ ] ✅ Processing status screen with real-time polling
- [ ] ✅ PDF viewer component with zoom, navigation, and highlighting
- [ ] ✅ Declaration review form with confidence color-coding
- [ ] ✅ Auto-save functionality (5-second debounce)
- [ ] ✅ PDF jump navigation (click field → highlight source)
- [ ] ✅ Validation warnings panel
- [ ] ✅ Approval/rejection workflow with confirmation
- [ ] ✅ Excel download functionality
- [ ] ✅ Declarations list table with sorting, filtering, pagination
- [ ] ✅ All API integration using TanStack Query
- [ ] ✅ TypeScript interfaces for all data structures
- [ ] ✅ Toast notifications for user actions
- [ ] ✅ Loading states and error handling
- [ ] ✅ Keyboard shortcuts (Ctrl+S, Ctrl+Enter)
- [ ] ✅ Accessibility features (ARIA labels, keyboard navigation)
- [ ] ✅ Professional light theme using shadcn/ui

---

## FINAL NOTES & QUALITY STANDARDS

**Code Quality:**
- Every component must have proper TypeScript types (no `any` types)
- All async operations must have loading and error states
- All forms must have validation with clear error messages
- All API calls must use TanStack Query with proper caching
- All user actions must provide feedback (toast notifications)

**User Experience:**
- Fast and responsive (no unnecessary animations)
- Clear visual hierarchy (users should know where to look)
- Trust through transparency (show confidence scores, validation warnings)
- Power-user optimized (keyboard shortcuts, auto-save)
- Professional B2B aesthetic (not consumer/playful)

**Design Consistency:**
- Use shadcn/ui components exclusively
- Follow Tailwind CSS utility-first approach
- Maintain consistent spacing (4px grid: p-2, p-4, p-6, etc.)
- Use semantic color variables (--primary, --destructive, etc.)
- Professional light theme with high contrast

**Testing Considerations:**
- Code should be structured for easy testing (pure functions, separate logic from UI)
- API client should be mockable
- Components should accept props for dependency injection

---

## ⚠️ IMPORTANT HUMAN REVIEW NOTICE

**This AI-generated code requires careful human review, testing, and refinement before being considered production-ready.**

You MUST:
1. ✅ Review all generated components for correctness
2. ✅ Test all user workflows end-to-end
3. ✅ Verify API integration matches your backend
4. ✅ Test accessibility with keyboard navigation
5. ✅ Validate form handling and error states
6. ✅ Test PDF rendering performance with real documents
7. ✅ Review security implementation (JWT handling, XSS protection)
8. ✅ Test responsive breakpoints on actual devices
9. ✅ Validate TypeScript types match backend API contracts
10. ✅ Perform load testing with multiple concurrent users

Do NOT deploy this code without thorough testing and security review. AI-generated code is a starting point, not a finished product.

---

## HOW TO USE THIS PROMPT

### Option 1: Use with v0 by Vercel
1. Go to https://v0.dev
2. Copy the entire prompt from this file
3. Paste into v0's prompt interface
4. Review generated code iteratively
5. Download and integrate into your project

### Option 2: Use with Lovable.ai
1. Go to https://lovable.dev
2. Create new project
3. Copy the entire prompt from this file
4. Paste and let Lovable generate the full application
5. Review, test, and deploy

### Option 3: Use with Claude or ChatGPT
1. Copy the prompt from this file
2. Paste into Claude/ChatGPT
3. Ask to generate specific components one at a time
4. Iterate based on feedback

---

**Generated by:** UX Expert Agent (Sally)
**Date:** 2025-10-30
**Project:** Customs Declaration Automation Platform
**Framework:** BMAD-METHOD™
