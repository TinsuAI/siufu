# Vietnamese Localization - Brownfield Enhancement

**Epic Type:** Brownfield Enhancement
**Created:** 2025-11-10
**Status:** Ready for Story Development
**Estimated Effort:** 17-25 story points (2-3 sprints)

---

## Epic Goal

Enable full Vietnamese language support for the customs declaration platform to serve Vietnamese-speaking clients with accurate, formal customs terminology while maintaining English as a fallback language.

---

## Epic Description

### Existing System Context

**Current relevant functionality:**
- Complete customs declaration management system with authentication, file upload, declaration forms (77 fields), company management, and processing workflow
- All user-facing text is currently hardcoded in English across 96 TypeScript/TSX files
- No existing internationalization (i18n) infrastructure in place

**Technology stack:**
- Frontend: Next.js 15.5.6, React 19.2, TypeScript, Tailwind CSS, Shadcn/UI components
- Backend: Express/Node.js (API interactions)
- Current state: Zero i18n support, all text hardcoded in components

**Integration points:**
- All 96 TSX files contain hardcoded English text
- Critical file: `frontend/src/components/declarations/declaration-form-v2.tsx` (2,743 lines, 77 fields, 12 sections)
- Navigation, authentication, forms, validation messages, status labels
- Date/number/currency formatting throughout

### Enhancement Details

**What's being added/changed:**
- Implementation of `next-intl` internationalization framework for Next.js App Router
- Extraction of 500-600+ English strings into structured locale files
- Vietnamese translations using formal customs/governmental terminology
- Language switcher component in header navigation
- Locale-aware date/number/currency formatting following Vietnamese conventions
- Locale preference persistence (cookies/localStorage)

**How it integrates:**
- Wraps Next.js App Router with `IntlProvider` via middleware
- Components updated to use `useTranslations()` hook instead of hardcoded strings
- Zero functional changes - purely presentational text replacement
- Vietnamese (vi) as primary locale, English (en) as fallback
- Translation files organized by namespace (common, auth, declarations, etc.)

**Success criteria:**
- 100% of user-facing text available in Vietnamese
- Customs terminology accurately translated and verified by Vietnamese domain expert
- Language preference persists across browser sessions
- Zero functional regressions verified by existing test suite
- Date/number formats follow Vietnamese conventions (dd/MM/yyyy, 1.234.567,89)
- Performance impact <50KB additional payload per page

---

## Stories Breakdown

### Story 1: i18n Infrastructure & Core Navigation
**Effort:** 5-8 story points
**Priority:** Critical (Blocker for Stories 2 & 3)

**Summary:**
Set up next-intl framework, configure Next.js middleware for locale detection/routing, implement language switcher in header, and translate authentication flows (login/logout) and main navigation. This foundational story enables all subsequent translation work.

**Key deliverables:**
- next-intl installed and configured
- Middleware for locale routing (`/en`, `/vi`)
- Language switcher component in header
- Translation files structure: `messages/en/*.json`, `messages/vi/*.json`
- Authentication flows translated (login, logout, register if applicable)
- Navigation menu translated (10 items)
- Locale persistence mechanism

**Files to modify:**
- `frontend/src/middleware.ts` (create)
- `frontend/src/app/layout.tsx`
- `frontend/src/components/layout/header.tsx`
- `frontend/src/app/login/page.tsx`
- Create: `messages/en/common.json`, `messages/vi/common.json`
- Create: `messages/en/auth.json`, `messages/vi/auth.json`

---

### Story 2: Declaration Form Complete Translation
**Effort:** 8-10 story points
**Priority:** High (Critical business component)

**Summary:**
Translate the critical 77-field declaration form (`declaration-form-v2.tsx` - 2,743 lines) across all 12 sections using formal Vietnamese customs terminology. This is the most complex component requiring domain expert review for accurate terminology.

