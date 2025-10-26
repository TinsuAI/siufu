#!/usr/bin/env python3
"""
Comprehensive Sample Validation Tool
Validates ALL extraction results from results.json against ground truth from CD.xlsx
Can also generate validation-reference.json files from CD.xlsx

Usage:
    # Validate extraction results
    python3 validate_sample.py <sample_folder_path>

    # Generate validation-reference.json from CD.xlsx
    python3 validate_sample.py <sample_folder_path> --generate-reference

Examples:
    python3 validate_sample.py ../resources/sample/2
    python3 validate_sample.py ../resources/sample/1 --generate-reference
"""

import json
import sys
import argparse
from pathlib import Path
from difflib import SequenceMatcher
from datetime import datetime
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


def extract_ground_truth_from_cd_xlsx(xlsx_path):
    """Extract comprehensive ground truth data from CD.xlsx"""
    wb = load_workbook(xlsx_path)

    # Use the first sheet (sheet names vary: 'TKN', 'Tờ khai nhập ', etc.)
    ws = wb[wb.sheetnames[0]]

    print(f"   Using sheet: '{wb.sheetnames[0]}'")

    ground_truth = {}

    # Declaration Header
    ground_truth['declaration_header'] = {
        'declaration_number': str(ws.cell(4, 5).value or "") if ws.cell(4, 5).value else None,
        'representative_hs_code': str(ws.cell(6, 31).value or "") if ws.cell(6, 31).value else None,
    }

    # Importer Information
    ground_truth['importer'] = {
        'tax_code': str(ws.cell(10, 8).value or "") if ws.cell(10, 8).value else None,
        'name': str(ws.cell(11, 8).value or "") if ws.cell(11, 8).value else None,
        'postal_code': str(ws.cell(13, 8).value or "") if ws.cell(13, 8).value else None,
        'address': str(ws.cell(14, 8).value or "") if ws.cell(14, 8).value else None,
    }

    # Exporter Information
    ground_truth['exporter'] = {
        'name': str(ws.cell(23, 8).value or "") if ws.cell(23, 8).value else None,
        'address_line1': str(ws.cell(25, 8).value or "") if ws.cell(25, 8).value else None,
        'address_line2': str(ws.cell(25, 21).value or "") if ws.cell(25, 21).value else None,
        'address_line3': f"{ws.cell(26, 8).value or ''} {ws.cell(26, 21).value or ''}".strip() or None,
        'country_code': str(ws.cell(27, 8).value or "") if ws.cell(27, 8).value else None,
    }

    # Shipping/Transport
    bol_val = ws.cell(31, 4).value
    bol_number = None
    if bol_val:
        bol_str = str(bol_val)
        # Remove date prefix if present (e.g., 270925JJCXMHPALS53751 -> JJCXMHPALS53751)
        bol_number = bol_str[6:] if len(bol_str) > 15 else bol_str

    ground_truth['shipping_transport'] = {
        'warehouse_code': str(ws.cell(30, 21).value or "") if ws.cell(30, 21).value else None,
        'warehouse_name': str(ws.cell(30, 26).value or "") if ws.cell(30, 26).value else None,
        'bill_of_lading_number': bol_number,
        'vessel_name': str(ws.cell(34, 26).value or "") if ws.cell(34, 26).value else None,
        'arrival_date': str(ws.cell(35, 21).value or "") if ws.cell(35, 21).value else None,
        'port_of_loading_code': str(ws.cell(32, 8).value or "") if ws.cell(32, 8).value else None,
        'port_of_loading_name': str(ws.cell(33, 8).value or "") if ws.cell(33, 8).value else None,
        'port_of_discharge_code': str(ws.cell(32, 21).value or "") if ws.cell(32, 21).value else None,
        'port_of_discharge_name': str(ws.cell(30, 26).value or "") if ws.cell(30, 26).value else None,
    }

    # Package/Container
    packages_val = ws.cell(36, 11).value
    total_packages = None
    if packages_val:
        try:
            total_packages = float(str(packages_val).replace('.', '').replace(',', '.'))
        except:
            pass

    gross_weight_val = ws.cell(37, 11).value
    gross_weight = None
    if gross_weight_val:
        try:
            gross_weight = float(str(gross_weight_val).replace('.', '').replace(',', '.'))
        except:
            pass

    ground_truth['package_container'] = {
        'total_packages': total_packages,
        'package_unit': str(ws.cell(36, 21).value or "") if ws.cell(36, 21).value else None,
        'gross_weight_kg': gross_weight,
        'gross_weight_unit': str(ws.cell(37, 21).value or "") if ws.cell(37, 21).value else None,
        'container_count': ws.cell(38, 11).value if ws.cell(38, 11).value else None,
    }

    # Invoice
    invoice_num_val = ws.cell(41, 10).value
    invoice_number = None
    if invoice_num_val:
        # Extract invoice number (e.g., "A - LA2025-068" -> "LA2025-068")
        invoice_str = str(invoice_num_val)
        if ' - ' in invoice_str:
            invoice_number = invoice_str.split(' - ')[-1].strip()
        else:
            invoice_number = invoice_str.strip()

    invoice_total_val = ws.cell(45, 16).value
    invoice_total = None
    if invoice_total_val:
        try:
            # Handle European number format: "23.385,2" -> 23385.2
            total_str = str(invoice_total_val).replace('.', '').replace(',', '.')
            invoice_total = float(total_str)
        except:
            pass

    ground_truth['invoice'] = {
        'invoice_number': invoice_number,
        'invoice_date': str(ws.cell(42, 10).value or "") if ws.cell(42, 10).value else None,
        'invoice_total': invoice_total,
        'invoice_currency': str(ws.cell(45, 21).value or "") if ws.cell(45, 21).value else None,
        'invoice_incoterm': str(ws.cell(43, 10).value or "") if ws.cell(43, 10).value else None,
        'payment_method_code': str(ws.cell(44, 10).value or "") if ws.cell(44, 10).value else None,
        'exchange_rate': ws.cell(46, 10).value if ws.cell(46, 10).value else None,
    }

    # Certificate of Origin
    co_number_val = ws.cell(85, 10).value
    ground_truth['certificate_of_origin'] = {
        'co_number': str(co_number_val) if co_number_val else None,
        'co_date': str(ws.cell(50, 10).value or "") if ws.cell(50, 10).value else None,
        'co_form_type': str(ws.cell(49, 10).value or "") if ws.cell(49, 10).value else None,
    }

    # Products - Extract from second sheet (sheet names vary: 'HANG', 'HANG_NK', etc.)
    products = []
    try:
        # Use the second sheet for products (if it exists)
        if len(wb.sheetnames) > 1:
            ws_products = wb[wb.sheetnames[1]]
            print(f"   Using products sheet: '{wb.sheetnames[1]}'")
        else:
            raise Exception("No second sheet found for products")

        # Products typically start around row 40+
        for row in range(40, min(ws_products.max_row + 1, 200)):
            hs_code_cell = ws_products.cell(row, 3).value
            if hs_code_cell and len(str(hs_code_cell)) == 8 and str(hs_code_cell).isdigit():
                product = {
                    'item_number': len(products) + 1,
                    'hs_code': str(hs_code_cell),
                    'product_description': str(ws_products.cell(row + 1, 3).value or "") if ws_products.cell(row + 1, 3).value else None,
                    'quantity_1': ws_products.cell(row + 3, 19).value if ws_products.cell(row + 3, 19).value else None,
                    'quantity_unit_1': str(ws_products.cell(row + 3, 21).value or "") if ws_products.cell(row + 3, 21).value else None,
                    'quantity_2': ws_products.cell(row + 4, 19).value if ws_products.cell(row + 4, 19).value else None,
                    'quantity_unit_2': str(ws_products.cell(row + 4, 21).value or "") if ws_products.cell(row + 4, 21).value else None,
                    'invoice_unit_price': ws_products.cell(row + 5, 19).value if ws_products.cell(row + 5, 19).value else None,
                    'country_of_origin_code': str(ws_products.cell(row + 2, 3).value or "") if ws_products.cell(row + 2, 3).value else None,
                }
                products.append(product)
    except Exception as e:
        print(f"⚠️  Warning: Could not extract product data from HANG_NK sheet: {e}")

    ground_truth['products'] = products

    return ground_truth


