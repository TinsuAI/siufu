"""
Pydantic schemas for LLM-extracted customs data
"""
from pydantic import BaseModel, Field
from typing import List, Dict


class CompanyDetails(BaseModel):
    """Shipper or Consignee company information"""
    name: str | None = None
    address: str | None = None
    tax_id: str | None = None  # Vietnam: MST (Ma So Thue)
    contact_person: str | None = None
    phone: str | None = None
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "ACME Manufacturing Co., Ltd",
                "address": "123 Industrial Park, Guangzhou, China",
                "tax_id": "91440101MA5ABC123",
                "contact_person": "John Chen",
                "phone": "+86-20-1234-5678",
                "confidence": 0.95
            }
        }
    }


class ProductItem(BaseModel):
    """Individual product line item"""
    description: str
    quantity: float
    unit: str  # e.g., "PCS", "KG", "CBM"
    unit_price: float
    total_price: float
    hs_code: str | None = None  # 8-digit HS code
    origin_country: str | None = None
    weight: float | None = None
    confidence_scores: Dict[str, float] = Field(default_factory=dict)
    # confidence_scores keys: "description", "quantity", "unit_price", "hs_code", etc.

    model_config = {
        "json_schema_extra": {
            "example": {
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
            }
        }
    }


class ContainerDetails(BaseModel):
    """Shipping container information"""
    container_number: str
    size: str  # e.g., "20'", "40'", "40HC"
    weight: float | None = None
    seal_number: str | None = None
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)

    model_config = {
        "json_schema_extra": {
            "example": {
                "container_number": "MSCU1234567",
                "size": "40HC",
                "weight": 15000.0,
                "seal_number": "SN123456",
                "confidence": 0.97
            }
        }
    }


class ShipmentDates(BaseModel):
    """Key dates from documents"""
    invoice_date: str | None = None  # ISO format or DD/MM/YYYY
    bol_date: str | None = None
    arrival_date: str | None = None
    confidence_scores: Dict[str, float] = Field(default_factory=dict)

    model_config = {
        "json_schema_extra": {
            "example": {
                "invoice_date": "2025-09-15",
                "bol_date": "2025-09-18",
                "arrival_date": "2025-10-10",
                "confidence_scores": {
                    "invoice_date": 0.99,
                    "bol_date": 0.96,
                    "arrival_date": 0.94
                }
            }
        }
    }


class ExtractedData(BaseModel):
    """Complete extracted customs declaration data"""
    shipper: CompanyDetails
    consignee: CompanyDetails
    products: List[ProductItem]
    containers: List[ContainerDetails]
    dates: ShipmentDates
    invoice_total: float
    currency: str  # e.g., "USD", "EUR", "VND"
    invoice_number: str | None = None
    bol_number: str | None = None
    overall_confidence: float = Field(ge=0.0, le=1.0)

    model_config = {
        "json_schema_extra": {
            "example": {
                "shipper": {
                    "name": "ACME Manufacturing Co., Ltd",
                    "address": "123 Industrial Park, Guangzhou, China",
                    "tax_id": "91440101MA5ABC123",
                    "confidence": 0.95
                },
                "consignee": {
                    "name": "Vietnam Import Export JSC",
                    "address": "456 Nguyen Hue, District 1, HCMC",
                    "tax_id": "0123456789",
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
            }
        }
    }
