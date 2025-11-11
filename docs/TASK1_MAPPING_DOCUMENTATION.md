# Task 1: Excel Template Mapping Documentation
# Story 2.5: Excel Template Generation

**Template File**: `resources/sample/2/CD.xlsx`
**Template Name**: Vietnamese Customs Declaration (Tờ khai nhập)

---

## Template Overview

- **Worksheet Name**: "Tờ khai nhập "
- **Total Rows**: 222
- **Total Columns**: 37 (A through AK)
- **Structure**: Multi-page official Vietnamese customs declaration form
- **Encoding**: UTF-8 (handled by openpyxl by default)

---

## 1. HEADER SECTION MAPPING (Rows 9-16)

### Consignee/Importer Information

| Field Description | Excel Cell | draft_data Field Path | Data Type | Format | Example Value |
|-------------------|------------|----------------------|-----------|---------|---------------|
| **Importer Tax ID** | H10 | `consignee.tax_id` | String | Text (@) | "0104118221" |
| **Importer Name** | H11:AH12 (merged) | `consignee.name` | String | Text (@) | "Công ty TNHH..." |
| **Postal Code** | H13 | `consignee.postal_code` (if available) | String | Text (@) | "100000" |
| **Importer Address** | H14:AH15 (merged) | `consignee.address` | String | Text (@) | "Tràng An, phường..." |
| **Phone Number** | H16 | `consignee.phone` (if available) | String | Text (@) | "+24..." |

**Static Labels** (DO NOT overwrite):
- Row 9 C9: "Người nhập khẩu" (Importer)
- Row 10 D10: "Mã" (Code)
- Row 11 D11: "Tên" (Name)
- Row 13 D13: "Mã bưu chính" (Postal Code)
- Row 14 D14: "Địa chỉ" (Address)
- Row 16 D16: "Số điện thoại" (Phone Number)

### Declaration Date

| Field Description | Excel Cell | draft_data Field Path | Data Type | Format | Example Value |
|-------------------|------------|----------------------|-----------|---------|---------------|
| **Declaration Date** | G8:K8 (merged) | `declaration_date` | Date | DD/MM/YYYY | "01/10/2025" |

**Note**: Input `declaration_date` is ISO format (YYYY-MM-DD), must convert to DD/MM/YYYY format.

---

## 2. EXPORTER SECTION (Rows 21-27) - OPTIONAL

| Field Description | Excel Cell | draft_data Field Path | Data Type | Format | Example Value |
|-------------------|------------|----------------------|-----------|---------|---------------|
| **Exporter Name** | H23 | `shipper.name` (if available) | String | Text (@) | "QUANZHOU YOULI..." |
| **Exporter Address (Line 1)** | H25:T25 | `shipper.address` | String | Text (@) | "ROOM A10-219..." |
| **Exporter Address (Line 2)** | U25:AG25 | - | String | Text (@) | "YUTOU VILLAGE..." |
| **Exporter Address (Line 3)** | H26:T26 | - | String | Text (@) | "QUANZHOU, FUJIAN" |
| **Exporter Country** | U26:AG26 | `shipper.country` | String | Text (@) | "CHINA" |
| **Exporter Country Code** | H27 | - | String | Text (@) | "CN" |

**Static Labels** (DO NOT overwrite):
- Row 21 C21: "Người xuất khẩu" (Exporter)
- Row 22 D22: "Mã" (Code)
- Row 23 D23: "Tên" (Name)
- Row 25 D25: "Địa chỉ" (Address)
- Row 27 D27: "Mã nước" (Country Code)

---

## 3. INVOICE SECTION (Rows 41-47)

| Field Description | Excel Cell | draft_data Field Path | Data Type | Format | Example Value |
|-------------------|------------|----------------------|-----------|---------|---------------|
| **Invoice Number** | J41:AH41 | `invoice_number` (if available) | String | Text (@) | "A - LA2025-068" |
| **Invoice Date** | J43:AH43 | `invoice_date` (if available) | Date | DD/MM/YYYY | "26/09/2025" |
| **Total Invoice Value** | P45:X45 | `total_invoice_value` | Decimal | #,##0.00 | "23.385,2" (USD) |
| **Total Tax Value (VND)** | J46:X46 | `total_invoice_value` (in VND) | Decimal | #,##0 | "613.393.796" |

