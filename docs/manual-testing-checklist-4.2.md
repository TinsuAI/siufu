# Manual Testing Checklist - Story 4.2
## Declaration Form Complete Translation

**Tester:** _____________________
**Date:** _____________________
**Environment:** Development / Staging
**URL:** http://tinxudev.airplane-manta.ts.net

---

## Pre-Test Setup

- [ ] Backend is running (`docker compose up -d`)
- [ ] Frontend is running (`npm run dev`)
- [ ] Database has test declaration data
- [ ] Browser dev tools open (check for console errors)
- [ ] Test user account logged in

---

## Test 1: Locale Switching

### English to Vietnamese
- [ ] Navigate to declaration form
- [ ] Verify form loads in English (default)
- [ ] Switch locale to Vietnamese using locale switcher
- [ ] **Expected:** All text changes to Vietnamese instantly
- [ ] **Expected:** No console errors
- [ ] **Expected:** Form data retained after locale switch

### Vietnamese to English
- [ ] Start with form in Vietnamese
- [ ] Switch locale to English
- [ ] **Expected:** All text changes to English instantly
- [ ] **Expected:** No console errors
- [ ] **Expected:** Form data retained after locale switch

**Status:** ☐ Pass ☐ Fail
**Notes:** ______________________________________

---

## Test 2: Section Titles Translation

### English Locale
- [ ] Verify "Declaration Header"
- [ ] Verify "Importer Information"
- [ ] Verify "Exporter Information"
- [ ] Verify "Shipping & Transport"
- [ ] Verify "Package & Container"
- [ ] Verify "Invoice Details"
- [ ] Verify "Certificate of Origin"
- [ ] Verify "Product Line Items"
- [ ] Verify "Import Duty"
- [ ] Verify "VAT & Other Taxes"
- [ ] Verify "Tax Summary"

### Vietnamese Locale
- [ ] Verify "Tiêu Đề Tờ Khai"
- [ ] Verify "Thông Tin Người Nhập Khẩu"
- [ ] Verify "Thông Tin Người Xuất Khẩu"
- [ ] Verify "Vận Chuyển & Giao Nhận"
- [ ] Verify "Kiện Hàng & Container"
- [ ] Verify "Chi Tiết Hóa Đơn"
- [ ] Verify "Chứng Nhận Xuất Xứ"
- [ ] Verify "Danh Mục Hàng Hóa"
- [ ] Verify "Thuế Nhập Khẩu"
- [ ] Verify "Thuế GTGT & Các Loại Thuế Khác"
- [ ] Verify "Tổng Hợp Thuế"

**Status:** ☐ Pass ☐ Fail
**Notes:** ______________________________________

---

## Test 3: Field Labels - Declaration Header

### English
- [ ] "Declaration Number (Read-only)"
- [ ] "Declaration Type Code"
- [ ] "Customs Office Code"
- [ ] "Processing Division Code"
- [ ] "Registration Date"
- [ ] "Representative HS Code"

### Vietnamese
- [ ] "Số Tờ Khai (Chỉ Đọc)"
- [ ] "Loại Tờ Khai"
- [ ] "Cục Hải Quan"
- [ ] "Bộ Phận Xử Lý"
- [ ] "Ngày Đăng Ký"
- [ ] "Mã HS Đại Diện"

**Status:** ☐ Pass ☐ Fail
**Notes:** ______________________________________

---

## Test 4: Field Placeholders

### English Placeholders
- [ ] Declaration Type Code: "e.g., A11 2 [4]"
- [ ] Customs Office Code: "e.g., HQHOALAC"
- [ ] Processing Division Code: "e.g., 00"
- [ ] Registration Date: "DD/MM/YYYY"
- [ ] Representative HS Code: "First 4 digits"

### Vietnamese Placeholders
- [ ] Declaration Type Code: "Ví dụ: A11 2 [4]"
- [ ] Customs Office Code: "Ví dụ: HQHOALAC"
- [ ] Processing Division Code: "Ví dụ: 00"
- [ ] Registration Date: "DD/MM/YYYY"
- [ ] Representative HS Code: "4 chữ số đầu"

**Status:** ☐ Pass ☐ Fail
**Notes:** ______________________________________

---

## Test 5: Product Management Buttons

### Add Product Button
- [ ] English: Shows "Add Product"
- [ ] Vietnamese: Shows "Thêm Hàng Hóa"
- [ ] Click button adds new product
- [ ] New product appears with correct header ("Product 2" / "Hàng Hóa 2")

