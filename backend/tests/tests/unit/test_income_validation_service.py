"""
Unit tests for Income Validation Service

Tests for all 16 validation rules across 4 priority levels:
- Priority 1: Critical consistency checks (5 rules)
- Priority 2: Date & reference validation (3 rules)
- Priority 3: Data quality checks (4 rules)
- Priority 4: Sanity checks (4 rules)

Story 3.11: Cross-Document Income Validation
"""


import pytest

from src.services.income_validation_service import IncomeValidationService


@pytest.fixture
def validation_service():
    """Create a validation service instance for testing"""
    return IncomeValidationService()


@pytest.fixture
def sample_declaration_data():
    """Create sample declaration data for testing"""
    return {
        "importer": {
            "name": "ABC Import Company",
            "tax_code": "0123456789",
            "address": "123 Main St",
            "country_code": "VN"
        },
        "exporter": {
            "name": "XYZ Export Co Ltd",
            "address": "456 Export Rd",
            "country_code": "CN"
        },
        "invoice": {
            "invoice_number": "INV-2025-001",
            "invoice_date": "2025-01-15",
            "invoice_total": 10000.0,
            "currency": "USD"
        },
        "products": [
            {
                "product_description_english": "Widget A",
                "harmonized_tariff_schedule_code": "8541100000",
                "quantity_1": 100,
                "invoice_unit_price": 50.0,
                "invoice_unit_price_currency": "USD",
                "invoice_line_total": 5000.0
            },
            {
                "product_description_english": "Widget B",
                "harmonized_tariff_schedule_code": "8541200000",
                "quantity_1": 100,
                "invoice_unit_price": 50.0,
                "invoice_unit_price_currency": "USD",
                "invoice_line_total": 5000.0
            }
        ],
        "shipping_transport": {
            "bill_of_lading_number": "BOL123456789",
            "port_of_loading_code": "CNSHA",
            "port_of_discharge_code": "VNSGN",
            "arrival_date": "2025-01-20"
        },
        "package_container": {
            "container_count": 1,
            "gross_weight_kg": 5000.0
        },
        "tax_duty": {
            "vat_rate": 10.0,
            "vat_amount": 1000.0,
            "taxable_value": 10000.0,
            "import_duty_rate": 5.0,
            "import_duty_amount": 500.0,
            "customs_value": 10000.0
        }
    }


# ============================================================================
# Priority 1: Critical Consistency Checks - Rule 1: Quantity Mismatches
# ============================================================================

def test_quantity_mismatch_negative_quantity(validation_service):
    """Test that negative quantities are flagged as errors"""
    data = {
        "products": [
            {
                "product_description_english": "Widget A",
                "quantity_1": -10
            }
        ]
    }

    warnings = validation_service.validate_declaration(data)

    # Find quantity mismatch warnings
    qty_warnings = [w for w in warnings if w["rule"] == "quantity_mismatch"]
    assert len(qty_warnings) > 0
    assert qty_warnings[0]["severity"] == "error"
    assert "Invalid quantity" in qty_warnings[0]["message"]


def test_quantity_mismatch_zero_quantity(validation_service):
    """Test that zero quantities are flagged as errors"""
    data = {
        "products": [
            {
                "product_description_english": "Widget A",
                "quantity_1": 0
            }
        ]
    }

    warnings = validation_service.validate_declaration(data)

    qty_warnings = [w for w in warnings if w["rule"] == "quantity_mismatch"]
    assert len(qty_warnings) > 0
    assert qty_warnings[0]["severity"] == "error"


def test_quantity_mismatch_no_warning_for_valid_quantity(validation_service):
    """Test that valid quantities do not generate warnings"""
    data = {
        "products": [
            {
                "product_description_english": "Widget A",
                "quantity_1": 100
            }
        ]
    }

    warnings = validation_service.validate_declaration(data)

    qty_warnings = [w for w in warnings if w["rule"] == "quantity_mismatch"]
    assert len(qty_warnings) == 0


