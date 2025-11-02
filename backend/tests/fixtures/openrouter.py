"""
Mock fixtures for OpenRouter API testing
"""
from typing import Dict, Any
from unittest.mock import AsyncMock


def mock_openrouter_response_success() -> Dict[str, Any]:
    """Mock successful OpenRouter API response with ExtractedData JSON"""
    return {
        "id": "gen-abc123",
        "model": "openai/gpt-5",
        "choices": [{
            "message": {
                "role": "assistant",
                "content": """{
                    "shipper": {
                        "name": "ACME Manufacturing Co., Ltd",
                        "address": "123 Industrial Park, Guangzhou, China",
                        "tax_id": "91440101MA5ABC123",
                        "contact_person": "John Chen",
                        "phone": "+86-20-1234-5678",
                        "confidence": 0.95
                    },
                    "consignee": {
                        "name": "Vietnam Import Export JSC",
                        "address": "456 Nguyen Hue, District 1, HCMC",
                        "tax_id": "0123456789",
                        "contact_person": "Nguyen Van A",
                        "phone": "+84-28-1234-5678",
                        "confidence": 0.92
                    },
                    "products": [{
                        "description": "Cotton T-Shirts, Men's, Size M-XL",
                        "quantity": 5000.0,
                        "unit": "PCS",
                        "unit_price": 4.50,
                        "total_price": 22500.00,
                        "hs_code": "62052000",
                        "origin_country": "China",
                        "weight": 2500.0,
                        "confidence_scores": {
                            "description": 0.98,
                            "quantity": 0.95,
                            "unit_price": 0.93,
                            "hs_code": 0.88
                        }
                    }],
                    "containers": [{
                        "container_number": "MSCU1234567",
                        "size": "40HC",
                        "weight": 15000.0,
                        "seal_number": "SN123456",
                        "confidence": 0.97
                    }],
                    "dates": {
                        "invoice_date": "2025-09-15",
                        "bol_date": "2025-09-18",
                        "arrival_date": "2025-10-10",
                        "confidence_scores": {
                            "invoice_date": 0.99,
                            "bol_date": 0.96,
                            "arrival_date": 0.94
                        }
                    },
                    "invoice_total": 22500.00,
                    "currency": "USD",
                    "invoice_number": "INV-2025-001",
                    "bol_number": "BOL-ABC-123456",
                    "overall_confidence": 0.94
                }"""
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 1200,
            "completion_tokens": 800,
            "total_tokens": 2000
        }
    }


def mock_openrouter_response_with_markdown() -> Dict[str, Any]:
    """Mock response where JSON is wrapped in markdown code blocks"""
    return {
        "id": "gen-xyz789",
        "model": "openai/gpt-5",
        "choices": [{
            "message": {
                "role": "assistant",
                "content": """Here's the extracted data:

```json
{
    "shipper": {
        "name": "Test Company",
        "address": null,
        "tax_id": null,
        "confidence": 0.8
    },
    "consignee": {
        "name": "Test Consignee",
        "address": null,
        "tax_id": null,
        "confidence": 0.8
    },
    "products": [],
    "containers": [],
    "dates": {
        "invoice_date": null,
        "bol_date": null,
        "arrival_date": null,
        "confidence_scores": {}
    },
    "invoice_total": 0.0,
    "currency": "USD",
    "overall_confidence": 0.8
}
```

That's the extraction result."""
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 800,
            "completion_tokens": 400,
            "total_tokens": 1200
        }
    }


def mock_openrouter_response_invalid_json() -> Dict[str, Any]:
    """Mock response with invalid JSON (for testing error handling)"""
    return {
        "id": "gen-error123",
        "model": "openai/gpt-5",
        "choices": [{
            "message": {
                "role": "assistant",
                "content": "I'm sorry, I cannot extract data from this document because..."
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 500,
            "completion_tokens": 100,
            "total_tokens": 600
        }
    }


def sample_ocr_result():
    """Sample OCR result for testing"""
    from src.schemas.ocr import OCRResult, KeyValuePair, Table

    return OCRResult(
        text="""COMMERCIAL INVOICE

Invoice No: INV-2025-001
Date: 15/09/2025

SHIPPER:
ACME Manufacturing Co., Ltd
123 Industrial Park, Guangzhou, China
Tax ID: 91440101MA5ABC123

CONSIGNEE:
Vietnam Import Export JSC
456 Nguyen Hue, District 1, HCMC
Tax ID: 0123456789

PRODUCT DETAILS:
Description: Cotton T-Shirts, Men's, Size M-XL
Quantity: 5,000 PCS
Unit Price: USD 4.50
Total: USD 22,500.00
HS Code: 62052000
Origin: China

Total Amount: USD 22,500.00""",
        key_value_pairs=[
            KeyValuePair(key="invoice_number", value="INV-2025-001", confidence=0.99),
            KeyValuePair(key="invoice_date", value="15/09/2025", confidence=0.98),
            KeyValuePair(key="total_amount", value="22500.00", confidence=0.97)
        ],
        tables=[
            Table(
                headers=["Description", "Quantity", "Unit Price", "Total"],
                rows=[["Cotton T-Shirts, Men's, Size M-XL", "5,000 PCS", "USD 4.50", "USD 22,500.00"]],
                confidence=0.95
            )
        ],
        confidence_scores={"invoice_number": 0.99, "total_amount": 0.97},
        page_count=1,
        file_name="INVOICE.jpg",
        processing_time_ms=1250
    )


def _create_mock_openrouter_client_success(monkeypatch, mock_openrouter_response_success):
    """Mock OpenRouterClient for successful API calls"""
    from backend.src.core.openrouter import OpenRouterClient

    async def mock_chat_completion(*args, **kwargs):
        return mock_openrouter_response_success

    monkeypatch.setattr(OpenRouterClient, "chat_completion", mock_chat_completion)


def _create_mock_openrouter_client_rate_limit(monkeypatch):
    """Mock OpenRouterClient that simulates rate limit error"""
    from src.core.openrouter import OpenRouterClient
    import httpx

    async def mock_chat_completion(*args, **kwargs):
        response = httpx.Response(
            status_code=429,
            json={"error": "Rate limit exceeded"},
            headers={"Retry-After": "60"}
        )
        raise httpx.HTTPStatusError(
            "Rate limit exceeded",
            request=httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions"),
            response=response
        )

    monkeypatch.setattr(OpenRouterClient, "chat_completion", mock_chat_completion)


def _create_mock_openrouter_client_timeout(monkeypatch):
    """Mock OpenRouterClient that simulates timeout"""
    from src.core.openrouter import OpenRouterClient
    import httpx

    async def mock_chat_completion(*args, **kwargs):
        raise httpx.TimeoutException("Request timeout")

    monkeypatch.setattr(OpenRouterClient, "chat_completion", mock_chat_completion)


def _create_mock_openrouter_client_auth_error(monkeypatch):
    """Mock OpenRouterClient that simulates auth error (401)"""
    from src.core.openrouter import OpenRouterClient
    import httpx

    async def mock_chat_completion(*args, **kwargs):
        response = httpx.Response(
            status_code=401,
            json={"error": "Invalid API key"}
        )
        raise httpx.HTTPStatusError(
            "Invalid API key",
            request=httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions"),
            response=response
        )

    monkeypatch.setattr(OpenRouterClient, "chat_completion", mock_chat_completion)
