# Declaration Form Translation Integration Guide

**Component:** `frontend/src/components/declarations/declaration-form-v2.tsx`
**Story:** 4.2 - Declaration Form Complete Translation
**Status:** Partially Integrated - Pattern Established

---

## Integration Status

### ✅ Completed
- [x] Import `useTranslations` from next-intl added (line 19)
- [x] Translation hook `tDecl` added to component (line 216)
- [x] All 12 section titles translated
- [x] Product buttons translated (Add Product, Remove)
- [x] Section 1 (Declaration Header) - All 6 fields complete

### ⚠️ Remaining Work
- [ ] Section 2 (Importer) - 5 fields
- [ ] Section 3 (Exporter) - 5 fields
- [ ] Section 4 (Shipping & Transport) - 10 fields
- [ ] Section 5 (Package & Container) - 6 fields
- [ ] Section 6 (Invoice) - 8 fields
- [ ] Section 7 (Certificate of Origin) - 3 fields
- [ ] Section 8 (Products) - 18 fields per item
- [ ] Section 9 (Import Duty) - 4 fields
- [ ] Section 10 (VAT) - 6 fields
- [ ] Section 11 (Tax Summary) - 4 fields

**Total Remaining:** 71 fields (mechanical replacement following established pattern)

---

## Established Integration Pattern

### Pattern for Labels
```typescript
// Before:
<Label>Tax Code</Label>

// After:
<Label>{tDecl('importer.taxCode.label')}</Label>
```

### Pattern for Placeholders
```typescript
// Before:
placeholder="10-digit tax ID"

// After:
placeholder={tDecl('importer.taxCode.placeholder')}
```

### Pattern for Section Titles (Already Complete)
```typescript
// Before:
<CardTitle>Importer Information</CardTitle>

// After:
<CardTitle>{tDecl('importer.title')}</CardTitle>
```

---

## Field-by-Field Integration Checklist

### Section 2: Importer Information (Lines ~577-687)

- [ ] Line ~580: `<Label>Tax Code</Label>` → `<Label>{tDecl('importer.taxCode.label')}</Label>`
- [ ] Line ~591: `placeholder="10-digit tax ID"` → `placeholder={tDecl('importer.taxCode.placeholder')}`
- [ ] Line ~600: `<Label>Name</Label>` → `<Label>{tDecl('importer.name.label')}</Label>`
- [ ] Line ~611: `placeholder="Full legal name"` → `placeholder={tDecl('importer.name.placeholder')}`
- [ ] Line ~623: `<Label>Postal Code</Label>` → `<Label>{tDecl('importer.postalCode.label')}</Label>`
- [ ] Line ~634: `placeholder="Postal code"` → `placeholder={tDecl('importer.postalCode.placeholder')}`
- [ ] Line ~643: `<Label>Phone</Label>` → `<Label>{tDecl('importer.phone.label')}</Label>`
- [ ] Line ~654: `placeholder="Phone number"` → `placeholder={tDecl('importer.phone.placeholder')}`
- [ ] Line ~665: `<Label>Address</Label>` → `<Label>{tDecl('importer.address.label')}</Label>`
- [ ] Line ~676: `placeholder="Full address in Vietnam"` → `placeholder={tDecl('importer.address.placeholder')}`

### Section 3: Exporter Information (Lines ~720-831)

- [ ] Line ~723: `<Label>Name</Label>` → `<Label>{tDecl('exporter.name.label')}</Label>`
- [ ] Line ~734: `placeholder="Full legal name of exporter"` → `placeholder={tDecl('exporter.name.placeholder')}`
- [ ] Line ~744: `<Label>Address Line 1</Label>` → `<Label>{tDecl('exporter.addressLine1.label')}</Label>`
- [ ] Line ~755: `placeholder="Primary address line"` → `placeholder={tDecl('exporter.addressLine1.placeholder')}`
- [ ] Line ~765: `<Label>Address Line 2</Label>` → `<Label>{tDecl('exporter.addressLine2.label')}</Label>`
- [ ] Line ~776: `placeholder="Additional address line"` → `placeholder={tDecl('exporter.addressLine2.placeholder')}`
- [ ] Line ~787: `<Label>Address Line 3</Label>` → `<Label>{tDecl('exporter.addressLine3.label')}</Label>`
- [ ] Line ~798: `placeholder="City, province, country"` → `placeholder={tDecl('exporter.addressLine3.placeholder')}`
- [ ] Line ~807: `<Label>Country Code</Label>` → `<Label>{tDecl('exporter.countryCode.label')}</Label>`
- [ ] Line ~818: `placeholder="e.g., CN, US"` → `placeholder={tDecl('exporter.countryCode.placeholder')}`

