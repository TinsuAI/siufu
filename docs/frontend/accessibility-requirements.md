# Accessibility Requirements

## Compliance Target

**Standard:** WCAG 2.1 Level AA

This ensures the platform is usable by people with:
- Visual impairments (low vision, color blindness)
- Motor impairments (keyboard-only navigation)
- Cognitive impairments (clear language, consistent patterns)

## Key Requirements

### Visual

**Color Contrast Ratios:**
- Normal text (16px): Minimum 4.5:1 contrast ratio
- Large text (24px+): Minimum 3:1 contrast ratio
- Interactive elements: Minimum 3:1 for borders/icons
- **Testing:** Use WebAIM Contrast Checker or browser DevTools

**Focus Indicators:**
- Visible focus ring on all interactive elements (buttons, links, inputs)
- Focus ring: 2px solid blue (#3B82F6), 2px offset
- Never remove focus styles with `outline: none` unless replacing with alternative

**Text Sizing:**
- Support browser zoom up to 200% without horizontal scrolling
- Use `rem` units for font sizes (not `px`)
- Don't disable pinch-to-zoom on mobile

### Interaction

**Keyboard Navigation:**
- All functionality accessible via keyboard (no mouse-only interactions)
- Logical tab order (top to bottom, left to right)
- Skip links: "Skip to main content" at page top
- Modals trap focus (Tab cycles within modal, Escape closes)
- Keyboard shortcuts documented and discoverable

**Screen Reader Support:**
- Semantic HTML: Use `<button>` for buttons, `<a>` for links, `<nav>` for navigation
- ARIA labels for icon-only buttons: `aria-label="Delete declaration"`
- ARIA live regions for dynamic updates: `<div aria-live="polite">` for toast notifications
- Form field labels: Always use `<label>` with `htmlFor` attribute
- Error announcements: Use `aria-describedby` to link errors to fields

**Touch Targets:**
- Minimum 44x44px tap target size (WCAG 2.5.5)
- Spacing between tap targets: 8px minimum
- Avoid hover-only interactions (provide tap alternative)

### Content

**Alternative Text:**
- All images have `alt` text (or `alt=""` if decorative)
- Icon-only buttons have `aria-label`
- PDF thumbnails: `alt="Page 2 of Invoice"`

**Heading Structure:**
- Proper heading hierarchy (H1 → H2 → H3, no skipping levels)
- One H1 per page (page title)
- Headings describe following content

**Form Labels:**
- Every form field has associated `<label>`
- Required fields indicated with `*` AND `aria-required="true"`
- Error messages linked with `aria-describedby`
- Group related fields with `<fieldset>` and `<legend>`

## Testing Strategy

**Automated Testing:**
- Lighthouse accessibility audits (CI/CD pipeline)
- axe DevTools browser extension (dev testing)
- Jest + jest-axe for component unit tests

**Manual Testing:**
- Keyboard-only navigation testing (unplug mouse)
- Screen reader testing: NVDA (Windows), VoiceOver (macOS)
- Color blindness simulation: Chrome DevTools or browser extensions
- Zoom testing: Verify layout at 200% zoom

**User Testing:**
- Include users with disabilities in UAT (Week 9-10)
- Collect accessibility feedback via dedicated email/form

---