**Static Labels** (DO NOT overwrite):
- Row 41 C41: "Số hóa đơn" (Invoice Number)
- Row 43 C43: "Ngày phát hành" (Issue Date)
- Row 45 C45: "Tổng trị giá hóa đơn" (Total Invoice Value)
- Row 46 C46: "Tổng trị giá tính thuế" (Total Taxable Value)

**Note**: The template shows both USD and VND values. We will populate VND values from our calculations.

---

## 4. PRODUCT TABLE SECTION (Rows 160-202)

### Product Item Details (Starting Row 160)

Each product entry spans approximately 40+ rows with detailed breakdowns. Here's the key mapping:

| Field Description | Excel Cell | draft_data Field Path | Data Type | Format | Example |
|-------------------|------------|----------------------|-----------|---------|---------|
| **HS Code** | G160 | `products[i].hs_code` | String | Text (@) | "96190014" |
| **Product Description** | G161:AG163 (merged) | `products[i].description` | String | Text (@) | "Bỉm quần..." |
| **Quantity** | V164 | `products[i].quantity` | Decimal | #,##0.00 | "307.700" |
| **Quantity Unit** | AE164 | `products[i].quantity_unit` | String | Text (@) | "PCE" |
| **Invoice Value** | I166 | `products[i].invoice_value` | Decimal | #,##0.00 | "23.385,2" |
| **Unit Price (Invoice)** | V166 | `products[i].unit_price` | Decimal | 0.000 | "0,076" |
| **Currency** | AC166 | - | String | Text (@) | "USD" |
| **Tax Base Value (VND)** | I168 | `products[i].invoice_value` (VND) | Decimal | #,##0 | "613.393.796" |
| **Unit Price (Tax, VND)** | V169 | - | Decimal | #,##0.00 | "1.993,48" |
| **Import Duty Rate** | I170 | - | String | Text (@) | "0%" |
| **Import Duty Amount** | I171 | `products[i].import_duty` | Decimal | #,##0.00 | "0" |
| **Origin Country Code** | X171 | `products[i].origin_country` | String | Text (@) | "CN" |
| **Origin Country Name** | Z171 | - | String | Text (@) | "CHINA" |
| **Origin Certificate Code** | AC171 | - | String | Text (@) | "B05" |
| **VAT Rate** | I180 | - | String | Text (@) | "8%" |
| **VAT Base** | I179 | - | Decimal | #,##0 | "613.393.796" |
| **VAT Amount** | I181 | `products[i].vat` | Decimal | #,##0.00 | "49.071.503,68" |

**Static Labels per Product** (DO NOT overwrite):
- Row 160 C160: "Mã số hàng hóa" (HS Code)
- Row 161 C161: "Mô tả hàng hóa" (Product Description)
- Row 164 S164: "Số lượng (1)" (Quantity 1)
- Row 166 C166: "Trị giá hóa đơn" (Invoice Value)
- Row 166 S166: "Đơn giá hóa đơn" (Invoice Unit Price)
- Row 167 C167: "Thuế nhập khẩu" (Import Duty)
- Row 168 D168: "Trị giá tính thuế (S)" (Tax Base Value)
- Row 171 D171: "Số tiền thuế" (Tax Amount)
- Row 171 S171: "Nước xuất xứ" (Origin Country)
- Row 177 C177: "Thuế và thu khác" (Other Taxes)
- Row 178 D178/H178: "Tên" / "Thuế GTGT" (Name / VAT)
- Row 179 D179: "Trị giá tính thuế" (Tax Base)
- Row 180 D180: "Thuế suất" (Tax Rate)
- Row 181 D181: "Số tiền thuế" (Tax Amount)

**Important Notes**:
1. **Product row spacing**: Each product starts at row 160 (for first product). The template appears designed for ONE product per page/section.
2. **Multiple products**: For multiple products, we need to determine if we add them sequentially or if there are separate sections.
3. **The template structure**: This is a 3-page template (indicated by row 1 "1/3"). Each page appears to be for a separate product.

---

## 5. TAX SUMMARY SECTION (Rows 67-70)

| Field Description | Excel Cell | draft_data Field Path | Data Type | Format | Example |
|-------------------|------------|----------------------|-----------|---------|---------|
| **Tax Type Label** | D68 | (static: "V  Thuế GTGT") | String | Text (@) | "V  Thuế GTGT" |
| **Total Tax Amount** | H67 | `total_vat` | Decimal | #,##0.00 | Calculated sum |
| **Total Payable** | R68 | `total_payable` | Decimal | #,##0.00 | Total with taxes |

