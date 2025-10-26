"""
Comprehensive LLM extraction prompt for Vietnamese Customs Declaration (77 fields)

Based on field mapping specification in docs/stories/1.7-field-mapping.md
"""


VIETNAMESE_DECLARATION_SYSTEM_PROMPT = """You are a customs data extraction specialist for Vietnamese import declarations.

Your task is to extract ALL 77 fields from 4 source documents (Arrival Notice, Bill of Lading, Certificate of Origin, and Invoice) following Vietnamese customs declaration format.

**CRITICAL RULES:**

1. Extract ALL fields defined in the schema - do not skip any fields
2. Provide per-field confidence score (0.0-1.0) for EVERY extracted field
3. If field not found in any document, set value to null and confidence to 0.0
4. Use Vietnamese labels and formatting conventions
5. Calculate derived fields (taxable values, unit prices in VND) using specified formulas
6. Preserve Vietnamese Unicode characters (diacritics) exactly
7. Format dates as DD/MM/YYYY
8. Use comma for thousands separator (e.g., 23,385.2)

**DOCUMENT PRIORITY FOR CONFLICTS:**
When same field appears in multiple documents with different values:
1. INVOICE (highest priority for pricing, quantities, product descriptions)
2. Certificate of Origin (highest priority for origin country, CO details)
3. Bill of Lading (highest priority for shipping details, weights, containers)
4. Arrival Notice (lowest priority, used only for arrival dates and warehouse)

**CALCULATION FORMULAS:**

1. total_taxable_value_vnd = invoice_total × exchange_rate
2. unit_price_vnd = invoice_unit_price × exchange_rate
3. invoice_line_total = quantity_1 × invoice_unit_price
4. import_duty_amount = taxable_value_vnd × import_duty_rate
5. vat_amount = (taxable_value_vnd + import_duty_amount) × vat_rate
6. total_tax_amount_vnd = import_duty_amount + vat_amount

**CONFIDENCE SCORING GUIDELINES:**

- High (0.90-1.00): Field clearly printed, no ambiguity, single source
- Medium (0.70-0.89): Field readable but handwritten, or conflicts resolved
- Low (0.50-0.69): Field partially visible, multiple interpretations possible
- Very Low (0.00-0.49): Field missing, illegible, or high uncertainty

**RESPONSE FORMAT:**

Return ONLY valid JSON following the exact structure specified below. Do not include any markdown formatting or explanatory text.
"""


