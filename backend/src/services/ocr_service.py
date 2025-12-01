"""
OCR service using Gemini Vision via OpenRouter

Replaces Google Cloud Document AI with Gemini 3 Pro vision model
for document text extraction, key-value pair detection, and table extraction.
"""
import asyncio
import base64
import io
import json
import os
import time
from typing import Any, Dict, List

import sentry_sdk
import structlog
from json_repair import repair_json
from pdf2image import convert_from_path
from PIL import Image

from src.core.cache import cache_ocr_result, get_cached_ocr_result
from src.core.config import settings
from src.core.errors import VisionOCRException
from src.core.openrouter import OpenRouterClient
from src.schemas.ocr import KeyValuePair, OCRResult, Table
from src.services.ocr_extraction_prompt import get_ocr_system_prompt, get_ocr_user_prompt

logger = structlog.get_logger()


class OCRService:
    """Service for OCR processing using Gemini Vision via OpenRouter"""

    def __init__(self, model: str | None = None):
        """
        Initialize OCR service with Gemini vision model

        Args:
            model: Vision model to use. Defaults to settings.VISION_OCR_MODEL
        """
        self.client = OpenRouterClient()
        self.model = model or settings.VISION_OCR_MODEL
        self.max_pages = settings.VISION_MAX_PAGES
        self.image_dpi = settings.VISION_IMAGE_DPI
        logger.info(
            "OCR service initialized with vision model",
            model=self.model,
            max_pages=self.max_pages,
            image_dpi=self.image_dpi
        )

    async def process_document_ocr(self, file_path: str) -> OCRResult:
        """
        Process document with Gemini Vision OCR

        Args:
            file_path: Path to PDF or image file

        Returns:
            OCRResult with extracted text, key-value pairs, and tables

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file type not supported
            VisionOCRException: If vision API call fails
        """
        start_time = time.time()

        # Validate file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Check cache first
        cached_result = get_cached_ocr_result(file_path)
        if cached_result:
            logger.info("Returning cached OCR result", file=file_path)
            sentry_sdk.add_breadcrumb(
                category="ocr",
                message=f"Cache hit for {os.path.basename(file_path)}",
                level="info"
            )
            return cached_result

        # Read and validate file
        with open(file_path, 'rb') as f:
            document_content = f.read()

        # Validate file size (max 20MB)
        file_size_mb = len(document_content) / (1024 * 1024)
        if file_size_mb > 20:
            raise VisionOCRException(
                f"Document exceeds maximum size (20MB). File size: {file_size_mb:.2f}MB"
            )

        # Convert document to images
        images_base64 = self._document_to_base64_images(file_path)
        page_count = len(images_base64)

        # Handle large documents by batching
        if page_count > self.max_pages:
            logger.warning(
                f"Document has {page_count} pages, processing in batches of {self.max_pages}",
                file=file_path
            )
            result = await self._process_batched(file_path, images_base64, start_time)
        else:
            result = await self._process_single_batch(file_path, images_base64, start_time)

        # Cache the result
        cache_ocr_result(file_path, result)

        return result

    def _document_to_base64_images(self, file_path: str) -> List[str]:
        """
        Convert document (PDF or image) to list of base64-encoded PNG images

        Args:
            file_path: Path to PDF or image file

        Returns:
            List of base64-encoded image strings
        """
        ext = os.path.splitext(file_path)[1].lower()

        if ext == '.pdf':
            # Convert PDF pages to images
            images = convert_from_path(file_path, dpi=self.image_dpi)
            base64_images = []
            for img in images:
                buffer = io.BytesIO()
                img.save(buffer, format='PNG', optimize=True)
                base64_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
                base64_images.append(base64_str)
            return base64_images

        elif ext in ['.jpg', '.jpeg', '.png']:
            # Read and encode image directly
            with open(file_path, 'rb') as f:
                image_bytes = f.read()

            # Detect actual format for proper MIME type
            if ext == '.png':
                base64_str = base64.b64encode(image_bytes).decode('utf-8')
            else:
                # Convert JPEG to PNG for consistency
                img = Image.open(io.BytesIO(image_bytes))
                buffer = io.BytesIO()
                img.save(buffer, format='PNG', optimize=True)
                base64_str = base64.b64encode(buffer.getvalue()).decode('utf-8')

            return [base64_str]

        else:
            raise ValueError(
                f"Unsupported file type: {ext}. "
                f"Supported formats: PDF, JPEG, PNG"
            )

    async def _process_single_batch(
        self,
        file_path: str,
        images_base64: List[str],
        start_time: float
    ) -> OCRResult:
        """Process all images in a single vision API call"""
        page_count = len(images_base64)

        # Build multimodal message content
        content: List[Dict[str, Any]] = [
            {"type": "text", "text": get_ocr_user_prompt()}
        ]

        # Add all images
        for i, img_base64 in enumerate(images_base64):
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{img_base64}",
                    "detail": "high"
                }
            })

        # Build messages
        messages = [
            {"role": "system", "content": get_ocr_system_prompt()},
            {"role": "user", "content": content}
        ]

        # Call vision model
        logger.info("Processing document with vision model", file=file_path, pages=page_count)

        try:
            response = await self.client.multimodal_chat_completion(
                messages=messages,
                model=self.model,
                temperature=0.1,
                max_tokens=8192
            )
        except Exception as e:
            logger.error("Vision API call failed", error=str(e), file=file_path)
            sentry_sdk.capture_exception(e)
            raise VisionOCRException(
                "Vision OCR API unavailable. Please try again later.",
                original_error=e
            )

        # Parse response
        llm_response_text = response["choices"][0]["message"]["content"]
        ocr_data = self._parse_ocr_response(llm_response_text)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Log usage to Sentry
        usage = response.get("usage", {})
        sentry_sdk.set_measurement("vision_ocr_pages", page_count)
        sentry_sdk.set_measurement("vision_ocr_processing_ms", processing_time_ms)
        sentry_sdk.set_measurement("vision_ocr_prompt_tokens", usage.get("prompt_tokens", 0))
        sentry_sdk.set_measurement("vision_ocr_completion_tokens", usage.get("completion_tokens", 0))
        sentry_sdk.set_tag("vision_ocr_file", os.path.basename(file_path))
        sentry_sdk.add_breadcrumb(
            category="ocr",
            message=f"Processed {os.path.basename(file_path)} - {page_count} pages with vision",
            level="info",
            data={
                "page_count": page_count,
                "processing_time_ms": processing_time_ms,
                "model": self.model,
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0)
            }
        )

        logger.info(
            "Document processed successfully with vision",
            file=file_path,
            page_count=page_count,
            processing_time_ms=processing_time_ms,
            text_length=len(ocr_data.get("text", "")),
            model=self.model
        )

        # Build OCRResult
        return OCRResult(
            text=ocr_data.get("text", ""),
            key_value_pairs=self._parse_key_value_pairs(ocr_data.get("key_value_pairs", [])),
            tables=self._parse_tables(ocr_data.get("tables", [])),
            confidence_scores=self._extract_confidence_scores(ocr_data.get("key_value_pairs", [])),
            page_count=page_count,
            file_name=os.path.basename(file_path),
            processing_time_ms=processing_time_ms
        )

    async def _process_batched(
        self,
        file_path: str,
        images_base64: List[str],
        start_time: float
    ) -> OCRResult:
        """Process large documents in batches and merge results"""
        all_text_parts = []
        all_key_value_pairs = []
        all_tables = []
        page_count = len(images_base64)

        # Process in batches
        for batch_start in range(0, page_count, self.max_pages):
            batch_end = min(batch_start + self.max_pages, page_count)
            batch_images = images_base64[batch_start:batch_end]

            logger.info(
                f"Processing batch {batch_start // self.max_pages + 1}",
                file=file_path,
                pages=f"{batch_start + 1}-{batch_end}"
            )

            # Process batch
            batch_result = await self._process_single_batch(
                file_path,
                batch_images,
                start_time
            )

            # Accumulate results
            all_text_parts.append(batch_result.text)

            # Adjust page numbers for key-value pairs
            for kv in batch_result.key_value_pairs:
                if kv.page is not None:
                    kv.page += batch_start
                all_key_value_pairs.append(kv)

            all_tables.extend(batch_result.tables)

        # Calculate total processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Merge results
        merged_text = "\n\n--- Page Break ---\n\n".join(all_text_parts)
        confidence_scores = {kv.key: kv.confidence for kv in all_key_value_pairs}

        return OCRResult(
            text=merged_text,
            key_value_pairs=all_key_value_pairs,
            tables=all_tables,
            confidence_scores=confidence_scores,
            page_count=page_count,
            file_name=os.path.basename(file_path),
            processing_time_ms=processing_time_ms
        )

    def _parse_ocr_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse OCR JSON response from vision model

        Handles various response formats including markdown code blocks
        and malformed JSON.
        """
        # Try direct JSON parsing
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        # Try extracting from markdown code block
        if "```json" in response_text:
            try:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
                return json.loads(json_str)
            except (json.JSONDecodeError, ValueError):
                pass

        # Try extracting from generic code block
        if "```" in response_text:
            try:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
                return json.loads(json_str)
            except (json.JSONDecodeError, ValueError):
                pass

        # Try finding JSON object in response
        try:
            first_brace = response_text.find("{")
            last_brace = response_text.rfind("}")
            if first_brace != -1 and last_brace != -1:
                json_str = response_text[first_brace:last_brace + 1]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass

        # Last resort: use json_repair
        try:
            logger.warning("Using json_repair for malformed OCR response")
            sentry_sdk.add_breadcrumb(
                category="ocr",
                message="Used json_repair for malformed OCR response",
                level="warning",
                data={"response_preview": response_text[:500]}
            )
            repaired = repair_json(response_text)
            return json.loads(repaired)
        except Exception as e:
            logger.error("Failed to parse OCR response", error=str(e))
            sentry_sdk.capture_message(
                f"OCR response parsing failed: {str(e)}",
                level="error"
            )
            # Return empty result rather than failing
            return {"text": response_text, "key_value_pairs": [], "tables": []}

    def _parse_key_value_pairs(self, pairs_data: List[Dict]) -> List[KeyValuePair]:
        """Parse key-value pairs from OCR response"""
        pairs = []
        for item in pairs_data:
            try:
                pairs.append(KeyValuePair(
                    key=str(item.get("key", "")),
                    value=str(item.get("value", "")),
                    confidence=float(item.get("confidence", 0.8)),
                    page=item.get("page"),
                    bbox=item.get("bbox")
                ))
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping invalid key-value pair: {e}")
                continue
        return pairs

    def _parse_tables(self, tables_data: List[Dict]) -> List[Table]:
        """Parse tables from OCR response"""
        tables = []
        for item in tables_data:
            try:
                tables.append(Table(
                    headers=item.get("headers", []),
                    rows=item.get("rows", []),
                    confidence=float(item.get("confidence", 0.9))
                ))
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping invalid table: {e}")
                continue
        return tables

    def _extract_confidence_scores(self, pairs_data: List[Dict]) -> Dict[str, float]:
        """Extract confidence scores from key-value pairs"""
        scores = {}
        for item in pairs_data:
            key = item.get("key", "")
            confidence = item.get("confidence", 0.8)
            if key:
                scores[key] = float(confidence)
        return scores

    async def close(self):
        """Close the OpenRouter client connection"""
        await self.client.close()

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()


# Synchronous wrapper for backward compatibility with Celery tasks
def process_document_ocr_sync(file_path: str, model: str | None = None) -> OCRResult:
    """
    Synchronous wrapper for OCR processing

    This function creates a new event loop for each call, which is safe
    for use in Celery tasks or other synchronous contexts.

    Args:
        file_path: Path to PDF or image file
        model: Optional vision model override

    Returns:
        OCRResult with extracted text, key-value pairs, and tables
    """
    async def _run():
        service = OCRService(model=model)
        try:
            return await service.process_document_ocr(file_path)
        finally:
            await service.close()

    return asyncio.run(_run())