### Remove Button
- [ ] English: Shows "Remove"
- [ ] Vietnamese: Shows "Xóa"
- [ ] Button only appears when 2+ products exist
- [ ] Click removes correct product

**Status:** ☐ Pass ☐ Fail
**Notes:** ______________________________________

---

## Test 6: Dynamic Product Numbers

### Test Sequence
- [ ] Start with 1 product
- [ ] Product header shows "Product 1" (EN) / "Hàng Hóa 1" (VI)
- [ ] Add product, second shows "Product 2" (EN) / "Hàng Hóa 2" (VI)
- [ ] Add third product, shows "Product 3" (EN) / "Hàng Hóa 3" (VI)
- [ ] Remove product 2
- [ ] Remaining products renumber correctly
- [ ] Switch locale - numbers update to translated format

**Status:** ☐ Pass ☐ Fail
**Notes:** ______________________________________

---

## Test 7: Auto-Save Functionality

### English Locale
- [ ] Fill in Declaration Header fields
- [ ] Wait 5 seconds (auto-save interval)
- [ ] **Expected:** Data saves automatically
- [ ] Refresh page
- [ ] **Expected:** Data persists in English

### Vietnamese Locale
- [ ] Switch to Vietnamese
- [ ] Edit form fields (labels should be in Vietnamese)
- [ ] Wait 5 seconds
- [ ] **Expected:** Data saves automatically
- [ ] Refresh page
- [ ] **Expected:** Data persists, UI shows Vietnamese

**Status:** ☐ Pass ☐ Fail
**Notes:** ______________________________________

---

## Test 8: Form Validation Messages

### Trigger Validation Errors
- [ ] Clear a required field
- [ ] Enter invalid HS code (not 8 digits)
- [ ] Enter invalid date format
- [ ] Enter invalid phone number
- [ ] Try to submit form

### English Validation
- [ ] "This field is required"
- [ ] "HS Code must be 8 digits"
- [ ] "Invalid date format (DD/MM/YYYY)"
- [ ] "Invalid phone number format"

### Vietnamese Validation
- [ ] Switch to Vietnamese
- [ ] Trigger same errors
- [ ] "Trường này là bắt buộc"
- [ ] "Mã HS phải có 8 chữ số"
- [ ] "Định dạng ngày không hợp lệ (DD/MM/YYYY)"
- [ ] "Định dạng số điện thoại không hợp lệ"

**Status:** ☐ Pass ☐ Fail
**Notes:** ______________________________________

---

## Test 9: Field Flagging Functionality

### Test in Both Locales
- [ ] Flag a field for correction (English)
- [ ] **Expected:** Flag icon appears
- [ ] Switch to Vietnamese
- [ ] **Expected:** Flag persists, labels in Vietnamese
- [ ] Switch back to English
- [ ] **Expected:** Flag still present

**Status:** ☐ Pass ☐ Fail
**Notes:** ______________________________________

---

## Test 10: Confidence Indicators

### Test in Both Locales
- [ ] Fields with confidence scores show color coding
- [ ] High confidence (>0.8): Green border
- [ ] Medium confidence (0.5-0.8): Yellow border
- [ ] Low confidence (<0.5): Red border
- [ ] Switch locale
- [ ] **Expected:** Confidence indicators remain unchanged
- [ ] **Expected:** Labels update to new locale

**Status:** ☐ Pass ☐ Fail
**Notes:** ______________________________________

---

## Test 11: Section Completion Badges

### English
- [ ] Badges show "X/Y" format (e.g., "4/6")
- [ ] Badge count updates when fields filled
- [ ] Badge appears on all sections with fields