**Static Labels** (DO NOT overwrite):
- Row 67 D67: "Tên sắc thuế" (Tax Type Name)
- Row 67 H67: "Tổng tiền thuế" (Total Tax Amount)
- Row 68 R68: "Tổng tiền thuế phải nộp" (Total Tax Payable)

---

## 6. NUMBER FORMAT SPECIFICATIONS

### Currency Formats (VND)
- **Format String**: `#,##0.00` or `#,##0`
- **Thousand Separator**: Dot (.) in Vietnamese locale, but openpyxl uses comma
- **Decimal Separator**: Comma (,) in Vietnamese, but openpyxl uses period
- **openpyxl Constant**: `numbers.FORMAT_NUMBER_COMMA_SEPARATED1` = `#,##0.00`

### Date Formats
- **Format String**: `DD/MM/YYYY`
- **openpyxl Constant**: `'DD/MM/YYYY'` (custom string)

### Quantity Formats
- **Integer quantities**: `0` (no decimals)
- **Decimal quantities**: `#,##0.00`

### Text Formats
- **Format String**: `@` (text format)
- **Used for**: HS codes, country codes, product descriptions, addresses

---

## 7. VIETNAMESE STATIC LABELS PRESERVATION

**Critical Rule**: The following cells contain static Vietnamese labels and MUST NOT be overwritten:

### Section Headers
- C9: "Người nhập khẩu" (Importer)
- C17: "Người ủy thác nhập khẩu" (Import Trustee)
- C21: "Người xuất khẩu" (Exporter)
- C29: "Đại lý Hải quan" (Customs Agent)
- C41: "Số hóa đơn" (Invoice Number)
- C43: "Ngày phát hành" (Issue Date)
- C45: "Tổng trị giá hóa đơn" (Total Invoice Value)
- C46: "Tổng trị giá tính thuế" (Total Tax Base)

### Field Labels (Column D, E)
- D10: "Mã" (Code)
- D11: "Tên" (Name)
- D13: "Mã bưu chính" (Postal Code)
- D14: "Địa chỉ" (Address)
- D16: "Số điện thoại" (Phone)
- And many more...

### Product Section Labels (Column C, D, S)
- C160: "Mã số hàng hóa" (HS Code)
- C161: "Mô tả hàng hóa" (Product Description)
- S164: "Số lượng (1)" (Quantity 1)
- S166: "Đơn giá hóa đơn" (Unit Price)
- And all other Vietnamese field labels...

**Implementation Strategy**:
- Only write to specific data cells (e.g., H10, H11, G160, V164)
- Never write to label cells (C*, D* columns where they contain Vietnamese text)
- Load template using `load_workbook()` which preserves all formatting and labels

---

## 8. MERGED CELLS IDENTIFICATION

The template has **203 merged cell ranges**. Key merged areas:

### Header Section
- H11:AH12 (Importer Name - 2 rows)
- H14:AH15 (Importer Address - 2 rows)
- H10:AH10 (Tax ID - 1 row)
- G8:K8 (Date - 1 row)

### Exporter Section
- H23:AF23 (Exporter Name)
- H25:T25 (Address line 1)
- U25:AG25 (Address line 2)
- H26:T26 (City, Province)
- U26:AG26 (Country)

### Product Section
- G161:AG163 (Product Description - 3 rows merged)
- Many other merged cells for various fields

**Implementation Note**:
- When writing to merged cells, write to the **top-left cell** of the merged range
- openpyxl will automatically handle the merge

---

## 9. DRAFT_DATA SCHEMA TO EXCEL CELL MAPPING

### Complete Mapping Table

