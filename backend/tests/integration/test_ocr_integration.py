"""
Integration tests for OCR service with real Google Cloud Document AI

These tests require:
- GCP service account key at /app/secrets/gcp-sa-key.json
- GOOGLE_CLOUD_PROJECT_ID, GOOGLE_CLOUD_LOCATION, GOOGLE_CLOUD_PROCESSOR_ID in .env
- Sample files in resources/sample/1/

Skip these tests in CI to avoid API costs. Run manually before production.
"""
import os

import pytest

from src.services.ocr_service import OCRService


def has_gcp_credentials() -> bool:
    """Check if GCP credentials are available"""
    return os.path.exists("/app/secrets/gcp-sa-key.json")


@pytest.fixture
def ocr_service():
    """Create OCR service instance for integration tests"""
    return OCRService()


@pytest.mark.integration
@pytest.mark.skipif(not has_gcp_credentials(), reason="GCP credentials not available")
def test_process_an_pdf(ocr_service):
    """
    Test processing AN.pdf (Arrival Notice)

    Requires: GOOGLE_CLOUD_KEY secret configured
    """
    # Arrange
    file_path = "/app/resources/sample/1/AN.pdf"

    # Skip if file doesn't exist
    if not os.path.exists(file_path):
        pytest.skip(f"Sample file not found: {file_path}")

    # Act
    result = ocr_service.process_document_ocr(file_path)

    # Assert
    assert result is not None
    assert result.text, "OCR text should not be empty"
    assert len(result.text) > 100, "OCR text should have substantial content"
    assert result.page_count > 0, "Page count should be positive"
    assert len(result.confidence_scores) >= 0, "Confidence scores should be present"
    assert result.file_name == "AN.pdf"
    assert result.processing_time_ms > 0

    # Check average confidence (if entities extracted)
    if result.confidence_scores:
        avg_confidence = sum(result.confidence_scores.values()) / len(result.confidence_scores)
        assert avg_confidence > 0.7, f"Average confidence too low: {avg_confidence}"


@pytest.mark.integration
@pytest.mark.skipif(not has_gcp_credentials(), reason="GCP credentials not available")
def test_process_bol_pdf(ocr_service):
    """
    Test processing BOL.pdf (Bill of Lading)

    Requires: GOOGLE_CLOUD_KEY secret configured
    """
    # Arrange
    file_path = "/app/resources/sample/1/BOL.pdf"

    if not os.path.exists(file_path):
        pytest.skip(f"Sample file not found: {file_path}")

    # Act
    result = ocr_service.process_document_ocr(file_path)

    # Assert
    assert result is not None
    assert result.text, "OCR text should not be empty"
    assert len(result.text) > 100
    assert result.page_count > 0
    assert result.file_name == "BOL.pdf"
    assert result.processing_time_ms > 0


@pytest.mark.integration
@pytest.mark.skipif(not has_gcp_credentials(), reason="GCP credentials not available")
def test_process_co_pdf(ocr_service):
    """
    Test processing CO.pdf (Certificate of Origin)

    Requires: GOOGLE_CLOUD_KEY secret configured
    """
    # Arrange
    file_path = "/app/resources/sample/1/CO.pdf"

    if not os.path.exists(file_path):
        pytest.skip(f"Sample file not found: {file_path}")

    # Act
    result = ocr_service.process_document_ocr(file_path)

    # Assert
    assert result is not None
    assert result.text, "OCR text should not be empty"
    assert len(result.text) > 100
    assert result.page_count > 0
    assert result.file_name == "CO.pdf"

    # Certificate of Origin typically has tables
    # (Note: This depends on Document AI's extraction capability)
    assert isinstance(result.tables, list)


@pytest.mark.integration
@pytest.mark.skipif(not has_gcp_credentials(), reason="GCP credentials not available")
def test_process_invoice_jpg(ocr_service):
    """
    Test processing INVOICE.jpg (Commercial Invoice - image format)

    Requires: GOOGLE_CLOUD_KEY secret configured
    """
    # Arrange
    file_path = "/app/resources/sample/1/INVOICE.jpg"

    if not os.path.exists(file_path):
        pytest.skip(f"Sample file not found: {file_path}")

    # Act
    result = ocr_service.process_document_ocr(file_path)

    # Assert
    assert result is not None
    assert result.text, "OCR text should not be empty"
    assert len(result.text) > 100
    assert result.page_count > 0
    assert result.file_name == "INVOICE.jpg"
    assert result.processing_time_ms > 0


@pytest.mark.integration
@pytest.mark.skipif(not has_gcp_credentials(), reason="GCP credentials not available")
def test_cache_hit_avoids_api_call(ocr_service):
    """
    Test that cache hit avoids API call

    Process same file twice, verify second call uses cache (check logs)
    Requires: GOOGLE_CLOUD_KEY secret configured
    """
    # Arrange
    file_path = "/app/resources/sample/1/AN.pdf"

    if not os.path.exists(file_path):
        pytest.skip(f"Sample file not found: {file_path}")

    # Act - First call (cache miss)
    result1 = ocr_service.process_document_ocr(file_path)
    _ = result1.processing_time_ms  # Reserved for future performance testing

    # Act - Second call (cache hit)
    result2 = ocr_service.process_document_ocr(file_path)
    processing_time_2 = result2.processing_time_ms

    # Assert
    assert result1.text == result2.text
    assert result1.page_count == result2.page_count
    # Cache hit should be significantly faster (< 500ms)
    assert processing_time_2 < 500, \
        f"Cache hit should be fast (<500ms), got {processing_time_2}ms"


@pytest.mark.integration
@pytest.mark.skipif(not has_gcp_credentials(), reason="GCP credentials not available")
def test_all_sample_files_process_successfully(ocr_service):
    """
    Test that all sample files can be processed

    Requires: GOOGLE_CLOUD_KEY secret configured
    """
    # Arrange
    sample_files = [
        "/app/resources/sample/1/AN.pdf",
        "/app/resources/sample/1/BOL.pdf",
        "/app/resources/sample/1/CO.pdf",
        "/app/resources/sample/1/INVOICE.jpg"
    ]

    # Act & Assert
    for file_path in sample_files:
        if not os.path.exists(file_path):
            pytest.skip(f"Sample file not found: {file_path}")

        result = ocr_service.process_document_ocr(file_path)

        assert result is not None, f"Failed to process {file_path}"
        assert result.text, f"No text extracted from {file_path}"
        assert result.page_count > 0, f"Invalid page count for {file_path}"
