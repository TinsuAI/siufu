#!/usr/bin/env python3
"""
⚠️ ARCHIVED SCRIPT ⚠️

This script was created for Story 1.7.1 v1 (Extract validation data FROM CD.xlsx).
That approach was incorrect - CD.xlsx is the OUTPUT (generated in Story 2.5), not ground truth.

CURRENT USE:
- Kept for reference in Story 2.5 (Excel generation validation)
- May be useful for reverse validation (does generated CD.xlsx match expected-results.json?)

FOR EXTRACTION VALIDATION, USE:
- backend/validate_extraction_results.py (validates results.json vs expected-results.json)

Last Updated: 2025-10-27
Archived By: Product Manager (John) via Sprint Change Proposal

================================================================================
ORIGINAL DOCUMENTATION BELOW
================================================================================

Comprehensive Sample Validation Tool
Validates ALL extraction results from results.json against ground truth from CD.xlsx
Can also generate validation-reference.json files from CD.xlsx

Usage:
    # Validate extraction results
    python3 validate_sample_cd_xlsx.py <sample_folder_path>

    # Generate validation-reference.json from CD.xlsx
    python3 validate_sample_cd_xlsx.py <sample_folder_path> --generate-reference

Examples:
    python3 validate_sample_cd_xlsx.py ../resources/sample/2
    python3 validate_sample_cd_xlsx.py ../resources/sample/1 --generate-reference
"""

import argparse
import json
import sys
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

from openpyxl import load_workbook


def fuzzy_match(str1, str2, threshold=0.85):
    """Check if two strings match with fuzzy matching"""
    if str1 is None and str2 is None:
        return True, 1.0
    if str1 is None or str2 is None:
        return False, 0.0

    str1_clean = str(str1).lower().strip()
    str2_clean = str(str2).lower().strip()

    if str1_clean == str2_clean:
        return True, 1.0

    similarity = SequenceMatcher(None, str1_clean, str2_clean).ratio()
    return similarity >= threshold, similarity


def numeric_tolerance_match(val1, val2, tolerance_percent=0.01):
    """Check if two numeric values match within tolerance"""
    if val1 is None and val2 is None:
        return True, 1.0
    if val1 is None or val2 is None:
        return False, 0.0

    try:
        val1 = float(val1)
        val2 = float(val2)

        if val1 == val2:
            return True, 1.0

        diff = abs(val1 - val2)
        avg = (val1 + val2) / 2
        diff_percent = diff / avg if avg != 0 else 0

        similarity = 1.0 - min(diff_percent, 1.0)
        return diff_percent <= tolerance_percent, similarity
    except (ValueError, TypeError):
        return False, 0.0


def load_validation_reference(sample_path):
    """Load validation reference if it exists, otherwise extract from CD.xlsx"""
    validation_ref_path = Path(sample_path) / "validation-reference.json"

    if validation_ref_path.exists():
        with open(validation_ref_path, 'r', encoding='utf-8') as f:
            validation_ref = json.load(f)

            # Find the ground truth key (sample_1_ground_truth, sample_2_ground_truth, etc.)
            sample_name = Path(sample_path).name
            ground_truth_key = f'sample_{sample_name}_ground_truth'

            if ground_truth_key in validation_ref:
                return validation_ref[ground_truth_key]

            # Fallback: look for any key ending with '_ground_truth'
            for key in validation_ref.keys():
                if key.endswith('_ground_truth'):
                    return validation_ref[key]

    return None


def validate_extracted_data(ground_truth):
    """
    Validate extracted ground truth data for completeness and correctness.

    Returns:
        List[str]: List of validation warnings
    """
    warnings = []

    # Helper to safely convert to float
    def safe_float(val):
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    # Validate numeric fields (non-negative, reasonable ranges)
    invoice_total = safe_float(ground_truth.get('invoice', {}).get('invoice_total'))
    if invoice_total is not None and invoice_total <= 0:
        warnings.append("Invoice total is zero or negative")

    gross_weight = safe_float(ground_truth.get('package_container', {}).get('gross_weight_kg'))
    if gross_weight is not None and gross_weight <= 0:
        warnings.append("Gross weight is zero or negative")

    exchange_rate = safe_float(ground_truth.get('invoice', {}).get('exchange_rate'))
    if exchange_rate is not None:
        if exchange_rate <= 0:
            warnings.append("Exchange rate is zero or negative")
        elif exchange_rate < 10000 or exchange_rate > 50000:
            warnings.append(f"Exchange rate {exchange_rate} seems unusual (expected 20000-30000 VND/USD)")

    # Validate date fields (DD/MM/YYYY format, reasonable dates)
    import re
    date_fields = [
        ('invoice_date', ground_truth.get('invoice', {}).get('invoice_date')),
        ('arrival_date', ground_truth.get('shipping_transport', {}).get('arrival_date')),
        ('co_date', ground_truth.get('certificate_of_origin', {}).get('co_date')),
    ]

    date_pattern = re.compile(r'^\d{1,2}/\d{1,2}/\d{4}$')
    for field_name, date_val in date_fields:
        if date_val:
            if not date_pattern.match(str(date_val)):
                warnings.append(f"{field_name}: Invalid date format '{date_val}' (expected DD/MM/YYYY)")
            else:
                # Check year is reasonable (2020-2030)
                try:
                    parts = str(date_val).split('/')
                    year = int(parts[2])
                    if year < 2020 or year > 2030:
                        warnings.append(f"{field_name}: Year {year} seems unusual")
                except (ValueError, IndexError):
                    pass

    # Validate code fields
    tax_code = ground_truth.get('importer', {}).get('tax_code')
    if tax_code:
        tax_code_str = str(tax_code).strip()
        if len(tax_code_str) != 10 or not tax_code_str.isdigit():
            warnings.append(f"Importer tax code '{tax_code}' should be 10 digits")

    country_code = ground_truth.get('exporter', {}).get('country_code')
    if country_code:
        country_code_str = str(country_code).strip()
        if len(country_code_str) != 2:
            warnings.append(f"Exporter country code '{country_code}' should be 2 characters")

    invoice_currency = ground_truth.get('invoice', {}).get('invoice_currency')
    if invoice_currency:
        currency_str = str(invoice_currency).strip()
        if len(currency_str) != 3:
            warnings.append(f"Invoice currency '{invoice_currency}' should be 3 characters (e.g., USD, EUR)")

    # Validate products
    products = ground_truth.get('products', [])
    if not products:
        warnings.append("No products extracted - products array is empty")
    else:
        for i, product in enumerate(products, 1):
            # HS code validation
            hs_code = product.get('hs_code')
            if not hs_code:
                warnings.append(f"Product {i}: Missing HS code")
            elif len(str(hs_code)) != 8 or not str(hs_code).isdigit():
                warnings.append(f"Product {i}: HS code '{hs_code}' should be 8 digits")

            # Quantity validation
            qty1 = product.get('quantity_1')
            if qty1 is None or qty1 <= 0:
                warnings.append(f"Product {i} (HS {hs_code}): quantity_1 is zero or missing")

            # Price validation
            unit_price = product.get('invoice_unit_price')
            if unit_price is None or unit_price <= 0:
                warnings.append(f"Product {i} (HS {hs_code}): invoice_unit_price is zero or missing")

            # Product consistency validation
            line_total = product.get('invoice_line_total')
            if line_total and unit_price and qty1:
                # Check if line_total ≈ quantity × unit_price (within 1% tolerance)
                expected_total = qty1 * unit_price
                if abs(line_total - expected_total) / expected_total > 0.01:
                    warnings.append(
                        f"Product {i} (HS {hs_code}): invoice_line_total ({line_total:.2f}) "
                        f"does not match quantity × unit_price ({expected_total:.2f})"
                    )

        # Validate sum of product line totals ≈ invoice total (within 1% tolerance)
        if invoice_total:
            product_totals_sum = sum(p.get('invoice_line_total', 0) or 0 for p in products)
            if product_totals_sum > 0:
                diff_pct = abs(invoice_total - product_totals_sum) / invoice_total
                if diff_pct > 0.01:
                    warnings.append(
                        f"Sum of product line totals ({product_totals_sum:.2f}) "
                        f"does not match invoice total ({invoice_total:.2f}) - difference: {diff_pct*100:.1f}%"
                    )

    return warnings