```python
# Pseudo-code mapping structure
HEADER_MAPPING = {
    "consignee": {
        "tax_id": "H10",
        "name": "H11",  # Merged H11:AH12
        "postal_code": "H13",
        "address": "H14",  # Merged H14:AH15
        "phone": "H16"
    },
    "declaration_date": "G8",  # Merged G8:K8, format DD/MM/YYYY
    "shipper": {
        "name": "H23",
        "address_line1": "H25",
        "address_line2": "U25",
        "city": "H26",
        "country": "U26",
        "country_code": "H27"
    }
}

INVOICE_MAPPING = {
    "invoice_number": "J41",
    "invoice_date": "J43",  # Format DD/MM/YYYY
    "total_invoice_value": "P45",  # USD value
    "total_invoice_value_vnd": "J46"  # VND value
}

# Product starts at row 160 for first product
PRODUCT_START_ROW = 160
PRODUCT_MAPPING = {
    "hs_code": ("G", 0),  # G160 for product 0
    "description": ("G", 1),  # G161:AG163 merged
    "quantity": ("V", 4),  # V164
    "quantity_unit": ("AE", 4),  # AE164
    "invoice_value": ("I", 6),  # I166
    "unit_price": ("V", 6),  # V166
    "currency": ("AC", 6),  # AC166
    "tax_base_vnd": ("I", 8),  # I168
    "import_duty_rate": ("I", 10),  # I170
    "import_duty": ("I", 11),  # I171 (should be blank if 0%)
    "origin_country_code": ("X", 11),  # X171
    "origin_country_name": ("Z", 11),  # Z171
    "vat_rate": ("I", 20),  # I180 (row 160+20=180)
    "vat_base": ("I", 19),  # I179
    "vat_amount": ("I", 21)  # I181
}

TAX_SUMMARY_MAPPING = {
    "total_vat": "H67",  # Or calculated sum
    "total_payable": "R68"
}
```

---

## 10. MULTI-PRODUCT HANDLING STRATEGY

**Analysis Finding**: The template is designed as a **multi-page declaration** (indicated by "1/3" in AF1).

**Options for Multiple Products**:

1. **Option A**: Each product gets a separate "page" section (repeating rows 160-202 structure)
   - Product 1: Rows 160-202
   - Product 2: Would need rows ~230-272 (if we extend)
   - Product 3: Would need rows ~300-342

2. **Option B**: Simplified single-product template (MVP approach)
   - Only support ONE product per declaration for Story 2.5
   - Document limitation in completion notes
   - Future story can add multi-product support

**Recommended Approach for Story 2.5**: **Option B** (Single Product MVP)
- Simpler implementation
- Meets AC requirements (AC doesn't specify multi-product support)
- Can validate with sample/2 which appears to have 1 main product
- Future enhancement: Add multi-product support in later story

---

## 11. COLUMN WIDTH AND STYLING REQUIREMENTS

### Column Widths (Preserved from template)
All column widths are defined in the template and will be preserved when loading via `load_workbook()`.

Key columns:
- Column C: 4.0 (narrow, for row labels)
- Column D-G: 4.5-4.6 (field label columns)
- Column H-AH: Variable widths for data entry
- Column AE: 7.6 (wider for units)

### Cell Styling
- **Font**: Preserved from template (appears to be Arial or similar)
- **Borders**: Preserved from template (complex grid structure)
- **Alignment**: Preserved from template (left/right/center)
- **Background**: White/gray alternating (preserved)

**Implementation**: Use `load_workbook(template_path)` which preserves all styling.

---

## 12. KEY FINDINGS SUMMARY

1. **Template Structure**: 222 rows, 37 columns, multi-page Vietnamese customs form
2. **Main Sections**:
   - Header (rows 1-50): Importer, exporter, invoice info
   - Tax Summary (rows 67-70): VAT and total payable
   - Product Details (rows 160-202): Single product with full tax breakdown
3. **Cell Mapping**: Documented for all key `draft_data` fields
4. **Number Formats**: Currency (#,##0.00), Date (DD/MM/YYYY), Quantity (0)
5. **Vietnamese Labels**: 100+ static labels that must be preserved
6. **Merged Cells**: 203 merged ranges - write to top-left cell
7. **Multi-Product**: Recommend single-product MVP for Story 2.5

---

## 13. NEXT STEPS FOR TASK 2 IMPLEMENTATION

1. Create `ExcelGenerationService` class
2. Implement `generate_cd_file()` method:
   - Load template: `load_workbook('resources/sample/2/CD.xlsx')`
   - Get active worksheet
   - Map header fields using mappings above
   - Map single product fields (row 160 base)
   - Map tax summary fields
   - Apply number formats
   - Save to export directory
3. Handle missing fields validation
4. Error handling for template not found

---

**Analysis Complete**: Task 1 completed with comprehensive mapping documentation.

**Files Created**:
- `/home/tinxu-luna/logai/TASK1_MAPPING_DOCUMENTATION.md` (this file)
- `/home/tinxu-luna/logai/analyze_template.py` (analysis script)
- `/home/tinxu-luna/logai/analyze_product_section.py` (detailed product analysis script)

**Ready for**: Task 2 - Create Excel Generation Service
