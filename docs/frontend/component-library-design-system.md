# Component Library / Design System

**Design System Approach:** Use shadcn/ui as the foundation with minimal customization. shadcn/ui provides:
- Radix UI primitives for accessibility
- Tailwind CSS styling
- TypeScript support
- Tree-shakeable components (copy into project)

This approach balances speed (no custom design system needed) with flexibility (components are editable source code, not npm package).

## Core Components

### Component: Button

**Purpose:** Primary action trigger throughout application

**Variants:**
- `primary`: Filled background, white text (used for main actions: Process, Approve, Upload)
- `secondary`: Outline style (used for Cancel, View Details)
- `destructive`: Red background (used for Delete, Reject)
- `ghost`: No background, hover state only (used for icon buttons)

**States:**
- Default
- Hover (darker shade)
- Active/Pressed (darkest shade)
- Disabled (50% opacity, cursor not-allowed)
- Loading (spinner + "Loading..." text)

**Usage Guidelines:**
- Maximum one primary button per screen section
- Loading state must show spinner to indicate async action
- Destructive actions require confirmation dialog
- Icon buttons must have aria-label for accessibility

---

### Component: Input Field

**Purpose:** Text, number, and date input with validation

**Variants:**
- `text`: Standard text input
- `email`: Email validation
- `number`: Numeric input with step controls
- `date`: Date picker integration

**States:**
- Default (neutral border)
- Focus (blue border, ring)
- Error (red border, error message below)
- Disabled (gray background, cursor not-allowed)
- With confidence indicator (green/yellow/red left border, 4px width)

**Usage Guidelines:**
- Always pair label with input (htmlFor/id association)
- Error messages should be specific: "HS Code must be 8 digits" not "Invalid input"
- Confidence indicator on left border for extracted fields only
- Placeholder text should be example, not instruction

---

### Component: Badge

**Purpose:** Display status, confidence, or category labels

**Variants:**
- `success`: Green background (Approved, High confidence >90%)
- `warning`: Yellow background (Medium confidence 70-90%)
- `error`: Red background (Low confidence <70%, Rejected)
- `info`: Blue background (Processing)
- `neutral`: Gray background (Uploaded, Archived)

**States:**
- Default only (badges are non-interactive)

**Usage Guidelines:**
- Use with icons for additional clarity (✓ for success, ⚠ for warning)
- Keep text concise (1-2 words max)
- Don't rely on color alone - include text or icon (accessibility)

---

### Component: Data Table

**Purpose:** Display list of declarations, corrections, version history

**Variants:**
- `default`: Standard table with borders
- `striped`: Alternating row colors for readability

**States:**
- Row hover (light background)
- Row selected (blue background)
- Sortable column header (with sort icon)

**Usage Guidelines:**
- Maximum 10 columns for readability
- Include pagination for lists >20 items
- Sortable columns show up/down arrow icon
- Actions column always right-aligned
- Mobile: Consider stacked cards instead of table

---

### Component: Modal/Dialog

**Purpose:** Upload file, confirm actions, show details

**Variants:**
- `sm`: 400px width (confirmations)
- `md`: 600px width (forms)
- `lg`: 800px width (file preview)
- `full`: 90vw width (version history table)

**States:**
- Open (with backdrop overlay, 50% black)
- Closing (fade out animation, 200ms)

**Usage Guidelines:**
- Always include close button (X icon, top-right)
- Escape key closes modal
- Click backdrop closes modal (unless form has unsaved changes)
- Focus trap: Tab cycles through modal elements only
- Primary action button on right, cancel on left

---

### Component: Toast Notification

**Purpose:** Show success/error feedback for async actions

**Variants:**
- `success`: Green background, checkmark icon
- `error`: Red background, X icon
- `info`: Blue background, info icon
- `warning`: Yellow background, warning icon

**States:**
- Entering (slide in from top-right, 300ms)
- Visible (auto-dismiss after 5s, or user clicks close)
- Exiting (fade out, 200ms)

**Usage Guidelines:**
- Position: Top-right corner, stacked vertically if multiple
- Maximum 3 toasts visible at once (oldest auto-dismissed)
- Action buttons optional: "Undo", "View Details"
- Keep message concise (1 sentence)

---

### Component: Progress Indicator

**Purpose:** Show processing status, upload progress

**Variants:**
- `linear`: Horizontal bar (0-100%)
- `circular`: Spinner (indeterminate)
- `stepper`: Multi-stage workflow (Processing Status screen)

**States:**
- In progress (animated)
- Paused (static)
- Complete (green checkmark)
- Failed (red X)

**Usage Guidelines:**
- Show percentage if known: "Processing... 67%"
- Show time estimate if >10s: "Approximately 45 seconds remaining"
- Linear for determinate progress, circular for indeterminate
- Stepper shows current stage highlighted, completed stages with checkmark

---

### Component: PDF Viewer

**Purpose:** Display source documents with navigation and zoom

**Variants:**
- `sidebar`: With thumbnail sidebar
- `compact`: No sidebar (mobile)

**States:**
- Loading (skeleton screen)
- Loaded (canvas rendering)
- Error (fallback message + download link)
- Highlighting (red bounding box for 3s when field clicked)

**Usage Guidelines:**
- Use react-pdf 9.1 library
- Lazy load pages (render viewport + 1 page buffer)
- Provide fallback for unsupported browsers: "Download PDF to view"
- Zoom levels: 50%, 75%, 100% (Fit Page), 125%, 150%, 200%, Fit Width
- Search highlights all matches in yellow, current match in orange

---
