"""Mock fixtures for Google Document AI responses."""

from typing import Dict, Any


def mock_ocr_invoice_response() -> Dict[str, Any]:
    """Mock OCR response for invoice document."""
    return {
        "document": {
            "text": "COMMERCIAL INVOICE\\nInvoice No: INV-2024-001\\nDate: 2024-01-15\\n"
                   "Seller: ABC Trading Co.\\nBuyer: XYZ Import Ltd.\\n"
                   "Total Amount: $10,500.00\\nCurrency: USD",
            "pages": [
                {
                    "pageNumber": 1,
                    "dimension": {"width": 612, "height": 792, "unit": "pixels"},
                    "layout": {
                        "textAnchor": {
                            "textSegments": [{"startIndex": 0, "endIndex": 150}]
                        },
                        "confidence": 0.98,
                        "boundingPoly": {
                            "normalizedVertices": [
                                {"x": 0.1, "y": 0.1},
                                {"x": 0.9, "y": 0.1},
                                {"x": 0.9, "y": 0.9},
                                {"x": 0.1, "y": 0.9}
                            ]
                        }
                    }
                }
            ],
            "entities": [
                {
                    "type": "invoice_number",
                    "mentionText": "INV-2024-001",
                    "confidence": 0.95,
                    "pageAnchor": {"pageRefs": [{"page": 0}]}
                },
                {
                    "type": "invoice_date",
                    "mentionText": "2024-01-15",
                    "confidence": 0.97,
                    "normalizedValue": {"text": "2024-01-15"}
                },
                {
                    "type": "total_amount",
                    "mentionText": "$10,500.00",
                    "confidence": 0.99,
                    "normalizedValue": {"moneyValue": {"currencyCode": "USD", "units": 10500}}
                }
            ]
        }
    }


def mock_ocr_bill_of_lading_response() -> Dict[str, Any]:
    """Mock OCR response for Bill of Lading document."""
    return {
        "document": {
            "text": "BILL OF LADING\\nB/L No: BOL-2024-5678\\nVessel: OCEAN CARRIER\\n"
                   "Port of Loading: Shanghai\\nPort of Discharge: Los Angeles\\n"
                   "Container No: CONT123456",
            "pages": [
                {
                    "pageNumber": 1,
                    "dimension": {"width": 612, "height": 792, "unit": "pixels"}
                }
            ],
            "entities": [
                {
                    "type": "bl_number",
                    "mentionText": "BOL-2024-5678",
                    "confidence": 0.96
                },
                {
                    "type": "vessel_name",
                    "mentionText": "OCEAN CARRIER",
                    "confidence": 0.94
                },
                {
                    "type": "port_of_loading",
                    "mentionText": "Shanghai",
                    "confidence": 0.98
                },
                {
                    "type": "port_of_discharge",
                    "mentionText": "Los Angeles",
                    "confidence": 0.98
                }
            ]
        }
    }


def mock_ocr_certificate_of_origin_response() -> Dict[str, Any]:
    """Mock OCR response for Certificate of Origin document."""
    return {
        "document": {
            "text": "CERTIFICATE OF ORIGIN\\nCertificate No: CO-2024-9999\\n"
                   "Country of Origin: China\\nExporter: ABC Trading Co.\\n"
                   "Goods Description: Electronic Components",
            "pages": [
                {
                    "pageNumber": 1,
                    "dimension": {"width": 612, "height": 792, "unit": "pixels"}
                }
            ],
            "entities": [
                {
                    "type": "certificate_number",
                    "mentionText": "CO-2024-9999",
                    "confidence": 0.97
                },
                {
                    "type": "country_of_origin",
                    "mentionText": "China",
                    "confidence": 0.99
                }
            ]
        }
    }


def mock_ocr_error_response() -> Dict[str, Any]:
    """Mock OCR error response for testing error handling."""
    return {
        "error": {
            "code": 400,
            "message": "Invalid document format",
            "status": "INVALID_ARGUMENT"
        }
    }