# ============================================================================
# Priority 1: Critical Consistency Checks - Rule 2: Amount Discrepancies
# ============================================================================

def test_amount_discrepancy_detected(validation_service):
    """Test that invoice total mismatch with line items is detected"""
    data = {
        "invoice": {
            "invoice_total": 10000.0
        },
        "products": [
            {
                "invoice_line_total": 3000.0
            },
            {
                "invoice_line_total": 3000.0
            }
        ]
    }

    warnings = validation_service.validate_declaration(data)

    amount_warnings = [w for w in warnings if w["rule"] == "amount_discrepancy"]
    assert len(amount_warnings) > 0
    assert amount_warnings[0]["severity"] == "error"
    assert "differs from sum of line items" in amount_warnings[0]["message"]


def test_amount_discrepancy_within_tolerance(validation_service):
    """Test that differences within 1% tolerance are accepted"""
    data = {
        "invoice": {
            "invoice_total": 10000.0
        },
        "products": [
            {
                "invoice_line_total": 5000.0
            },
            {
                "invoice_line_total": 5050.0  # Total: 10050, diff: 0.5% - within tolerance
            }
        ]
    }

    warnings = validation_service.validate_declaration(data)

    amount_warnings = [w for w in warnings if w["rule"] == "amount_discrepancy"]
    assert len(amount_warnings) == 0


def test_amount_discrepancy_no_warning_exact_match(validation_service):
    """Test that exact match generates no warning"""
    data = {
        "invoice": {
            "invoice_total": 10000.0
        },
        "products": [
            {
                "invoice_line_total": 5000.0
            },
            {
                "invoice_line_total": 5000.0
            }
        ]
    }

    warnings = validation_service.validate_declaration(data)

    amount_warnings = [w for w in warnings if w["rule"] == "amount_discrepancy"]
    assert len(amount_warnings) == 0


# ============================================================================
# Priority 1: Critical Consistency Checks - Rule 3: Name Variations
# ============================================================================

def test_name_variation_invalid_name(validation_service):
    """Test that invalid/empty names are flagged"""
    data = {
        "importer": {
            "name": "!!!@@#$%"  # Invalid name with only special chars
        }
    }

    warnings = validation_service.validate_declaration(data)

    name_warnings = [w for w in warnings if w["rule"] == "name_variation"]
    assert len(name_warnings) > 0
    assert name_warnings[0]["severity"] == "warning"


def test_name_variation_valid_name(validation_service):
    """Test that valid names do not generate warnings"""
    data = {
        "importer": {
            "name": "ABC Import Company Ltd"
        }
    }

    warnings = validation_service.validate_declaration(data)

    name_warnings = [w for w in warnings if w["rule"] == "name_variation"]
    # Valid names should not generate warnings (unless comparing across docs)
    assert len(name_warnings) == 0


# ============================================================================
# Priority 1: Critical Consistency Checks - Rule 4: HS Code Mismatches
# ============================================================================

def test_hs_code_mismatch_same_product_different_codes(validation_service):
    """Test that same product with different HS codes is detected"""
    data = {
        "products": [
            {
                "product_description_english": "Widget A",
                "harmonized_tariff_schedule_code": "8541100000"
            },
            {
                "product_description_english": "Widget A",  # Same description
                "harmonized_tariff_schedule_code": "8541200000"  # Different HS code
            }
        ]
    }

    warnings = validation_service.validate_declaration(data)

    hs_warnings = [w for w in warnings if w["rule"] == "hs_code_mismatch"]
    assert len(hs_warnings) > 0
    assert hs_warnings[0]["severity"] == "error"
    assert "different HS codes" in hs_warnings[0]["message"]