### Section 4: Shipping & Transport (Lines ~858-1127)

- [ ] Line ~859: `<Label>Bill of Lading Number</Label>` → `<Label>{tDecl('shipping.billOfLadingNumber.label')}</Label>`
- [ ] Line ~877: `placeholder="B/L or AWB number"` → `placeholder={tDecl('shipping.billOfLadingNumber.placeholder')}`
- [ ] Line ~886: `<Label>Warehouse Code</Label>` → `<Label>{tDecl('shipping.warehouseCode.label')}</Label>`
- [ ] Line ~901: `placeholder="Warehouse/CFS code"` → `placeholder={tDecl('shipping.warehouseCode.placeholder')}`
- [ ] Line ~912: `<Label>Warehouse Name</Label>` → `<Label>{tDecl('shipping.warehouseName.label')}</Label>`
- [ ] Line ~927: `placeholder="Warehouse name"` → `placeholder={tDecl('shipping.warehouseName.placeholder')}`
- [ ] Line ~938: `<Label>Port of Discharge Code</Label>` → `<Label>{tDecl('shipping.portOfDischargeCode.label')}</Label>`
- [ ] Line ~956: `placeholder="UN/LOCODE"` → `placeholder={tDecl('shipping.portOfDischargeCode.placeholder')}`
- [ ] Line ~965: `<Label>Port of Discharge Name</Label>` → `<Label>{tDecl('shipping.portOfDischargeName.label')}</Label>`
- [ ] Line ~983: `placeholder="Port name"` → `placeholder={tDecl('shipping.portOfDischargeName.placeholder')}`
- [ ] Line ~995: `<Label>Port of Loading Code</Label>` → `<Label>{tDecl('shipping.portOfLoadingCode.label')}</Label>`
- [ ] Line ~1013: `placeholder="UN/LOCODE"` → `placeholder={tDecl('shipping.portOfLoadingCode.placeholder')}`
- [ ] Line ~1022: `<Label>Port of Loading Name</Label>` → `<Label>{tDecl('shipping.portOfLoadingName.label')}</Label>`
- [ ] Line ~1040: `placeholder="Port name"` → `placeholder={tDecl('shipping.portOfLoadingName.placeholder')}`
- [ ] Line ~1052: `<Label>Transport Mode Code</Label>` → `<Label>{tDecl('shipping.transportModeCode.label')}</Label>`
- [ ] Line ~1067: `placeholder="e.g., 9999"` → `placeholder={tDecl('shipping.transportModeCode.placeholder')}`
- [ ] Line ~1076: `<Label>Vessel Name</Label>` → `<Label>{tDecl('shipping.vesselName.label')}</Label>`
- [ ] Line ~1091: `placeholder="Vessel name and voyage"` → `placeholder={tDecl('shipping.vesselName.placeholder')}`
- [ ] Line ~1100: `<Label>Arrival Date</Label>` → `<Label>{tDecl('shipping.arrivalDate.label')}</Label>`
- [ ] Line ~1115: `placeholder="DD/MM/YYYY"` → `placeholder={tDecl('shipping.arrivalDate.placeholder')}`

### Section 5: Package & Container (Lines ~1154-1316)

- [ ] Line ~1155: `<Label>Total Packages</Label>` → `<Label>{tDecl('package.totalPackages.label')}</Label>`
- [ ] Line ~1173: `placeholder="Number"` → `placeholder={tDecl('package.totalPackages.placeholder')}`
- [ ] Line ~1182: `<Label>Package Unit</Label>` → `<Label>{tDecl('package.packageUnit.label')}</Label>`
- [ ] Line ~1197: `placeholder="e.g., PK, CT"` → `placeholder={tDecl('package.packageUnit.placeholder')}`
- [ ] Line ~1206: `<Label>Container Count</Label>` → `<Label>{tDecl('package.containerCount.label')}</Label>`
- [ ] Line ~1224: `placeholder="Number"` → `placeholder={tDecl('package.containerCount.placeholder')}`
- [ ] Line ~1235: `<Label>Package Marks</Label>` → `<Label>{tDecl('package.packageMarks.label')}</Label>`
- [ ] Line ~1250: `placeholder="Shipping marks and numbers"` → `placeholder={tDecl('package.packageMarks.placeholder')}`
- [ ] Line ~1261: `<Label>Gross Weight (kg)</Label>` → `<Label>{tDecl('package.grossWeightKg.label')}</Label>`
- [ ] Line ~1280: `placeholder="Weight"` → `placeholder={tDecl('package.grossWeightKg.placeholder')}`
- [ ] Line ~1289: `<Label>Weight Unit</Label>` → `<Label>{tDecl('package.weightUnit.label')}</Label>`
- [ ] Line ~1304: `placeholder="e.g., KGM"` → `placeholder={tDecl('package.weightUnit.placeholder')}`

