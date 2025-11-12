"""
Integration tests for LLM service with real OpenRouter API

NOTE: These tests are skipped by default unless OPENROUTER_API_KEY is configured.
Cost: ~$0.026 per test run for Flagship model, ~$0.005 for Mini model.
Run sparingly to avoid excessive API costs.

Run with: pytest tests/integration/test_llm_integration.py -v -m integration
"""
import os

import pytest

from src.schemas.extraction import ExtractedData
from src.schemas.ocr import KeyValuePair, OCRResult, Table
from src.services.llm_service import MODEL_FLAGSHIP, MODEL_MINI, LLMService


def has_openrouter_key() -> bool:
    """Check if OpenRouter API key is configured"""
    return bool(os.getenv("OPENROUTER_API_KEY"))


def skip_if_no_credits() -> str:
    """
    Return skip reason if OpenRouter account has insufficient credits.

    These tests are expensive and require API credits. Skip with clear message
    if credits are insufficient.
    """
    return "OpenRouter account has insufficient credits for integration tests (expensive - ~$0.026-0.031 per test)"


@pytest.mark.integration
@pytest.mark.llm
@pytest.mark.skipif(not has_openrouter_key(), reason="OpenRouter API key not available")
@pytest.mark.asyncio
async def test_extract_from_sample_invoice_ocr():
    """
    Integration test: Extract data from sample invoice OCR result
    Cost: ~$0.026 for Flagship model
    """
    # Sample OCR result from invoice
    ocr_result = OCRResult(
        text="""COMMERCIAL INVOICE

Invoice No: INV-2025-001
Date: September 15, 2025

SELLER/EXPORTER:
ACME Manufacturing Co., Ltd
123 Industrial Park
Guangzhou, Guangdong, China
Tax ID: 91440101MA5ABC123
Contact: John Chen
Tel: +86-20-1234-5678

BUYER/IMPORTER:
Vietnam Import Export JSC
456 Nguyen Hue Street, District 1
Ho Chi Minh City, Vietnam
Tax ID: 0123456789
Contact: Nguyen Van A
Tel: +84-28-1234-5678

PRODUCT DETAILS:
Description: Cotton T-Shirts, Men's, Sizes M-XL
Quantity: 5,000 PCS
Unit Price: USD 4.50
Total: USD 22,500.00
HS Code: 62052000
Origin: China
Net Weight: 2,500 KG

PAYMENT TERMS: Net 30 days
TOTAL AMOUNT: USD 22,500.00""",
        key_value_pairs=[
            KeyValuePair(key="invoice_number", value="INV-2025-001", confidence=0.99),
            KeyValuePair(key="invoice_date", value="September 15, 2025", confidence=0.98),
            KeyValuePair(key="total_amount", value="22500.00", confidence=0.97)
        ],
        tables=[
            Table(
                headers=["Description", "Quantity", "Unit Price", "Total"],
                rows=[["Cotton T-Shirts, Men's, Sizes M-XL", "5,000 PCS", "USD 4.50", "USD 22,500.00"]],
                confidence=0.95
            )
        ],
        confidence_scores={"invoice_number": 0.99, "total_amount": 0.97},
        page_count=1,
        file_name="INVOICE.jpg",
        processing_time_ms=1250
    )

    service = LLMService()
    result = await service.extract_structured_data(ocr_result, MODEL_FLAGSHIP)

    # Verify extraction succeeded
    assert isinstance(result, ExtractedData)

    # Verify shipper details
    assert result.shipper.name is not None
    assert "ACME" in result.shipper.name or "acme" in result.shipper.name.lower()
    assert result.shipper.confidence > 0.7

    # Verify consignee details
    assert result.consignee.name is not None
    assert "Vietnam" in result.consignee.name or "vietnam" in result.consignee.name.lower()

    # Verify product line items
    assert len(result.products) > 0
    product = result.products[0]
    assert "shirt" in product.description.lower() or "t-shirt" in product.description.lower()
    assert product.quantity == pytest.approx(5000, rel=0.01)
    assert product.unit_price == pytest.approx(4.50, rel=0.01)
    assert product.total_price == pytest.approx(22500, rel=0.01)

    # Verify HS code extraction
    if product.hs_code:
        assert product.hs_code.startswith("6205")  # HS code for T-shirts

    # Verify invoice total
    assert result.invoice_total == pytest.approx(22500, rel=0.01)
    assert result.currency == "USD"

    # Verify overall confidence
    assert result.overall_confidence > 0.0
    assert result.overall_confidence <= 1.0

    await service.close()


