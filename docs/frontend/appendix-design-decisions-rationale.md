# Appendix: Design Decisions & Rationale

## Why Side-by-Side Layout?

**Decision:** 40/60 split with PDF on left, form on right

**Rationale:**
- User research (from PRD) shows constant context switching between PDF and Excel is major pain point
- Verification is faster when source and extracted data are simultaneously visible
- Western reading pattern (left to right) means reading PDF first, then checking form feels natural
- 40/60 ratio gives PDF enough space (400-600px wide) while prioritizing form real estate

**Alternative Considered:** Tabs (PDF tab, Form tab)
- **Pros:** Simpler implementation, works on tablet
- **Cons:** Requires switching, breaks flow, increases cognitive load
- **Decision:** Use tabs only for tablet breakpoint

## Why Color-Coded Confidence?

**Decision:** Green >90%, Yellow 70-90%, Red <70%

**Rationale:**
- Traffic light metaphor is universally understood (even for colorblind users when paired with icons)
- Draws user attention to fields most likely to need review (red first, then yellow)
- Reduces review time by 50%+ (users don't need to check every field)
- Confidence scores directly from AI (no UX interpretation needed)

**Alternative Considered:** Numerical confidence scores (e.g., "92%")
- **Pros:** More precise
- **Cons:** Harder to scan quickly, users must interpret threshold
- **Decision:** Show numerical score on hover for power users, color for quick scanning

## Why Auto-Save Every 5 Seconds?

**Decision:** Debounced auto-save at 5-second intervals

**Rationale:**
- Prevents data loss if user navigates away or browser crashes
- 5 seconds balances saving frequently (lower risk) vs server load (fewer requests)
- Visual indicator ("Saving..." → "Saved") provides reassurance
- Aligns with NFR7 requirement

**Alternative Considered:** Save on every field blur
- **Pros:** More immediate
- **Cons:** Excessive API calls, user might not be done with field
- **Decision:** Use blur for validation, auto-save for persistence

## Why shadcn/ui Over Custom Components?

**Decision:** Use shadcn/ui component library

**Rationale:**
- 8-week timeline is aggressive - building custom components from scratch would take 2+ weeks
- shadcn/ui provides accessible, well-tested components (Radix UI primitives)
- Components are copyable source code (not npm dependency) - full customization control
- Tailwind CSS integration is seamless
- Active community and documentation

**Alternative Considered:** Build custom component library
- **Pros:** Perfect brand fit, no dependencies
- **Cons:** 2-3 weeks extra dev time, accessibility testing required, maintenance burden
- **Decision:** Use shadcn/ui for MVP, consider custom components post-MVP if needed

## Why react-pdf for PDF Viewer?

**Decision:** Use react-pdf 9.1 library

**Rationale:**
- Most popular React PDF library (2.7M weekly downloads)
- Canvas rendering mode has best performance (meets NFR2: <3s for 10 pages)
- Actively maintained (latest version Sept 2025)
- Supports bounding box highlighting (critical for jump-to-source feature)

**Alternative Considered:** PDF.js directly (without React wrapper)
- **Pros:** More control, slightly smaller bundle
- **Cons:** More complex integration, no React hooks
- **Decision:** react-pdf for developer velocity

---

**END OF UI/UX SPECIFICATION**

*This specification was created by Sally (UX Expert) using the BMAD-METHOD™ framework, based on the comprehensive PRD for the Customs Declaration Automation Platform.*

---