**Key deliverables:**
- All 12 form sections translated:
  1. Declaration Header (Tiêu Đề Tờ Khai)
  2. Importer Information (Thông Tin Người Nhập Khẩu)
  3. Exporter Information (Thông Tin Người Xuất Khẩu)
  4. Shipping Information (Thông Tin Vận Chuyển)
  5. Package Information (Thông Tin Kiện Hàng)
  6. Invoice Information (Thông Tin Hóa Đơn)
  7. Certificate of Origin (Chứng Nhận Xuất Xứ/C/O)
  8. Products (Danh Mục Hàng Hóa)
  9. Duties & Taxes (Thuế & Phí)
  10. VAT Information (Thuế GTGT)
  11. Tax Summary (Tổng Hợp Thuế Phí)
  12. Special Cases (Trường Hợp Đặc Biệt)
- 77 field labels + placeholders + help text translated
- Validation messages for form fields
- Vietnamese customs domain expert review completed

**Files to modify:**
- `frontend/src/components/declarations/declaration-form-v2.tsx`
- Create: `messages/en/declarations.json`, `messages/vi/declarations.json`
- Create: `messages/en/customs-terms.json`, `messages/vi/customs-terms.json`

**Critical customs terminology requiring expert review:**
- Bill of Lading → Vận Đơn
- HS Code → Mã HS
- Tax Code → Mã Số Thuế
- Certificate of Origin → Chứng Nhận Xuất Xứ (C/O)
- Import Duty → Thuế Nhập Khẩu
- VAT → Thuế GTGT (Thuế Giá Trị Gia Tăng)
- Special Consumption Tax → Thuế Tiêu Thụ Đặc Biệt
- Environmental Protection Tax → Thuế Bảo Vệ Môi Trường

---

### Story 3: Remaining Pages & Validation Messages
**Effort:** 4-7 story points
**Priority:** Medium (Completion work)

**Summary:**
Translate all remaining pages (upload, declarations list, companies management), dialogs, confirmation messages, processing stages, status labels, and validation/error messages. Complete locale-aware formatting for dates, numbers, and currency throughout the application.

**Key deliverables:**
- Upload page translated (`/upload`)
- Declarations list page translated (`/declarations`)
- Companies management page translated (`/companies`)
- Processing stages translated (6 stages: uploaded, processing, extracting, validating, completed, failed)
- Status labels translated (7 statuses)
- All dialog/modal messages translated
- Confirmation prompts translated
- All validation/error messages translated
- Date formatting: `dd/MM/yyyy` (Vietnamese convention)
- Number formatting: `1.234.567,89` (period for thousands, comma for decimal)
- Currency formatting: `1.234.567 ₫` or `1.234.567 VND`

**Files to modify:**
- `frontend/src/app/upload/page.tsx`
- `frontend/src/app/declarations/page.tsx`
- `frontend/src/app/companies/page.tsx`
- `frontend/src/components/declarations/validation-warnings.tsx`
- `frontend/src/types/declaration.ts` (status/stage enums with display labels)
- Create: `messages/en/upload.json`, `messages/vi/upload.json`
- Create: `messages/en/companies.json`, `messages/vi/companies.json`
- Create: `messages/en/validation.json`, `messages/vi/validation.json`

---

## Compatibility Requirements

- ✅ **Existing APIs remain unchanged** - Backend API contracts unaffected; no API modifications required
- ✅ **Database schema changes are backward compatible** - Only locale preference storage needed (optional; can use cookies)
- ✅ **UI changes follow existing patterns** - Only text replaced; all component structure, styling, and layouts preserved exactly
- ✅ **Performance impact is minimal** - Translation bundles lazy-loaded per page, estimated <50KB additional payload per page

---

## Risk Mitigation

### Primary Risk
**Incorrect customs terminology causing regulatory compliance issues or user confusion**

Translation errors in formal governmental documents could lead to:
- Customs clearance delays or rejections
- Legal/compliance issues for clients
- Loss of credibility and client trust
- Misunderstanding of critical requirements

