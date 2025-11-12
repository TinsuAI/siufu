"""
Unit tests for OCR service
"""
from unittest.mock import MagicMock, mock_open, patch

import pytest
from google.api_core import exceptions as google_exceptions

from src.core.errors import DocumentAIException
from src.services.ocr_service import OCRService
from tests.fixtures.document_ai import (
    mock_document_ai_response_an,
    mock_document_ai_response_bol,
    mock_document_ai_response_co,
    mock_document_ai_response_invoice,
)


@pytest.fixture
def mock_gcp_credentials():
    """Mock GCP credentials"""
    with patch('src.services.ocr_service.load_gcp_credentials') as mock_creds:
        mock_creds.return_value = MagicMock()
        yield mock_creds


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    with patch('src.core.cache.redis_client') as mock_client:
        mock_client.get.return_value = None
        mock_client.setex.return_value = True
        yield mock_client


@pytest.fixture
def ocr_service(mock_gcp_credentials):
    """Create OCR service instance with mocked credentials"""
    with patch('src.services.ocr_service.documentai.DocumentProcessorServiceClient'):
        service = OCRService()
        return service


def test_process_document_ocr_extracts_text(ocr_service, mock_redis):
    """Test that OCR extracts text from document"""
    # Arrange
    mock_response = mock_document_ai_response_an()
    ocr_service.client.process_document = MagicMock(return_value=mock_response)

    file_content = b"fake pdf content"
    with patch('builtins.open', mock_open(read_data=file_content)):
        with patch('os.path.exists', return_value=True):
            with patch('os.path.basename', return_value='AN.pdf'):
                # Act
                result = ocr_service.process_document_ocr('/fake/path/AN.pdf')

    # Assert
    assert result.text == mock_response.document.text
    assert "MSC GEMMA" in result.text
    assert result.file_name == 'AN.pdf'
    assert result.page_count == 1


def test_process_document_ocr_extracts_key_value_pairs(ocr_service, mock_redis):
    """Test that OCR extracts key-value pairs"""
    # Arrange
    mock_response = mock_document_ai_response_bol()
    ocr_service.client.process_document = MagicMock(return_value=mock_response)

    file_content = b"fake pdf content"
    with patch('builtins.open', mock_open(read_data=file_content)):
        with patch('os.path.exists', return_value=True):
            with patch('os.path.basename', return_value='BOL.pdf'):
                # Act
                result = ocr_service.process_document_ocr('/fake/path/BOL.pdf')

    # Assert
    assert len(result.key_value_pairs) > 0
    keys = [pair.key for pair in result.key_value_pairs]
    assert 'bol_number' in keys
    assert 'shipper' in keys
    assert 'consignee' in keys

    # Check confidence scores
    for pair in result.key_value_pairs:
        assert 0.0 <= pair.confidence <= 1.0


def test_process_document_ocr_extracts_tables(ocr_service, mock_redis):
    """Test that OCR extracts tables"""
    # Arrange
    mock_response = mock_document_ai_response_co()
    ocr_service.client.process_document = MagicMock(return_value=mock_response)

    file_content = b"fake pdf content"
    with patch('builtins.open', mock_open(read_data=file_content)):
        with patch('os.path.exists', return_value=True):
            with patch('os.path.basename', return_value='CO.pdf'):
                # Act
                result = ocr_service.process_document_ocr('/fake/path/CO.pdf')

    # Assert
    assert len(result.tables) > 0
    table = result.tables[0]
    # CO document has 4 headers (from actual mock data)
    assert len(table.headers) == 4
    # Verify table has data rows
    assert len(table.rows) == 2
    # Verify table has confidence score
    assert table.confidence > 0


def test_process_document_ocr_includes_confidence_scores(ocr_service, mock_redis):
    """Test that OCR includes confidence scores"""
    # Arrange
    mock_response = mock_document_ai_response_invoice()
    ocr_service.client.process_document = MagicMock(return_value=mock_response)

    file_content = b"fake pdf content"
    with patch('builtins.open', mock_open(read_data=file_content)):
        with patch('os.path.exists', return_value=True):
            with patch('os.path.basename', return_value='INVOICE.jpg'):
                # Act
                result = ocr_service.process_document_ocr('/fake/path/INVOICE.jpg')

    # Assert
    assert len(result.confidence_scores) > 0
    assert 'invoice_number' in result.confidence_scores
    assert result.confidence_scores['invoice_number'] > 0.9


def test_ocr_result_cached_in_redis(ocr_service, mock_redis):
    """Test that OCR result is cached in Redis"""
    # Arrange
    mock_response = mock_document_ai_response_an()
    ocr_service.client.process_document = MagicMock(return_value=mock_response)

    file_content = b"fake pdf content"
    with patch('builtins.open', mock_open(read_data=file_content)):
        with patch('os.path.exists', return_value=True):
            with patch('os.path.basename', return_value='AN.pdf'):
                # Act
                _ = ocr_service.process_document_ocr('/fake/path/AN.pdf')

    # Assert
    mock_redis.setex.assert_called_once()
    args = mock_redis.setex.call_args
    assert args[0][1] == 86400  # 24 hours TTL


