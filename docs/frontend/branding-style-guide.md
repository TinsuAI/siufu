# Branding & Style Guide

**Visual Identity:**
No existing brand guidelines. MVP uses minimal professional aesthetic optimized for data-dense interfaces.

## Color Palette

| Color Type | Hex Code | Usage |
|------------|----------|-------|
| **Primary** | `#1E40AF` (Navy Blue 700) | Primary buttons, links, active states, header background |
| **Secondary** | `#64748B` (Slate 500) | Secondary text, borders, disabled states |
| **Accent** | `#3B82F6` (Blue 500) | Interactive elements on hover, focus rings |
| **Success** | `#10B981` (Green 500) | Approved status, high confidence >90%, success messages |
| **Warning** | `#F59E0B` (Amber 500) | Medium confidence 70-90%, warning messages, caution states |
| **Error** | `#EF4444` (Red 500) | Low confidence <70%, errors, destructive actions, rejected status |
| **Neutral** | `#F8FAFC` (Slate 50) for backgrounds, `#1E293B` (Slate 800) for text | Page backgrounds, card backgrounds, body text, headings |

**Rationale:**
- Navy blue conveys trust and professionalism (appropriate for customs/government context)
- Green/yellow/red traffic light system is universally understood for confidence levels
- Slate grays provide excellent readability for data-heavy interfaces
- All colors meet WCAG AA contrast requirements (4.5:1 minimum)

## Typography

### Font Families
- **Primary:** `Inter` (sans-serif) - Optimized for screen readability, excellent for dense tabular data
- **Secondary:** `Inter` (same as primary for consistency)
- **Monospace:** `JetBrains Mono` - For Declaration IDs, HS Codes, timestamps

**Font Loading Strategy:**
- Use `next/font` for optimized font loading (zero layout shift)
- Subset to Latin + Vietnamese characters only
- Fallback stack: `Inter, system-ui, -apple-system, "Segoe UI", sans-serif`

### Type Scale

| Element | Size | Weight | Line Height | Usage |
|---------|------|--------|-------------|-------|
| **H1** | `2rem` (32px) | 700 (Bold) | 1.2 | Page titles (Upload New Declaration) |
| **H2** | `1.5rem` (24px) | 600 (Semi-bold) | 1.3 | Section headers (Company Information) |
| **H3** | `1.25rem` (20px) | 600 (Semi-bold) | 1.4 | Subsection headers (Product Line Items) |
| **Body** | `1rem` (16px) | 400 (Regular) | 1.5 | Form fields, table data, body text |
| **Small** | `0.875rem` (14px) | 400 (Regular) | 1.4 | Helper text, timestamps, secondary info |
| **Tiny** | `0.75rem` (12px) | 500 (Medium) | 1.3 | Badge labels, metadata |

**Accessibility Notes:**
- Never use font size <12px (WCAG requirement)
- Line height 1.5 for body text improves readability
- Bold weights (700) only for headings to avoid visual noise

## Iconography

**Icon Library:** Lucide Icons (https://lucide.dev/)
- Modern, consistent stroke width
- 24x24px default size (scale down to 16px for inline icons)
- Tree-shakeable (import only icons used)
- MIT license (safe for commercial use)

**Usage Guidelines:**
- Use icons to supplement text, not replace it (except for universally understood icons like ✓, X, ⚠)
- Icon buttons must have aria-label: `<button aria-label="Delete declaration">`
- Maintain 2px stroke width for consistency
- Color: Inherit from parent text color
- Hover state: Slight scale up (1.05x) for feedback

**Common Icons:**
- Upload: `Upload` icon
- Download: `Download` icon
- Checkmark: `Check` icon
- Warning: `AlertTriangle` icon
- Error: `XCircle` icon
- Info: `Info` icon
- Search: `Search` icon
- Edit: `Pencil` icon
- Delete: `Trash2` icon
- View: `Eye` icon
- PDF: `FileText` icon

## Spacing & Layout

**Grid System:**
- 12-column grid (desktop)
- 8-column grid (tablet)
- 4-column grid (mobile)
- Gutter: 24px (desktop), 16px (tablet/mobile)
- Max content width: 1440px (centered)

**Spacing Scale:** (Tailwind default scale, base 4px)
- `xs`: 4px (0.25rem) - Icon spacing
- `sm`: 8px (0.5rem) - Tight spacing between related elements
- `md`: 16px (1rem) - Default spacing between form fields
- `lg`: 24px (1.5rem) - Spacing between sections
- `xl`: 32px (2rem) - Spacing between major page sections
- `2xl`: 48px (3rem) - Top/bottom page padding

**Component Spacing:**
- Form field label to input: `sm` (8px)
- Between form fields: `md` (16px)
- Section heading to content: `md` (16px)
- Between sections: `xl` (32px)
- Page padding: `2xl` (48px) top/bottom, `lg` (24px) left/right

**Layout Patterns:**
- **Card:** White background, 1px border (slate-200), 8px border-radius, 24px padding
- **Panel:** Light background (slate-50), no border, 16px padding
- **Sticky Header:** 60px height, white background, 1px bottom border, z-index 50

---
