"""Mock fixtures for OpenRouter LLM responses."""

from typing import Dict, Any, List


def mock_llm_extraction_response() -> Dict[str, Any]:
    """Mock LLM response for data extraction task."""
    return {
        "id": "gen-mock-12345",
        "model": "openrouter/gpt-5",
        "created": 1705334400,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": """{
  "invoice_number": "INV-2024-001",
  "invoice_date": "2024-01-15",
  "seller_name": "ABC Trading Co.",
  "seller_address": "123 Business St, Shanghai, China",
  "buyer_name": "XYZ Import Ltd.",
  "buyer_address": "456 Commerce Ave, Los Angeles, CA, USA",
  "total_amount": 10500.00,
  "currency": "USD",
  "line_items": [
    {
      "description": "Electronic Component A",
      "quantity": 100,
      "unit_price": 50.00,
      "total": 5000.00
    },
    {
      "description": "Electronic Component B",
      "quantity": 150,
      "unit_price": 35.00,
      "total": 5250.00
    }
  ],
  "payment_terms": "Net 30 days",
  "incoterms": "FOB Shanghai"
}"""
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 850,
            "completion_tokens": 180,
            "total_tokens": 1030
        }
    }


def mock_llm_hs_code_classification_response() -> Dict[str, Any]:
    """Mock LLM response for HS code classification."""
    return {
        "id": "gen-mock-67890",
        "model": "openrouter/gpt-5",
        "created": 1705334500,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": """{
  "hs_code": "8542.31.00",
  "description": "Electronic integrated circuits: Processors and controllers",
  "confidence": 0.92,
  "reasoning": "Based on the product description 'Electronic Component A - Microprocessor', this falls under Chapter 85 (Electrical machinery), heading 8542 (Electronic integrated circuits), subheading 8542.31 (Processors and controllers).",
  "alternative_codes": [
    {
      "code": "8542.39.00",
      "description": "Electronic integrated circuits: Other",
      "confidence": 0.78
    }
  ],
  "duty_rate": "0%",
  "notes": "Check for any trade agreements that may affect duty rates."
}"""
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 320,
            "completion_tokens": 145,
            "total_tokens": 465
        }
    }


def mock_llm_validation_response(is_valid: bool = True) -> Dict[str, Any]:
    """Mock LLM response for document validation."""
    content = {
        "is_valid": is_valid,
        "validation_errors": [] if is_valid else [
            {
                "field": "invoice_date",
                "error": "Date format is inconsistent with standard format",
                "severity": "warning"
            },
            {
                "field": "total_amount",
                "error": "Total does not match sum of line items",
                "severity": "error"
            }
        ],
        "suggestions": [] if is_valid else [
            "Verify the invoice date format with the supplier",
            "Recalculate the total amount including all line items and taxes"
        ]
    }

    return {
        "id": "gen-mock-11111",
        "model": "openrouter/gpt-5",
        "created": 1705334600,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": str(content).replace("'", '"')
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 450,
            "completion_tokens": 95,
            "total_tokens": 545
        }
    }


def mock_llm_streaming_response() -> List[Dict[str, Any]]:
    """Mock streaming LLM response chunks."""
    return [
        {
            "id": "gen-mock-stream-1",
            "model": "openrouter/gpt-5",
            "created": 1705334700,
            "choices": [
                {
                    "index": 0,
                    "delta": {"role": "assistant", "content": "{"},
                    "finish_reason": None
                }
            ]
        },
        {
            "id": "gen-mock-stream-1",
            "model": "openrouter/gpt-5",
            "created": 1705334700,
            "choices": [
                {
                    "index": 0,
                    "delta": {"content": '"invoice_number": "INV-2024-001"'},
                    "finish_reason": None
                }
            ]
        },
        {
            "id": "gen-mock-stream-1",
            "model": "openrouter/gpt-5",
            "created": 1705334700,
            "choices": [
                {
                    "index": 0,
                    "delta": {"content": "}"},
                    "finish_reason": "stop"
                }
            ]
        }
    ]


def mock_llm_error_response() -> Dict[str, Any]:
    """Mock LLM error response for testing error handling."""
    return {
        "error": {
            "code": "rate_limit_exceeded",
            "message": "Rate limit exceeded. Please try again later.",
            "type": "invalid_request_error"
        }
    }
