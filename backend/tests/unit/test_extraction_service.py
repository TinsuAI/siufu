"""
Unit tests for ExtractionService (Story 3.7)
"""
from src.schemas.ocr import KeyValuePair, OCRResult
from src.services.extraction_service import ExtractionService


class TestExtractionService:
    """Test ExtractionService source metadata generation"""

    def test_flatten_dict_simple(self):
        """Test flattening simple nested dict"""
        data = {
            "company": {
                "name": "ABC Corp",
                "address": "123 Main St"
            }
        }

        flat = ExtractionService._flatten_dict(data)

        assert flat == {
            "company.name": "ABC Corp",
            "company.address": "123 Main St"
        }

    def test_flatten_dict_with_lists(self):
        """Test flattening dict with lists"""
        data = {
            "products": [
                {"name": "Widget", "price": 10.99},
                {"name": "Gadget", "price": 20.99}
            ]
        }

        flat = ExtractionService._flatten_dict(data)

        assert flat == {
            "products.0.name": "Widget",
            "products.0.price": 10.99,
            "products.1.name": "Gadget",
            "products.1.price": 20.99
        }

    def test_find_value_in_ocr_exact_match(self):
        """Test finding exact match in OCR entities"""
        ocr_result = OCRResult(
            text="Test document",
            key_value_pairs=[
                KeyValuePair(
                    key="company_name",
                    value="ABC Corporation",
                    confidence=0.95,
                    page=1,
                    bbox=[0.1, 0.2, 0.3, 0.05]
                )
            ],
            tables=[],
            confidence_scores={},
            page_count=1,
            file_name="test.pdf",
            processing_time_ms=100
        )

        ocr_results = {"INVOICE": ocr_result}

        result = ExtractionService._find_value_in_ocr(
            "ABC Corporation",
            ocr_results
        )

        assert result is not None
        assert result["source"] == "INVOICE"
        assert result["page"] == 1
        assert result["bbox"] == [0.1, 0.2, 0.3, 0.05]

    def test_find_value_in_ocr_substring_match(self):
        """Test finding substring match in OCR entities"""
        ocr_result = OCRResult(
            text="Test document",
            key_value_pairs=[
                KeyValuePair(
                    key="total_amount",
                    value="USD $23,208.80 (including tax)",
                    confidence=0.92,
                    page=2,
                    bbox=[0.5, 0.6, 0.2, 0.03]
                )
            ],
            tables=[],
            confidence_scores={},
            page_count=2,
            file_name="invoice.pdf",
            processing_time_ms=150
        )

        ocr_results = {"INVOICE": ocr_result}

        # Search for just the numeric value
        result = ExtractionService._find_value_in_ocr(
            "$23,208.80",
            ocr_results
        )

        assert result is not None
        assert result["source"] == "INVOICE"
        assert result["page"] == 2

    def test_find_value_in_ocr_not_found(self):
        """Test value not found in OCR entities"""
        ocr_result = OCRResult(
            text="Test document",
            key_value_pairs=[
                KeyValuePair(
                    key="company_name",
                    value="XYZ Inc",
                    confidence=0.95,
                    page=1,
                    bbox=[0.1, 0.2, 0.3, 0.05]
                )
            ],
            tables=[],
            confidence_scores={},
            page_count=1,
            file_name="test.pdf",
            processing_time_ms=100
        )

        ocr_results = {"INVOICE": ocr_result}

        result = ExtractionService._find_value_in_ocr(
            "ABC Corporation",  # Not in OCR
            ocr_results
        )

        assert result is None

    def test_find_value_in_ocr_case_insensitive(self):
        """Test case-insensitive matching"""
        ocr_result = OCRResult(
            text="Test document",
            key_value_pairs=[
                KeyValuePair(
                    key="vessel_name",
                    value="MSC GEMMA",
                    confidence=0.98,
                    page=1,
                    bbox=[0.2, 0.3, 0.4, 0.06]
                )
            ],
            tables=[],
            confidence_scores={},
            page_count=1,
            file_name="an.pdf",
            processing_time_ms=120
        )

        ocr_results = {"AN": ocr_result}

        # Search with different case
        result = ExtractionService._find_value_in_ocr(
            "msc gemma",
            ocr_results
        )

        assert result is not None
        assert result["source"] == "AN"

    def test_find_value_prefers_mapped_document_type(self):
        """Test that search prefers document type from field mapping"""
        # Same value in both documents
        invoice_ocr = OCRResult(
            text="Invoice doc",
            key_value_pairs=[
                KeyValuePair(
                    key="importer",
                    value="ABC Corp",
                    confidence=0.95,
                    page=1,
                    bbox=[0.1, 0.1, 0.2, 0.02]
                )
            ],
            tables=[],
            confidence_scores={},
            page_count=1,
            file_name="invoice.pdf",
            processing_time_ms=100
        )

        bol_ocr = OCRResult(
            text="BOL doc",
            key_value_pairs=[
                KeyValuePair(
                    key="importer",
                    value="ABC Corp",
                    confidence=0.90,
                    page=1,
                    bbox=[0.3, 0.3, 0.2, 0.02]
                )
            ],
            tables=[],
            confidence_scores={},
            page_count=1,
            file_name="bol.pdf",
            processing_time_ms=100
        )

        ocr_results = {"INVOICE": invoice_ocr, "BOL": bol_ocr}

        # With INVOICE preference, should find in INVOICE first
        result = ExtractionService._find_value_in_ocr(
            "ABC Corp",
            ocr_results,
            field_type_mapping="INVOICE"
        )

        assert result is not None
        assert result["source"] == "INVOICE"
        assert result["bbox"] == [0.1, 0.1, 0.2, 0.02]

    def test_build_source_metadata_full_flow(self):
        """Test full source metadata building flow"""
        extracted_data = {
            "shipper": {
                "name": "ACME Manufacturing Co., Ltd",
                "address": "123 Industrial Park, Guangzhou"
            },
            "invoice_total": 22500.00,
            "invoice_number": "INV-2025-001"
        }

        invoice_ocr = OCRResult(
            text="Invoice",
            key_value_pairs=[
                KeyValuePair(
                    key="shipper_name",
                    value="ACME Manufacturing Co., Ltd",
                    confidence=0.95,
                    page=1,
                    bbox=[0.1, 0.2, 0.3, 0.05]
                ),
                KeyValuePair(
                    key="invoice_total",
                    value="22500.0",
                    confidence=0.92,
                    page=1,
                    bbox=[0.7, 0.8, 0.15, 0.03]
                ),
                KeyValuePair(
                    key="invoice_no",
                    value="INV-2025-001",
                    confidence=0.98,
                    page=1,
                    bbox=[0.1, 0.1, 0.2, 0.02]
                )
            ],
            tables=[],
            confidence_scores={},
            page_count=1,
            file_name="invoice.pdf",
            processing_time_ms=150
        )

        ocr_results = {"INVOICE": invoice_ocr}
        field_mapping = ExtractionService.get_default_field_type_mapping()

        source_metadata = ExtractionService.build_source_metadata(
            extracted_data,
            ocr_results,
            field_mapping
        )

        # Should find all three values
        assert "shipper.name" in source_metadata
        assert source_metadata["shipper.name"]["source"] == "INVOICE"
        assert source_metadata["shipper.name"]["page"] == 1

        assert "invoice_total" in source_metadata
        assert source_metadata["invoice_total"]["source"] == "INVOICE"

        assert "invoice_number" in source_metadata
        assert source_metadata["invoice_number"]["source"] == "INVOICE"

    def test_build_source_metadata_skips_none_values(self):
        """Test that None and empty values are skipped"""
        extracted_data = {
            "shipper": {
                "name": "ACME Corp",
                "tax_id": None  # Should be skipped
            },
            "notes": ""  # Should be skipped
        }

        invoice_ocr = OCRResult(
            text="Invoice",
            key_value_pairs=[
                KeyValuePair(
                    key="shipper_name",
                    value="ACME Corp",
                    confidence=0.95,
                    page=1,
                    bbox=[0.1, 0.2, 0.3, 0.05]
                )
            ],
            tables=[],
            confidence_scores={},
            page_count=1,
            file_name="invoice.pdf",
            processing_time_ms=100
        )

        ocr_results = {"INVOICE": invoice_ocr}
        field_mapping = {}

        source_metadata = ExtractionService.build_source_metadata(
            extracted_data,
            ocr_results,
            field_mapping
        )

        # Should only find name, not tax_id or notes
        assert "shipper.name" in source_metadata
        assert "shipper.tax_id" not in source_metadata
        assert "notes" not in source_metadata
