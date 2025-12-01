"""
Unit tests for OCR service using Gemini Vision via OpenRouter
"""
import json
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest

from src.core.errors import VisionOCRException
from src.schemas.ocr import OCRResult
from src.services.ocr_service import OCRService, process_document_ocr_sync


# Sample OCR response from Gemini
MOCK_OCR_RESPONSE_AN = {
    "text": "ARRIVAL NOTICE\n\nVessel: MSC GEMMA\nVoyage: 123ABC\nETA: 2024-01-15\nPort of Loading: Shanghai\nPort of Discharge: Ho Chi Minh City\n\nContainer Details:\nMSCU1234567  40'HC  20,000 kg",
    "key_value_pairs": [
        {"key": "vessel_name", "value": "MSC GEMMA", "confidence": 0.95, "page": 1},
        {"key": "voyage_number", "value": "123ABC", "confidence": 0.93, "page": 1},
        {"key": "eta", "value": "2024-01-15", "confidence": 0.91, "page": 1},
        {"key": "port_of_loading", "value": "Shanghai", "confidence": 0.94, "page": 1},
        {"key": "port_of_discharge", "value": "Ho Chi Minh City", "confidence": 0.92, "page": 1},
    ],
    "tables": [
        {
            "headers": ["Container", "Size", "Weight"],
            "rows": [["MSCU1234567", "40'HC", "20,000 kg"]],
            "confidence": 0.90
        }
    ]
}

MOCK_OCR_RESPONSE_BOL = {
    "text": "BILL OF LADING\n\nB/L Number: MSCUBOL123456\nShipper: ABC Trading Co., Ltd.\nConsignee: XYZ Import Export JSC\nNotify Party: Same as consignee",
    "key_value_pairs": [
        {"key": "bol_number", "value": "MSCUBOL123456", "confidence": 0.97, "page": 1},
        {"key": "shipper", "value": "ABC Trading Co., Ltd.", "confidence": 0.94, "page": 1},
        {"key": "consignee", "value": "XYZ Import Export JSC", "confidence": 0.95, "page": 1},
    ],
    "tables": []
}

MOCK_OCR_RESPONSE_CO = {
    "text": "CERTIFICATE OF ORIGIN\n\nCO Number: CO-2024-001\nExporter: ABC Trading Co., Ltd.\nOrigin: China",
    "key_value_pairs": [
        {"key": "co_number", "value": "CO-2024-001", "confidence": 0.96, "page": 1},
        {"key": "exporter", "value": "ABC Trading Co., Ltd.", "confidence": 0.94, "page": 1},
        {"key": "origin_country", "value": "China", "confidence": 0.98, "page": 1},
    ],
    "tables": [
        {
            "headers": ["Item", "Description", "HS Code", "Quantity"],
            "rows": [
                ["1", "Electronic Components", "8542.31", "1000 pcs"],
                ["2", "Circuit Boards", "8534.00", "500 pcs"]
            ],
            "confidence": 0.92
        }
    ]
}

MOCK_OCR_RESPONSE_INVOICE = {
    "text": "COMMERCIAL INVOICE\n\nInvoice Number: INV-2024-0001\nInvoice Date: 2024-01-10\nTotal Amount: USD 50,000.00",
    "key_value_pairs": [
        {"key": "invoice_number", "value": "INV-2024-0001", "confidence": 0.98, "page": 1},
        {"key": "invoice_date", "value": "2024-01-10", "confidence": 0.95, "page": 1},
        {"key": "total_amount", "value": "USD 50,000.00", "confidence": 0.94, "page": 1},
    ],
    "tables": []
}


