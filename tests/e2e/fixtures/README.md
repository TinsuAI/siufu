# E2E Test Fixtures

This directory contains anonymized test files for end-to-end testing.

## Required Files

The following files should be present for comprehensive E2E tests:

### Document Files (from `resources/sample/1/`)

1. **invoice.pdf** - Commercial Invoice (INVOICE)
   - Anonymized invoice document for testing OCR extraction
   - Should contain: invoice number, date, seller/buyer info, line items, total amount

2. **bill-of-lading.pdf** - Bill of Lading (BOL.pdf)
   - Shipping document for testing transport information extraction
   - Should contain: B/L number, vessel, ports, container numbers

3. **certificate-of-origin.pdf** - Certificate of Origin (CO.pdf)
   - Origin certification for testing country/manufacturer extraction
   - Should contain: certificate number, country of origin, exporter details

4. **packing-list.xlsx** - Packing List
   - Excel file with package details
   - Should contain: package numbers, dimensions, weights

5. **goods-list.xlsx** - Goods List (goodlist)
   - Excel file with detailed product information
   - Should contain: product descriptions, quantities, HS codes

6. **tariff-classification.xlsx** - Tariff Classification (tariff)
   - Excel file with HS code mappings
   - Should contain: product names, HS codes, duty rates

## File Preparation

To prepare test fixtures:

1. Copy files from `resources/sample/1/` directory
2. Anonymize sensitive information:
   - Replace real company names with "Test Company", "ABC Corp", etc.
   - Replace real addresses with generic addresses
   - Replace real contact info with test@example.com, +1-555-0100
   - Ensure no real trade secrets or proprietary data

3. Rename files to match the names listed above

## Usage in Tests

Import and use files in Playwright tests:

```typescript
import { uploadFile } from './helpers/file-upload'

await uploadFile(page, 'invoice.pdf')
await uploadFile(page, 'bill-of-lading.pdf')
```

## Note

These files are for testing purposes only and should not contain any real or sensitive business data.
