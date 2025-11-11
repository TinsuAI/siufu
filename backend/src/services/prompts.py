"""
Prompt templates for LLM extraction
"""
import json
from typing import Any, Dict

SYSTEM_PROMPT = """You are an expert customs data extraction assistant specializing in Vietnamese import declarations.
Your task is to extract structured data from OCR text of customs documents with high accuracy.

Documents you will process:
- Arrival Notice (AN): Contains vessel, container, arrival date, port information
- Bill of Lading (BOL): Contains shipper, consignee, container details, port of loading/discharge
- Certificate of Origin (CO): Contains exporter, importer, product descriptions, HS codes, quantities, origin country
- Commercial Invoice: Contains buyer, seller, product line items with prices, invoice total, currency

Extraction Guidelines:
1. Extract all fields specified in the schema
2. If a field is not found in the documents, set value to null and confidence to 0.0
3. Assign confidence scores (0.0-1.0) based on:
   - OCR text clarity (0.9-1.0 if clear, 0.5-0.8 if partially obscured)
   - Data consistency across documents (1.0 if values match, 0.7 if minor discrepancies)
   - Field completeness (1.0 if all required subfields present, lower if partial)
4. For product line items, extract from tables when available (typically in Invoice and CO)
5. For dates, preserve original format or convert to ISO format (YYYY-MM-DD)
6. For monetary values, extract currency separately from amounts
7. For HS codes, extract exactly as shown (8 digits if available)
8. Calculate overall_confidence as the average of all field confidence scores

Output Format:
- Return ONLY valid JSON matching the ExtractedData schema
- Do NOT include explanations, markdown formatting, or code blocks
- Ensure all JSON keys match schema field names exactly
- All confidence scores must be between 0.0 and 1.0"""


def get_extraction_user_prompt(
    ocr_text_an: str = "",
    ocr_text_bol: str = "",
    ocr_text_co: str = "",
    ocr_text_invoice: str = "",
    schema_json: Dict[str, Any] | None = None
) -> str:
    """
    Generate user prompt for LLM extraction with OCR results

    Args:
        ocr_text_an: OCR text from Arrival Notice
        ocr_text_bol: OCR text from Bill of Lading
        ocr_text_co: OCR text from Certificate of Origin
        ocr_text_invoice: OCR text from Commercial Invoice
        schema_json: JSON schema for ExtractedData (optional, for reference)

    Returns:
        Formatted user prompt with OCR text
    """
    prompt = "Extract customs declaration data from the following documents:\n\n"

    if ocr_text_an:
        prompt += "=== ARRIVAL NOTICE (AN.pdf) ===\n"
        prompt += f"{ocr_text_an}\n\n"

    if ocr_text_bol:
        prompt += "=== BILL OF LADING (BOL.pdf) ===\n"
        prompt += f"{ocr_text_bol}\n\n"

    if ocr_text_co:
        prompt += "=== CERTIFICATE OF ORIGIN (CO.pdf) ===\n"
        prompt += f"{ocr_text_co}\n\n"

    if ocr_text_invoice:
        prompt += "=== COMMERCIAL INVOICE (INVOICE.jpg) ===\n"
        prompt += f"{ocr_text_invoice}\n\n"

    prompt += """Extract the following information:
1. Shipper details (company name, address, tax ID from BOL/Invoice)
2. Consignee details (company name, address, tax ID from BOL/Invoice)
3. Product line items from Invoice/CO tables:
   - Product description
   - Quantity and unit (PCS, KG, etc.)
   - Unit price and total price
   - HS code (8 digits from CO if available)
   - Country of origin (from CO)
   - Weight (from Invoice/CO)
4. Container details from AN/BOL (container numbers, sizes, weights, seal numbers)
5. Dates: Invoice date, BOL date, Arrival date (from respective documents)
6. Invoice total and currency
7. Document reference numbers: Invoice number, BOL number

Return JSON with the following structure:
{
  "shipper": {
    "name": "string or null",
    "address": "string or null",
    "tax_id": "string or null",
    "contact_person": "string or null",
    "phone": "string or null",
    "confidence": 0.0-1.0
  },
  "consignee": {
    "name": "string or null",
    "address": "string or null",
    "tax_id": "string or null",
    "contact_person": "string or null",
    "phone": "string or null",
    "confidence": 0.0-1.0
  },
  "products": [
    {
      "description": "string (required)",
      "quantity": number (required),
      "unit": "string (required)",
      "unit_price": number (required),
      "total_price": number (required),
      "hs_code": "string or null (8 digits)",
      "origin_country": "string or null",
      "weight": number or null,
      "confidence_scores": {
        "description": 0.0-1.0,
        "quantity": 0.0-1.0,
        "unit_price": 0.0-1.0,
        "hs_code": 0.0-1.0
      }
    }
  ],
  "containers": [
    {
      "container_number": "string (required)",
      "size": "string (required)",
      "weight": number or null,
      "seal_number": "string or null",
      "confidence": 0.0-1.0
    }
  ],
  "dates": {
    "invoice_date": "string or null (YYYY-MM-DD or DD/MM/YYYY)",
    "bol_date": "string or null",
    "arrival_date": "string or null",
    "confidence_scores": {
      "invoice_date": 0.0-1.0,
      "bol_date": 0.0-1.0,
      "arrival_date": 0.0-1.0
    }
  },
  "invoice_total": number (required),
  "currency": "string (required)",
  "invoice_number": "string or null",
  "bol_number": "string or null",
  "overall_confidence": 0.0-1.0
}"""

    if schema_json:
        prompt += f"\n\nReference Schema:\n{json.dumps(schema_json, indent=2)}"

    return prompt


def get_single_document_extraction_prompt(
    ocr_text: str,
    document_type: str = "customs document"
) -> str:
    """
    Generate simplified prompt for single document extraction

    Args:
        ocr_text: OCR text from single document
        document_type: Type of document (e.g., "Invoice", "BOL", "CO")

    Returns:
        Formatted user prompt for single document
    """
    prompt = f"Extract customs declaration data from the following {document_type}:\n\n"
    prompt += f"=== {document_type.upper()} ===\n"
    prompt += f"{ocr_text}\n\n"
    prompt += """Extract all available information (shipper, consignee, products, containers, dates, totals).
For missing fields, set value to null and confidence to 0.0.

Return JSON matching the ExtractedData schema."""

    return prompt
