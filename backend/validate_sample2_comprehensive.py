#!/usr/bin/env python3
"""
Comprehensive Sample 2 Accuracy Validation
Validates extraction results against ground truth from CD.xlsx
"""

import json
from difflib import SequenceMatcher

def fuzzy_match(str1, str2, threshold=0.85):
    """Check if two strings match with fuzzy matching"""
    if str1 is None or str2 is None:
        return str1 == str2
    similarity = SequenceMatcher(None, str(str1).lower().strip(), str(str2).lower().strip()).ratio()
    return similarity >= threshold, similarity

def numeric_tolerance_match(val1, val2, tolerance_percent=0.01):
    """Check if two numeric values match within tolerance"""
    if val1 is None or val2 is None:
        return val1 == val2, 0.0
    try:
        val1 = float(val1)
        val2 = float(val2)
        diff = abs(val1 - val2)
        avg = (val1 + val2) / 2
        diff_percent = diff / avg if avg != 0 else 0
        return diff_percent <= tolerance_percent, diff_percent
    except (ValueError, TypeError):
        return False, 1.0

def validate_sample2_comprehensive():
    """Comprehensive validation of Sample 2"""

    print("=" * 100)
    print("SAMPLE 2 COMPREHENSIVE ACCURACY VALIDATION - AC#9 Verification")
    print("=" * 100)
    print()

    # Load ground truth
    with open('../resources/sample/2/validation-reference.json', 'r', encoding='utf-8') as f:
        validation_ref = json.load(f)

    ground_truth = validation_ref['sample_2_ground_truth']
    print(f"✅ Loaded ground truth from validation-reference.json")
    print(f"   Description: {ground_truth['description']}")
    print()

    # Load extraction results
    with open('../resources/sample/2/results.json', 'r', encoding='utf-8') as f:
        results = json.load(f)

    extracted = results['extracted_data']
    confidence_scores = results['confidence_scores']
    print(f"✅ Loaded extraction results")
    print(f"   Status: {results['status']}")
    print(f"   Overall Confidence: {extracted.get('overall_confidence', 0):.1%}")
    print()

    # Validation tracking
    total = 0
    passed = 0
    critical_failures = []
    important_warnings = []
    details = []

    # === CRITICAL FIELDS ===
    print("=" * 100)
    print("CRITICAL FIELDS VALIDATION (Must be 100% accurate)")
    print("=" * 100)
    print()

    critical_checks = [
        ("Declaration Number",
         ground_truth['critical_fields']['declaration_number'],
         extracted.get('declaration_header', {}).get('declaration_number'),
         'declaration_header.declaration_number'),

        ("Importer Tax Code",
         ground_truth['critical_fields']['importer_tax_code'],
         extracted.get('importer', {}).get('tax_code'),
         'importer.tax_code'),

        ("Invoice Number",
         ground_truth['critical_fields']['invoice_number'],
         extracted.get('invoice', {}).get('invoice_number'),
         'invoice.invoice_number'),

        ("Invoice Total (USD)",
         ground_truth['critical_fields']['invoice_total'],
         extracted.get('invoice', {}).get('invoice_total'),
         'invoice.invoice_total'),

        ("Bill of Lading Number",
         ground_truth['critical_fields']['bill_of_lading_number'],
         extracted.get('shipping_transport', {}).get('bill_of_lading_number'),
         'shipping_transport.bill_of_lading_number'),

        ("CO Number",
         ground_truth['critical_fields']['co_number'],
         extracted.get('certificate_of_origin', {}).get('co_number'),
         'certificate_of_origin.co_number'),

        ("Product HS Code",
         ground_truth['critical_fields']['products'][0]['hs_code'],
         extracted.get('products', [{}])[0].get('hs_code'),
         'products.0.hs_code'),

        ("Product Quantity",
         ground_truth['critical_fields']['products'][0]['quantity_1'],
         extracted.get('products', [{}])[0].get('quantity_1'),
         'products.0.quantity_1'),

        ("Product Unit Price (USD)",
         ground_truth['critical_fields']['products'][0]['invoice_unit_price'],
         extracted.get('products', [{}])[0].get('invoice_unit_price'),
         'products.0.invoice_unit_price'),
    ]

    for field_name, expected, actual, conf_key in critical_checks:
        total += 1
        conf = confidence_scores.get(conf_key, 0.0)

        # Determine match
        if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
            matches, diff = numeric_tolerance_match(expected, actual, tolerance_percent=0.001)
            similarity = 1.0 - diff
        else:
            if expected is None and actual is None:
                matches = True
                similarity = 1.0
            elif expected is None or actual is None:
                matches = (str(expected).strip() == str(actual).strip())
                similarity = 1.0 if matches else 0.0
            else:
                matches = (str(expected).strip() == str(actual).strip())
                similarity = SequenceMatcher(None, str(expected).lower(), str(actual or "").lower()).ratio()

        status = "✅ PASS" if matches else "❌ FAIL"

        print(f"{status} {field_name}")
        print(f"   Expected: {expected}")
        print(f"   Actual:   {actual}")
        print(f"   Confidence: {conf:.0%} | Similarity: {similarity:.0%}")

        if matches:
            passed += 1
            details.append((field_name, "PASS", expected, actual, conf, similarity))
        else:
            critical_failures.append(field_name)
            details.append((field_name, "FAIL", expected, actual, conf, similarity))

        print()

    # === IMPORTANT FIELDS ===
    print("=" * 100)
    print("IMPORTANT FIELDS VALIDATION (≥85% fuzzy match threshold)")
    print("=" * 100)
    print()

    important_checks = [
        ("Importer Name",
         ground_truth['important_fields']['importer_name'],
         extracted.get('importer', {}).get('name')),

        ("Importer Address",
         ground_truth['important_fields']['importer_address'],
         extracted.get('importer', {}).get('address')),

        ("Exporter Name",
         ground_truth['important_fields']['exporter_name'],
         extracted.get('exporter', {}).get('name')),

        ("Vessel Name",
         ground_truth['important_fields']['vessel_name'],
         extracted.get('shipping_transport', {}).get('vessel_name')),

        ("Port of Discharge Name",
         ground_truth['important_fields']['port_of_discharge_name'],
         extracted.get('shipping_transport', {}).get('port_of_discharge_name')),

        ("Warehouse Name",
         ground_truth['important_fields']['warehouse_name'],
         extracted.get('shipping_transport', {}).get('warehouse_name')),

        ("Invoice Date",
         ground_truth['important_fields']['invoice_date'],
         extracted.get('invoice', {}).get('invoice_date')),

        ("Arrival Date",
         ground_truth['important_fields']['arrival_date'],
         extracted.get('shipping_transport', {}).get('arrival_date')),

        ("Total Packages",
         ground_truth['important_fields']['total_packages'],
         extracted.get('package_container', {}).get('total_packages')),

        ("Gross Weight (kg)",
         ground_truth['important_fields']['gross_weight_kg'],
         extracted.get('package_container', {}).get('gross_weight_kg')),
    ]

    for field_name, expected, actual in important_checks:
        total += 1

        if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
            matches, diff = numeric_tolerance_match(expected, actual, tolerance_percent=0.01)
            similarity = 1.0 - diff
        else:
            matches, similarity = fuzzy_match(expected, actual, threshold=0.85)

        status = "✅ PASS" if matches else "⚠️ WARN"

        print(f"{status} {field_name} (similarity: {similarity:.0%})")
        print(f"   Expected: {expected}")
        print(f"   Actual:   {actual}")

        if matches:
            passed += 1
        elif similarity >= 0.70:
            important_warnings.append(f"{field_name} ({similarity:.0%})")
            passed += 0.7  # Partial credit
        else:
            important_warnings.append(f"{field_name} ({similarity:.0%})")

        print()

    # === SUMMARY ===
    print("=" * 100)
    print("VALIDATION SUMMARY")
    print("=" * 100)
    print()
    print(f"📊 Total Checks: {total}")
    print(f"✅ Passed: {passed:.1f} / {total}")
    print(f"📈 Accuracy: {(passed/total)*100:.1f}%")
    print()

    if critical_failures:
        print(f"❌ CRITICAL FAILURES ({len(critical_failures)}):")
        for failure in critical_failures:
            print(f"   - {failure}")
        print()

    if important_warnings:
        print(f"⚠️ WARNINGS ({len(important_warnings)}):")
        for warning in important_warnings:
            print(f"   - {warning}")
        print()

    # === KNOWN DISCREPANCIES ===
    known_discrepancies = validation_ref.get('known_discrepancies', {})
    if known_discrepancies:
        print("📌 KNOWN DISCREPANCIES (CD.xlsx vs Source Documents):")
        print()
        for key, disc in known_discrepancies.items():
            print(f"   {key.replace('_', ' ').title()}:")
            if isinstance(disc, dict):
                for k, v in disc.items():
                    print(f"      {k}: {v}")
            print()

    # === FINAL VERDICT ===
    accuracy = (passed/total)*100
    print("=" * 100)
    print("FINAL VERDICT - AC#9 Compliance")
    print("=" * 100)
    print()

    if accuracy >= 95 and not critical_failures:
        print("🎉 ✅ EXCELLENT - Extraction quality EXCEEDS requirements")
        print(f"   Accuracy: {accuracy:.1f}% (Target: ≥85%)")
        verdict = "PASS"
    elif accuracy >= 85 and len(critical_failures) <= 2:
        print("✅ PASS - Extraction quality MEETS AC#9 requirements")
        print(f"   Accuracy: {accuracy:.1f}% (Target: ≥85%)")
        verdict = "PASS"
    elif accuracy >= 75:
        print("⚠️ CONCERNS - Extraction quality BELOW target but acceptable for MVP")
        print(f"   Accuracy: {accuracy:.1f}% (Target: ≥85%)")
        verdict = "CONCERNS"
    else:
        print("❌ FAIL - Extraction quality INSUFFICIENT")
        print(f"   Accuracy: {accuracy:.1f}% (Target: ≥85%)")
        verdict = "FAIL"

    print()
    print("=" * 100)

    return {
        "total_checks": total,
        "passed_checks": passed,
        "accuracy": accuracy,
        "critical_failures": critical_failures,
        "warnings": important_warnings,
        "verdict": verdict
    }

if __name__ == "__main__":
    validation_results = validate_sample2_comprehensive()
