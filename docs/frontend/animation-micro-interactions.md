# Animation & Micro-interactions

## Motion Principles

1. **Purposeful, Not Decorative:** Animations should guide attention or provide feedback, not distract
2. **Fast and Subtle:** Duration 150-300ms max. Users should barely notice the animation consciously.
3. **Respectful of Preferences:** Honor `prefers-reduced-motion` media query (disable animations)
4. **Performance First:** Use CSS transforms (`translate`, `scale`) and opacity only (not `left`, `width`, etc.)

## Key Animations

- **Button Click:** Scale down to 0.95x on active state (Duration: 100ms, Easing: ease-out)
- **Modal Open:** Fade in backdrop (0 → 0.5 opacity) + Scale modal (0.95 → 1.0) (Duration: 200ms, Easing: ease-out)
- **Modal Close:** Reverse of open (Duration: 150ms, Easing: ease-in)
- **Toast Enter:** Slide in from right + fade in (Duration: 300ms, Easing: cubic-bezier(0.4, 0, 0.2, 1))
- **Toast Exit:** Slide out to right + fade out (Duration: 200ms, Easing: ease-in)
- **Field Save Indicator:** Fade "Saving..." to "Saved" with checkmark (Duration: 300ms, Easing: ease-in-out)
- **Progress Bar:** Smooth fill (Duration: 500ms, Easing: linear) - updates every 2s during processing
- **PDF Highlight:** Red bounding box fades in (100ms) → holds 3s → fades out (500ms)
- **Accordion Expand/Collapse:** Height animation (Duration: 200ms, Easing: ease-in-out)
- **Drag-over Drop Zone:** Border color change + subtle scale up 1.02x (Duration: 150ms, Easing: ease-out)

**Reduced Motion:**
```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---
