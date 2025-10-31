#!/usr/bin/env python3
"""
LLM Extraction Results Validation Tool

Validates extraction results from results.json against manually-curated expected-results.json
Handles schema translation between camelCase (expected) and snake_case (results)
Generates visual markdown validation reports with color-coded status

Usage:
    python3 validate_extraction_results.py <sample_folder_path>

Example:
    python3 validate_extraction_results.py ../resources/sample/1

Output:
    - Console: Summary statistics
    - File: resources/sample/{N}/validation-report-{timestamp}.md

Created: 2025-10-27
Story: 1.7.1 (LLM Extraction Results Validation Against Expected Results)
Author: Product Manager (John) via Sprint Change Proposal
"""

import json
import sys
import argparse
import re
from pathlib import Path
from difflib import SequenceMatcher
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional


# =============================================================================
# FIELD MAPPING: camelCase (expected-results.json) → snake_case (results.json)
# =============================================================================

FIELD_MAPPING = {
    # Declaration Header
    "declarationHeader": "declaration_header",
    "declarationNumber": "declaration_number",
    "correspondingTempImportExportDeclNo": "corresponding_temp_import_export_decl_no",
    "inspectionClassificationCode": "inspection_classification_code",
    "firstDeclarationNumber": "first_declaration_number",
    "receivingCustomsAgencyName": "receiving_customs_agency_name",
    "typeCode": "type_code",
    "representativeHScode": "representative_hs_code",
    "processingDivisionCode": "processing_division_code",
    "registrationDate": "registration_date",
    "registrationChangeDate": "registration_change_date",
    "reimportExportDeadline": "reimport_export_deadline",

    # Importer
    "importer.code": "importer.tax_code",
    "importer.name": "importer.name",
    "importer.postalCode": "importer.postal_code",
    "importer.address": "importer.address",
    "importer.phone": "importer.phone",

    # Import Trustor
    "importTrustor.code": "import_trustor.code",
    "importTrustor.name": "import_trustor.name",

    # Exporter
    "exporter.code": "exporter.code",
    "exporter.name": "exporter.name",
    "exporter.postalCode": "exporter.postal_code",
    "exporter.address": "exporter.address",
    "exporter.countryCode": "exporter.country_code",

    # Export Trustor
    "exportTrustor.name": "export_trustor.name",

    # Customs Agent
    "customsAgent.name": "customs_agent.name",

    # Transport Details
    "transportDetails.billOfLadingNumbers": "shipping_transport.bill_of_lading_number",
    "transportDetails.quantityPackages": "package_container.total_packages",
    "transportDetails.quantityPackagesUnit": "package_container.package_unit",
    "transportDetails.grossWeight": "package_container.gross_weight_kg",
    "transportDetails.grossWeightUnit": "package_container.gross_weight_unit",
    "transportDetails.containerCount": "package_container.container_count",
    "transportDetails.customsOfficerCode": "customs_officer_code",
    "transportDetails.storageLocation": "shipping_transport.warehouse_code",
    "transportDetails.portOfDischarge": "shipping_transport.port_of_discharge_name",
    "transportDetails.portOfLoading": "shipping_transport.port_of_loading_name",
    "transportDetails.transportMode": "shipping_transport.transport_mode_code",
    "transportDetails.vesselName": "shipping_transport.vessel_name",
    "transportDetails.arrivalDate": "shipping_transport.arrival_date",

    # Invoice (both invoice and invoiceDetails map to same fields)
    "invoice.invoiceNumber": "invoice.invoice_number",
    "invoice.invoiceDate": "invoice.invoice_date",
    "invoice.paymentMethod": "invoice.payment_method_code",
    "invoice.totalValue": "invoice.invoice_total",
    "invoice.currency": "invoice.invoice_currency",
    "invoice.incoterm": "invoice.invoice_incoterm",
    "invoice.exchangeRate": "invoice.exchange_rate",

    # InvoiceDetails (from expected-results.json) → invoice (in results.json)
    "invoiceDetails.invoiceNumber": "invoice.invoice_number",
    "invoiceDetails.issueDate": "invoice.invoice_date",
    "invoiceDetails.paymentMethod": "invoice.payment_method_code",
    "invoiceDetails.totalInvoiceValue": "invoice.invoice_total",
    "invoiceDetails.currency": "invoice.invoice_currency",
    "invoiceDetails.incoterms": "invoice.invoice_incoterm",
    "invoiceDetails.exchangeRate": "invoice.exchange_rate",

    # Certificate of Origin
    "certificateOfOrigin.formType": "certificate_of_origin.co_form_type",
    "certificateOfOrigin.number": "certificate_of_origin.co_number",
    "certificateOfOrigin.issueDate": "certificate_of_origin.co_date",

    # Products (array fields - handle specially)
    "products.itemNumber": "products.item_number",
    "products.hsCode": "products.hs_code",
    "products.description": "products.product_description",
    "products.quantity": "products.quantity_1",
    "products.quantityUnit": "products.quantity_unit_1",
    "products.unitPrice": "products.invoice_unit_price",
    "products.currency": "products.invoice_unit_price_currency",
    "products.totalValue": "products.invoice_line_total",
    "products.originCountry": "products.country_of_origin_code",
    "products.manufacturer": "products.manufacturer_name",
    "products.brand": "products.brand_name",

    # Tax
    "tax.importDuty.rate": "import_duty.rate",
    "tax.importDuty.amount": "import_duty.amount",
    "tax.vat.rate": "vat.rate",
    "tax.vat.amount": "vat.amount",
    "tax.totalTaxAmount": "tax_summary.total_tax_amount_vnd",
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def camel_to_snake(name: str) -> str:
    """Convert camelCase to snake_case."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def get_nested_value(data: dict, path: str) -> Any:
    """
    Get nested value from dict using dot notation path.

    Example: get_nested_value(data, "importer.name") → data["importer"]["name"]
    """
    keys = path.split('.')
    value = data
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
            if value is None:
                return None
        else:
            return None
    return value


def fuzzy_match(str1: Any, str2: Any, threshold: float = 0.85) -> Tuple[bool, float]:
    """
    Check if two strings match with fuzzy matching.

    Returns:
        (matches, similarity_score)
    """
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


def numeric_tolerance_match(val1: Any, val2: Any, tolerance_percent: float = 0.01) -> Tuple[bool, float]:
    """
    Check if two numeric values match within tolerance.

    Returns:
        (matches, similarity_score)
    """
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


# =============================================================================
# LOADING FUNCTIONS
# =============================================================================

def load_expected_results(sample_path: Path) -> dict:
    """
    Load expected-results.json (ground truth, camelCase schema).

    Args:
        sample_path: Path to sample folder

    Returns:
        Expected results dict (with declarationHeader wrapper flattened)

    Raises:
        FileNotFoundError: If expected-results.json doesn't exist
    """
    expected_path = sample_path / "expected-results.json"

    if not expected_path.exists():
        raise FileNotFoundError(
            f"Expected results file not found: {expected_path}\n"
            f"Please create expected-results.json in the sample folder."
        )

    with open(expected_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

        # expected-results.json is an array, extract first element
        if isinstance(data, list) and len(data) > 0:
            data = data[0]

        # Flatten declarationHeader wrapper if present
        # expected-results.json has structure:
        #   { "declarationHeader": { ...header fields... }, "items": [...] }
        # results.json has structure:
        #   { ...header fields..., "products": [...] }
        # We need to flatten expected-results to match results structure
        if "declarationHeader" in data:
            # Extract contents of declarationHeader to root level
            header_data = data["declarationHeader"]
            # Preserve any fields outside declarationHeader (items, etc.)
            flattened = {k: v for k, v in data.items() if k != "declarationHeader"}
            # Merge header data into root
            flattened.update(header_data)

            # Also rename 'items' to 'products' if present to match results.json schema
            if "items" in flattened:
                flattened["products"] = flattened.pop("items")

            return flattened

        return data


def load_extraction_results(sample_path: Path) -> dict:
    """
    Load results.json (LLM extraction output, snake_case schema).

    Args:
        sample_path: Path to sample folder

    Returns:
        Extraction results dict

    Raises:
        FileNotFoundError: If results.json doesn't exist
    """
    results_path = sample_path / "results.json"

    if not results_path.exists():
        raise FileNotFoundError(
            f"Results file not found: {results_path}\n"
            f"Please run LLM extraction first to generate results.json."
        )

    with open(results_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

        # results.json may have extracted_data wrapper
        if "extracted_data" in data:
            return data["extracted_data"]

        return data


# =============================================================================
# COMPARISON LOGIC
# =============================================================================

def compare_field(expected_val: Any, actual_val: Any, field_name: str) -> Dict[str, Any]:
    """
    Compare a single field with appropriate matching strategy.

    Returns:
        {
            "field": field_name,
            "expected": expected_val,
            "actual": actual_val,
            "status": "PASS" | "PARTIAL" | "FAIL" | "MISSING",
            "similarity": 0.0-1.0
        }
    """
    # Determine field type and matching strategy
    # Check is_code first as it takes precedence (e.g., 'quantityUnit' is code, not numeric)
    is_code = any(keyword in field_name.lower() for keyword in [
        'code', 'number', 'hs_code', 'tax_code', 'currency', 'unit', 'itemnumber'
    ])

    is_numeric = any(keyword in field_name.lower() for keyword in [
        'quantity', 'weight', 'price', 'value', 'amount', 'rate', 'total', 'count'
    ]) and not is_code  # Exclude if already identified as code

    # Missing values
    if expected_val is None and actual_val is None:
        return {
            "field": field_name,
            "expected": expected_val,
            "actual": actual_val,
            "status": "PASS",
            "similarity": 1.0,
            "note": "Both null (acceptable)"
        }

    if expected_val is None:
        return {
            "field": field_name,
            "expected": expected_val,
            "actual": actual_val,
            "status": "PASS",
            "similarity": 1.0,
            "note": "Expected null (optional field)"
        }

    if actual_val is None:
        return {
            "field": field_name,
            "expected": expected_val,
            "actual": actual_val,
            "status": "MISSING",
            "similarity": 0.0,
            "note": "Missing in extraction results"
        }

    # Numeric comparison
    if is_numeric:
        matches, similarity = numeric_tolerance_match(expected_val, actual_val)
        if matches:
            status = "PASS"
        elif similarity >= 0.95:
            status = "PARTIAL"
        else:
            status = "FAIL"

        return {
            "field": field_name,
            "expected": expected_val,
            "actual": actual_val,
            "status": status,
            "similarity": similarity
        }

    # Exact match for codes
    if is_code:
        # Special handling: "01" should match 1, "02" should match 2, etc.
        # But only for numeric codes, not alphabetic ones like "USD", "CN"
        expected_str = str(expected_val).strip()
        actual_str = str(actual_val).strip()

        # If both are numeric-like (can have leading zeros), normalize
        if expected_str.isdigit() or actual_str.isdigit():
            expected_normalized = expected_str.lstrip('0') or '0'
            actual_normalized = actual_str.lstrip('0') or '0'
            matches = expected_normalized == actual_normalized
        else:
            # Otherwise, case-insensitive comparison for alphabetic codes
            matches = expected_str.upper() == actual_str.upper()

        return {
            "field": field_name,
            "expected": expected_val,
            "actual": actual_val,
            "status": "PASS" if matches else "FAIL",
            "similarity": 1.0 if matches else 0.0
        }

    # Fuzzy match for text fields
    matches, similarity = fuzzy_match(expected_val, actual_val)
    if matches:
        status = "PASS"
    elif similarity >= 0.70:
        status = "PARTIAL"
    else:
        status = "FAIL"

    return {
        "field": field_name,
        "expected": expected_val,
        "actual": actual_val,
        "status": status,
        "similarity": similarity
    }


def compare_all_fields(expected: dict, actual: dict) -> List[Dict[str, Any]]:
    """
    Compare all fields between expected and actual results.

    Returns:
        List of comparison results
    """
    results = []

    # Helper to flatten nested dicts
    def flatten_dict(d: dict, parent_key: str = '') -> dict:
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}.{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(flatten_dict(v, new_key).items())
            elif isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                # Handle product arrays - compare first product
                for i, item in enumerate(v[:3]):  # Compare first 3 items
                    items.extend(flatten_dict(item, f"{new_key}[{i}]").items())
            else:
                items.append((new_key, v))
        return dict(items)

    expected_flat = flatten_dict(expected)
    actual_flat = flatten_dict(actual)

    # Special handling for multi-line address fields
    # Combine address_line1, address_line2, address_line3 into single address
    for parent in ['exporter', 'importer']:
        address_lines = []
        for i in [1, 2, 3]:
            line_key = f"{parent}.address_line{i}"
            if line_key in actual_flat and actual_flat[line_key]:
                address_lines.append(str(actual_flat[line_key]))
        if address_lines:
            actual_flat[f"{parent}.address"] = ", ".join(address_lines)

    # Compare all expected fields
    for expected_key, expected_val in expected_flat.items():
        # Try to find matching actual key
        actual_key = None
        actual_val = None

        # Direct match (if schemas aligned)
        if expected_key in actual_flat:
            actual_key = expected_key
            actual_val = actual_flat[expected_key]
        else:
            # Try field mapping
            mapped_key = FIELD_MAPPING.get(expected_key)
            if mapped_key and mapped_key in actual_flat:
                actual_key = mapped_key
                actual_val = actual_flat[mapped_key]
            else:
                # Try camelCase to snake_case conversion
                snake_key = camel_to_snake(expected_key)
                if snake_key in actual_flat:
                    actual_key = snake_key
                    actual_val = actual_flat[snake_key]

        # Compare field
        comparison = compare_field(expected_val, actual_val, expected_key)
        if actual_key and actual_key != expected_key:
            comparison["mapped_to"] = actual_key
        results.append(comparison)

    # Find extra fields in actual (not in expected)
    expected_keys = set(expected_flat.keys())
    actual_keys = set(actual_flat.keys())
    extra_keys = actual_keys - expected_keys

    for extra_key in extra_keys:
        results.append({
            "field": extra_key,
            "expected": None,
            "actual": actual_flat[extra_key],
            "status": "EXTRA",
            "similarity": 0.0,
            "note": "Present in results but not in expected (may be calculated field)"
        })

    return results


# =============================================================================
# MARKDOWN REPORT GENERATION
# =============================================================================

def generate_markdown_report(
    comparison_results: List[Dict[str, Any]],
    sample_name: str,
    output_path: Path
):
    """
    Generate visual markdown validation report.

    Args:
        comparison_results: List of field comparison results
        sample_name: Sample folder name (e.g., "1", "2", "3")
        output_path: Path to save markdown file
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Calculate statistics
    total_fields = len([r for r in comparison_results if r["status"] != "EXTRA"])
    pass_count = len([r for r in comparison_results if r["status"] == "PASS"])
    partial_count = len([r for r in comparison_results if r["status"] == "PARTIAL"])
    fail_count = len([r for r in comparison_results if r["status"] == "FAIL"])
    missing_count = len([r for r in comparison_results if r["status"] == "MISSING"])
    extra_count = len([r for r in comparison_results if r["status"] == "EXTRA"])

    accuracy = (pass_count / total_fields * 100) if total_fields > 0 else 0

    # Generate markdown
    md = []
    md.append(f"# Validation Report: Sample {sample_name}")
    md.append(f"")
    md.append(f"**Generated:** {timestamp}")
    md.append(f"")
    md.append(f"---")
    md.append(f"")
    md.append(f"## Summary")
    md.append(f"")
    md.append(f"| Metric | Count | Percentage |")
    md.append(f"|--------|-------|------------|")
    md.append(f"| **Total Fields** | {total_fields} | 100% |")
    md.append(f"| ✅ **PASS** | {pass_count} | {pass_count/total_fields*100:.1f}% |")
    md.append(f"| ⚠️ **PARTIAL** | {partial_count} | {partial_count/total_fields*100:.1f}% |")
    md.append(f"| ❌ **FAIL** | {fail_count} | {fail_count/total_fields*100:.1f}% |")
    md.append(f"| 🔴 **MISSING** | {missing_count} | {missing_count/total_fields*100:.1f}% |")
    md.append(f"| ➕ **EXTRA** | {extra_count} | - |")
    md.append(f"")
    md.append(f"**Overall Accuracy:** {accuracy:.1f}%")
    md.append(f"")
    md.append(f"---")
    md.append(f"")

    # Status legend
    md.append(f"## Status Legend")
    md.append(f"")
    md.append(f"- ✅ **PASS**: Field matches exactly (or within tolerance)")
    md.append(f"- ⚠️ **PARTIAL**: Field partially matches (fuzzy match 70-85%)")
    md.append(f"- ❌ **FAIL**: Field does not match expected value")
    md.append(f"- 🔴 **MISSING**: Field missing in extraction results")
    md.append(f"- ➕ **EXTRA**: Field present in results but not expected")
    md.append(f"")
    md.append(f"---")
    md.append(f"")

    # Detailed comparison by status
    for status_name, status_filter, emoji in [
        ("Critical Failures", "FAIL", "❌"),
        ("Missing Fields", "MISSING", "🔴"),
        ("Partial Matches", "PARTIAL", "⚠️"),
        ("Passed Fields", "PASS", "✅"),
        ("Extra Fields", "EXTRA", "➕"),
    ]:
        filtered = [r for r in comparison_results if r["status"] == status_filter]

        if not filtered:
            continue

        md.append(f"## {emoji} {status_name} ({len(filtered)})")
        md.append(f"")
        md.append(f"| Field | Expected | Actual | Similarity | Notes |")
        md.append(f"|-------|----------|--------|------------|-------|")

        for result in filtered:
            field = result["field"]
            expected = result["expected"]
            actual = result["actual"]
            similarity = result.get("similarity", 0.0)
            note = result.get("note", "")

            # Truncate long values
            expected_str = str(expected)[:50] + "..." if len(str(expected)) > 50 else str(expected)
            actual_str = str(actual)[:50] + "..." if len(str(actual)) > 50 else str(actual)

            similarity_str = f"{similarity:.0%}" if similarity is not None else "-"
            note_str = note if note else "-"

            md.append(f"| `{field}` | {expected_str} | {actual_str} | {similarity_str} | {note_str} |")

        md.append(f"")

    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))

    return accuracy, output_path


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Validate LLM extraction results against expected results"
    )
    parser.add_argument(
        "sample_path",
        type=str,
        help="Path to sample folder (e.g., ../resources/sample/1)"
    )

    args = parser.parse_args()
    sample_path = Path(args.sample_path).resolve()

    if not sample_path.exists():
        print(f"❌ Error: Sample path does not exist: {sample_path}")
        sys.exit(1)

    sample_name = sample_path.name

    print(f"🔍 Validating Sample {sample_name}")
    print(f"📁 Sample path: {sample_path}")
    print("")

    # Load files
    try:
        print("📥 Loading expected-results.json...")
        expected = load_expected_results(sample_path)
        print(f"   ✅ Loaded expected results")
    except FileNotFoundError as e:
        print(f"   ❌ {e}")
        sys.exit(1)

    try:
        print("📥 Loading results.json...")
        actual = load_extraction_results(sample_path)
        print(f"   ✅ Loaded extraction results")
    except FileNotFoundError as e:
        print(f"   ❌ {e}")
        sys.exit(1)

    print("")

    # Compare fields
    print("🔄 Comparing fields...")
    comparison_results = compare_all_fields(expected, actual)
    print(f"   ✅ Compared {len(comparison_results)} fields")
    print("")

    # Generate report
    timestamp_str = datetime.now().strftime("%Y%m%d-%H%M%S")
    report_path = sample_path / f"validation-report-{timestamp_str}.md"

    print("📝 Generating markdown report...")
    accuracy, report_path = generate_markdown_report(
        comparison_results,
        sample_name,
        report_path
    )
    print(f"   ✅ Report saved: {report_path}")
    print("")

    # Print summary
    print("=" * 60)
    print(f"✅ Validation Complete: Sample {sample_name}")
    print("=" * 60)
    print(f"Overall Accuracy: {accuracy:.1f}%")
    print(f"Report: {report_path}")
    print("")

    # Exit code based on critical field accuracy
    critical_failures = len([r for r in comparison_results if r["status"] == "FAIL"])
    if critical_failures > 0:
        print(f"⚠️ Warning: {critical_failures} critical field failures")
        sys.exit(1)
    else:
        print("✅ All critical fields passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