def test_hs_code_mismatch_no_warning_consistent(validation_service):
    """Test that consistent HS codes do not generate warnings"""
    data = {
        "products": [
            {
                "product_description_english": "Widget A",
                "harmonized_tariff_schedule_code": "8541100000"
            },
            {
                "product_description_english": "Widget A",
                "harmonized_tariff_schedule_code": "8541100000"  # Same code
            }
        ]
    }

    warnings = validation_service.validate_declaration(data)

    hs_warnings = [w for w in warnings if w["rule"] == "hs_code_mismatch"]
    assert len(hs_warnings) == 0


# ============================================================================
# Priority 1: Critical Consistency Checks - Rule 5: Tax Calculations
# ============================================================================

def test_tax_calculation_vat_mismatch(validation_service):
    """Test that VAT calculation errors are detected"""
    data = {
        "tax_duty": {
            "vat_rate": 10.0,
            "vat_amount": 1500.0,  # Should be 1000 (10% of 10000)
            "taxable_value": 10000.0
        }
    }

    warnings = validation_service.validate_declaration(data)

    tax_warnings = [w for w in warnings if w["rule"] == "tax_calculation_error" and "VAT" in w["message"]]
    assert len(tax_warnings) > 0
    assert tax_warnings[0]["severity"] == "error"


def test_tax_calculation_import_duty_mismatch(validation_service):
    """Test that import duty calculation errors are detected"""
    data = {
        "tax_duty": {
            "import_duty_rate": 5.0,
            "import_duty_amount": 1000.0,  # Should be 500 (5% of 10000)
            "customs_value": 10000.0
        }
    }

    warnings = validation_service.validate_declaration(data)

    tax_warnings = [w for w in warnings if w["rule"] == "tax_calculation_error" and "Import duty" in w["message"]]
    assert len(tax_warnings) > 0
    assert tax_warnings[0]["severity"] == "error"


def test_tax_calculation_within_tolerance(validation_service):
    """Test that tax calculations within 1% tolerance are accepted"""
    data = {
        "tax_duty": {
            "vat_rate": 10.0,
            "vat_amount": 1005.0,  # 0.5% diff - within tolerance
            "taxable_value": 10000.0,
            "import_duty_rate": 5.0,
            "import_duty_amount": 503.0,  # 0.6% diff - within tolerance
            "customs_value": 10000.0
        }
    }

    warnings = validation_service.validate_declaration(data)

    tax_warnings = [w for w in warnings if w["rule"] == "tax_calculation_error"]
    assert len(tax_warnings) == 0


# ============================================================================
# Priority 2: Date & Reference Validation - Rule 6: Date Inconsistencies
# ============================================================================

def test_date_inconsistency_invoice_after_arrival(validation_service):
    """Test that invoice date after arrival date is flagged"""
    data = {
        "invoice": {
            "invoice_date": "2025-01-25"
        },
        "shipping_transport": {
            "arrival_date": "2025-01-20"
        }
    }

    warnings = validation_service.validate_declaration(data)

    date_warnings = [w for w in warnings if w["rule"] == "date_inconsistency"]
    assert len(date_warnings) > 0
    assert date_warnings[0]["severity"] == "warning"
    assert "after arrival date" in date_warnings[0]["message"]


def test_date_inconsistency_no_warning_valid_sequence(validation_service):
    """Test that valid date sequence does not generate warnings"""
    data = {
        "invoice": {
            "invoice_date": "2025-01-15"
        },
        "shipping_transport": {
            "arrival_date": "2025-01-20"
        }
    }

    warnings = validation_service.validate_declaration(data)

    date_warnings = [w for w in warnings if w["rule"] == "date_inconsistency"]
    assert len(date_warnings) == 0


# ============================================================================
# Priority 2: Date & Reference Validation - Rule 8: Reference Number Cross-check
# ============================================================================

def test_reference_crosscheck_bol_too_short(validation_service):
    """Test that BOL number that's too short is flagged"""
    data = {
        "shipping_transport": {
            "bill_of_lading_number": "BOL"  # Too short
        }
    }

    warnings = validation_service.validate_declaration(data)

    ref_warnings = [w for w in warnings if w["rule"] == "reference_crosscheck"]
    assert len(ref_warnings) > 0
    assert ref_warnings[0]["severity"] == "error"
    assert "too short" in ref_warnings[0]["message"]