### Mitigation Strategy
1. **Domain Expert Review:** Vietnamese customs domain expert (ideally licensed customs broker or customs officer) reviews ALL translations before deployment
2. **English Fallback:** Maintain English as fallback locale for any missing translations, preventing broken UI
3. **Pilot Release:** Deploy to subset of internal users or trusted clients for real-world feedback before full rollout
4. **Translation Documentation:** Maintain comprehensive mapping document (English→Vietnamese) with context/notes for future reference
5. **Glossary Creation:** Build standardized customs terminology glossary for consistency across all translations
6. **Iterative Review:** Allow 1-2 weeks for translation refinement based on pilot feedback before general availability

### Rollback Plan
If critical issues are discovered post-deployment:

1. **Immediate:** Feature flag to disable Vietnamese locale and revert to English-only (can be toggled without deployment)
2. **Short-term:** Next.js middleware configuration can redirect all users to English locale while fixes are implemented
3. **No Database Impact:** No database migrations required, so no schema rollback complexity
4. **Simple Code Revert:** Standard Git revert to previous commit if feature flag insufficient
5. **User Communication:** Email notification template prepared for affected users explaining temporary English-only mode

**Rollback Time Estimate:** <15 minutes via feature flag, <1 hour for full code revert

---

## Definition of Done

### Story Completion
- ✅ All 3 stories completed with acceptance criteria met
- ✅ Code reviews completed and approved by senior developer
- ✅ All new code follows existing TypeScript/React patterns

### Functional Verification
- ✅ Existing functionality verified through regression testing (all current tests pass)
- ✅ Integration points working correctly (next-intl properly integrated across all pages)
- ✅ Language switcher tested in all user flows (auth, upload, declarations, companies)
- ✅ Locale persistence working across browser sessions and devices

### Translation Quality
- ✅ Vietnamese customs domain expert approval on all terminology
- ✅ Translation completeness verified: 100% of user-facing text available in Vietnamese
- ✅ Glossary document created and reviewed
- ✅ Translation key naming conventions documented

### Documentation & Testing
- ✅ Documentation updated:
  - README.md with i18n usage instructions
  - Translation contribution guide for future additions
  - Customs terminology glossary
- ✅ No regression in existing features (zero functional changes verified by test suite)
- ✅ Visual regression testing completed for both locales
- ✅ Browser compatibility tested (Chrome, Firefox, Safari, Edge)

### Performance & Deployment
- ✅ Performance budget met: <50KB additional payload per page verified
- ✅ Lighthouse scores maintained (no degradation in performance/accessibility scores)
- ✅ Feature flag configured for Vietnamese locale (enable/disable without deployment)
- ✅ Pilot release completed successfully with positive feedback

---

## Dependencies

### Technical Dependencies
- **next-intl library** (v3.0+) - Next.js App Router compatible i18n solution
- **Existing test infrastructure** - Must pass all current tests

### Team Dependencies
- **Story 1 blocks Stories 2 & 3** - i18n infrastructure must be in place before translation work begins
- **Stories 2 & 3 can proceed in parallel** - Once Story 1 complete, both can be worked simultaneously by different developers

### External Dependencies
- **Vietnamese Customs Domain Expert** - Required for Story 2 terminology review (estimated 4-8 hours of expert time)
- **Pilot Users** - 3-5 Vietnamese-speaking clients for pilot testing (1-2 week pilot period)

---

## Story Manager Handoff

**Please develop detailed user stories for this brownfield epic. Key considerations:**

### System Context
- This is an enhancement to an existing system running: **Next.js 15.5.6 + React 19.2 + TypeScript + Tailwind CSS + Shadcn/UI components** with **NO existing i18n infrastructure**

### Integration Points
- 96 TSX files with hardcoded English strings requiring text extraction
- Critical file: `declaration-form-v2.tsx` (2,743 lines, 77 fields, 12 sections) - highest complexity
- Header navigation (10 items)
- Authentication flows (login/logout)
- Upload, declarations list, companies pages
- Validation/error messages distributed throughout codebase
- Date/number/currency formatting in tables, forms, and displays

### Existing Patterns to Follow
- **Next.js App Router middleware pattern** for locale detection/routing
- **React Hook Form** for all form implementations
- **Shadcn/UI component structure** and styling conventions
- **TypeScript strict typing** with proper interfaces/types
- **Server/Client component separation** following Next.js best practices