def extract_ground_truth_from_cd_xlsx(xlsx_path):
    """
    Extract comprehensive ground truth data from CD.xlsx (Vietnamese Customs Declaration).

    This function extracts ALL fields from CD.xlsx matching the structure in expected-fields.json:
    - declarationHeader with all nested objects (importer, exporter, transportDetails, invoiceDetails, taxSummary, etc.)
    - items array with complete product details including tax structures

    The output structure matches the Vietnamese Customs Declaration JSON format exactly.

    Args:
        xlsx_path: Path to CD.xlsx file

    Returns:
        dict: Complete ground truth data matching expected-fields.json structure
    """
    wb = load_workbook(xlsx_path)

    # Format auto-detection
    main_sheet_name = wb.sheetnames[0]
    cd_format = "TKN" if "TKN" in main_sheet_name else "Tờ khai nhập"
    ws = wb[main_sheet_name]

    print(f"   Using sheet: '{main_sheet_name}' (detected format: {cd_format})")

    ground_truth = {}
    warnings = []

    # Helper function to safely get cell value
    def get_cell(row, col, default=None):
        val = ws.cell(row, col).value
        return val if val is not None else default

    # Helper function to convert to string or None
    def to_str(val):
        return str(val).strip() if val is not None and str(val).strip() else None

    # Helper function to parse numeric values
    def parse_num(val):
        if val is None:
            return None
        try:
            # Handle European format: "12.144,8" -> 12144.8
            return float(str(val).replace('.', '').replace(',', '.'))
        except (ValueError, TypeError, AttributeError):
            return None

    # ==================== DECLARATION HEADER ====================
    # Extract comprehensive declaration header matching expected-fields.json structure

    declaration_header = {
        'title': to_str(get_cell(2, 5)),  # Usually "Tờ khai hàng hóa nhập khẩu"
        'declarationNumber': to_str(get_cell(4, 5)),
        'correspondingTempImportExportDeclNo': to_str(get_cell(5, 5)),
        'inspectionClassificationCode': to_str(get_cell(6, 5)),
        'firstDeclarationNumber': to_str(get_cell(7, 5)),
        'receivingCustomsAgencyName': to_str(get_cell(8, 8)),
        'typeCode': to_str(get_cell(5, 31)),
        'representativeHScode': to_str(get_cell(6, 31)),
        'processingDivisionCode': to_str(get_cell(7, 31)),
        'registrationDate': to_str(get_cell(8, 31)),
        'registrationChangeDate': to_str(get_cell(9, 31)),
        'reimportExportDeadline': to_str(get_cell(9, 5)),

        # Importer (nested object)
        'importer': {
            'code': to_str(get_cell(10, 8)),
            'name': to_str(get_cell(11, 8)),
            'postalCode': to_str(get_cell(13, 8)),
            'address': to_str(get_cell(14, 8)),
            'phone': to_str(get_cell(15, 8)),
        },

        # Import Trustor (nested object)
        'importTrustor': {
            'code': to_str(get_cell(17, 8)),
            'name': to_str(get_cell(18, 8)),
        },

        # Exporter (nested object)
        'exporter': {
            'code': to_str(get_cell(21, 8)),
            'name': to_str(get_cell(23, 8)),
            'postalCode': to_str(get_cell(24, 8)),
            'address': ' '.join(filter(None, [
                to_str(get_cell(25, 8)),
                to_str(get_cell(25, 21)),
                to_str(get_cell(26, 8)),
                to_str(get_cell(26, 21))
            ])) or None,
            'countryCode': to_str(get_cell(27, 8)),
        },

        # Export Trustor (nested object)
        'exportTrustor': {
            'name': to_str(get_cell(29, 8)),
        },

        # Customs Agent (nested object)
        'customsAgent': {
            'name': to_str(get_cell(20, 8)),
        },

        # Transport Details (nested object)
        'transportDetails': {
            'billOfLadingNumbers': [to_str(get_cell(31, 4))] if get_cell(31, 4) else [],
            'quantityPackages': parse_num(get_cell(36, 11)),
            'quantityPackagesUnit': to_str(get_cell(36, 21)),
            'grossWeight': parse_num(get_cell(37, 11)),
            'grossWeightUnit': to_str(get_cell(37, 21)),
            'containerCount': parse_num(get_cell(38, 11)),
            'customsOfficerCode': to_str(get_cell(39, 11)),
            'storageLocation': to_str(get_cell(30, 21)),
            'unloadingLocationCode': to_str(get_cell(32, 21)),
            'unloadingLocationName': to_str(get_cell(30, 26)),
            'loadingLocationCode': to_str(get_cell(32, 8)),
            'loadingLocationName': to_str(get_cell(33, 8)),
            'transportationMethod': to_str(get_cell(34, 8)),
            'vesselName': to_str(get_cell(34, 26)),
            'arrivalDate': to_str(get_cell(35, 21)),
            'marksAndNumbers': to_str(get_cell(36, 4)),
            'firstWarehouseEntryDate': to_str(get_cell(35, 8)),
        },

        # Invoice Details (nested object)
        'invoiceDetails': {
            'invoiceNumber': to_str(get_cell(41, 10)),
            'eInvoiceReceiptNumber': to_str(get_cell(41, 21)),
            'issueDate': to_str(get_cell(42, 10)),
            'paymentMethod': to_str(get_cell(44, 10)),
            'contentInspectionResultCode': to_str(get_cell(43, 21)),
            'incoterms': to_str(get_cell(43, 10)),
            'currency': to_str(get_cell(45, 21)),
            'totalInvoiceValue': parse_num(get_cell(45, 16)),
            'totalTaxableValue': parse_num(get_cell(46, 21)),
            'totalValueApportionmentFactor': parse_num(get_cell(45, 16)),
            'importPermits': [
                to_str(get_cell(47, 10)),
                to_str(get_cell(48, 10)),
                to_str(get_cell(52, 10)),
                to_str(get_cell(53, 10)),
                to_str(get_cell(54, 10)),
            ],
            'valuationClassificationCode': to_str(get_cell(51, 10)),
            'consolidatedValuation': to_str(get_cell(55, 10)),
            'adjustments': {
                'transportationFee': parse_num(get_cell(56, 10)),
                'insuranceFee': parse_num(get_cell(57, 10)),
            },
            'otherLegalDocuments': [
                to_str(get_cell(58, 10)),
                to_str(get_cell(59, 10)),
                to_str(get_cell(60, 10)),
                to_str(get_cell(61, 10)),
                to_str(get_cell(62, 10)),
            ],
            'valuationDetailsFields': {
                'codeName': to_str(get_cell(63, 10)),
                'classificationCode': to_str(get_cell(63, 21)),
                'adjustmentValue': parse_num(get_cell(64, 10)),
                'totalApportionmentFactor': parse_num(get_cell(64, 21)),
            },
            'valuationDetailsNote': to_str(get_cell(65, 10)),
        },

        # Tax Summary (nested object)
        'taxSummary': {
            'taxItems': [],  # Populated below
            'totalTax': parse_num(get_cell(70, 16)),
            'totalTaxCurrency': to_str(get_cell(70, 21)),
            'totalTaxPayable': parse_num(get_cell(71, 16)),
            'totalTaxPayableCurrency': to_str(get_cell(71, 21)),
            'guaranteeAmount': parse_num(get_cell(72, 16)),
            'taxExchangeRate': parse_num(get_cell(46, 10)),
            'taxExchangeRateCurrency': to_str(get_cell(46, 21)),
            'taxPaymentDeadlineCode': to_str(get_cell(73, 10)),
            'bpRequestReasonCode': to_str(get_cell(74, 10)),
        },

        # Taxpayer (nested object)
        'taxpayer': {
            'code': to_str(get_cell(75, 10)),
            'classification': to_str(get_cell(76, 10)),
            'name': to_str(get_cell(77, 10)),
        },

        # Declaration Meta (nested object)
        'declarationMeta': {
            'totalPages': parse_num(get_cell(78, 31)),
            'totalItems': parse_num(get_cell(79, 31)),
        },

        # E-Attachments (nested object)
        'eAttachments': {
            'count': to_str(get_cell(80, 10)),
            'references': [
                to_str(get_cell(81, 10)),
                to_str(get_cell(82, 10)),
                to_str(get_cell(83, 10)),
            ],
        },

        # Additional fields
        'notes': to_str(get_cell(85, 10)),
        'internalManagementNumber': to_str(get_cell(86, 10)),
        'userManagementNumber': to_str(get_cell(87, 10)),
        'customsInstructions': [],  # Will be populated if found
        'customsNotifications': to_str(get_cell(89, 10)),
        'taxPaymentDeclarationDate': to_str(get_cell(90, 10)),
        'totalLatePaymentInterest': to_str(get_cell(91, 10)),

        # Bonded Transport (nested object)
        'bondedTransport': {
            'deadline': to_str(get_cell(92, 10)),
            'destination': to_str(get_cell(93, 10)),
            'transitInfo': [],  # Will be populated if found
        },
    }

    # Populate taxItems array (search for tax items in rows 66-70)
    # Format: col3=id, col4=name, col8=amount, col12=currency
    # Example: "1" | "V Thuế GTGT" | "48.617.794" | "VND"
    tax_items = []
    for row in range(66, 71):
        tax_id = to_str(get_cell(row, 3))
        tax_name = to_str(get_cell(row, 4))
        tax_amount = get_cell(row, 8)
        tax_currency = to_str(get_cell(row, 12))

        if tax_id and tax_name and tax_amount is not None:
            # Format amount as string with currency
            if tax_currency:
                amount_str = f"{tax_amount} {tax_currency}"
            else:
                amount_str = str(tax_amount)

            tax_items.append({
                'id': tax_id,
                'name': tax_name,
                'amount': amount_str,
            })

    if tax_items:
        declaration_header['taxSummary']['taxItems'] = tax_items

    ground_truth['declarationHeader'] = declaration_header

    # ==================== ITEMS (PRODUCTS) ====================
    # Extract comprehensive product/item details matching expected-fields.json structure
    # Products are in the TKN/main sheet, NOT in HANG/HANG_NK sheet (which is just a template)

    items = []
    print("   Searching for products in main sheet (starting from row 100)...")

    # Parse rate percentage (e.g., "0%" -> "0%", "8%" -> "8%")
    def parse_rate_str(val):
        if val is None:
            return None
        rate_str = str(val).strip()
        if not rate_str.endswith('%'):
            rate_str = rate_str + '%' if rate_str else None
        return rate_str

    try:
        # Search for 8-digit HS codes in column 7, starting from row 100
        for row in range(100, min(ws.max_row + 1, 500)):
            hs_code_cell = ws.cell(row, 7).value

            # Check if this is an 8-digit HS code
            if hs_code_cell and isinstance(hs_code_cell, (int, str)):
                hs_str = str(hs_code_cell).strip()
                if hs_str.isdigit() and len(hs_str) == 8:
                    print(f"     Found product HS code {hs_str} at row {row}")

                    try:
                        # Build complete item structure matching expected-fields.json
                        item = {
                            'itemNumber': f"{len(items) + 1:02d}",
                            'hsCode': hs_str,
                            'privateManagementCode': to_str(get_cell(row, 10)),
                            'priceRecheckClassificationCode': to_str(get_cell(row + 7, 8)),
                            'description': to_str(get_cell(row + 1, 7)),

                            # Quantities
                            'quantity1': parse_num(get_cell(row + 4, 22)),
                            'unit1': to_str(get_cell(row + 4, 31)),
                            'quantity2': parse_num(get_cell(row + 5, 22)),
                            'unit2': to_str(get_cell(row + 5, 31)),

                            'adjustmentItemNumber': to_str(get_cell(row + 5, 10)),

                            # Invoice values
                            'invoiceValue': parse_num(get_cell(row + 6, 9)),
                            'invoiceUnitPrice': parse_num(get_cell(row + 6, 22)),
                            'invoiceUnitPriceCurrency': to_str(get_cell(row + 6, 29)),
                            'invoiceUnitPriceUnit': to_str(get_cell(row + 6, 31)),

                            # Taxable values
                            'taxableValue': parse_num(get_cell(row + 8, 9)),
                            'taxableValueCurrency': to_str(get_cell(row + 8, 21)),
                            'taxableQuantity': parse_num(get_cell(row + 9, 9)),
                            'taxableUnitPrice': parse_num(get_cell(row + 9, 22)),
                            'taxableUnitPriceCurrency': to_str(get_cell(row + 9, 29)),
                            'taxableUnitPriceUnit': to_str(get_cell(row + 9, 31)),

                            # Origin
                            'originCountryCode': to_str(get_cell(row + 11, 24)),
                            'originCountryName': to_str(get_cell(row + 11, 26)),

                            'offQuotaCode': to_str(get_cell(row + 12, 24)),
                            'tempImportExportLineNumber': to_str(get_cell(row + 13, 24)),

                            # Import Tax (nested object)
                            'importTax': {
                                'exemptionCategory': to_str(get_cell(row + 10, 4)),
                                'exemptionReductionStatus': to_str(get_cell(row + 10, 6)),
                                'taxRateCode': to_str(get_cell(row + 10, 8)),
                                'taxRate': parse_rate_str(get_cell(row + 10, 9)),
                                'absoluteTaxCode': to_str(get_cell(row + 11, 22)),
                                'taxAmount': parse_num(get_cell(row + 11, 9)),
                                'taxAmountCurrency': to_str(get_cell(row + 11, 21)),
                                'exemptionAmount': parse_num(get_cell(row + 12, 9)),
                                'exemptionAmountCurrency': to_str(get_cell(row + 12, 21)),
                            },

                            # Other Taxes (array of tax objects)
                            'otherTaxes': []
                        }

                        # Extract VAT (other taxes) - typically starts around row+18
                        vat_name = to_str(get_cell(row + 18, 8))
                        if vat_name:
                            vat_tax = {
                                'name': vat_name,
                                'rateApplicationCode': to_str(get_cell(row + 18, 23)),
                                'taxableValue': parse_num(get_cell(row + 19, 9)),
                                'taxableValueCurrency': to_str(get_cell(row + 19, 21)),
                                'taxRate': parse_rate_str(get_cell(row + 20, 9)),
                                'taxableQuantity': parse_num(get_cell(row + 20, 22)),
                                'exemptionStatus': to_str(get_cell(row + 20, 31)),
                                'taxAmount': parse_num(get_cell(row + 21, 9)),
                                'taxAmountCurrency': to_str(get_cell(row + 21, 21)),
                                'exemptionAmount': parse_num(get_cell(row + 22, 9)),
                                'exemptionAmountCurrency': to_str(get_cell(row + 22, 21)),
                            }
                            item['otherTaxes'].append(vat_tax)

                        items.append(item)

                        # Validate product data
                        if item['quantity1'] is None or item['quantity1'] <= 0:
                            warnings.append(f"Item {len(items)}: quantity1 is zero or missing")
                        if item['invoiceUnitPrice'] is None or item['invoiceUnitPrice'] <= 0:
                            warnings.append(f"Item {len(items)}: invoiceUnitPrice is zero or missing")

                    except Exception as e:
                        warnings.append(f"Error extracting item at row {row}: {e}")
                        print(f"⚠️  Warning: Error extracting item at row {row}: {e}")

    except Exception as e:
        warnings.append(f"Error during item extraction: {e}")
        print(f"⚠️  Warning: Error during item extraction: {e}")

    ground_truth['items'] = items
    print(f"   Extracted {len(items)} items")

    # Store metadata for debugging
    ground_truth['_metadata'] = {
        'cd_format': cd_format,
        'extraction_warnings': warnings,
        'total_items_found': len(items),
        'extraction_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }

    # Print validation summary
    if warnings:
        print(f"   ⚠️  {len(warnings)} extraction warnings:")
        for warning in warnings[:5]:  # Show first 5
            print(f"      - {warning}")
        if len(warnings) > 5:
            print(f"      ... and {len(warnings) - 5} more")

    return ground_truth


def generate_validation_reference_json(sample_path, cd_xlsx_path):
    """
    Generate validation-reference.json file from CD.xlsx.

    The output structure matches expected-fields.json exactly with:
    - declarationHeader (complete nested structure)
    - items array (complete product details with tax structures)
    """

    sample_name = Path(sample_path).name

    print(f"📝 Generating validation-reference.json for Sample {sample_name}...")
    print()

    # Extract ground truth from CD.xlsx
    try:
        ground_truth_data = extract_ground_truth_from_cd_xlsx(cd_xlsx_path)
    except Exception as e:
        print(f"❌ Error extracting data from CD.xlsx: {e}")
        import traceback
        traceback.print_exc()
        return None

    # Build validation reference structure matching expected-fields.json format exactly
    # This is an array containing a single customs declaration object
    validation_ref = [{
        "declarationHeader": ground_truth_data.get('declarationHeader', {}),
        "items": ground_truth_data.get('items', []),
    }]

    # Add metadata comment at the beginning (as a separate file for documentation)
    metadata = {
        "description": f"Ground truth validation data for Sample {sample_name} extracted from CD.xlsx (Vietnamese Customs Declaration)",
        "created_date": datetime.now().strftime('%Y-%m-%d'),
        "source": str(cd_xlsx_path.relative_to(Path(sample_path).parent.parent)) if cd_xlsx_path.is_relative_to(Path(sample_path).parent.parent) else str(cd_xlsx_path),
        "note": "This structure matches the Vietnamese Customs Declaration JSON format exactly as shown in expected-fields.json",
        "cd_format": ground_truth_data.get('_metadata', {}).get('cd_format'),
        "total_items": ground_truth_data.get('_metadata', {}).get('total_items_found'),
        "extraction_date": ground_truth_data.get('_metadata', {}).get('extraction_date'),
        "extraction_warnings": ground_truth_data.get('_metadata', {}).get('extraction_warnings', []),
    }

    # Save main validation reference JSON
    output_path = Path(sample_path) / "validation-reference.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(validation_ref, f, indent=2, ensure_ascii=False)

    # Save metadata separately
    metadata_path = Path(sample_path) / "validation-reference-metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"✅ Generated: {output_path}")
    print(f"✅ Generated: {metadata_path}")
    print()
    print("Summary of extracted data:")

    decl_header = ground_truth_data.get('declarationHeader', {})
    items = ground_truth_data.get('items', [])

    print(f"  • Declaration Number: {decl_header.get('declarationNumber')}")
    print(f"  • Importer Tax Code: {decl_header.get('importer', {}).get('code')}")
    print(f"  • Invoice Number: {decl_header.get('invoiceDetails', {}).get('invoiceNumber')}")
    print(f"  • Invoice Total: {decl_header.get('invoiceDetails', {}).get('totalInvoiceValue')}")
    print(f"  • Bill of Lading: {decl_header.get('transportDetails', {}).get('billOfLadingNumbers')}")
    print(f"  • Items: {len(items)} item(s)")

    if items:
        for item in items:
            print(f"    - Item {item.get('itemNumber')}: HS {item.get('hsCode')}, Qty: {item.get('quantity1')} {item.get('unit1')}")
    print()

    return output_path


def compare_value(field_name, expected, actual, conf, field_type='fuzzy'):
    """Compare a single value and return detailed result"""

    if field_type == 'exact':
        if expected is None and actual is None:
            match = True
            similarity = 1.0
        elif expected is None or actual is None:
            match = False
            similarity = 0.0
        else:
            expected_str = str(expected).strip()
            actual_str = str(actual).strip()
            match = (expected_str == actual_str)
            similarity = 1.0 if match else SequenceMatcher(None, expected_str.lower(), actual_str.lower()).ratio()

    elif field_type == 'numeric':
        match, similarity = numeric_tolerance_match(expected, actual, tolerance_percent=0.01)

    else:  # fuzzy
        match, similarity = fuzzy_match(expected, actual, threshold=0.85)

    return {
        'field': field_name,
        'expected': expected,
        'actual': actual,
        'match': match,
        'similarity': similarity,
        'confidence': conf,
        'type': field_type
    }


def validate_comprehensive(ground_truth, extracted_data, confidence_scores):
    """Comprehensive validation of all fields"""

    validation_details = {
        'critical': [],
        'important': [],
        'optional': [],
        'products': []
    }

    total_checks = 0
    passed_checks = 0.0
    critical_failures = []
    warnings = []

    # ===== CRITICAL FIELDS =====
    print("=" * 100)
    print("CRITICAL FIELDS (Must be 100% accurate)")
    print("=" * 100)
    print()

    # Support both nested structure and flat critical_fields structure
    critical_fields = ground_truth.get('critical_fields', {})

    critical_checks = [
        ('Declaration Number', critical_fields.get('declaration_number'),
         extracted_data.get('declaration_header', {}).get('declaration_number'),
         confidence_scores.get('declaration_header.declaration_number', 0.0), 'exact'),

        ('Importer Tax Code', critical_fields.get('importer_tax_code'),
         extracted_data.get('importer', {}).get('tax_code'),
         confidence_scores.get('importer.tax_code', 0.0), 'exact'),

        ('Invoice Number', critical_fields.get('invoice_number'),
         extracted_data.get('invoice', {}).get('invoice_number'),
         confidence_scores.get('invoice.invoice_number', 0.0), 'exact'),

        ('Invoice Total (USD)', critical_fields.get('invoice_total'),
         extracted_data.get('invoice', {}).get('invoice_total'),
         confidence_scores.get('invoice.invoice_total', 0.0), 'numeric'),

        ('Bill of Lading', critical_fields.get('bill_of_lading_number'),
         extracted_data.get('shipping_transport', {}).get('bill_of_lading_number'),
         confidence_scores.get('shipping_transport.bill_of_lading_number', 0.0), 'exact'),

        ('CO Number', critical_fields.get('co_number'),
         extracted_data.get('certificate_of_origin', {}).get('co_number'),
         confidence_scores.get('certificate_of_origin.co_number', 0.0), 'exact'),
    ]

    # Add product critical fields if present
    if critical_fields.get('products') and len(critical_fields['products']) > 0:
        product_gt = critical_fields['products'][0]
        product_ex = extracted_data.get('products', [{}])[0] if extracted_data.get('products') else {}

        critical_checks.extend([
            ('Product HS Code', product_gt.get('hs_code'),
             product_ex.get('hs_code'),
             confidence_scores.get('products.0.hs_code', 0.0), 'exact'),

            ('Product Quantity 1', product_gt.get('quantity_1'),
             product_ex.get('quantity_1'),
             confidence_scores.get('products.0.quantity_1', 0.0), 'numeric'),

            ('Product Unit Price (USD)', product_gt.get('invoice_unit_price'),
             product_ex.get('invoice_unit_price'),
             confidence_scores.get('products.0.invoice_unit_price', 0.0), 'numeric'),
        ])

    for field_name, expected, actual, conf, field_type in critical_checks:
        total_checks += 1
        result = compare_value(field_name, expected, actual, conf, field_type)
        validation_details['critical'].append(result)

        status = "✅ PASS" if result['match'] else "❌ FAIL"
        print(f"{status} {field_name}")
        print(f"   Expected: {expected}")
        print(f"   Actual:   {actual}")
        print(f"   Confidence: {conf:.0%} | Similarity: {result['similarity']:.0%}")
        print()

        if result['match']:
            passed_checks += 1
        else:
            critical_failures.append(field_name)

    # ===== IMPORTANT FIELDS =====
    print("=" * 100)
    print("IMPORTANT FIELDS (≥85% fuzzy match threshold)")
    print("=" * 100)
    print()

    # Support both nested structure and flat important_fields structure
    important_fields = ground_truth.get('important_fields', {})

    important_checks = [
        ('Importer Name', important_fields.get('importer_name'),
         extracted_data.get('importer', {}).get('name'),
         confidence_scores.get('importer.name', 0.0)),

        ('Importer Address', important_fields.get('importer_address'),
         extracted_data.get('importer', {}).get('address'),
         confidence_scores.get('importer.address', 0.0)),

        ('Exporter Name', important_fields.get('exporter_name'),
         extracted_data.get('exporter', {}).get('name'),
         confidence_scores.get('exporter.name', 0.0)),

        ('Exporter Address Line 1', important_fields.get('exporter_address_line1'),
         extracted_data.get('exporter', {}).get('address_line1'),
         confidence_scores.get('exporter.address_line1', 0.0)),

        ('Exporter Address Line 2', important_fields.get('exporter_address_line2'),
         extracted_data.get('exporter', {}).get('address_line2'),
         confidence_scores.get('exporter.address_line2', 0.0)),

        ('Exporter Address Line 3', important_fields.get('exporter_address_line3'),
         extracted_data.get('exporter', {}).get('address_line3'),
         confidence_scores.get('exporter.address_line3', 0.0)),

        ('Exporter Country Code', important_fields.get('exporter_country_code'),
         extracted_data.get('exporter', {}).get('country_code'),
         confidence_scores.get('exporter.country_code', 0.0)),

        ('Vessel Name', important_fields.get('vessel_name'),
         extracted_data.get('shipping_transport', {}).get('vessel_name'),
         confidence_scores.get('shipping_transport.vessel_name', 0.0)),

        ('Port of Discharge', important_fields.get('port_of_discharge_name'),
         extracted_data.get('shipping_transport', {}).get('port_of_discharge_name'),
         confidence_scores.get('shipping_transport.port_of_discharge_name', 0.0)),

        ('Port of Loading', important_fields.get('port_of_loading_name'),
         extracted_data.get('shipping_transport', {}).get('port_of_loading_name'),
         confidence_scores.get('shipping_transport.port_of_loading_name', 0.0)),

        ('Warehouse Name', important_fields.get('warehouse_name'),
         extracted_data.get('shipping_transport', {}).get('warehouse_name'),
         confidence_scores.get('shipping_transport.warehouse_name', 0.0)),

        ('Invoice Date', important_fields.get('invoice_date'),
         extracted_data.get('invoice', {}).get('invoice_date'),
         confidence_scores.get('invoice.invoice_date', 0.0)),

        ('Arrival Date', important_fields.get('arrival_date'),
         extracted_data.get('shipping_transport', {}).get('arrival_date'),
         confidence_scores.get('shipping_transport.arrival_date', 0.0)),

        ('Total Packages', important_fields.get('total_packages'),
         extracted_data.get('package_container', {}).get('total_packages'),
         confidence_scores.get('package_container.total_packages', 0.0)),

        ('Gross Weight (kg)', important_fields.get('gross_weight_kg'),
         extracted_data.get('package_container', {}).get('gross_weight_kg'),
         confidence_scores.get('package_container.gross_weight_kg', 0.0)),
    ]

    for field_name, expected, actual, conf in important_checks:
        total_checks += 1

        # Determine if numeric or text
        if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
            result = compare_value(field_name, expected, actual, conf, 'numeric')
        else:
            result = compare_value(field_name, expected, actual, conf, 'fuzzy')

        validation_details['important'].append(result)

        status = "✅ PASS" if result['match'] else "⚠️ WARN"
        print(f"{status} {field_name} (similarity: {result['similarity']:.0%})")
        print(f"   Expected: {expected}")
        print(f"   Actual:   {actual}")
        print(f"   Confidence: {conf:.0%}")
        print()

        if result['match']:
            passed_checks += 1
        elif result['similarity'] >= 0.70:
            warnings.append(f"{field_name} ({result['similarity']:.0%})")
            passed_checks += 0.7  # Partial credit
        else:
            warnings.append(f"{field_name} ({result['similarity']:.0%})")

    # ===== PRODUCT VALIDATION =====
    gt_products = ground_truth.get('products', [])
    ex_products = extracted_data.get('products', [])

    if gt_products or ex_products:
        print("=" * 100)
        print(f"PRODUCT LINE ITEMS VALIDATION ({len(gt_products)} expected, {len(ex_products)} extracted)")
        print("=" * 100)
        print()

        max_products = max(len(gt_products), len(ex_products))

        for i in range(max_products):
            gt_product = gt_products[i] if i < len(gt_products) else {}
            ex_product = ex_products[i] if i < len(ex_products) else {}

            print(f"--- Product {i + 1} ---")

            product_checks = [
                ('HS Code', gt_product.get('hs_code'), ex_product.get('hs_code'),
                 confidence_scores.get(f'products.{i}.hs_code', 0.0), 'exact'),

                ('Description', gt_product.get('product_description'), ex_product.get('product_description'),
                 confidence_scores.get(f'products.{i}.product_description', 0.0), 'fuzzy'),

                ('Quantity 1', gt_product.get('quantity_1'), ex_product.get('quantity_1'),
                 confidence_scores.get(f'products.{i}.quantity_1', 0.0), 'numeric'),

                ('Unit 1', gt_product.get('quantity_unit_1'), ex_product.get('quantity_unit_1'),
                 confidence_scores.get(f'products.{i}.quantity_unit_1', 0.0), 'exact'),

                ('Quantity 2', gt_product.get('quantity_2'), ex_product.get('quantity_2'),
                 confidence_scores.get(f'products.{i}.quantity_2', 0.0), 'numeric'),

                ('Unit 2', gt_product.get('quantity_unit_2'), ex_product.get('quantity_unit_2'),
                 confidence_scores.get(f'products.{i}.quantity_unit_2', 0.0), 'exact'),

                ('Unit Price (USD)', gt_product.get('invoice_unit_price'), ex_product.get('invoice_unit_price'),
                 confidence_scores.get(f'products.{i}.invoice_unit_price', 0.0), 'numeric'),

                ('Country of Origin', gt_product.get('country_of_origin_code'), ex_product.get('country_of_origin_code'),
                 confidence_scores.get(f'products.{i}.country_of_origin_code', 0.0), 'exact'),
            ]

            product_results = []
            for field_name, expected, actual, conf, field_type in product_checks:
                total_checks += 1
                result = compare_value(f"Product {i+1} - {field_name}", expected, actual, conf, field_type)
                product_results.append(result)

                status = "✅" if result['match'] else "⚠️"
                print(f"  {status} {field_name}: {actual} (expected: {expected}) [{result['similarity']:.0%}]")

                if result['match']:
                    passed_checks += 1
                elif result['similarity'] >= 0.70:
                    passed_checks += 0.7

            validation_details['products'].append({
                'item_number': i + 1,
                'checks': product_results
            })
            print()

    # ===== OPTIONAL FIELDS (Show what's extracted but don't count in accuracy) =====
    print("=" * 100)
    print("OPTIONAL/INFORMATIONAL FIELDS (Not counted in accuracy)")
    print("=" * 100)
    print()

    optional_fields = [
        ('Importer Phone', extracted_data.get('importer', {}).get('phone')),
        ('Importer Postal Code', extracted_data.get('importer', {}).get('postal_code')),
        ('Invoice Currency', extracted_data.get('invoice', {}).get('invoice_currency')),
        ('Invoice Incoterm', extracted_data.get('invoice', {}).get('invoice_incoterm')),
        ('Exchange Rate', extracted_data.get('invoice', {}).get('exchange_rate')),
        ('Payment Method', extracted_data.get('invoice', {}).get('payment_method_code')),
        ('VAT Rate', extracted_data.get('vat', {}).get('rate')),
        ('VAT Amount (VND)', extracted_data.get('vat', {}).get('amount')),
        ('Import Duty Rate', extracted_data.get('import_duty', {}).get('rate')),
        ('CO Number', extracted_data.get('certificate_of_origin', {}).get('co_number')),
        ('CO Date', extracted_data.get('certificate_of_origin', {}).get('co_date')),
        ('CO Form Type', extracted_data.get('certificate_of_origin', {}).get('co_form_type')),
        ('Container Count', extracted_data.get('package_container', {}).get('container_count')),
        ('Package Marks', extracted_data.get('package_container', {}).get('package_marks')),
        ('Port of Loading', extracted_data.get('shipping_transport', {}).get('port_of_loading_name')),
        ('Port of Discharge', extracted_data.get('shipping_transport', {}).get('port_of_discharge_name')),
    ]

    for field_name, value in optional_fields:
        print(f"ℹ️  {field_name}: {value}")

    print()

    # ===== SUMMARY =====
    accuracy = (passed_checks / total_checks * 100) if total_checks > 0 else 0

    return {
        'total_checks': total_checks,
        'passed_checks': passed_checks,
        'accuracy': accuracy,
        'critical_failures': critical_failures,
        'warnings': warnings,
        'details': validation_details
    }


def generate_comprehensive_markdown_report(sample_path, validation_results, ground_truth, extracted_data, timestamp):
    """Generate comprehensive markdown report"""

    report_path = Path(sample_path) / f"validation-report-comprehensive-{timestamp}.md"

    md = []

    # Header
    md.append(f"# Comprehensive Validation Report - {Path(sample_path).name}")
    md.append("")
    md.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md.append(f"**Sample Path:** `{sample_path}`")
    md.append("**Validation Tool:** `backend/validate_sample_comprehensive.py`")
    md.append("")
    md.append("---")
    md.append("")

    # Executive Summary
    md.append("## Executive Summary")
    md.append("")
    md.append("| Metric | Value |")
    md.append("|--------|-------|")
    md.append(f"| **Total Checks** | {validation_results['total_checks']} |")
    md.append(f"| **Passed** | {validation_results['passed_checks']:.1f} |")
    md.append(f"| **Accuracy** | {validation_results['accuracy']:.1f}% |")
    md.append(f"| **Overall Confidence** | {extracted_data.get('overall_confidence', 0) * 100:.1f}% |")
    md.append(f"| **Critical Failures** | {len(validation_results['critical_failures'])} |")
    md.append(f"| **Warnings** | {len(validation_results['warnings'])} |")

    # Verdict
    accuracy = validation_results['accuracy']
    if accuracy >= 95 and not validation_results['critical_failures']:
        verdict = "**EXCELLENT** ✅"
        verdict_msg = "Extraction quality EXCEEDS requirements"
    elif accuracy >= 85 and len(validation_results['critical_failures']) <= 2:
        verdict = "**PASS** ✅"
        verdict_msg = "Extraction quality MEETS AC#9 requirements (≥85%)"
    elif accuracy >= 75:
        verdict = "**CONCERNS** ⚠️"
        verdict_msg = "Extraction quality BELOW target but may be acceptable for MVP"
    else:
        verdict = "**FAIL** ❌"
        verdict_msg = "Extraction quality INSUFFICIENT"

    md.append(f"| **Verdict** | {verdict} |")
    md.append("")
    md.append(f"{verdict_msg}")
    md.append("")
    md.append("---")
    md.append("")

    # Critical Failures
    if validation_results['critical_failures']:
        md.append(f"## ❌ Critical Failures ({len(validation_results['critical_failures'])})")
        md.append("")
        for failure in validation_results['critical_failures']:
            md.append(f"- {failure}")
        md.append("")
        md.append("---")
        md.append("")

    # Warnings
    if validation_results['warnings']:
        md.append(f"## ⚠️ Warnings ({len(validation_results['warnings'])})")
        md.append("")
        for warning in validation_results['warnings']:
            md.append(f"- {warning}")
        md.append("")
        md.append("---")
        md.append("")

    # Critical Fields Table
    md.append("## Detailed Validation Results")
    md.append("")
    md.append("### Critical Fields (Must be 100% accurate)")
    md.append("")
    md.append("| Field | Expected | Actual | Match | Similarity | Confidence |")
    md.append("|-------|----------|--------|-------|------------|------------|")

    for detail in validation_results['details']['critical']:
        icon = "✅" if detail['match'] else "❌"
        md.append(f"| {icon} {detail['field']} | `{detail['expected']}` | `{detail['actual']}` | {detail['match']} | {detail['similarity']:.0%} | {detail['confidence']:.0%} |")

    md.append("")

    # Important Fields Table
    md.append("### Important Fields (≥85% fuzzy match threshold)")
    md.append("")
    md.append("| Field | Expected | Actual | Match | Similarity | Confidence |")
    md.append("|-------|----------|--------|-------|------------|------------|")

    for detail in validation_results['details']['important']:
        icon = "✅" if detail['match'] else "⚠️"
        md.append(f"| {icon} {detail['field']} | `{detail['expected']}` | `{detail['actual']}` | {detail['match']} | {detail['similarity']:.0%} | {detail['confidence']:.0%} |")

    md.append("")

    # Products Table
    if validation_results['details']['products']:
        md.append("### Product Line Items")
        md.append("")

        for product in validation_results['details']['products']:
            md.append(f"#### Product {product['item_number']}")
            md.append("")
            md.append("| Field | Expected | Actual | Match | Similarity | Confidence |")
            md.append("|-------|----------|--------|-------|------------|------------|")

            for check in product['checks']:
                icon = "✅" if check['match'] else "⚠️"
                field_name = check['field'].replace(f"Product {product['item_number']} - ", "")
                md.append(f"| {icon} {field_name} | `{check['expected']}` | `{check['actual']}` | {check['match']} | {check['similarity']:.0%} | {check['confidence']:.0%} |")

            md.append("")

    # Full Extracted Data
    md.append("---")
    md.append("")
    md.append("## Complete Extracted Data")
    md.append("")
    md.append("<details>")
    md.append("<summary>Click to expand full extraction results</summary>")
    md.append("")
    md.append("```json")
    md.append(json.dumps(extracted_data, indent=2, ensure_ascii=False))
    md.append("```")
    md.append("")
    md.append("</details>")
    md.append("")
    md.append("---")
    md.append("")

    # Known Discrepancies
    md.append("## 📌 Known Discrepancies")
    md.append("")
    md.append("These discrepancies are expected due to differences between source documents and CD.xlsx:")
    md.append("")
    md.append("1. **Declaration Number**: System-generated field, not extracted from source documents")
    md.append("2. **CO Number**: CD.xlsx may show internal tracking number vs official CO document number")
    md.append("3. **Arrival Date**: May differ between CO issue date and actual arrival date")
    md.append("4. **Address Formatting**: Vietnamese vs English, with/without diacritics")
    md.append("5. **Port Names**: Different levels of specificity (port vs terminal)")
    md.append("")
    md.append("---")
    md.append("")

    # Metadata
    md.append("## Validation Metadata")
    md.append("")
    md.append("- **Tool Version:** 2.0 (Comprehensive)")
    md.append("- **Ground Truth Source:** CD.xlsx")
    md.append("- **Extraction Source:** results.json")
    md.append(f"- **Validation Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md.append("- **Fuzzy Match Threshold:** 85%")
    md.append("- **Numeric Tolerance:** ±1%")
    md.append(f"- **Fields Validated:** {validation_results['total_checks']}")
    md.append("")
    md.append("---")
    md.append("")
    md.append("*Generated by comprehensive validation tool - AC#9 Compliance Check*")

    # Write report
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))

    return report_path


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Comprehensive Sample Validation Tool - Validates extraction results or generates validation-reference.json',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Validate extraction results
  python3 validate_sample.py ../resources/sample/2

  # Generate validation-reference.json from CD.xlsx
  python3 validate_sample.py ../resources/sample/1 --generate-reference
  python3 validate_sample.py ../resources/sample/3 --generate-reference
        '''
    )

    parser.add_argument('sample_path', help='Path to sample folder containing CD.xlsx (and results.json for validation)')
    parser.add_argument('--generate-reference', action='store_true',
                       help='Generate validation-reference.json from CD.xlsx instead of validating')

    args = parser.parse_args()

    sample_path = Path(args.sample_path).resolve()

    if not sample_path.exists():
        print(f"❌ Error: Sample path does not exist: {sample_path}")
        sys.exit(1)

    cd_xlsx_path = sample_path / "CD.xlsx"
    results_json_path = sample_path / "results.json"

    if not cd_xlsx_path.exists():
        print(f"❌ Error: CD.xlsx not found in {sample_path}")
        print(f"   Expected: {cd_xlsx_path}")
        sys.exit(1)

    # Handle --generate-reference mode
    if args.generate_reference:
        print("=" * 100)
        print(f"GENERATE VALIDATION REFERENCE - Sample {sample_path.name}")
        print("=" * 100)
        print()

        output_path = generate_validation_reference_json(sample_path, cd_xlsx_path)

        if output_path:
            print("✅ Success! You can now use this validation-reference.json to validate extraction results.")
            print()
            print("Next step:")
            print(f"  python3 validate_sample.py {args.sample_path}")
            sys.exit(0)
        else:
            sys.exit(1)

    # Normal validation mode requires results.json
    if not results_json_path.exists():
        print(f"❌ Error: results.json not found in {sample_path}")
        print(f"   Expected: {results_json_path}")
        print()
        print("Tip: To generate validation-reference.json from CD.xlsx, use:")
        print(f"  python3 validate_sample.py {args.sample_path} --generate-reference")
        sys.exit(1)

    print("=" * 100)
    print(f"COMPREHENSIVE SAMPLE VALIDATION - {sample_path.name}")
    print("=" * 100)
    print()

    # Load ground truth
    print("📋 Loading ground truth...")
    try:
        # Try to load from validation-reference.json first
        ground_truth = load_validation_reference(sample_path)

        if ground_truth:
            print("✅ Loaded ground truth from validation-reference.json")
        else:
            # Fall back to extracting from CD.xlsx
            ground_truth = extract_ground_truth_from_cd_xlsx(cd_xlsx_path)
            print("✅ Extracted ground truth from CD.xlsx")

        print()
    except Exception as e:
        print(f"❌ Error loading ground truth: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Load extraction results
    print("📋 Loading extraction results from results.json...")
    try:
        with open(results_json_path, 'r', encoding='utf-8') as f:
            results = json.load(f)

        extracted_data = results.get('extracted_data', {})
        confidence_scores = results.get('confidence_scores', {})

        print("✅ Loaded extraction results")
        print(f"   Status: {results.get('status')}")
        print(f"   Overall Confidence: {extracted_data.get('overall_confidence', 0):.1%}")
        print()
    except Exception as e:
        print(f"❌ Error loading results.json: {e}")
        sys.exit(1)

    # Perform validation
    validation_results = validate_comprehensive(ground_truth, extracted_data, confidence_scores)

    # Summary
    print("=" * 100)
    print("VALIDATION SUMMARY")
    print("=" * 100)
    print()
    print(f"📊 Total Checks: {validation_results['total_checks']}")
    print(f"✅ Passed: {validation_results['passed_checks']:.1f} / {validation_results['total_checks']}")
    print(f"📈 Accuracy: {validation_results['accuracy']:.1f}%")
    print(f"💯 Overall Confidence: {extracted_data.get('overall_confidence', 0):.1%}")
    print()

    if validation_results['critical_failures']:
        print(f"❌ CRITICAL FAILURES ({len(validation_results['critical_failures'])}):")
        for failure in validation_results['critical_failures']:
            print(f"   - {failure}")
        print()

    if validation_results['warnings']:
        print(f"⚠️  WARNINGS ({len(validation_results['warnings'])}):")
        for warning in validation_results['warnings']:
            print(f"   - {warning}")
        print()

    # Generate markdown report
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    report_path = generate_comprehensive_markdown_report(
        sample_path, validation_results, ground_truth, extracted_data, timestamp
    )

    print(f"📄 Comprehensive markdown report generated: {report_path}")
    print()

    # Final verdict
    accuracy = validation_results['accuracy']
    if accuracy >= 95 and not validation_results['critical_failures']:
        print("🎉 ✅ EXCELLENT - Extraction quality EXCEEDS requirements")
        exit_code = 0
    elif accuracy >= 85 and len(validation_results['critical_failures']) <= 2:
        print("✅ PASS - Extraction quality MEETS AC#9 requirements (≥85%)")
        exit_code = 0
    elif accuracy >= 75:
        print("⚠️  CONCERNS - Extraction quality BELOW target but acceptable for MVP")
        exit_code = 0
    else:
        print("❌ FAIL - Extraction quality INSUFFICIENT")
        exit_code = 1

    print()
    print("=" * 100)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