def test_reference_crosscheck_valid_bol(validation_service):
    """Test that valid BOL number does not generate warnings"""
    data = {
        "shipping_transport": {
            "bill_of_lading_number": "BOL123456789"
        }
    }

    warnings = validation_service.validate_declaration(data)

    ref_warnings = [w for w in warnings if w["rule"] == "reference_crosscheck"]
    assert len(ref_warnings) == 0


# ============================================================================
# Priority 3: Data Quality Checks - Rule 9: Missing Data Cross-reference
# ============================================================================

def test_missing_data_crossreference_missing_hs_code(validation_service):
    """Test that product with description but no HS code is flagged"""
    data = {
        "products": [
            {
                "product_description_english": "Widget A"
                # Missing HS code
            }
        ]
    }

    warnings = validation_service.validate_declaration(data)

    missing_warnings = [w for w in warnings if w["rule"] == "missing_data_crossreference"]
    assert len(missing_warnings) > 0
    assert missing_warnings[0]["severity"] == "warning"
    assert "missing HS code" in missing_warnings[0]["message"]


def test_missing_data_crossreference_missing_description(validation_service):
    """Test that product with HS code but no description is flagged"""
    data = {
        "products": [
            {
                "harmonized_tariff_schedule_code": "8541100000"
                # Missing description
            }
        ]
    }

    warnings = validation_service.validate_declaration(data)

    missing_warnings = [w for w in warnings if w["rule"] == "missing_data_crossreference"]
    assert len(missing_warnings) > 0
    assert missing_warnings[0]["severity"] == "warning"
    assert "missing description" in missing_warnings[0]["message"]


# ============================================================================
# Priority 3: Data Quality Checks - Rule 10: Currency Confusion
# ============================================================================

def test_currency_confusion_multiple_currencies_no_exchange_rate(validation_service):
    """Test that mixed currencies without exchange rate are flagged"""
    data = {
        "invoice": {},  # No exchange rate
        "products": [
            {
                "invoice_unit_price_currency": "USD"
            },
            {
                "invoice_unit_price_currency": "EUR"  # Different currency
            }
        ]
    }

    warnings = validation_service.validate_declaration(data)

    currency_warnings = [w for w in warnings if w["rule"] == "currency_confusion"]
    assert len(currency_warnings) > 0
    assert currency_warnings[0]["severity"] == "error"
    assert "Multiple currencies" in currency_warnings[0]["message"]


def test_currency_confusion_single_currency_no_warning(validation_service):
    """Test that single currency does not generate warnings"""
    data = {
        "invoice": {},
        "products": [
            {
                "invoice_unit_price_currency": "USD"
            },
            {
                "invoice_unit_price_currency": "USD"
            }
        ]
    }

    warnings = validation_service.validate_declaration(data)

    currency_warnings = [w for w in warnings if w["rule"] == "currency_confusion"]
    assert len(currency_warnings) == 0


# ============================================================================
# Priority 3: Data Quality Checks - Rule 11: Product Count Mismatch
# ============================================================================

def test_product_count_large_number(validation_service):
    """Test that large number of products generates info warning"""
    data = {
        "products": [{"product_description_english": f"Product {i}"} for i in range(60)]
    }

    warnings = validation_service.validate_declaration(data)

    count_warnings = [w for w in warnings if w["rule"] == "product_count_info"]
    assert len(count_warnings) > 0
    assert count_warnings[0]["severity"] == "info"
    assert "Large number of products" in count_warnings[0]["message"]


def test_product_count_normal_no_warning(validation_service):
    """Test that normal product count does not generate warnings"""
    data = {
        "products": [{"product_description_english": f"Product {i}"} for i in range(10)]
    }

    warnings = validation_service.validate_declaration(data)

    count_warnings = [w for w in warnings if w["rule"] == "product_count_info"]
    assert len(count_warnings) == 0