### Section 6: Invoice Details (Lines ~1344-1532)

- [ ] Line ~1344: `<Label>Invoice Number</Label>` → `<Label>{tDecl('invoice.invoiceNumber.label')}</Label>`
- [ ] Line ~1355: `placeholder="Commercial invoice number"` → `placeholder={tDecl('invoice.invoiceNumber.placeholder')}`
- [ ] Line ~1364: `<Label>Invoice Date</Label>` → `<Label>{tDecl('invoice.invoiceDate.label')}</Label>`
- [ ] Line ~1375: `placeholder="DD/MM/YYYY"` → `placeholder={tDecl('invoice.invoiceDate.placeholder')}`
- [ ] Line ~1387: `<Label>Payment Method Code</Label>` → `<Label>{tDecl('invoice.paymentMethodCode.label')}</Label>`
- [ ] Line ~1400: `placeholder="e.g., KC"` → `placeholder={tDecl('invoice.paymentMethodCode.placeholder')}`
- [ ] Line ~1409: `<Label>Invoice Total</Label>` → `<Label>{tDecl('invoice.invoiceTotal.label')}</Label>`
- [ ] Line ~1424: `placeholder="Total value"` → `placeholder={tDecl('invoice.invoiceTotal.placeholder')}`
- [ ] Line ~1433: `<Label>Currency</Label>` → `<Label>{tDecl('invoice.currency.label')}</Label>`
- [ ] Line ~1444: `placeholder="e.g., USD"` → `placeholder={tDecl('invoice.currency.placeholder')}`
- [ ] Line ~1457: `<Label>Incoterm</Label>` → `<Label>{tDecl('invoice.incoterm.label')}</Label>`
- [ ] Line ~1468: `placeholder="e.g., FOB, CIF"` → `placeholder={tDecl('invoice.incoterm.placeholder')}`
- [ ] Line ~1477: `<Label>Total Taxable Value (VND)</Label>` → `<Label>{tDecl('invoice.totalTaxableValueVnd.label')}</Label>`
- [ ] Line ~1496: `placeholder="Calculated value"` → `placeholder={tDecl('invoice.totalTaxableValueVnd.placeholder')}`
- [ ] Line ~1505: `<Label>Exchange Rate</Label>` → `<Label>{tDecl('invoice.exchangeRate.label')}</Label>`
- [ ] Line ~1520: `placeholder="USD to VND rate"` → `placeholder={tDecl('invoice.exchangeRate.placeholder')}`

### Section 7: Certificate of Origin (Lines ~1560-1635)

- [ ] Line ~1560: `<Label>Form Type</Label>` → `<Label>{tDecl('certificateOfOrigin.formType.label')}</Label>`
- [ ] Line ~1575: `placeholder="e.g., Form E, Form AK"` → `placeholder={tDecl('certificateOfOrigin.formType.placeholder')}`
- [ ] Line ~1584: `<Label>C/O Number</Label>` → `<Label>{tDecl('certificateOfOrigin.coNumber.label')}</Label>`
- [ ] Line ~1599: `placeholder="Certificate number"` → `placeholder={tDecl('certificateOfOrigin.coNumber.placeholder')}`
- [ ] Line ~1608: `<Label>C/O Date</Label>` → `<Label>{tDecl('certificateOfOrigin.coDate.label')}</Label>`
- [ ] Line ~1623: `placeholder="DD/MM/YYYY"` → `placeholder={tDecl('certificateOfOrigin.coDate.placeholder')}`

### Section 8: Product Line Items (Lines ~1712-2251)

**Note:** 18 fields per product, dynamic array. Pattern same as other sections.

Sample fields (apply pattern to all 18):
- [ ] Line ~1712: `<Label>Item Number</Label>` → `<Label>{tDecl('products.itemNumber.label')}</Label>`
- [ ] Line ~1739: `<Label>HS Code (8 digits)</Label>` → `<Label>{tDecl('products.hsCode.label')}</Label>`
- [ ] Line ~1766: `<Label>Product Description</Label>` → `<Label>{tDecl('products.productDescription.label')}</Label>`
- (Continue pattern for remaining 15 product fields...)

### Section 9: Import Duty (Lines ~2279-2379)

