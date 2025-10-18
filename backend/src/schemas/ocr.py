"""
OCR result schemas
"""
from pydantic import BaseModel, Field
from typing import List, Dict


class KeyValuePair(BaseModel):
    """Key-value pair extracted from document"""
    key: str
    value: str
    confidence: float = Field(ge=0.0, le=1.0)


class Table(BaseModel):
    """Table extracted from document"""
    headers: List[str]
    rows: List[List[str]]
    confidence: float = Field(ge=0.0, le=1.0)


class OCRResult(BaseModel):
    """Complete OCR result for a document"""
    text: str
    key_value_pairs: List[KeyValuePair]
    tables: List[Table]
    confidence_scores: Dict[str, float]
    page_count: int
    file_name: str
    processing_time_ms: int

    model_config = {
        "json_schema_extra": {
            "example": {
                "text": "ARRIVAL NOTICE\\nVessel: MSC GEMMA...",
                "key_value_pairs": [
                    {"key": "vessel_name", "value": "MSC GEMMA", "confidence": 0.95}
                ],
                "tables": [
                    {
                        "headers": ["Container", "Size", "Weight"],
                        "rows": [["MSCU1234567", "40'", "20,000 kg"]],
                        "confidence": 0.92
                    }
                ],
                "confidence_scores": {"vessel_name": 0.95, "container_number": 0.92},
                "page_count": 1,
                "file_name": "AN.pdf",
                "processing_time_ms": 1250
            }
        }
    }
