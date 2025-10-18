# Performance Considerations

## Performance Goals

- **Page Load:** < 2 seconds for initial page load (NFR5)
- **Interaction Response:** < 100ms for button clicks, < 300ms for form submission feedback
- **Animation FPS:** Maintain 60 FPS for all animations (avoid jank)
- **PDF Rendering:** < 3 seconds for 10-page PDF (NFR2)

## Design Strategies

**Lazy Loading:**
- PDF pages: Render viewport + 1 page buffer (don't render all pages at once)
- Images: Use Next.js `<Image>` component with `loading="lazy"`
- Heavy components: Use React `lazy()` and `Suspense` for code splitting

**Optimize Initial Load:**
- Critical CSS inline in `<head>` (Tailwind JIT generates minimal CSS)
- Font preloading: `<link rel="preload" href="/fonts/inter.woff2" as="font">`
- Minimize JavaScript bundle: Tree-shake unused dependencies, code split by route

**Reduce Re-renders:**
- Memoize expensive components with `React.memo()`
- Use Zustand selectors to subscribe to only needed state slices
- Debounce search inputs (300ms) to avoid excessive filtering

**PDF Viewer Performance:**
- Use canvas rendering (not SVG) for better performance
- Limit concurrent page renders (max 3 at once)
- Provide low-res preview while high-res loads
- Cache rendered pages in memory (limit: 10 pages)

**Form Performance:**
- Auto-save debounce: 5 seconds (don't save on every keystroke)
- Validate on blur, not on change (reduce computation)
- Use `React Hook Form` with uncontrolled inputs (fewer re-renders)

**Table Performance:**
- Virtualize long tables (>100 rows) with `@tanstack/react-virtual`
- Paginate server-side (max 20 rows per page)
- Avoid inline styles (use CSS classes for consistency)

---