def create_mock_openrouter_response(ocr_data: dict) -> dict:
    """Create a mock OpenRouter API response"""
    return {
        "id": "gen-test-123",
        "model": "google/gemini-3-pro-preview",
        "choices": [{
            "message": {
                "role": "assistant",
                "content": json.dumps(ocr_data)
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 1500,
            "completion_tokens": 500,
            "total_tokens": 2000
        }
    }


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    with patch('src.core.cache.redis_client') as mock_client:
        mock_client.get.return_value = None
        mock_client.setex.return_value = True
        yield mock_client


@pytest.fixture
def mock_openrouter_client():
    """Mock OpenRouter client"""
    with patch('src.services.ocr_service.OpenRouterClient') as mock_client_class:
        mock_instance = MagicMock()
        mock_instance.multimodal_chat_completion = AsyncMock()
        mock_instance.close = AsyncMock()
        mock_client_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_pdf2image():
    """Mock pdf2image convert_from_path"""
    with patch('src.services.ocr_service.convert_from_path') as mock_convert:
        # Create a mock PIL Image
        mock_image = MagicMock()
        mock_image.save = MagicMock(side_effect=lambda buf, format, optimize: buf.write(b"fake_png_data"))
        mock_convert.return_value = [mock_image]  # Single page PDF
        yield mock_convert


@pytest.mark.asyncio
async def test_process_document_ocr_extracts_text(mock_openrouter_client, mock_redis, mock_pdf2image):
    """Test that OCR extracts text from document"""
    # Arrange
    mock_openrouter_client.multimodal_chat_completion.return_value = create_mock_openrouter_response(MOCK_OCR_RESPONSE_AN)

    file_content = b"fake pdf content"
    with patch('builtins.open', mock_open(read_data=file_content)):
        with patch('os.path.exists', return_value=True):
            # Act
            service = OCRService()
            result = await service.process_document_ocr('/fake/path/AN.pdf')
            await service.close()

    # Assert
    assert "MSC GEMMA" in result.text
    assert result.file_name == 'AN.pdf'
    assert result.page_count == 1


@pytest.mark.asyncio
async def test_process_document_ocr_extracts_key_value_pairs(mock_openrouter_client, mock_redis, mock_pdf2image):
    """Test that OCR extracts key-value pairs"""
    # Arrange
    mock_openrouter_client.multimodal_chat_completion.return_value = create_mock_openrouter_response(MOCK_OCR_RESPONSE_BOL)

    file_content = b"fake pdf content"
    with patch('builtins.open', mock_open(read_data=file_content)):
        with patch('os.path.exists', return_value=True):
            # Act
            service = OCRService()
            result = await service.process_document_ocr('/fake/path/BOL.pdf')
            await service.close()

    # Assert
    assert len(result.key_value_pairs) > 0
    keys = [pair.key for pair in result.key_value_pairs]
    assert 'bol_number' in keys
    assert 'shipper' in keys
    assert 'consignee' in keys

    # Check confidence scores
    for pair in result.key_value_pairs:
        assert 0.0 <= pair.confidence <= 1.0


@pytest.mark.asyncio
async def test_process_document_ocr_extracts_tables(mock_openrouter_client, mock_redis, mock_pdf2image):
    """Test that OCR extracts tables"""
    # Arrange
    mock_openrouter_client.multimodal_chat_completion.return_value = create_mock_openrouter_response(MOCK_OCR_RESPONSE_CO)

    file_content = b"fake pdf content"
    with patch('builtins.open', mock_open(read_data=file_content)):
        with patch('os.path.exists', return_value=True):
            # Act
            service = OCRService()
            result = await service.process_document_ocr('/fake/path/CO.pdf')
            await service.close()

    # Assert
    assert len(result.tables) > 0
    table = result.tables[0]
    assert len(table.headers) == 4
    assert len(table.rows) == 2
    assert table.confidence > 0


@pytest.mark.asyncio
async def test_process_document_ocr_includes_confidence_scores(mock_openrouter_client, mock_redis, mock_pdf2image):
    """Test that OCR includes confidence scores"""
    # Arrange
    mock_openrouter_client.multimodal_chat_completion.return_value = create_mock_openrouter_response(MOCK_OCR_RESPONSE_INVOICE)

    file_content = b"fake pdf content"
    with patch('builtins.open', mock_open(read_data=file_content)):
        with patch('os.path.exists', return_value=True):
            # Act
            service = OCRService()
            result = await service.process_document_ocr('/fake/path/INVOICE.jpg')
            await service.close()

    # Assert
    assert len(result.confidence_scores) > 0
    assert 'invoice_number' in result.confidence_scores
    assert result.confidence_scores['invoice_number'] > 0.9


@pytest.mark.asyncio
async def test_ocr_result_cached_in_redis(mock_openrouter_client, mock_redis, mock_pdf2image):
    """Test that OCR result is cached in Redis"""
    # Arrange
    mock_openrouter_client.multimodal_chat_completion.return_value = create_mock_openrouter_response(MOCK_OCR_RESPONSE_AN)

    file_content = b"fake pdf content"
    with patch('builtins.open', mock_open(read_data=file_content)):
        with patch('os.path.exists', return_value=True):
            # Act
            service = OCRService()
            _ = await service.process_document_ocr('/fake/path/AN.pdf')
            await service.close()

    # Assert
    mock_redis.setex.assert_called_once()
    args = mock_redis.setex.call_args
    assert args[0][1] == 86400  # 24 hours TTL


@pytest.mark.asyncio
async def test_cached_ocr_result_retrieved(mock_openrouter_client, mock_redis, mock_pdf2image):
    """Test that cached OCR result is retrieved (no API call)"""
    # Arrange - First call sets up cache
    mock_openrouter_client.multimodal_chat_completion.return_value = create_mock_openrouter_response(MOCK_OCR_RESPONSE_AN)

    file_content = b"fake pdf content"
    with patch('builtins.open', mock_open(read_data=file_content)):
        with patch('os.path.exists', return_value=True):
            service = OCRService()
            result1 = await service.process_document_ocr('/fake/path/AN.pdf')
            cached_json = result1.model_dump_json()
            await service.close()

    # Setup mock to return cached result
    mock_redis.get.return_value = cached_json
    mock_openrouter_client.multimodal_chat_completion.reset_mock()

    # Second call - cache hit
    with patch('builtins.open', mock_open(read_data=file_content)):
        with patch('os.path.exists', return_value=True):
            service = OCRService()
            result2 = await service.process_document_ocr('/fake/path/AN.pdf')
            await service.close()

    # Assert - API not called on second request
    mock_openrouter_client.multimodal_chat_completion.assert_not_called()
    assert result2.text == result1.text


@pytest.mark.asyncio
async def test_vision_api_error_handling(mock_openrouter_client, mock_redis, mock_pdf2image):
    """Test graceful error handling for Vision API errors"""
    # Arrange
    mock_openrouter_client.multimodal_chat_completion.side_effect = Exception("Service unavailable")

    file_content = b"fake pdf content"
    with patch('builtins.open', mock_open(read_data=file_content)):
        with patch('os.path.exists', return_value=True):
            # Act & Assert
            service = OCRService()
            with pytest.raises(VisionOCRException) as exc_info:
                await service.process_document_ocr('/fake/path/AN.pdf')
            await service.close()

            assert "unavailable" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_file_not_found_error(mock_openrouter_client, mock_redis):
    """Test error when file doesn't exist"""
    # Arrange
    with patch('os.path.exists', return_value=False):
        # Act & Assert
        service = OCRService()
        with pytest.raises(FileNotFoundError):
            await service.process_document_ocr('/fake/nonexistent.pdf')
        await service.close()


@pytest.mark.asyncio
async def test_file_size_exceeds_limit(mock_openrouter_client, mock_redis):
    """Test error when file exceeds 20MB limit"""
    # Arrange - 25MB file
    large_file_content = b"x" * (25 * 1024 * 1024)

    with patch('builtins.open', mock_open(read_data=large_file_content)):
        with patch('os.path.exists', return_value=True):
            # Act & Assert
            service = OCRService()
            with pytest.raises(VisionOCRException) as exc_info:
                await service.process_document_ocr('/fake/path/large.pdf')
            await service.close()

            assert "20MB" in str(exc_info.value)


@pytest.mark.asyncio
async def test_unsupported_file_type(mock_openrouter_client, mock_redis):
    """Test error for unsupported file type"""
    # Arrange
    file_content = b"fake content"
    with patch('builtins.open', mock_open(read_data=file_content)):
        with patch('os.path.exists', return_value=True):
            # Act & Assert
            service = OCRService()
            with pytest.raises(ValueError) as exc_info:
                await service.process_document_ocr('/fake/path/document.docx')
            await service.close()

            assert "Unsupported file type" in str(exc_info.value)


@pytest.mark.asyncio
async def test_handles_markdown_code_block_response(mock_openrouter_client, mock_redis, mock_pdf2image):
    """Test parsing response with markdown code blocks"""
    # Arrange - Response wrapped in markdown code block
    markdown_response = {
        "id": "gen-test-123",
        "model": "google/gemini-3-pro-preview",
        "choices": [{
            "message": {
                "role": "assistant",
                "content": f"```json\n{json.dumps(MOCK_OCR_RESPONSE_AN)}\n```"
            },
            "finish_reason": "stop"
        }],
        "usage": {"prompt_tokens": 1500, "completion_tokens": 500, "total_tokens": 2000}
    }
    mock_openrouter_client.multimodal_chat_completion.return_value = markdown_response

    file_content = b"fake pdf content"
    with patch('builtins.open', mock_open(read_data=file_content)):
        with patch('os.path.exists', return_value=True):
            # Act
            service = OCRService()
            result = await service.process_document_ocr('/fake/path/AN.pdf')
            await service.close()

    # Assert - should still parse correctly
    assert "MSC GEMMA" in result.text


@pytest.mark.asyncio
async def test_handles_image_files(mock_openrouter_client, mock_redis):
    """Test OCR handles image files (JPEG/PNG)"""
    # Arrange
    mock_openrouter_client.multimodal_chat_completion.return_value = create_mock_openrouter_response(MOCK_OCR_RESPONSE_INVOICE)

    # Create fake PNG header
    png_content = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

    with patch('builtins.open', mock_open(read_data=png_content)):
        with patch('os.path.exists', return_value=True):
            with patch('src.services.ocr_service.Image') as mock_pil:
                mock_image = MagicMock()
                mock_image.save = MagicMock(side_effect=lambda buf, format, optimize: buf.write(b"fake_png_data"))
                mock_pil.open.return_value = mock_image

                # Act
                service = OCRService()
                result = await service.process_document_ocr('/fake/path/invoice.png')
                await service.close()

    # Assert
    assert result.page_count == 1
    assert 'invoice_number' in [kv.key for kv in result.key_value_pairs]


def test_sync_wrapper_works(mock_openrouter_client, mock_redis, mock_pdf2image):
    """Test synchronous wrapper for Celery tasks"""
    # Arrange
    mock_openrouter_client.multimodal_chat_completion.return_value = create_mock_openrouter_response(MOCK_OCR_RESPONSE_AN)

    file_content = b"fake pdf content"
    with patch('builtins.open', mock_open(read_data=file_content)):
        with patch('os.path.exists', return_value=True):
            # Act
            result = process_document_ocr_sync('/fake/path/AN.pdf')

    # Assert
    assert "MSC GEMMA" in result.text
    assert isinstance(result, OCRResult)


@pytest.mark.asyncio
async def test_multi_page_pdf_processing(mock_openrouter_client, mock_redis):
    """Test processing multi-page PDF"""
    # Arrange
    mock_openrouter_client.multimodal_chat_completion.return_value = create_mock_openrouter_response(MOCK_OCR_RESPONSE_AN)

    file_content = b"fake pdf content"

    with patch('builtins.open', mock_open(read_data=file_content)):
        with patch('os.path.exists', return_value=True):
            with patch('src.services.ocr_service.convert_from_path') as mock_convert:
                # Simulate 3-page PDF
                mock_images = []
                for _ in range(3):
                    mock_image = MagicMock()
                    mock_image.save = MagicMock(side_effect=lambda buf, format, optimize: buf.write(b"fake_png"))
                    mock_images.append(mock_image)
                mock_convert.return_value = mock_images

                # Act
                service = OCRService()
                result = await service.process_document_ocr('/fake/path/multi_page.pdf')
                await service.close()

    # Assert
    assert result.page_count == 3


@pytest.mark.asyncio
async def test_custom_model_override(mock_openrouter_client, mock_redis, mock_pdf2image):
    """Test using a custom model instead of default"""
    # Arrange
    mock_openrouter_client.multimodal_chat_completion.return_value = create_mock_openrouter_response(MOCK_OCR_RESPONSE_AN)

    file_content = b"fake pdf content"
    with patch('builtins.open', mock_open(read_data=file_content)):
        with patch('os.path.exists', return_value=True):
            # Act
            service = OCRService(model="openai/gpt-4o")
            await service.process_document_ocr('/fake/path/AN.pdf')
            await service.close()

    # Assert - check that custom model was used
    call_args = mock_openrouter_client.multimodal_chat_completion.call_args
    assert call_args[1]['model'] == "openai/gpt-4o"