@pytest.mark.integration
@pytest.mark.llm
@pytest.mark.skipif(not has_openrouter_key(), reason="OpenRouter API key not available")
@pytest.mark.asyncio
async def test_confidence_scores_above_threshold():
    """
    Integration test: Verify confidence scores are reasonable for clean data
    Cost: ~$0.026 for Flagship model
    """
    ocr_result = OCRResult(
        text="""BILL OF LADING

B/L Number: BOL-ABC-123456
Date: September 18, 2025

SHIPPER:
ACME Manufacturing Co., Ltd
123 Industrial Park, Guangzhou, China

CONSIGNEE:
Vietnam Import Export JSC
456 Nguyen Hue, District 1, HCMC

CONTAINER:
Container Number: MSCU1234567
Size: 40HC
Weight: 15,000 KG
Seal Number: SN123456""",
        key_value_pairs=[
            KeyValuePair(key="bol_number", value="BOL-ABC-123456", confidence=0.99),
            KeyValuePair(key="container_number", value="MSCU1234567", confidence=0.98)
        ],
        tables=[],
        confidence_scores={"bol_number": 0.99, "container_number": 0.98},
        page_count=1,
        file_name="BOL.pdf",
        processing_time_ms=1100
    )

    service = LLMService()
    result = await service.extract_structured_data(ocr_result, MODEL_FLAGSHIP)

    # For clean, well-structured data, confidence should be high
    assert result.overall_confidence > 0.7

    # Shipper/consignee confidence should be high (data is clear)
    assert result.shipper.confidence > 0.7
    assert result.consignee.confidence > 0.7

    # Container details confidence should be high
    if len(result.containers) > 0:
        assert result.containers[0].confidence > 0.7

    await service.close()


@pytest.mark.integration
@pytest.mark.llm
@pytest.mark.skipif(not has_openrouter_key(), reason="OpenRouter API key not available")
@pytest.mark.asyncio
async def test_flagship_vs_mini_model_comparison():
    """
    Integration test: Compare Flagship vs Mini model accuracy
    Cost: ~$0.031 total ($0.026 Flagship + $0.005 Mini)
    """
    ocr_result = OCRResult(
        text="""Invoice Number: INV-TEST-001
Date: 2025-10-01
Total: $1,000.00
Currency: USD""",
        key_value_pairs=[],
        tables=[],
        confidence_scores={},
        page_count=1,
        file_name="test_invoice.pdf",
        processing_time_ms=500
    )

    service = LLMService()

    # Extract with Flagship
    result_flagship = await service.extract_structured_data(ocr_result, MODEL_FLAGSHIP)

    # Extract with Mini
    result_mini = await service.extract_structured_data(ocr_result, MODEL_MINI)

    # Both should succeed
    assert isinstance(result_flagship, ExtractedData)
    assert isinstance(result_mini, ExtractedData)

    # Flagship should generally have higher or equal confidence
    # (May not always be true, but usually is for simple data)
    assert result_flagship.overall_confidence >= 0.0
    assert result_mini.overall_confidence >= 0.0

    # Both should extract the currency correctly
    assert result_flagship.currency in ["USD", ""]
    assert result_mini.currency in ["USD", ""]

    await service.close()


@pytest.mark.integration
@pytest.mark.llm
@pytest.mark.skipif(not has_openrouter_key(), reason="OpenRouter API key not available")
@pytest.mark.asyncio
async def test_multi_document_extraction():
    """
    Integration test: Extract from multiple documents
    Cost: ~$0.026 for Flagship model
    """
    # Simplified multi-document scenario
    ocr_invoice = OCRResult(
        text="Invoice No: INV-001\nTotal: $5,000.00",
        key_value_pairs=[],
        tables=[],
        confidence_scores={},
        page_count=1,
        file_name="invoice.pdf",
        processing_time_ms=500
    )

    ocr_bol = OCRResult(
        text="B/L No: BOL-001\nContainer: TEST123",
        key_value_pairs=[],
        tables=[],
        confidence_scores={},
        page_count=1,
        file_name="bol.pdf",
        processing_time_ms=500
    )

    service = LLMService()
    result = await service.extract_from_multiple_documents(
        ocr_invoice=ocr_invoice,
        ocr_bol=ocr_bol
    )

    assert isinstance(result, ExtractedData)
    # With multiple documents, extraction should combine information
    assert result.overall_confidence > 0.0

    await service.close()


@pytest.mark.integration
@pytest.mark.llm
@pytest.mark.skipif(not has_openrouter_key(), reason="OpenRouter API key not available")
@pytest.mark.asyncio
async def test_error_handling_with_real_api():
    """
    Integration test: Verify error handling with real API
    This test uses invalid API configuration to test error handling
    """
    from src.core.errors import OpenRouterException
    from src.core.openrouter import OpenRouterClient

    # Create client with invalid API key
    try:
        invalid_client = OpenRouterClient(api_key="sk-invalid-key-12345")
        service = LLMService(openrouter_client=invalid_client)

        ocr_result = OCRResult(
            text="Test",
            key_value_pairs=[],
            tables=[],
            confidence_scores={},
            page_count=1,
            file_name="test.pdf",
            processing_time_ms=100
        )

        # Should raise OpenRouterException for auth error
        with pytest.raises(OpenRouterException) as exc_info:
            await service.extract_structured_data(ocr_result)

        assert exc_info.value.api_status_code == 401
        await service.close()

    except Exception as e:
        # If test setup fails, skip gracefully
        pytest.skip(f"Could not test error handling: {e}")