def generate_validation_reference_json(sample_path, cd_xlsx_path):
    """Generate validation-reference.json file from CD.xlsx"""

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

    # Build validation reference structure
    validation_ref = {
        "description": f"Ground truth validation data for Sample {sample_name} extracted from CD.xlsx (Vietnamese Customs Declaration)",
        "created_date": datetime.now().strftime('%Y-%m-%d'),
        "source": str(cd_xlsx_path.relative_to(Path(sample_path).parent.parent)),
        "note": "These values represent the ACTUAL declared data in the official customs form CD.xlsx. Used to validate LLM extraction accuracy.",

        f"sample_{sample_name}_ground_truth": {
            "critical_fields": {
                "note": "Must be 100% accurate - these are compliance-critical",
                "declaration_number": ground_truth_data.get('declaration_header', {}).get('declaration_number'),
                "importer_tax_code": ground_truth_data.get('importer', {}).get('tax_code'),
                "invoice_number": ground_truth_data.get('invoice', {}).get('invoice_number'),
                "invoice_total": ground_truth_data.get('invoice', {}).get('invoice_total'),
                "invoice_currency": ground_truth_data.get('invoice', {}).get('invoice_currency'),
                "bill_of_lading_number": ground_truth_data.get('shipping_transport', {}).get('bill_of_lading_number'),
                "co_number": ground_truth_data.get('certificate_of_origin', {}).get('co_number'),
                "products": []
            },

            "important_fields": {
                "note": "Should be ≥90% accurate with fuzzy matching allowed",
                "importer_name": ground_truth_data.get('importer', {}).get('name'),
                "importer_postal_code": ground_truth_data.get('importer', {}).get('postal_code'),
                "importer_address": ground_truth_data.get('importer', {}).get('address'),
                "exporter_name": ground_truth_data.get('exporter', {}).get('name'),
                "exporter_country_code": ground_truth_data.get('exporter', {}).get('country_code'),
                "exporter_address_line1": ground_truth_data.get('exporter', {}).get('address_line1'),
                "exporter_address_line2": ground_truth_data.get('exporter', {}).get('address_line2'),
                "exporter_address_line3": ground_truth_data.get('exporter', {}).get('address_line3'),
                "invoice_date": ground_truth_data.get('invoice', {}).get('invoice_date'),
                "invoice_incoterm": ground_truth_data.get('invoice', {}).get('invoice_incoterm'),
                "payment_method_code": ground_truth_data.get('invoice', {}).get('payment_method_code'),
                "arrival_date": ground_truth_data.get('shipping_transport', {}).get('arrival_date'),
                "vessel_name": ground_truth_data.get('shipping_transport', {}).get('vessel_name'),
                "port_of_loading_code": ground_truth_data.get('shipping_transport', {}).get('port_of_loading_code'),
                "port_of_loading_name": ground_truth_data.get('shipping_transport', {}).get('port_of_loading_name'),
                "port_of_discharge_code": ground_truth_data.get('shipping_transport', {}).get('port_of_discharge_code'),
                "port_of_discharge_name": ground_truth_data.get('shipping_transport', {}).get('port_of_discharge_name'),
                "warehouse_code": ground_truth_data.get('shipping_transport', {}).get('warehouse_code'),
                "warehouse_name": ground_truth_data.get('shipping_transport', {}).get('warehouse_name'),
                "total_packages": ground_truth_data.get('package_container', {}).get('total_packages'),
                "package_unit": ground_truth_data.get('package_container', {}).get('package_unit'),
                "gross_weight_kg": ground_truth_data.get('package_container', {}).get('gross_weight_kg'),
                "gross_weight_unit": ground_truth_data.get('package_container', {}).get('gross_weight_unit'),
                "container_count": ground_truth_data.get('package_container', {}).get('container_count'),
                "co_date": ground_truth_data.get('certificate_of_origin', {}).get('co_date'),
                "co_form_type": ground_truth_data.get('certificate_of_origin', {}).get('co_form_type'),
                "representative_hs_code": ground_truth_data.get('declaration_header', {}).get('representative_hs_code'),
            }
        },

        "known_discrepancies": {
            "note": "These are expected differences between source documents and CD.xlsx",
            "declaration_number": "System-generated field, not extracted from source documents",
            "arrival_date": "May differ between CO issue date and actual arrival date",
            "co_number": "CD.xlsx may show internal tracking number vs official CO document number",
            "bol_number": "CD.xlsx may include date prefix that source BOL does not have"
        }
    }

    # Add products to critical fields
    products = ground_truth_data.get('products', [])
    if products:
        for product in products:
            validation_ref[f"sample_{sample_name}_ground_truth"]["critical_fields"]["products"].append({
                "item_number": product.get('item_number'),
                "hs_code": product.get('hs_code'),
                "quantity_1": product.get('quantity_1'),
                "quantity_unit_1": product.get('quantity_unit_1'),
                "quantity_2": product.get('quantity_2'),
                "quantity_unit_2": product.get('quantity_unit_2'),
                "invoice_unit_price": product.get('invoice_unit_price'),
                "country_of_origin_code": product.get('country_of_origin_code'),
            })

    # Save to validation-reference.json
    output_path = Path(sample_path) / "validation-reference.json"

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(validation_ref, f, indent=2, ensure_ascii=False)

    print(f"✅ Generated: {output_path}")
    print()
    print("Summary of extracted data:")
    print(f"  • Declaration Number: {validation_ref[f'sample_{sample_name}_ground_truth']['critical_fields']['declaration_number']}")
    print(f"  • Importer Tax Code: {validation_ref[f'sample_{sample_name}_ground_truth']['critical_fields']['importer_tax_code']}")
    print(f"  • Invoice Number: {validation_ref[f'sample_{sample_name}_ground_truth']['critical_fields']['invoice_number']}")
    print(f"  • Invoice Total: {validation_ref[f'sample_{sample_name}_ground_truth']['critical_fields']['invoice_total']}")
    print(f"  • Bill of Lading: {validation_ref[f'sample_{sample_name}_ground_truth']['critical_fields']['bill_of_lading_number']}")
    print(f"  • Products: {len(products)} item(s)")
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
    md.append(f"")
    md.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md.append(f"**Sample Path:** `{sample_path}`")
    md.append(f"**Validation Tool:** `backend/validate_sample_comprehensive.py`")
    md.append(f"")
    md.append(f"---")
    md.append(f"")

    # Executive Summary
    md.append(f"## Executive Summary")
    md.append(f"")
    md.append(f"| Metric | Value |")
    md.append(f"|--------|-------|")
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
    md.append(f"")
    md.append(f"{verdict_msg}")
    md.append(f"")
    md.append(f"---")
    md.append(f"")

    # Critical Failures
    if validation_results['critical_failures']:
        md.append(f"## ❌ Critical Failures ({len(validation_results['critical_failures'])})")
        md.append(f"")
        for failure in validation_results['critical_failures']:
            md.append(f"- {failure}")
        md.append(f"")
        md.append(f"---")
        md.append(f"")

    # Warnings
    if validation_results['warnings']:
        md.append(f"## ⚠️ Warnings ({len(validation_results['warnings'])})")
        md.append(f"")
        for warning in validation_results['warnings']:
            md.append(f"- {warning}")
        md.append(f"")
        md.append(f"---")
        md.append(f"")

    # Critical Fields Table
    md.append(f"## Detailed Validation Results")
    md.append(f"")
    md.append(f"### Critical Fields (Must be 100% accurate)")
    md.append(f"")
    md.append(f"| Field | Expected | Actual | Match | Similarity | Confidence |")
    md.append(f"|-------|----------|--------|-------|------------|------------|")

    for detail in validation_results['details']['critical']:
        icon = "✅" if detail['match'] else "❌"
        md.append(f"| {icon} {detail['field']} | `{detail['expected']}` | `{detail['actual']}` | {detail['match']} | {detail['similarity']:.0%} | {detail['confidence']:.0%} |")

    md.append(f"")

    # Important Fields Table
    md.append(f"### Important Fields (≥85% fuzzy match threshold)")
    md.append(f"")
    md.append(f"| Field | Expected | Actual | Match | Similarity | Confidence |")
    md.append(f"|-------|----------|--------|-------|------------|------------|")

    for detail in validation_results['details']['important']:
        icon = "✅" if detail['match'] else "⚠️"
        md.append(f"| {icon} {detail['field']} | `{detail['expected']}` | `{detail['actual']}` | {detail['match']} | {detail['similarity']:.0%} | {detail['confidence']:.0%} |")

    md.append(f"")

    # Products Table
    if validation_results['details']['products']:
        md.append(f"### Product Line Items")
        md.append(f"")

        for product in validation_results['details']['products']:
            md.append(f"#### Product {product['item_number']}")
            md.append(f"")
            md.append(f"| Field | Expected | Actual | Match | Similarity | Confidence |")
            md.append(f"|-------|----------|--------|-------|------------|------------|")

            for check in product['checks']:
                icon = "✅" if check['match'] else "⚠️"
                field_name = check['field'].replace(f"Product {product['item_number']} - ", "")
                md.append(f"| {icon} {field_name} | `{check['expected']}` | `{check['actual']}` | {check['match']} | {check['similarity']:.0%} | {check['confidence']:.0%} |")

            md.append(f"")

    # Full Extracted Data
    md.append(f"---")
    md.append(f"")
    md.append(f"## Complete Extracted Data")
    md.append(f"")
    md.append(f"<details>")
    md.append(f"<summary>Click to expand full extraction results</summary>")
    md.append(f"")
    md.append(f"```json")
    md.append(json.dumps(extracted_data, indent=2, ensure_ascii=False))
    md.append(f"```")
    md.append(f"")
    md.append(f"</details>")
    md.append(f"")
    md.append(f"---")
    md.append(f"")

    # Known Discrepancies
    md.append(f"## 📌 Known Discrepancies")
    md.append(f"")
    md.append(f"These discrepancies are expected due to differences between source documents and CD.xlsx:")
    md.append(f"")
    md.append(f"1. **Declaration Number**: System-generated field, not extracted from source documents")
    md.append(f"2. **CO Number**: CD.xlsx may show internal tracking number vs official CO document number")
    md.append(f"3. **Arrival Date**: May differ between CO issue date and actual arrival date")
    md.append(f"4. **Address Formatting**: Vietnamese vs English, with/without diacritics")
    md.append(f"5. **Port Names**: Different levels of specificity (port vs terminal)")
    md.append(f"")
    md.append(f"---")
    md.append(f"")

    # Metadata
    md.append(f"## Validation Metadata")
    md.append(f"")
    md.append(f"- **Tool Version:** 2.0 (Comprehensive)")
    md.append(f"- **Ground Truth Source:** CD.xlsx")
    md.append(f"- **Extraction Source:** results.json")
    md.append(f"- **Validation Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md.append(f"- **Fuzzy Match Threshold:** 85%")
    md.append(f"- **Numeric Tolerance:** ±1%")
    md.append(f"- **Fields Validated:** {validation_results['total_checks']}")
    md.append(f"")
    md.append(f"---")
    md.append(f"")
    md.append(f"*Generated by comprehensive validation tool - AC#9 Compliance Check*")

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
            print(f"✅ Loaded ground truth from validation-reference.json")
        else:
            # Fall back to extracting from CD.xlsx
            ground_truth = extract_ground_truth_from_cd_xlsx(cd_xlsx_path)
            print(f"✅ Extracted ground truth from CD.xlsx")

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

        print(f"✅ Loaded extraction results")
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