### Critical Compatibility Requirements
- **Zero functional changes** - purely presentational text replacement; all business logic untouched
- **All existing tests must continue passing unchanged** - no test modifications required
- **English fallback required** for missing translations to prevent broken UI
- **Formal Vietnamese customs terminology** (requires domain expert review for accuracy and compliance)
- **Locale preference persistence** via cookies/localStorage across sessions
- **Performance budget:** <50KB additional payload per page (lazy-loaded translation bundles)

### Verification Requirements for Each Story
Each story must include explicit verification that existing functionality remains intact:
- ✅ **Regression test suite passes 100%** - no test failures introduced
- ✅ **No changes to API contracts** - backend interactions remain identical
- ✅ **No changes to backend** - purely frontend work
- ✅ **UI component structure and styling preserved exactly** - only text content changes
- ✅ **All user flows continue working identically** - click-through testing confirms no breakage

### Epic Goal
The epic should maintain system integrity while delivering **full Vietnamese language support for Vietnamese-speaking customs clients using accurate, formal governmental terminology** suitable for official customs declaration processes.

---

## Technical Notes

### Recommended Technology Stack
- **next-intl** (v3.0+) - Best-in-class Next.js App Router i18n library with excellent TypeScript support

### Translation File Structure
```
messages/
├── en/
│   ├── common.json          # Shared UI elements, navigation
│   ├── auth.json            # Login, logout, authentication
│   ├── declarations.json    # Declaration form fields
│   ├── customs-terms.json   # Formal customs terminology
│   ├── upload.json          # Upload page
│   ├── companies.json       # Companies management
│   └── validation.json      # Validation/error messages
└── vi/
    ├── common.json
    ├── auth.json
    ├── declarations.json
    ├── customs-terms.json
    ├── upload.json
    ├── companies.json
    └── validation.json
```

### Key Implementation Patterns

**Component translation pattern:**
```typescript
// Before
<label>Tax Code</label>

// After
import { useTranslations } from 'next-intl';

const t = useTranslations('customs-terms');
<label>{t('taxCode')}</label>
```

**Date formatting pattern:**
```typescript
import { useFormatter } from 'next-intl';

const format = useFormatter();
const formattedDate = format.dateTime(date, {
  year: 'numeric',
  month: '2-digit',
  day: '2-digit'
}); // Output: 10/11/2025 (Vietnamese convention)
```

**Number formatting pattern:**
```typescript
const formattedNumber = format.number(1234567.89, {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2
}); // Output: 1.234.567,89 (Vietnamese convention)
```

---

## Success Metrics

### Completion Metrics
- ✅ 100% of user-facing text available in Vietnamese (quantified via translation coverage report)
- ✅ 0 functional regressions (verified by test suite)
- ✅ <50KB payload increase per page (verified by bundle analysis)

### Quality Metrics
- ✅ Vietnamese customs domain expert approval obtained
- ✅ Pilot users provide positive feedback (satisfaction score ≥4/5)
- ✅ Zero translation-related support tickets during pilot period

### Performance Metrics
- ✅ Lighthouse performance score maintained (no degradation >5 points)
- ✅ Time to Interactive (TTI) increase <200ms
- ✅ First Contentful Paint (FCP) maintained

---

## Future Enhancements (Out of Scope)

Items explicitly NOT included in this epic but may be considered in future:

- ❌ Backend API response message translation (currently English only)
- ❌ Additional languages beyond Vietnamese/English
- ❌ RTL (right-to-left) language support
- ❌ User-customizable locale preferences dashboard
- ❌ Real-time translation updates without deployment
- ❌ Machine translation integration for user-generated content
- ❌ Voice/audio translation features

---

**Epic Status:** ✅ Ready for Story Development

**Next Steps:**
1. Review epic with development team and Vietnamese customs domain expert
2. Develop detailed user stories with full acceptance criteria
3. Obtain domain expert commitment for terminology review
4. Schedule pilot users for testing phase
5. Begin Story 1 development (i18n infrastructure)

---

*Generated by BMAD™ Product Management Agent - 2025-11-10*
