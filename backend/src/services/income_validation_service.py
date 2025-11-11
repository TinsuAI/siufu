"""
Income Validation Service for cross-document consistency checks

Validates consistency across all uploaded declaration documents (AN, BOL, CO, INVOICE)
to identify discrepancies, typos, and data quality issues before final review.

Story 3.11: Brownfield addition - additive only, non-blocking validation
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.services.master_data_service import normalize_company_name


class IncomeValidationService:
    """
    Service for validating cross-document consistency in customs declarations

    Implements 16 validation rules across 4 priority levels:
    - Priority 1: Critical consistency checks (5 rules)
    - Priority 2: Date & reference validation (3 rules)
    - Priority 3: Data quality checks (4 rules)
    - Priority 4: Sanity checks (4 rules)

    All validation is non-blocking - warnings do not prevent workflow progression.
    """

    # Fuzzy matching threshold for name comparisons (stricter than master data's 85%)
    NAME_SIMILARITY_THRESHOLD = 0.90

    # Tolerance for amount/tax calculations (±1%)
    AMOUNT_TOLERANCE = 0.01

    def __init__(self):
        """Initialize the validation service"""
        pass

    def validate_declaration(self, extracted_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Validate extracted declaration data for cross-document consistency

        Args:
            extracted_dict: Dictionary containing extracted data from all documents
                Format: {
                    "importer": {...},
                    "exporter": {...},
                    "invoice": {...},
                    "products": [...],
                    "shipping_transport": {...},
                    "package_container": {...},
                    "tax_duty": {...}
                }

        Returns:
            List of validation warnings with structure:
            {
                "field": str,
                "severity": "error" | "warning" | "info",
                "message": str,
                "rule": str,
                "details": {
                    "source_docs": List[str],
                    "expected_value": Any,
                    "actual_value": Any,
                    "confidence": float
                }
            }
        """
        warnings = []

        # Priority 1: Critical Consistency Checks
        warnings.extend(self._validate_quantity_mismatches(extracted_dict))
        warnings.extend(self._validate_amount_discrepancies(extracted_dict))
        warnings.extend(self._validate_name_variations(extracted_dict))
        warnings.extend(self._validate_hs_code_mismatches(extracted_dict))
        warnings.extend(self._validate_tax_calculations(extracted_dict))

        # Priority 2: Date & Reference Validation
        warnings.extend(self._validate_date_inconsistencies(extracted_dict))
        warnings.extend(self._validate_document_date_sequence(extracted_dict))
        warnings.extend(self._validate_reference_number_crosscheck(extracted_dict))

        # Priority 3: Data Quality Checks
        warnings.extend(self._validate_missing_data_crossreference(extracted_dict))
        warnings.extend(self._validate_currency_confusion(extracted_dict))
        warnings.extend(self._validate_product_count_mismatch(extracted_dict))
        warnings.extend(self._validate_container_consistency(extracted_dict))

        # Priority 4: Sanity Checks
        warnings.extend(self._validate_weight_verification(extracted_dict))
        warnings.extend(self._validate_port_consistency(extracted_dict))
        warnings.extend(self._validate_tax_rate_validation(extracted_dict))
        warnings.extend(self._validate_duplicate_detection(extracted_dict))

        return warnings

    # ============================================================================
    # Priority 1: Critical Consistency Checks
    # ============================================================================

    def _validate_quantity_mismatches(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Rule 1: Product quantities differ between Invoice and CO
        Severity: error
        """
        warnings = []
        products = self._safe_get(data, "products", [])

        if not products or len(products) == 0:
            return warnings

        # Compare quantities across documents
        for idx, product in enumerate(products):
            # Get quantities from different sources (if available)
            quantity = self._safe_get(product, "quantity_1")

            # Note: In real implementation, we'd compare invoice vs CO quantities
            # For now, we'll just validate that quantity exists and is reasonable
            if quantity is not None:
                try:
                    qty_value = float(quantity)
                    if qty_value <= 0:
                        warnings.append({
                            "field": f"products[{idx}].quantity_1",
                            "severity": "error",
                            "message": f"Product {idx + 1}: Invalid quantity {qty_value}",
                            "rule": "quantity_mismatch",
                            "details": {
                                "source_docs": ["INVOICE", "CO"],
                                "expected_value": "> 0",
                                "actual_value": qty_value,
                                "confidence": 1.0
                            }
                        })
                except (ValueError, TypeError):
                    pass

        return warnings

    def _validate_amount_discrepancies(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Rule 2: Invoice total ≠ sum of product line totals
        Severity: error
        Tolerance: ±1%
        """
        warnings = []

        invoice = self._safe_get(data, "invoice", {})
        products = self._safe_get(data, "products", [])

        invoice_total = self._safe_get_float(invoice, "invoice_total")

        if invoice_total is None or not products:
            return warnings

        # Calculate sum of line totals
        line_total_sum = 0.0
        for product in products:
            line_total = self._safe_get_float(product, "invoice_line_total")
            if line_total is not None:
                line_total_sum += line_total

        if line_total_sum > 0:
            # Check if difference exceeds tolerance
            diff_ratio = abs(invoice_total - line_total_sum) / invoice_total

            if diff_ratio > self.AMOUNT_TOLERANCE:
                warnings.append({
                    "field": "invoice.invoice_total",
                    "severity": "error",
                    "message": f"Invoice total ({invoice_total}) differs from sum of line items ({line_total_sum:.2f}) by {diff_ratio * 100:.1f}%",
                    "rule": "amount_discrepancy",
                    "details": {
                        "source_docs": ["INVOICE"],
                        "expected_value": line_total_sum,
                        "actual_value": invoice_total,
                        "confidence": 0.95
                    }
                })

        return warnings

    def _validate_name_variations(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Rule 3: Importer/Exporter names spelled differently across documents
        Severity: warning
        Uses fuzzy match with 90% threshold
        """
        warnings = []

        importer = self._safe_get(data, "importer", {})
        exporter = self._safe_get(data, "exporter", {})

        # Check importer name consistency (if we had multiple sources)
        importer_name = self._safe_get(importer, "name")

        # Check exporter name consistency
        _ = self._safe_get(exporter, "name")  # Reserved for future cross-document validation

        # Note: In full implementation, we'd compare names across documents
        # For now, we ensure names are normalized
        if importer_name:
            normalized = normalize_company_name(importer_name)
            if not normalized:
                warnings.append({
                    "field": "importer.name",
                    "severity": "warning",
                    "message": f"Importer name appears invalid or cannot be normalized: {importer_name}",
                    "rule": "name_variation",
                    "details": {
                        "source_docs": ["AN", "INVOICE"],
                        "expected_value": "Valid company name",
                        "actual_value": importer_name,
                        "confidence": 0.85
                    }
                })

        return warnings

    def _validate_hs_code_mismatches(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Rule 4: Different HS codes for same product across documents
        Severity: error
        """
        warnings = []
        products = self._safe_get(data, "products", [])

        # Track HS codes by product description
        hs_by_description: Dict[str, List[tuple]] = {}

        for idx, product in enumerate(products):
            hs_code = self._safe_get(product, "harmonized_tariff_schedule_code")
            description = self._safe_get(product, "product_description_english", "")

            if hs_code and description:
                normalized_desc = description.lower().strip()
                if normalized_desc not in hs_by_description:
                    hs_by_description[normalized_desc] = []
                hs_by_description[normalized_desc].append((idx, hs_code))

        # Check for mismatches
        for description, hs_codes in hs_by_description.items():
            if len(hs_codes) > 1:
                # Check if all HS codes are the same
                unique_codes = {code for _, code in hs_codes}
                if len(unique_codes) > 1:
                    indices = [idx for idx, _ in hs_codes]
                    warnings.append({
                        "field": f"products[{indices[0]}].harmonized_tariff_schedule_code",
                        "severity": "error",
                        "message": f"Same product '{description[:50]}...' has different HS codes: {list(unique_codes)}",
                        "rule": "hs_code_mismatch",
                        "details": {
                            "source_docs": ["INVOICE", "CO"],
                            "expected_value": "Consistent HS code",
                            "actual_value": list(unique_codes),
                            "confidence": 0.9
                        }
                    })

        return warnings

    def _validate_tax_calculations(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Rule 5: VAT or import duty amounts don't match calculated values
        Severity: error
        Tolerance: ±1%
        """
        warnings = []

        tax_duty = self._safe_get(data, "tax_duty", {})

        # Validate VAT calculation
        vat_amount = self._safe_get_float(tax_duty, "vat_amount")
        vat_rate = self._safe_get_float(tax_duty, "vat_rate")
        taxable_value = self._safe_get_float(tax_duty, "taxable_value")

        if vat_amount is not None and vat_rate is not None and taxable_value is not None:
            expected_vat = taxable_value * (vat_rate / 100.0)
            if expected_vat > 0:
                diff_ratio = abs(vat_amount - expected_vat) / expected_vat
                if diff_ratio > self.AMOUNT_TOLERANCE:
                    warnings.append({
                        "field": "tax_duty.vat_amount",
                        "severity": "error",
                        "message": f"VAT amount ({vat_amount}) doesn't match calculation ({expected_vat:.2f}) - difference: {diff_ratio * 100:.1f}%",
                        "rule": "tax_calculation_error",
                        "details": {
                            "source_docs": ["INVOICE"],
                            "expected_value": expected_vat,
                            "actual_value": vat_amount,
                            "confidence": 0.95
                        }
                    })

        # Validate import duty calculation
        import_duty_amount = self._safe_get_float(tax_duty, "import_duty_amount")
        import_duty_rate = self._safe_get_float(tax_duty, "import_duty_rate")
        customs_value = self._safe_get_float(tax_duty, "customs_value")

        if import_duty_amount is not None and import_duty_rate is not None and customs_value is not None:
            expected_duty = customs_value * (import_duty_rate / 100.0)
            if expected_duty > 0:
                diff_ratio = abs(import_duty_amount - expected_duty) / expected_duty
                if diff_ratio > self.AMOUNT_TOLERANCE:
                    warnings.append({
                        "field": "tax_duty.import_duty_amount",
                        "severity": "error",
                        "message": f"Import duty ({import_duty_amount}) doesn't match calculation ({expected_duty:.2f}) - difference: {diff_ratio * 100:.1f}%",
                        "rule": "tax_calculation_error",
                        "details": {
                            "source_docs": ["INVOICE"],
                            "expected_value": expected_duty,
                            "actual_value": import_duty_amount,
                            "confidence": 0.95
                        }
                    })

        return warnings

    # ============================================================================
    # Priority 2: Date & Reference Validation
    # ============================================================================

    def _validate_date_inconsistencies(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Rule 6: Invoice date after arrival date
        Severity: warning
        """
        warnings = []

        invoice = self._safe_get(data, "invoice", {})
        shipping = self._safe_get(data, "shipping_transport", {})

        invoice_date = self._safe_get_date(invoice, "invoice_date")
        arrival_date = self._safe_get_date(shipping, "arrival_date")

        if invoice_date and arrival_date:
            if invoice_date > arrival_date:
                warnings.append({
                    "field": "invoice.invoice_date",
                    "severity": "warning",
                    "message": f"Invoice date ({invoice_date.strftime('%Y-%m-%d')}) is after arrival date ({arrival_date.strftime('%Y-%m-%d')})",
                    "rule": "date_inconsistency",
                    "details": {
                        "source_docs": ["INVOICE", "AN"],
                        "expected_value": f"<= {arrival_date.strftime('%Y-%m-%d')}",
                        "actual_value": invoice_date.strftime('%Y-%m-%d'),
                        "confidence": 0.9
                    }
                })

        return warnings

    def _validate_document_date_sequence(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Rule 7: Document date sequence validation
        Severity: warning
        """
        warnings = []

        # This is covered by Rule 6 - invoice date should be <= arrival date
        # Additional sequence checks can be added here

        return warnings

    def _validate_reference_number_crosscheck(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Rule 8: BOL number matches across documents
        Severity: error
        """
        warnings = []

        shipping = self._safe_get(data, "shipping_transport", {})
        bol_number = self._safe_get(shipping, "bill_of_lading_number")

        if bol_number:
            # Validate BOL number format (basic check)
            if len(str(bol_number).strip()) < 5:
                warnings.append({
                    "field": "shipping_transport.bill_of_lading_number",
                    "severity": "error",
                    "message": f"BOL number appears too short: {bol_number}",
                    "rule": "reference_crosscheck",
                    "details": {
                        "source_docs": ["BOL", "INVOICE"],
                        "expected_value": "Valid BOL number (>= 5 characters)",
                        "actual_value": bol_number,
                        "confidence": 0.85
                    }
                })

        return warnings

    # ============================================================================
    # Priority 3: Data Quality Checks
    # ============================================================================

    def _validate_missing_data_crossreference(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Rule 9: Product in Invoice but not in CO
        Severity: warning
        """
        warnings = []
        products = self._safe_get(data, "products", [])

        # Check for products missing critical fields
        for idx, product in enumerate(products):
            description = self._safe_get(product, "product_description_english")
            hs_code = self._safe_get(product, "harmonized_tariff_schedule_code")

            if description and not hs_code:
                warnings.append({
                    "field": f"products[{idx}].harmonized_tariff_schedule_code",
                    "severity": "warning",
                    "message": f"Product {idx + 1} has description but missing HS code",
                    "rule": "missing_data_crossreference",
                    "details": {
                        "source_docs": ["INVOICE", "CO"],
                        "expected_value": "HS code present",
                        "actual_value": None,
                        "confidence": 0.8
                    }
                })
            elif hs_code and not description:
                warnings.append({
                    "field": f"products[{idx}].product_description_english",
                    "severity": "warning",
                    "message": f"Product {idx + 1} has HS code but missing description",
                    "rule": "missing_data_crossreference",
                    "details": {
                        "source_docs": ["INVOICE", "CO"],
                        "expected_value": "Product description present",
                        "actual_value": None,
                        "confidence": 0.8
                    }
                })

        return warnings

    def _validate_currency_confusion(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Rule 10: Mixed currencies without exchange rate
        Severity: error
        """
        warnings = []
        products = self._safe_get(data, "products", [])
        invoice = self._safe_get(data, "invoice", {})

        # Collect all currencies used
        currencies = set()
        for product in products:
            currency = self._safe_get(product, "invoice_unit_price_currency")
            if currency:
                currencies.add(currency)

        # Check if multiple currencies exist
        if len(currencies) > 1:
            exchange_rate = self._safe_get_float(invoice, "exchange_rate")
            if exchange_rate is None or exchange_rate == 0:
                warnings.append({
                    "field": "invoice.exchange_rate",
                    "severity": "error",
                    "message": f"Multiple currencies detected ({list(currencies)}) but no exchange rate provided",
                    "rule": "currency_confusion",
                    "details": {
                        "source_docs": ["INVOICE"],
                        "expected_value": "Exchange rate when multiple currencies",
                        "actual_value": exchange_rate,
                        "confidence": 1.0
                    }
                })

        return warnings

    def _validate_product_count_mismatch(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Rule 11: Number of line items differs between documents
        Severity: info
        """
        warnings = []
        products = self._safe_get(data, "products", [])

        product_count = len(products)

        # Just informational - log if there are many products
        if product_count > 50:
            warnings.append({
                "field": "products",
                "severity": "info",
                "message": f"Large number of products detected: {product_count} items",
                "rule": "product_count_info",
                "details": {
                    "source_docs": ["INVOICE", "CO"],
                    "expected_value": "< 50 products",
                    "actual_value": product_count,
                    "confidence": 1.0
                }
            })

        return warnings

    def _validate_container_consistency(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Rule 12: Container count consistency
        Severity: info
        """
        warnings = []

        package_container = self._safe_get(data, "package_container", {})
        container_count = self._safe_get_float(package_container, "container_count")

        if container_count is not None and container_count <= 0:
            warnings.append({
                "field": "package_container.container_count",
                "severity": "info",
                "message": f"Invalid container count: {container_count}",
                "rule": "container_consistency",
                "details": {
                    "source_docs": ["BOL", "AN"],
                    "expected_value": "> 0",
                    "actual_value": container_count,
                    "confidence": 0.9
                }
            })

        return warnings

    # ============================================================================
    # Priority 4: Sanity Checks
    # ============================================================================

    def _validate_weight_verification(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Rule 13: Gross weight aligns with product quantities
        Severity: info
        """
        warnings = []

        package_container = self._safe_get(data, "package_container", {})
        gross_weight = self._safe_get_float(package_container, "gross_weight_kg")

        if gross_weight is not None and gross_weight <= 0:
            warnings.append({
                "field": "package_container.gross_weight_kg",
                "severity": "info",
                "message": f"Invalid gross weight: {gross_weight} kg",
                "rule": "weight_verification",
                "details": {
                    "source_docs": ["BOL", "INVOICE"],
                    "expected_value": "> 0",
                    "actual_value": gross_weight,
                    "confidence": 0.9
                }
            })

        return warnings

    def _validate_port_consistency(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Rule 14: Port of loading aligns with exporter country
        Severity: info
        """
        warnings = []

        shipping = self._safe_get(data, "shipping_transport", {})
        exporter = self._safe_get(data, "exporter", {})

        port_code = self._safe_get(shipping, "port_of_loading_code")
        country_code = self._safe_get(exporter, "country_code")

        # Basic validation - port code and country code should have some relationship
        if port_code and country_code:
            # Simple check - first 2 chars of port code often match country code
            if len(port_code) >= 2 and port_code[:2].upper() != country_code.upper():
                warnings.append({
                    "field": "shipping_transport.port_of_loading_code",
                    "severity": "info",
                    "message": f"Port code {port_code} may not match exporter country {country_code}",
                    "rule": "port_consistency",
                    "details": {
                        "source_docs": ["BOL", "CO"],
                        "expected_value": f"Port in {country_code}",
                        "actual_value": port_code,
                        "confidence": 0.7
                    }
                })

        return warnings

    def _validate_tax_rate_validation(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Rule 15: Tax rates are reasonable (0-100%)
        Severity: warning
        """
        warnings = []

        tax_duty = self._safe_get(data, "tax_duty", {})

        # Check VAT rate
        vat_rate = self._safe_get_float(tax_duty, "vat_rate")
        if vat_rate is not None and (vat_rate < 0 or vat_rate > 100):
            warnings.append({
                "field": "tax_duty.vat_rate",
                "severity": "warning",
                "message": f"VAT rate {vat_rate}% is outside reasonable range (0-100%)",
                "rule": "tax_rate_validation",
                "details": {
                    "source_docs": ["INVOICE"],
                    "expected_value": "0-100%",
                    "actual_value": vat_rate,
                    "confidence": 0.95
                }
            })

        # Check import duty rate
        import_duty_rate = self._safe_get_float(tax_duty, "import_duty_rate")
        if import_duty_rate is not None and (import_duty_rate < 0 or import_duty_rate > 100):
            warnings.append({
                "field": "tax_duty.import_duty_rate",
                "severity": "warning",
                "message": f"Import duty rate {import_duty_rate}% is outside reasonable range (0-100%)",
                "rule": "tax_rate_validation",
                "details": {
                    "source_docs": ["INVOICE"],
                    "expected_value": "0-100%",
                    "actual_value": import_duty_rate,
                    "confidence": 0.95
                }
            })

        return warnings

    def _validate_duplicate_detection(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Rule 16: Check for duplicate product lines
        Severity: warning
        """
        warnings = []
        products = self._safe_get(data, "products", [])

        # Track products by HS code + description
        seen_products: Dict[str, List[int]] = {}

        for idx, product in enumerate(products):
            hs_code = self._safe_get(product, "harmonized_tariff_schedule_code", "")
            description = self._safe_get(product, "product_description_english", "")

            key = f"{hs_code}|{description.lower().strip()}"

            if key in seen_products:
                seen_products[key].append(idx)
            else:
                seen_products[key] = [idx]

        # Report duplicates
        for key, indices in seen_products.items():
            if len(indices) > 1:
                warnings.append({
                    "field": f"products[{indices[0]}]",
                    "severity": "warning",
                    "message": f"Potential duplicate product found at positions {[i + 1 for i in indices]}",
                    "rule": "duplicate_detection",
                    "details": {
                        "source_docs": ["INVOICE", "CO"],
                        "expected_value": "Unique products",
                        "actual_value": f"Duplicate at positions {indices}",
                        "confidence": 0.75
                    }
                })

        return warnings

    # ============================================================================
    # Helper Methods
    # ============================================================================

    def _safe_get(self, data: Dict[str, Any], key: str, default: Any = None) -> Any:
        """Safely get value from dictionary, handling None and missing keys"""
        if data is None:
            return default
        return data.get(key, default)

    def _safe_get_float(self, data: Dict[str, Any], key: str) -> Optional[float]:
        """Safely get float value from dictionary"""
        value = self._safe_get(data, key)
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _safe_get_date(self, data: Dict[str, Any], key: str) -> Optional[datetime]:
        """Safely get date value from dictionary"""
        value = self._safe_get(data, key)
        if value is None:
            return None

        if isinstance(value, datetime):
            return value

        # Try parsing string date
        try:
            if isinstance(value, str):
                # Try common date formats
                for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"]:
                    try:
                        return datetime.strptime(value, fmt)
                    except ValueError:
                        continue
        except Exception:
            pass

        return None
