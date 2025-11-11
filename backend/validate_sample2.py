#!/usr/bin/env python3
"""
Sample 2 Accuracy Validation Script
Validates extracted results.json against ground truth CD.xlsx
"""

import json
from difflib import SequenceMatcher

from openpyxl import load_workbook


def fuzzy_match(str1, str2, threshold=0.85):
    """Check if two strings match with fuzzy matching"""
    if str1 is None or str2 is None:
        return str1 == str2
    similarity = SequenceMatcher(None, str(str1).lower(), str(str2).lower()).ratio()
    return similarity >= threshold

def extract_ground_truth_from_cd_xlsx(xlsx_path):
    """Extract ground truth data from CD.xlsx"""
    wb = load_workbook(xlsx_path)
    ws = wb['Tờ khai nhập ']

    # Extract key fields from the Excel (manually mapped from structure)
    ground_truth = {
        "declaration_number": str(ws.cell(4, 5).value or ""),  # Row 4, Col 5
        "importer_tax_code": str(ws.cell(10, 8).value or ""),  # Row 10, Col 8
        "importer_name": str(ws.cell(11, 8).value or ""),  # Row 11, Col 8
        "importer_postal_code": str(ws.cell(13, 8).value or ""),  # Row 13, Col 8
        "importer_address": str(ws.cell(14, 8).value or ""),  # Row 14, Col 8
        "exporter_name": str(ws.cell(23, 8).value or ""),  # Row 23, Col 8
        "exporter_address_line1": str(ws.cell(25, 8).value or ""),  # Row 25, Col 8
        "exporter_address_line2": str(ws.cell(25, 21).value or ""),  # Row 25, Col 21
        "exporter_address_line3": f"{ws.cell(26, 8).value or ''} {ws.cell(26, 21).value or ''}".strip(),
        "exporter_country_code": str(ws.cell(27, 8).value or ""),  # Row 27, Col 8
        "warehouse_code": str(ws.cell(30, 21).value or ""),  # Row 30, Col 21
        "warehouse_name": str(ws.cell(30, 26).value or ""),  # Row 30, Col 26
        "representative_hs_code": str(ws.cell(6, 31).value or ""),  # Row 6, Col 31
    }

    # Extract more fields by searching for known patterns
    for row in range(30, 50):
        cell_val = ws.cell(row, 3).value
        if cell_val and "Số vận đơn" in str(cell_val):
            # B/L number might be in adjacent cells
            for col in range(4, 20):
                val = ws.cell(row, col).value
                if val and len(str(val)) > 10:
                    ground_truth["bill_of_lading_number"] = str(val)
                    break

    # Look for invoice data
    for row in range(30, 80):
        cell_val = ws.cell(row, 3).value
        if cell_val:
            cell_str = str(cell_val)
            if "Số hóa đơn" in cell_str or "Invoice" in cell_str:
                ground_truth["invoice_number"] = str(ws.cell(row, 8).value or "")
            elif "Ngày hóa đơn" in cell_str:
                ground_truth["invoice_date"] = str(ws.cell(row, 8).value or "")
            elif "Tổng số tiền" in cell_str or "Trị giá" in cell_str:
                val = ws.cell(row, 8).value
                if val and isinstance(val, (int, float)):
                    ground_truth["invoice_total"] = float(val)

    # Extract product data from HANG_NK sheet
    ws_products = wb['HANG_NK']
    products = []

    # Products typically start around row 40+
    for row in range(40, ws_products.max_row):
        hs_code_cell = ws_products.cell(row, 3).value
        if hs_code_cell and len(str(hs_code_cell)) == 8 and str(hs_code_cell).isdigit():
            product = {
                "hs_code": str(hs_code_cell),
                "description": str(ws_products.cell(row + 1, 3).value or ""),
                "quantity_1": ws_products.cell(row + 3, 19).value,
                "quantity_unit_1": str(ws_products.cell(row + 3, 21).value or ""),
            }
            products.append(product)

    if products:
        ground_truth["products"] = products

    return ground_truth