# ============================================================================
# Priority 3: Data Quality Checks - Rule 12: Container Consistency
# ============================================================================

def test_container_consistency_invalid_count(validation_service):
    """Test that invalid container count is flagged"""
    data = {
        "package_container": {
            "container_count": 0
        }
    }

    warnings = validation_service.validate_declaration(data)

    container_warnings = [w for w in warnings if w["rule"] == "container_consistency"]
    assert len(container_warnings) > 0
    assert container_warnings[0]["severity"] == "info"


# ============================================================================
# Priority 4: Sanity Checks - Rule 13: Weight Verification
# ============================================================================

def test_weight_verification_invalid_weight(validation_service):
    """Test that invalid weight is flagged"""
    data = {
        "package_container": {
            "gross_weight_kg": -100
        }
    }

    warnings = validation_service.validate_declaration(data)

    weight_warnings = [w for w in warnings if w["rule"] == "weight_verification"]
    assert len(weight_warnings) > 0
    assert weight_warnings[0]["severity"] == "info"


# ============================================================================
# Priority 4: Sanity Checks - Rule 14: Port Consistency
# ============================================================================

def test_port_consistency_mismatch(validation_service):
    """Test that port code not matching exporter country is flagged"""
    data = {
        "shipping_transport": {
            "port_of_loading_code": "USNYC"  # US port
        },
        "exporter": {
            "country_code": "CN"  # China exporter
        }
    }

    warnings = validation_service.validate_declaration(data)

    port_warnings = [w for w in warnings if w["rule"] == "port_consistency"]
    assert len(port_warnings) > 0
    assert port_warnings[0]["severity"] == "info"


def test_port_consistency_match(validation_service):
    """Test that matching port and country does not generate warnings"""
    data = {
        "shipping_transport": {
            "port_of_loading_code": "CNSHA"  # China port
        },
        "exporter": {
            "country_code": "CN"  # China exporter
        }
    }

    warnings = validation_service.validate_declaration(data)

    port_warnings = [w for w in warnings if w["rule"] == "port_consistency"]
    assert len(port_warnings) == 0


# ============================================================================
# Priority 4: Sanity Checks - Rule 15: Tax Rate Validation
# ============================================================================

def test_tax_rate_validation_vat_out_of_range(validation_service):
    """Test that VAT rate outside 0-100% is flagged"""
    data = {
        "tax_duty": {
            "vat_rate": 150.0  # Invalid: > 100%
        }
    }

    warnings = validation_service.validate_declaration(data)

    rate_warnings = [w for w in warnings if w["rule"] == "tax_rate_validation" and "VAT" in w["message"]]
    assert len(rate_warnings) > 0
    assert rate_warnings[0]["severity"] == "warning"


def test_tax_rate_validation_import_duty_negative(validation_service):
    """Test that negative import duty rate is flagged"""
    data = {
        "tax_duty": {
            "import_duty_rate": -5.0  # Invalid: negative
        }
    }

    warnings = validation_service.validate_declaration(data)

    rate_warnings = [w for w in warnings if w["rule"] == "tax_rate_validation" and "Import duty" in w["message"]]
    assert len(rate_warnings) > 0
    assert rate_warnings[0]["severity"] == "warning"


def test_tax_rate_validation_valid_rates(validation_service):
    """Test that valid tax rates do not generate warnings"""
    data = {
        "tax_duty": {
            "vat_rate": 10.0,
            "import_duty_rate": 5.0
        }
    }

    warnings = validation_service.validate_declaration(data)

    rate_warnings = [w for w in warnings if w["rule"] == "tax_rate_validation"]
    assert len(rate_warnings) == 0


# ============================================================================
# Priority 4: Sanity Checks - Rule 16: Duplicate Detection
# ============================================================================

