"""
Unit tests for LLM Service
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pydantic import ValidationError

from src.services.llm_service import LLMService, MODEL_FLAGSHIP, MODEL_MINI, MODEL_NANO
from src.schemas.extraction import ExtractedData
from src.core.errors import OpenRouterException


@pytest.mark.asyncio
async def test_extract_structured_data_success(
    sample_ocr_result,
    mock_openrouter_response_success
):
    """Test successful extraction with Flagship model"""
    with patch('src.services.llm_service.OpenRouterClient') as MockClient:
        mock_client = AsyncMock()
        mock_client.chat_completion.return_value = mock_openrouter_response_success
        MockClient.return_value = mock_client

        service = LLMService()
        result = await service.extract_structured_data(sample_ocr_result, MODEL_FLAGSHIP)

        assert isinstance(result, ExtractedData)
        assert result.shipper.name == "ACME Manufacturing Co., Ltd"
        assert result.consignee.name == "Vietnam Import Export JSC"
        assert len(result.products) == 1
        assert result.products[0].description == "Cotton T-Shirts, Men's, Size M-XL"
        assert result.invoice_total == 22500.00
        assert result.currency == "USD"


@pytest.mark.asyncio
async def test_extract_structured_data_mini_model(
    sample_ocr_result,
    mock_openrouter_response_success
):
    """Test extraction with Mini model"""
    with patch('src.services.llm_service.OpenRouterClient') as MockClient:
        mock_client = AsyncMock()
        mock_client.chat_completion.return_value = mock_openrouter_response_success
        MockClient.return_value = mock_client

        service = LLMService()
        result = await service.extract_structured_data(sample_ocr_result, MODEL_MINI)

        assert isinstance(result, ExtractedData)
        # Verify model parameter was passed correctly
        mock_client.chat_completion.assert_called_once()
        call_kwargs = mock_client.chat_completion.call_args.kwargs
        assert call_kwargs['model'] == MODEL_MINI


@pytest.mark.asyncio
async def test_extract_structured_data_nano_model(
    sample_ocr_result,
    mock_openrouter_response_success
):
    """Test extraction with Nano model"""
    with patch('src.services.llm_service.OpenRouterClient') as MockClient:
        mock_client = AsyncMock()
        mock_client.chat_completion.return_value = mock_openrouter_response_success
        MockClient.return_value = mock_client

        service = LLMService()
        result = await service.extract_structured_data(sample_ocr_result, MODEL_NANO)

        assert isinstance(result, ExtractedData)
        call_kwargs = mock_client.chat_completion.call_args.kwargs
        assert call_kwargs['model'] == MODEL_NANO


@pytest.mark.asyncio
async def test_extraction_includes_confidence_scores(
    sample_ocr_result,
    mock_openrouter_response_success
):
    """Test that confidence scores are populated"""
    with patch('src.services.llm_service.OpenRouterClient') as MockClient:
        mock_client = AsyncMock()
        mock_client.chat_completion.return_value = mock_openrouter_response_success
        MockClient.return_value = mock_client

        service = LLMService()
        result = await service.extract_structured_data(sample_ocr_result)

        assert result.shipper.confidence == 0.95
        assert result.consignee.confidence == 0.92
        assert result.products[0].confidence_scores['description'] == 0.98
        assert result.containers[0].confidence == 0.97


@pytest.mark.asyncio
async def test_extraction_calculates_overall_confidence(
    sample_ocr_result,
    mock_openrouter_response_success
):
    """Test overall confidence calculation"""
    with patch('src.services.llm_service.OpenRouterClient') as MockClient:
        mock_client = AsyncMock()
        mock_client.chat_completion.return_value = mock_openrouter_response_success
        MockClient.return_value = mock_client

        service = LLMService()
        result = await service.extract_structured_data(sample_ocr_result)

        assert result.overall_confidence == 0.94
        assert 0.0 <= result.overall_confidence <= 1.0


@pytest.mark.asyncio
async def test_temperature_set_to_0_1(
    sample_ocr_result,
    mock_openrouter_response_success
):
    """Test that temperature is set to 0.1 for deterministic extraction"""
    with patch('src.services.llm_service.OpenRouterClient') as MockClient:
        mock_client = AsyncMock()
        mock_client.chat_completion.return_value = mock_openrouter_response_success
        MockClient.return_value = mock_client

        service = LLMService()
        await service.extract_structured_data(sample_ocr_result)

        call_kwargs = mock_client.chat_completion.call_args.kwargs
        assert call_kwargs['temperature'] == 0.1


@pytest.mark.asyncio
async def test_json_extraction_from_markdown(
    sample_ocr_result,
    mock_openrouter_response_with_markdown
):
    """Test JSON extraction from markdown code blocks"""
    with patch('src.services.llm_service.OpenRouterClient') as MockClient:
        mock_client = AsyncMock()
        mock_client.chat_completion.return_value = mock_openrouter_response_with_markdown
        MockClient.return_value = mock_client

        service = LLMService()
        result = await service.extract_structured_data(sample_ocr_result)

        assert isinstance(result, ExtractedData)
        assert result.shipper.name == "Test Company"
        assert result.consignee.name == "Test Consignee"


@pytest.mark.asyncio
async def test_invalid_json_parsing(
    sample_ocr_result,
    mock_openrouter_response_invalid_json
):
    """Test handling of invalid JSON response"""
    with patch('src.services.llm_service.OpenRouterClient') as MockClient:
        mock_client = AsyncMock()
        mock_client.chat_completion.return_value = mock_openrouter_response_invalid_json
        MockClient.return_value = mock_client

        service = LLMService()
        with pytest.raises(ValueError, match="invalid JSON format"):
            await service.extract_structured_data(sample_ocr_result)


@pytest.mark.asyncio
async def test_token_usage_logging(
    sample_ocr_result,
    mock_openrouter_response_success
):
    """Test token usage logging for cost tracking"""
    with patch('src.services.llm_service.OpenRouterClient') as MockClient, \
         patch('src.services.llm_service.sentry_sdk') as mock_sentry:

        mock_client = AsyncMock()
        mock_client.chat_completion.return_value = mock_openrouter_response_success
        MockClient.return_value = mock_client

        service = LLMService()
        await service.extract_structured_data(sample_ocr_result)

        # Verify Sentry logging was called
        assert mock_sentry.set_tag.called
        assert mock_sentry.set_measurement.called
        assert mock_sentry.add_breadcrumb.called

        # Check that token metrics were logged
        measurement_calls = mock_sentry.set_measurement.call_args_list
        measurements = {call[0][0]: call[0][1] for call in measurement_calls}

        assert measurements['openrouter_prompt_tokens'] == 1200
        assert measurements['openrouter_completion_tokens'] == 800
        assert measurements['openrouter_total_tokens'] == 2000
        assert 'openrouter_cost' in measurements


@pytest.mark.asyncio
async def test_cost_calculation_flagship():
    """Test cost calculation for Flagship model"""
    service = LLMService()

    # 1200 prompt tokens * $15/1M + 800 completion tokens * $60/1M
    cost = service._calculate_cost(1200, 800, MODEL_FLAGSHIP)

    expected_cost = (1200 * 15 / 1_000_000) + (800 * 60 / 1_000_000)
    assert cost == pytest.approx(expected_cost, rel=1e-6)
    assert cost == pytest.approx(0.066, rel=1e-3)  # ~$0.066


@pytest.mark.asyncio
async def test_cost_calculation_mini():
    """Test cost calculation for Mini model"""
    service = LLMService()

    cost = service._calculate_cost(1200, 800, MODEL_MINI)

    expected_cost = (1200 * 0.15 / 1_000_000) + (800 * 0.60 / 1_000_000)
    assert cost == pytest.approx(expected_cost, rel=1e-6)
    assert cost < 0.001  # Much cheaper than Flagship


@pytest.mark.asyncio
async def test_format_ocr_result(sample_ocr_result):
    """Test OCR result formatting"""
    service = LLMService()

    formatted_text = service._format_ocr_result(sample_ocr_result)

    assert "COMMERCIAL INVOICE" in formatted_text
    assert "INV-2025-001" in formatted_text
    assert "Key-Value Pairs:" in formatted_text
    assert "Tables:" in formatted_text
    assert "invoice_number" in formatted_text


@pytest.mark.asyncio
async def test_parse_llm_response_plain_json():
    """Test parsing plain JSON response"""
    service = LLMService()

    response_text = '{"shipper": {"name": "Test", "confidence": 0.9}, "products": []}'
    result = service._parse_llm_response(response_text)

    assert isinstance(result, dict)
    assert result['shipper']['name'] == 'Test'


@pytest.mark.asyncio
async def test_calculate_overall_confidence():
    """Test overall confidence calculation"""
    from src.schemas.extraction import (
        ExtractedData, CompanyDetails, ProductItem,
        ContainerDetails, ShipmentDates
    )

    service = LLMService()

    extracted_data = ExtractedData(
        shipper=CompanyDetails(name="Test", confidence=0.9),
        consignee=CompanyDetails(name="Test", confidence=0.8),
        products=[
            ProductItem(
                description="Test",
                quantity=100,
                unit="PCS",
                unit_price=10,
                total_price=1000,
                confidence_scores={"description": 0.95, "quantity": 0.90}
            )
        ],
        containers=[ContainerDetails(container_number="TEST123", size="40'", confidence=0.85)],
        dates=ShipmentDates(confidence_scores={"invoice_date": 0.92}),
        invoice_total=1000,
        currency="USD",
        overall_confidence=0.0  # Will be calculated
    )

    calculated_confidence = service._calculate_overall_confidence(extracted_data)

    # Should average: 0.9, 0.8, 0.95, 0.90, 0.85, 0.92
    expected = (0.9 + 0.8 + 0.95 + 0.90 + 0.85 + 0.92) / 6
    assert calculated_confidence == pytest.approx(expected, rel=1e-3)


@pytest.mark.asyncio
async def test_extract_from_multiple_documents(mock_openrouter_response_success):
    """Test extraction from multiple documents"""
    from src.schemas.ocr import OCRResult

    with patch('src.services.llm_service.OpenRouterClient') as MockClient:
        mock_client = AsyncMock()
        mock_client.chat_completion.return_value = mock_openrouter_response_success
        MockClient.return_value = mock_client

        service = LLMService()

        ocr_invoice = OCRResult(
            text="Invoice text",
            key_value_pairs=[],
            tables=[],
            confidence_scores={},
            page_count=1,
            file_name="invoice.pdf",
            processing_time_ms=100
        )

        ocr_bol = OCRResult(
            text="BOL text",
            key_value_pairs=[],
            tables=[],
            confidence_scores={},
            page_count=1,
            file_name="bol.pdf",
            processing_time_ms=100
        )

        result = await service.extract_from_multiple_documents(
            ocr_invoice=ocr_invoice,
            ocr_bol=ocr_bol
        )

        assert isinstance(result, ExtractedData)
        # Verify both documents were included in prompt
        call_args = mock_client.chat_completion.call_args
        prompt_content = call_args.kwargs['messages'][1]['content']
        assert "COMMERCIAL INVOICE" in prompt_content or "Invoice text" in prompt_content
        assert "BILL OF LADING" in prompt_content or "BOL text" in prompt_content