- [ ] Line ~2279: `<Label>Rate (%)</Label>` → `<Label>{tDecl('importDuty.rate.label')}</Label>`
- [ ] Line ~2292: `placeholder="Duty rate"` → `placeholder={tDecl('importDuty.rate.placeholder')}`
- [ ] Line ~2301: `<Label>Rate Type</Label>` → `<Label>{tDecl('importDuty.rateType.label')}</Label>`
- [ ] Line ~2312: `placeholder="C, S, or M"` → `placeholder={tDecl('importDuty.rateType.placeholder')}`
- [ ] Line ~2324: `<Label>Amount (VND)</Label>` → `<Label>{tDecl('importDuty.amount.label')}</Label>`
- [ ] Line ~2339: `placeholder="Calculated amount"` → `placeholder={tDecl('importDuty.amount.placeholder')}`
- [ ] Line ~2348: `<Label>Exemption Amount (VND)</Label>` → `<Label>{tDecl('importDuty.exemptionAmount.label')}</Label>`
- [ ] Line ~2367: `placeholder="Exemption"` → `placeholder={tDecl('importDuty.exemptionAmount.placeholder')}`

### Section 10: VAT & Other Taxes (Lines ~2407-2536)

- [ ] Line ~2407: `<Label>Tax Name</Label>` → `<Label>{tDecl('vat.taxName.label')}</Label>`
- [ ] Line ~2418: `placeholder="e.g., Thuế GTGT"` → `placeholder={tDecl('vat.taxName.placeholder')}`
- [ ] Line ~2427: `<Label>Rate Code</Label>` → `<Label>{tDecl('vat.rateCode.label')}</Label>`
- [ ] Line ~2438: `placeholder="e.g., VB245"` → `placeholder={tDecl('vat.rateCode.placeholder')}`
- [ ] Line ~2447: `<Label>Rate (%)</Label>` → `<Label>{tDecl('vat.rate.label')}</Label>`
- [ ] Line ~2460: `placeholder="VAT rate"` → `placeholder={tDecl('vat.rate.placeholder')}`
- [ ] Line ~2472: `<Label>Taxable Value (VND)</Label>` → `<Label>{tDecl('vat.taxableValueVnd.label')}</Label>`
- [ ] Line ~2487: `placeholder="Taxable value"` → `placeholder={tDecl('vat.taxableValueVnd.placeholder')}`
- [ ] Line ~2496: `<Label>Amount (VND)</Label>` → `<Label>{tDecl('vat.amount.label')}</Label>`
- [ ] Line ~2509: `placeholder="VAT amount"` → `placeholder={tDecl('vat.amount.placeholder')}`
- [ ] Line ~2518: `<Label>Exemption (VND)</Label>` → `<Label>{tDecl('vat.exemption.label')}</Label>`
- [ ] Line ~2533: `placeholder="Exemption"` → `placeholder={tDecl('vat.exemption.placeholder')}`

### Section 11: Tax Summary (Lines ~2573-2671)

- [ ] Line ~2573: `<Label>Total Tax Amount (VND)</Label>` → `<Label>{tDecl('taxSummary.totalTaxAmountVnd.label')}</Label>`
- [ ] Line ~2592: `placeholder="Total taxes"` → `placeholder={tDecl('taxSummary.totalTaxAmountVnd.placeholder')}`
- [ ] Line ~2601: `<Label>Payment Deadline Code</Label>` → `<Label>{tDecl('taxSummary.paymentDeadlineCode.label')}</Label>`
- [ ] Line ~2616: `placeholder="e.g., D"` → `placeholder={tDecl('taxSummary.paymentDeadlineCode.placeholder')}`
- [ ] Line ~2628: `<Label>Taxpayer Type</Label>` → `<Label>{tDecl('taxSummary.taxpayerType.label')}</Label>`
- [ ] Line ~2641: `placeholder="e.g., 1"` → `placeholder={tDecl('taxSummary.taxpayerType.placeholder')}`
- [ ] Line ~2650: `<Label>Tax Classification</Label>` → `<Label>{tDecl('taxSummary.taxClassification.label')}</Label>`
- [ ] Line ~2665: `placeholder="e.g., A"` → `placeholder={tDecl('taxSummary.taxClassification.placeholder')}`

---

## Completion Steps

1. **Complete Remaining Field Integration** - Follow checklist above systematically
2. **Test in Development** - Verify form renders correctly in both locales
3. **Run TypeScript Check** - Ensure no type errors introduced
4. **Run Linter** - Fix any linting issues
5. **Manual QA** - Test all form functionality (auto-save, validation, etc.)

---

## Testing Commands

```bash
# TypeScript check
cd frontend && npx tsc --noEmit

# Linting
cd frontend && npm run lint

# Unit tests
cd frontend && npm test

# Development server
cd frontend && npm run dev
```

---

**Pattern Established ✅**
**Translations Complete ✅**
**Infrastructure Working ✅**
**Remaining Work: Mechanical field replacement (71 fields)**

**Estimated Completion Time:** 2-3 hours for experienced developer following this guide