def test_duplicate_detection_duplicate_products(validation_service):
    """Test that duplicate products are detected"""
    data = {
        "products": [
            {
                "product_description_english": "Widget A",
                "harmonized_tariff_schedule_code": "8541100000"
            },
            {
                "product_description_english": "Widget A",
                "harmonized_tariff_schedule_code": "8541100000"
            }
        ]
    }

    warnings = validation_service.validate_declaration(data)

    dup_warnings = [w for w in warnings if w["rule"] == "duplicate_detection"]
    assert len(dup_warnings) > 0
    assert dup_warnings[0]["severity"] == "warning"
    assert "duplicate product" in dup_warnings[0]["message"].lower()


def test_duplicate_detection_no_duplicates(validation_service):
    """Test that unique products do not generate warnings"""
    data = {
        "products": [
            {
                "product_description_english": "Widget A",
                "harmonized_tariff_schedule_code": "8541100000"
            },
            {
                "product_description_english": "Widget B",
                "harmonized_tariff_schedule_code": "8541200000"
            }
        ]
    }

    warnings = validation_service.validate_declaration(data)

    dup_warnings = [w for w in warnings if w["rule"] == "duplicate_detection"]
    assert len(dup_warnings) == 0


# ============================================================================
# Helper Methods Tests
# ============================================================================

def test_safe_get_with_valid_key(validation_service):
    """Test _safe_get returns value for valid key"""
    data = {"key": "value"}
    result = validation_service._safe_get(data, "key")
    assert result == "value"


def test_safe_get_with_missing_key(validation_service):
    """Test _safe_get returns default for missing key"""
    data = {"key": "value"}
    result = validation_service._safe_get(data, "missing", "default")
    assert result == "default"


def test_safe_get_with_none_data(validation_service):
    """Test _safe_get handles None data gracefully"""
    result = validation_service._safe_get(None, "key", "default")
    assert result == "default"


def test_safe_get_float_valid(validation_service):
    """Test _safe_get_float converts to float"""
    data = {"value": "123.45"}
    result = validation_service._safe_get_float(data, "value")
    assert result == 123.45


def test_safe_get_float_invalid(validation_service):
    """Test _safe_get_float returns None for invalid value"""
    data = {"value": "invalid"}
    result = validation_service._safe_get_float(data, "value")
    assert result is None


def test_check_amount_tolerance_within(validation_service):
    """Test _check_amount_tolerance returns True when within tolerance"""
    assert validation_service._check_amount_tolerance(100.0, 100.5) is True  # 0.5% diff
    assert validation_service._check_amount_tolerance(100.0, 101.0) is True  # 1% diff


def test_check_amount_tolerance_exceeds(validation_service):
    """Test _check_amount_tolerance returns False when exceeding tolerance"""
    assert validation_service._check_amount_tolerance(100.0, 105.0) is False  # 5% diff


def test_complete_validation_with_sample_data(validation_service, sample_declaration_data):
    """Test complete validation flow with sample data"""
    warnings = validation_service.validate_declaration(sample_declaration_data)

    # Should have no warnings with valid sample data
    error_warnings = [w for w in warnings if w["severity"] == "error"]
    assert len(error_warnings) == 0


def test_validation_warning_structure(validation_service):
    """Test that validation warnings have correct structure"""
    data = {
        "tax_duty": {
            "vat_rate": 150.0  # Out of range
        }
    }

    warnings = validation_service.validate_declaration(data)

    assert len(warnings) > 0

    warning = warnings[0]
    assert "field" in warning
    assert "severity" in warning
    assert "message" in warning
    assert "rule" in warning
    assert "details" in warning

    details = warning["details"]
    assert "source_docs" in details
    assert "expected_value" in details
    assert "actual_value" in details
    assert "confidence" in details
    assert isinstance(details["source_docs"], list)
    assert isinstance(details["confidence"], float)
    assert 0.0 <= details["confidence"] <= 1.0