def test_cached_ocr_result_retrieved(ocr_service, mock_redis):
    """Test that cached OCR result is retrieved (no API call)"""
    # Arrange
    mock_response = mock_document_ai_response_an()
    ocr_service.client.process_document = MagicMock(return_value=mock_response)

    # First call - cache miss
    file_content = b"fake pdf content"
    with patch('builtins.open', mock_open(read_data=file_content)):
        with patch('os.path.exists', return_value=True):
            with patch('os.path.basename', return_value='AN.pdf'):
                result1 = ocr_service.process_document_ocr('/fake/path/AN.pdf')
                cached_json = result1.model_dump_json()

    # Setup mock to return cached result
    mock_redis.get.return_value = cached_json
    ocr_service.client.process_document.reset_mock()

    # Second call - cache hit
    with patch('builtins.open', mock_open(read_data=file_content)):
        with patch('os.path.exists', return_value=True):
            with patch('os.path.basename', return_value='AN.pdf'):
                result2 = ocr_service.process_document_ocr('/fake/path/AN.pdf')

    # Assert - API not called on second request
    ocr_service.client.process_document.assert_not_called()
    assert result2.text == result1.text


def test_document_ai_api_error_handling(ocr_service, mock_redis):
    """Test graceful error handling for Document AI API errors"""
    # Arrange
    ocr_service.client.process_document = MagicMock(
        side_effect=google_exceptions.GoogleAPIError("Service unavailable")
    )

    file_content = b"fake pdf content"
    with patch('builtins.open', mock_open(read_data=file_content)):
        with patch('os.path.exists', return_value=True):
            # Act & Assert
            with pytest.raises(DocumentAIException) as exc_info:
                ocr_service.process_document_ocr('/fake/path/AN.pdf')

            assert "unavailable" in str(exc_info.value).lower()


def test_retry_logic_on_transient_failure(ocr_service, mock_redis):
    """Test retry logic with exponential backoff"""
    # Arrange - fail twice, then succeed
    mock_response = mock_document_ai_response_an()
    ocr_service.client.process_document = MagicMock(
        side_effect=[
            google_exceptions.GoogleAPIError("Temporary error"),
            google_exceptions.GoogleAPIError("Temporary error"),
            mock_response
        ]
    )

    file_content = b"fake pdf content"
    with patch('builtins.open', mock_open(read_data=file_content)):
        with patch('os.path.exists', return_value=True):
            with patch('os.path.basename', return_value='AN.pdf'):
                # Act
                result = ocr_service.process_document_ocr('/fake/path/AN.pdf')

    # Assert - should have retried 3 times total
    assert ocr_service.client.process_document.call_count == 3
    assert result.text == mock_response.document.text


def test_file_not_found_error(ocr_service, mock_redis):
    """Test error when file doesn't exist"""
    # Arrange
    with patch('os.path.exists', return_value=False):
        # Act & Assert
        with pytest.raises(FileNotFoundError):
            ocr_service.process_document_ocr('/fake/nonexistent.pdf')


def test_file_size_exceeds_limit(ocr_service, mock_redis):
    """Test error when file exceeds 20MB limit"""
    # Arrange - 25MB file
    large_file_content = b"x" * (25 * 1024 * 1024)

    with patch('builtins.open', mock_open(read_data=large_file_content)):
        with patch('os.path.exists', return_value=True):
            # Act & Assert
            with pytest.raises(DocumentAIException) as exc_info:
                ocr_service.process_document_ocr('/fake/path/large.pdf')

            assert "20MB" in str(exc_info.value)


def test_unsupported_file_type(ocr_service, mock_redis):
    """Test error for unsupported file type"""
    # Arrange
    file_content = b"fake content"
    with patch('builtins.open', mock_open(read_data=file_content)):
        with patch('os.path.exists', return_value=True):
            # Act & Assert
            with pytest.raises(ValueError) as exc_info:
                ocr_service.process_document_ocr('/fake/path/document.docx')

            assert "Unsupported file type" in str(exc_info.value)


def test_quota_exceeded_error(ocr_service, mock_redis):
    """Test error handling for quota exceeded"""
    # Arrange
    ocr_service.client.process_document = MagicMock(
        side_effect=google_exceptions.ResourceExhausted("Quota exceeded")
    )

    file_content = b"fake pdf content"
    with patch('builtins.open', mock_open(read_data=file_content)):
        with patch('os.path.exists', return_value=True):
            # Act & Assert
            with pytest.raises(DocumentAIException) as exc_info:
                ocr_service.process_document_ocr('/fake/path/AN.pdf')

            assert "quota" in str(exc_info.value).lower()
