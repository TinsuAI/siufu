"""
LLM Service for intelligent data extraction from OCR results
"""
import json
import re
from typing import Any, Dict

import sentry_sdk

from ..core.openrouter import OpenRouterClient
from ..schemas.extraction import ExtractedData
from ..schemas.ocr import OCRResult
from ..schemas.vietnamese_declaration import VietnameseDeclarationData
from .prompts import SYSTEM_PROMPT, get_extraction_user_prompt
from .vietnamese_extraction_prompt import (
    VIETNAMESE_DECLARATION_SYSTEM_PROMPT,
    get_vietnamese_extraction_prompt,
)

# Model tier constants
MODEL_FLAGSHIP = "openai/gpt-5"
MODEL_MINI = "openai/gpt-5-mini"
MODEL_NANO = "openai/gpt-5-nano"


class LLMService:
    """
    Service for LLM-based data extraction from OCR results

    Uses OpenRouter API to access GPT-5 models for intelligent extraction
    of structured customs declaration data from unstructured OCR text.
    """

    def __init__(self, openrouter_client: OpenRouterClient | None = None):
        """
        Initialize LLM service

        Args:
            openrouter_client: OpenRouter client instance. If None, creates new client.
        """
        self.client = openrouter_client or OpenRouterClient()

    async def extract_structured_data(
        self,
        ocr_result: OCRResult,
        model: str = MODEL_FLAGSHIP
    ) -> ExtractedData:
        """
        Extract structured customs data from OCR result using LLM

        Args:
            ocr_result: OCR result containing text and extracted entities
            model: Model tier to use (MODEL_FLAGSHIP, MODEL_MINI, or MODEL_NANO)

        Returns:
            ExtractedData object with parsed customs declaration data

        Raises:
            OpenRouterException: If API call fails
            ValidationError: If LLM response doesn't match schema

        Example:
            >>> service = LLMService()
            >>> ocr_result = await ocr_service.process_document("invoice.pdf")
            >>> extracted = await service.extract_structured_data(ocr_result)
            >>> print(extracted.shipper.name)
            'ACME Manufacturing Co., Ltd'
        """
        # Step 1: Format OCR result into prompt context
        ocr_text = self._format_ocr_result(ocr_result)

        # Step 2: Load extraction prompt template and inject OCR data
        user_prompt = get_extraction_user_prompt(ocr_text_invoice=ocr_text)

        # Step 3: Call OpenRouter API
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]

        response = await self.client.chat_completion(
            messages=messages,
            model=model,
            temperature=0.1,  # Deterministic extraction
            max_tokens=4096
        )

        # Step 4: Parse JSON response from LLM
        llm_response_text = response["choices"][0]["message"]["content"]
        parsed_json = self._parse_llm_response(llm_response_text)

        # Step 5: Validate JSON against ExtractedData schema
        extracted_data = ExtractedData.model_validate(parsed_json)

        # Step 6: Calculate overall confidence score if not provided
        if extracted_data.overall_confidence == 0.0:
            extracted_data.overall_confidence = self._calculate_overall_confidence(extracted_data)

        # Step 7: Log token usage for cost tracking
        self._log_token_usage(response, model)

        return extracted_data

    async def extract_from_multiple_documents(
        self,
        ocr_an: OCRResult | None = None,
        ocr_bol: OCRResult | None = None,
        ocr_co: OCRResult | None = None,
        ocr_invoice: OCRResult | None = None,
        model: str = MODEL_FLAGSHIP
    ) -> VietnameseDeclarationData:
        """
        Extract structured data from multiple customs documents (77 fields Vietnamese format)

        This method extracts ALL 77 fields required for Vietnamese customs declaration
        as specified in docs/stories/1.7-field-mapping.md

        Args:
            ocr_an: OCR result from Arrival Notice
            ocr_bol: OCR result from Bill of Lading
            ocr_co: OCR result from Certificate of Origin
            ocr_invoice: OCR result from Commercial Invoice
            model: Model tier to use (default: GPT-5 Flagship)

        Returns:
            VietnameseDeclarationData with all 77 extracted fields

        Raises:
            OpenRouterException: If API call fails
            ValidationError: If LLM response doesn't match schema
        """
        # Format all OCR results into comprehensive prompt
        user_prompt = get_vietnamese_extraction_prompt(
            ocr_text_an=self._format_ocr_result(ocr_an) if ocr_an else "",
            ocr_text_bol=self._format_ocr_result(ocr_bol) if ocr_bol else "",
            ocr_text_co=self._format_ocr_result(ocr_co) if ocr_co else "",
            ocr_text_invoice=self._format_ocr_result(ocr_invoice) if ocr_invoice else ""
        )

        messages = [
            {"role": "system", "content": VIETNAMESE_DECLARATION_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]

        response = await self.client.chat_completion(
            messages=messages,
            model=model,
            temperature=0.1,  # Deterministic extraction
            max_tokens=16384  # Increased for 77 fields + confidence scores (doubled to fix truncation)
        )

        llm_response_text = response["choices"][0]["message"]["content"]
        parsed_json = self._parse_llm_response(llm_response_text)

        # Validate against Vietnamese declaration schema
        extracted_data = VietnameseDeclarationData.model_validate(parsed_json)

        # Calculate overall confidence if not provided by LLM
        if extracted_data.overall_confidence == 0.0:
            extracted_data.overall_confidence = self._calculate_vietnamese_confidence(extracted_data)

        self._log_token_usage(response, model)

        return extracted_data

    def _format_ocr_result(self, ocr_result: OCRResult) -> str:
        """
        Format OCR result into text for LLM prompt

        Combines text, key-value pairs, and tables into structured text.

        Args:
            ocr_result: OCR result to format

        Returns:
            Formatted text with all OCR data
        """
        output = ocr_result.text

        # Add key-value pairs if present
        if ocr_result.key_value_pairs:
            output += "\n\nKey-Value Pairs:\n"
            for kv in ocr_result.key_value_pairs:
                output += f"- {kv.key}: {kv.value}\n"

        # Add tables if present (format as markdown)
        if ocr_result.tables:
            output += "\n\nTables:\n"
            for i, table in enumerate(ocr_result.tables):
                output += f"\nTable {i+1}:\n"
                # Header row
                output += "| " + " | ".join(table.headers) + " |\n"
                output += "| " + " | ".join(["---"] * len(table.headers)) + " |\n"
                # Data rows
                for row in table.rows:
                    output += "| " + " | ".join(row) + " |\n"

        return output

    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse LLM response text to extract JSON

        Handles responses that are:
        1. Plain JSON
        2. JSON wrapped in markdown code blocks
        3. JSON with extra text before/after

        Args:
            response_text: Raw LLM response text

        Returns:
            Parsed JSON dict

        Raises:
            ValueError: If JSON cannot be extracted
        """
        # Try parsing as-is
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        # Try extracting from markdown code block
        # Pattern: ```json ... ``` or ``` ... ```
        code_block_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        match = re.search(code_block_pattern, response_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Try extracting JSON object (find first { to last })
        json_pattern = r'\{.*\}'
        match = re.search(json_pattern, response_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError as e:
                # Log JSON decode error with context
                import logging
                logger = logging.getLogger(__name__)
                logger.error(
                    f"JSON decode error: {str(e)}. "
                    f"Response length: {len(response_text)}, "
                    f"Extracted JSON length: {len(match.group(0))}, "
                    f"First 500 chars: {response_text[:500]}, "
                    f"Last 500 chars: {response_text[-500:]}"
                )
                pass

        # Log raw response for debugging
        sentry_sdk.add_breadcrumb(
            category="llm",
            message="Failed to parse LLM response",
            level="error",
            data={"response_text": response_text[:500]}  # First 500 chars
        )

        raise ValueError(f"LLM returned invalid JSON format. Response: {response_text[:200]}")

    def _calculate_overall_confidence(self, extracted_data: ExtractedData) -> float:
        """
        Calculate overall confidence score from all field confidence scores

        Args:
            extracted_data: Extracted data with field-level confidence scores

        Returns:
            Average confidence score (0.0-1.0)
        """
        confidences = []

        # Shipper/consignee confidence
        if extracted_data.shipper:
            confidences.append(extracted_data.shipper.confidence)
        if extracted_data.consignee:
            confidences.append(extracted_data.consignee.confidence)

        # Product confidence scores
        for product in extracted_data.products:
            if product.confidence_scores:
                confidences.extend(product.confidence_scores.values())

        # Container confidence
        for container in extracted_data.containers:
            confidences.append(container.confidence)

        # Date confidence scores
        if extracted_data.dates.confidence_scores:
            confidences.extend(extracted_data.dates.confidence_scores.values())

        # Return average, or 0.0 if no confidences found
        return sum(confidences) / len(confidences) if confidences else 0.0

    def _calculate_vietnamese_confidence(self, extracted_data: VietnameseDeclarationData) -> float:
        """
        Calculate overall confidence score for Vietnamese declaration (77 fields)

        Uses confidence_scores dict with all field-level confidence scores

        Args:
            extracted_data: Vietnamese declaration data with per-field confidence scores

        Returns:
            Average confidence score (0.0-1.0)
        """
        if extracted_data.confidence_scores:
            confidences = list(extracted_data.confidence_scores.values())
            return sum(confidences) / len(confidences) if confidences else 0.0
        return 0.0

    def _log_token_usage(self, response: Dict[str, Any], model: str) -> None:
        """
        Log token usage and cost to Sentry for monitoring

        Args:
            response: OpenRouter API response with usage data
            model: Model tier used
        """
        usage = response.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", 0)

        # Calculate cost based on model tier
        cost = self._calculate_cost(prompt_tokens, completion_tokens, model)

        # Log to Sentry
        sentry_sdk.set_tag("openrouter_model", model)
        sentry_sdk.set_measurement("openrouter_prompt_tokens", prompt_tokens)
        sentry_sdk.set_measurement("openrouter_completion_tokens", completion_tokens)
        sentry_sdk.set_measurement("openrouter_total_tokens", total_tokens)
        sentry_sdk.set_measurement("openrouter_cost", cost)

        sentry_sdk.add_breadcrumb(
            category="llm",
            message=f"LLM extraction: {total_tokens} tokens, ${cost:.4f}",
            level="info",
            data={
                "model": model,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "cost_usd": cost
            }
        )

    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int, model: str) -> float:
        """
        Calculate API call cost based on token usage and model tier

        Pricing (per 1M tokens):
        - Flagship (gpt-5): $15 input / $60 output
        - Mini (gpt-5-mini): $0.15 input / $0.60 output
        - Nano (gpt-5-nano): $0.05 input / $0.20 output

        Args:
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens
            model: Model identifier

        Returns:
            Cost in USD
        """
        # Pricing per 1M tokens
        pricing = {
            MODEL_FLAGSHIP: {"input": 15.0, "output": 60.0},
            MODEL_MINI: {"input": 0.15, "output": 0.60},
            MODEL_NANO: {"input": 0.05, "output": 0.20}
        }

        rates = pricing.get(model, pricing[MODEL_FLAGSHIP])  # Default to Flagship if unknown

        cost = (
            (prompt_tokens * rates["input"] / 1_000_000) +
            (completion_tokens * rates["output"] / 1_000_000)
        )

        return cost

    async def close(self):
        """Close the OpenRouter client connection"""
        await self.client.close()

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