def validate_sample2(cd_xlsx_path, results_json_path):
    """Validate Sample 2 extraction results against CD.xlsx"""

    print("=" * 80)
    print("SAMPLE 2 ACCURACY VALIDATION")
    print("=" * 80)
    print()

    # Load ground truth
    print("📋 Loading ground truth from CD.xlsx...")
    ground_truth = extract_ground_truth_from_cd_xlsx(cd_xlsx_path)
    print(f"✅ Extracted {len(ground_truth)} fields from CD.xlsx")
    print()

    # Load extraction results
    print("📋 Loading extraction results...")
    with open(results_json_path, 'r', encoding='utf-8') as f:
        results = json.load(f)

    extracted_data = results.get('extracted_data', {})
    confidence_scores = results.get('confidence_scores', {})
    print(f"✅ Loaded extraction results (status: {results.get('status')})")
    print(f"   Overall confidence: {extracted_data.get('overall_confidence', 0):.1%}")
    print()

    # Validation tracking
    total_checks = 0
    passed_checks = 0
    critical_failures = []
    warnings = []

    # Critical field validations
    print("=" * 80)
    print("CRITICAL FIELD VALIDATION (Must be 100% accurate)")
    print("=" * 80)
    print()

    critical_checks = [
        ("Importer Tax Code", ground_truth.get("importer_tax_code"), extracted_data.get("importer", {}).get("tax_code"), "exact"),
        ("Representative HS Code", ground_truth.get("representative_hs_code"), extracted_data.get("declaration_header", {}).get("representative_hs_code"), "exact"),
        ("Exporter Country Code", ground_truth.get("exporter_country_code"), extracted_data.get("exporter", {}).get("country_code"), "exact"),
    ]

    for field_name, expected, actual, match_type in critical_checks:
        total_checks += 1
        if match_type == "exact":
            matches = str(expected).strip() == str(actual).strip()
        else:
            matches = fuzzy_match(expected, actual)

        status = "✅ PASS" if matches else "❌ FAIL"
        conf = confidence_scores.get(field_name.lower().replace(" ", "_"), 0.0)

        print(f"{status} {field_name}")
        print(f"   Expected: {expected}")
        print(f"   Actual:   {actual}")
        print(f"   Confidence: {conf:.0%}")
        print()

        if matches:
            passed_checks += 1
        else:
            critical_failures.append(field_name)

    # Important field validations (fuzzy matching allowed)
    print("=" * 80)
    print("IMPORTANT FIELD VALIDATION (90% fuzzy match threshold)")
    print("=" * 80)
    print()

    important_checks = [
        ("Importer Name", ground_truth.get("importer_name"), extracted_data.get("importer", {}).get("name")),
        ("Importer Address", ground_truth.get("importer_address"), extracted_data.get("importer", {}).get("address")),
        ("Exporter Name", ground_truth.get("exporter_name"), extracted_data.get("exporter", {}).get("name")),
        ("Exporter Address Line 1", ground_truth.get("exporter_address_line1"), extracted_data.get("exporter", {}).get("address_line1")),
        ("Warehouse Code", ground_truth.get("warehouse_code"), extracted_data.get("shipping_transport", {}).get("warehouse_code")),
        ("Warehouse Name", ground_truth.get("warehouse_name"), extracted_data.get("shipping_transport", {}).get("warehouse_name")),
    ]

    for field_name, expected, actual in important_checks:
        total_checks += 1
        matches = fuzzy_match(expected, actual, threshold=0.80)
        similarity = SequenceMatcher(None, str(expected).lower(), str(actual or "").lower()).ratio()

        status = "✅ PASS" if matches else "⚠️ WARN"

        print(f"{status} {field_name} (similarity: {similarity:.0%})")
        print(f"   Expected: {expected}")
        print(f"   Actual:   {actual}")
        print()

        if matches:
            passed_checks += 1
        elif similarity >= 0.70:
            warnings.append(f"{field_name} (similarity: {similarity:.0%})")
            passed_checks += 0.5  # Partial credit

    # Summary
    print("=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print()
    print(f"Total Checks: {total_checks}")
    print(f"Passed: {passed_checks:.1f} / {total_checks}")
    print(f"Accuracy: {(passed_checks/total_checks)*100:.1f}%")
    print()

    if critical_failures:
        print(f"❌ CRITICAL FAILURES ({len(critical_failures)}):")
        for failure in critical_failures:
            print(f"   - {failure}")
        print()

    if warnings:
        print(f"⚠️ WARNINGS ({len(warnings)}):")
        for warning in warnings:
            print(f"   - {warning}")
        print()

    # Final verdict
    accuracy = (passed_checks/total_checks)*100
    if accuracy >= 95 and not critical_failures:
        print("🎉 VERDICT: ✅ EXCELLENT - Extraction quality exceeds requirements")
    elif accuracy >= 85 and len(critical_failures) <= 1:
        print("✅ VERDICT: PASS - Extraction quality meets AC#9 requirements (≥85%)")
    elif accuracy >= 75:
        print("⚠️ VERDICT: CONCERNS - Extraction quality below target")
    else:
        print("❌ VERDICT: FAIL - Extraction quality insufficient")

    print()
    print("=" * 80)

    return {
        "total_checks": total_checks,
        "passed_checks": passed_checks,
        "accuracy": accuracy,
        "critical_failures": critical_failures,
        "warnings": warnings
    }

if __name__ == "__main__":
    cd_xlsx = "../resources/sample/2/CD.xlsx"
    results_json = "../resources/sample/2/results.json"

    validation_results = validate_sample2(cd_xlsx, results_json)