### Vietnamese
- [ ] Switch to Vietnamese
- [ ] Badge format remains "X/Y" (numbers don't translate)
- [ ] Badge count accurate

**Status:** ☐ Pass ☐ Fail
**Notes:** ______________________________________

---

## Test 12: Company Badges (Importer/Exporter)

### Test Display
- [ ] Importer section shows company badge
- [ ] Exporter section shows company badge
- [ ] Badge shows verification status icon
- [ ] Badge shows declaration count
- [ ] Switch locale
- [ ] **Expected:** Badges remain visible
- [ ] **Expected:** Section titles update

**Status:** ☐ Pass ☐ Fail
**Notes:** ______________________________________

---

## Test 13: All 12 Sections in Vietnamese

### Expand Each Section
- [ ] Tiêu Đề Tờ Khai (Declaration Header)
- [ ] Thông Tin Người Nhập Khẩu (Importer)
- [ ] Thông Tin Người Xuất Khẩu (Exporter)
- [ ] Vận Chuyển & Giao Nhận (Shipping)
- [ ] Kiện Hàng & Container (Package)
- [ ] Chi Tiết Hóa Đơn (Invoice)
- [ ] Chứng Nhận Xuất Xứ (C/O)
- [ ] Danh Mục Hàng Hóa (Products)
- [ ] Thuế Nhập Khẩu (Import Duty)
- [ ] Thuế GTGT & Các Loại Thuế Khác (VAT)
- [ ] Tổng Hợp Thuế (Tax Summary)

### Verify All Field Labels Translated
- [ ] Each section: All field labels in Vietnamese
- [ ] Each section: All placeholders in Vietnamese
- [ ] No English text visible in form fields

**Status:** ☐ Pass ☐ Fail
**Notes:** ______________________________________

---

## Test 14: Performance

### Load Time
- [ ] English form loads in < 2 seconds
- [ ] Vietnamese form loads in < 2 seconds
- [ ] Locale switch completes in < 500ms

### Translation Bundle Size
- [ ] Check Network tab: declarations.json < 15KB per locale
- [ ] Check Network tab: customs-terms.json < 5KB per locale
- [ ] Total translation bundle < 40KB

**Status:** ☐ Pass ☐ Fail
**Notes:** ______________________________________

---

## Test 15: Browser Compatibility

### Test in Each Browser
- [ ] Chrome: All features work
- [ ] Firefox: All features work
- [ ] Safari: All features work
- [ ] Edge: All features work

**Status:** ☐ Pass ☐ Fail
**Notes:** ______________________________________

---

## Test 16: Console Errors

### Check Dev Console
- [ ] No errors on page load (English)
- [ ] No errors on page load (Vietnamese)
- [ ] No errors on locale switch
- [ ] No errors on form submission
- [ ] No errors on product add/remove
- [ ] No warnings about missing translations

**Status:** ☐ Pass ☐ Fail
**Notes:** ______________________________________

---

## Test 17: Mobile Responsiveness

### Test on Mobile Device or Emulator
- [ ] Form displays correctly in English
- [ ] Form displays correctly in Vietnamese
- [ ] Vietnamese text doesn't overflow containers
- [ ] Buttons are tappable
- [ ] Locale switcher accessible

**Status:** ☐ Pass ☐ Fail
**Notes:** ______________________________________

---

## Test 18: Edge Cases

### Long Vietnamese Text
- [ ] Very long Vietnamese product description displays correctly
- [ ] Text wraps properly, no overflow
- [ ] Form remains usable

### Special Characters
- [ ] Vietnamese diacritics display correctly (ắ, ằ, ẳ, ẵ, ặ, etc.)
- [ ] No character encoding issues

### Empty Form
- [ ] Empty form shows placeholders in correct locale
- [ ] Placeholders guide user appropriately

**Status:** ☐ Pass ☐ Fail
**Notes:** ______________________________________

---

## Critical Bugs (If Any)

**Bug #1:**
Description: __________________________________
Severity: ☐ Critical ☐ High ☐ Medium ☐ Low
Steps to Reproduce: __________________________________

**Bug #2:**
Description: __________________________________
Severity: ☐ Critical ☐ High ☐ Medium ☐ Low
Steps to Reproduce: __________________________________

---

## Overall Test Result

- [ ] **PASS** - All critical tests passed, ready for Vietnamese expert review
- [ ] **CONDITIONAL PASS** - Minor issues found, documented above
- [ ] **FAIL** - Critical issues found, requires fixes before expert review

---

## Tester Sign-off

**Name:** _____________________
**Signature:** _____________________
**Date:** _____________________

---

## Next Steps

After passing manual QA:
1. Send `docs/vietnamese-customs-glossary.md` to Vietnamese customs expert
2. Schedule expert review of Vietnamese translations
3. Address any terminology feedback from expert
4. Re-test with corrected translations
5. Deploy to staging for final UAT

---

**Story:** 4.2 - Declaration Form Complete Translation
**Test Environment:** Development
**Created:** 2025-11-10
