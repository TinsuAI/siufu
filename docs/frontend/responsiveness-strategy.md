# Responsiveness Strategy

## Breakpoints

| Breakpoint | Min Width | Max Width | Target Devices | Notes |
|------------|-----------|-----------|----------------|-------|
| **Mobile** | 320px | 767px | Phones (portrait) | Out of scope for MVP - show message "Please use desktop for best experience" |
| **Tablet** | 768px | 1023px | iPad, Android tablets (landscape) | Vertical stacking of PDF and form OR tabs |
| **Desktop** | 1024px | 1439px | Laptop screens, small monitors | Side-by-side layout works |
| **Wide** | 1440px | - | Large monitors, 4K displays | Max content width 1440px (centered) |

## Adaptation Patterns

**Layout Changes:**
- **Desktop (1024px+):** Side-by-side PDF (40%) and form (60%)
- **Tablet (768-1023px):**
  - Option A: Tabs (PDF tab, Form tab) - switch between views
  - Option B: Vertical stack (PDF top 50vh, Form bottom scrollable)
  - **Recommended:** Tabs for simplicity
- **Mobile (<768px):** Show message "Desktop recommended. Mobile view coming in Phase 2."

**Navigation Changes:**
- **Desktop:** Horizontal navigation bar with all items visible
- **Tablet:** Horizontal navigation with abbreviated labels ("Declarations" → "Decl.")
- **Mobile:** Hamburger menu (out of scope for MVP)

**Content Priority:**
- **Desktop:** Show all fields, thumbnails, full labels
- **Tablet:** Hide thumbnails by default (collapse icon shows), abbreviate long labels
- **Mobile:** N/A (out of scope)

**Interaction Changes:**
- **Desktop:** Hover states on buttons/links
- **Tablet:** No hover (touch), larger tap targets (44x44px minimum)
- **Mobile:** N/A

**Implementation Notes:**
- Use Tailwind responsive prefixes: `md:grid-cols-2` (applies at 768px+)
- Test on real devices, not just browser DevTools
- Tablet support is "acceptable" quality, not pixel-perfect (desktop is priority)

---