def get_vietnamese_extraction_prompt(
    ocr_text_an: str,
    ocr_text_bol: str,
    ocr_text_co: str,
    ocr_text_invoice: str
) -> str:
    """
    Generate comprehensive extraction prompt for Vietnamese customs declaration

    Args:
        ocr_text_an: OCR text from Arrival Notice
        ocr_text_bol: OCR text from Bill of Lading
        ocr_text_co: OCR text from Certificate of Origin
        ocr_text_invoice: OCR text from Invoice

    Returns:
        Complete extraction prompt with all 4 documents
    """
    prompt = f"""**SOURCE DOCUMENTS:**

**Arrival Notice (AN):**
{ocr_text_an}

**Bill of Lading (BOL):**
{ocr_text_bol}

**Certificate of Origin (CO):**
{ocr_text_co}

**Invoice:**
{ocr_text_invoice}

---

**EXTRACTION TASK:**

Extract ALL 77 fields from the above documents and return as JSON following this EXACT structure:

{{
  "declaration_header": {{
    "declaration_number": null,  // System generated - leave null
    "declaration_type_code": "...",  // Import type classification (e.g., "A11 2 [4]")
    "customs_office_code": "...",  // Customs office code (e.g., "HQHOALAC")
    "processing_division_code": "...",  // Processing division code (e.g., "00")
    "registration_date": null,  // System generated - leave null
    "representative_hs_code": "..."  // First 4 digits of primary HS code (calculated from products)
  }},
  "importer": {{
    "tax_code": "...",  // CRITICAL: Vietnamese 10-digit tax ID (Mã số thuế)
    "name": "...",  // Full legal name in Vietnamese
    "postal_code": "...",  // Vietnamese postal code
    "address": "...",  // Full address in Vietnamese
    "phone": "..."  // Contact phone with country code
  }},
  "exporter": {{
    "name": "...",  // Full legal name of exporter
    "address_line1": "...",  // Primary address line
    "address_line2": "...",  // Additional address line (or null)
    "address_line3": "...",  // City, province, country (or null)
    "country_code": "..."  // ISO 3166-1 alpha-2 code (e.g., "CN", "US")
  }},
  "shipping_transport": {{
    "bill_of_lading_number": "...",  // CRITICAL: B/L or AWB number
    "warehouse_code": "...",  // Warehouse/CFS code
    "warehouse_name": "...",  // Warehouse name (or null)
    "port_of_discharge_code": "...",  // UN/LOCODE port code (e.g., "VNDVN")
    "port_of_discharge_name": "...",  // Port name (or null)
    "port_of_loading_code": "...",  // UN/LOCODE port code (e.g., "CNXMN")
    "port_of_loading_name": "...",  // Port name (or null)
    "transport_mode_code": "...",  // Transport mode code (9999=vessel)
    "vessel_name": "...",  // Vessel name and voyage number
    "arrival_date": "DD/MM/YYYY"  // CRITICAL: Date cargo arrived at port
  }},
  "package_container": {{
    "total_packages": 0.0,  // Total number of packages (numeric)
    "package_unit": "...",  // Package unit (PK=package, CT=carton, etc.)
    "package_marks": "...",  // Shipping marks (or null if empty)
    "gross_weight_kg": 0.0,  // Total gross weight in kilograms (numeric)
    "gross_weight_unit": "KGM",  // Weight unit (KGM=kilograms)
    "container_count": 0  // Number of containers (integer)
  }},
  "invoice": {{
    "invoice_number": "...",  // CRITICAL: Commercial invoice number
    "invoice_date": "DD/MM/YYYY",  // Invoice issue date
    "payment_method_code": "...",  // Payment method code (e.g., KC=Letter of Credit)
    "invoice_total": 0.0,  // CRITICAL: Total invoice value (numeric)
    "invoice_currency": "...",  // ISO 4217 currency code (e.g., "USD")
    "invoice_incoterm": "...",  // Incoterms (FOB, CIF, C&F, etc.)
    "total_taxable_value_vnd": 0.0,  // Calculated: invoice_total × exchange_rate
    "exchange_rate": 26230.0  // Use provided rate or current VND/USD rate
  }},
  "certificate_of_origin": {{
    "co_form_type": "...",  // Form type (e.g., "Form E", "Form AK")
    "co_number": "...",  // Certificate of Origin number
    "co_date": "DD/MM/YYYY"  // CO issue date
  }},
  "products": [  // Array of product line items (typically 1-50 items)
    {{
      "item_number": 1,  // Sequential line item number (1, 2, 3, ...)
      "hs_code": "12345678",  // CRITICAL: 8-digit HS code
      "product_description": "...",  // Full product description in Vietnamese
      "quantity_1": 0.0,  // Primary quantity (numeric)
      "quantity_unit_1": "...",  // Primary unit (PCE, KGM, etc.)
      "quantity_2": 0.0,  // Secondary quantity (or null)
      "quantity_unit_2": "...",  // Secondary unit (or null)
      "invoice_unit_price": 0.0,  // Unit price on invoice (numeric)
      "invoice_unit_price_currency": "USD",  // Invoice currency
      "invoice_line_total": 0.0,  // Calculated: quantity_1 × invoice_unit_price
      "taxable_value_vnd": 0.0,  // Calculated: invoice_line_total × exchange_rate
      "unit_price_vnd": 0.0,  // Calculated: invoice_unit_price × exchange_rate
      "country_of_origin_code": "CN",  // ISO 3166-1 alpha-2 country code
      "country_of_origin_name": "CHINA",  // Country name (or null)
      "preferential_code": "...",  // Preferential tariff code (or null)
      "manufacturer_name": "...",  // Manufacturer name (extract from description if embedded, or null)
      "brand_name": "...",  // Brand/trademark (or null)
      "condition": "..."  // New/used condition (e.g., "Mới 100%", or null)
    }}
    // ... repeat for each product line item
  ],
  "import_duty": {{
    "rate": 0.0,  // Import duty rate percentage (will be looked up in Story 2.4, use 0 for now)
    "rate_type": "C",  // Rate type: C=Ad valorem, S=Specific, M=Mixed
    "amount": 0.0,  // Calculated: taxable_value_vnd × rate
    "exemption_amount": 0.0  // Duty exemption amount (or 0)
  }},
  "vat": {{
    "name": "Thuế GTGT",  // Always "Thuế GTGT" for VAT
    "rate_code": "...",  // VAT rate code (will be looked up in Story 2.4, or null)
    "rate": 8.0,  // VAT rate percentage (use 8% default for Vietnam if not specified)
    "taxable_value_vnd": 0.0,  // VAT taxable value in VND
    "amount": 0.0,  // Calculated: (taxable_value_vnd + import_duty_amount) × rate
    "exemption_amount": 0.0  // VAT exemption amount (or 0)
  }},
  "tax_summary": {{
    "total_tax_amount_vnd": 0.0,  // CRITICAL: import_duty.amount + vat.amount
    "tax_payment_deadline_code": "D",  // Tax payment deadline code (use "D" as default)
    "taxpayer_type": "1",  // Taxpayer type (1=Importer)
    "tax_classification": "A"  // Tax classification code (use "A" as default)
  }},
  "metadata": {{
    "total_pages": 0,  // Total pages in declaration (count from source documents)
    "total_line_items": 0  // Total product line items (length of products array)
  }},
  "confidence_scores": {{
    // Flat structure with dot-notation keys for ALL extracted fields
    // Example keys:
    "importer.tax_code": 0.95,
    "importer.name": 0.98,
    "invoice.invoice_number": 0.98,
    "invoice.invoice_total": 0.99,
    "shipping_transport.bill_of_lading_number": 0.97,
    "products.0.hs_code": 0.87,
    "products.0.product_description": 0.92,
    "products.0.quantity_1": 0.95,
    "products.0.invoice_unit_price": 0.93
    // ... include confidence for ALL extracted fields
  }},
  "overall_confidence": 0.94  // Average of all field confidence scores
}}

**IMPORTANT INSTRUCTIONS:**

1. Extract manufacturer name from product description if it mentions "NSX:" or "Manufacturer:" or similar patterns
2. If multiple products are listed, create separate entries in the products array for each
3. For calculated fields, perform the calculations using the extracted values
4. Set metadata.total_line_items to the actual count of products extracted
5. Ensure all numeric fields use proper number format (no commas inside the number value itself)
6. For dates, always use DD/MM/YYYY format
7. For null fields, use JSON null (not string "null")
8. Extract brand names from product descriptions when mentioned (look for keywords like "hiệu:", "brand:", "nhãn hiệu:")
9. Preserve all Vietnamese diacritics (ă, â, ê, ô, ơ, ư, đ, and tone marks)
10. If exchange rate not explicitly stated, use standard rate of 26,230 VND/USD

**VALIDATION CHECKS:**

Before returning the JSON, verify:
- All mandatory fields have been extracted (58 fields must have values)
- All confidence scores are between 0.0 and 1.0
- All dates are in DD/MM/YYYY format
- All numeric fields contain valid numbers
- HS codes are exactly 8 digits
- Country codes are exactly 2 characters
- Currency codes are exactly 3 characters
- Products array is not empty

Return ONLY the JSON object. Do not include any explanatory text or markdown formatting.
"""

    return prompt
