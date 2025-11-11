"""
OCR service using Google Cloud Document AI
"""
import os
import time
from typing import Any, Dict

import sentry_sdk
import structlog
from google.api_core import exceptions as google_exceptions
from google.cloud import documentai
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.cache import cache_ocr_result, get_cached_ocr_result
from src.core.config import settings
from src.core.errors import DocumentAIException
from src.core.gcp import load_gcp_credentials
from src.schemas.ocr import KeyValuePair, OCRResult, Table

logger = structlog.get_logger()


class OCRService:
    """Service for OCR processing using Google Cloud Document AI"""

    def __init__(self):
        """Initialize Document AI client"""
        self.credentials = load_gcp_credentials()
        self.client = documentai.DocumentProcessorServiceClient(
            credentials=self.credentials
        )
        self.processor_name = (
            f"projects/{settings.GOOGLE_CLOUD_PROJECT_ID}/"
            f"locations/{settings.GOOGLE_CLOUD_LOCATION}/"
            f"processors/{settings.GOOGLE_CLOUD_PROCESSOR_ID}"
        )
        logger.info(
            "OCR service initialized",
            processor=self.processor_name
        )

    def process_document_ocr(self, file_path: str) -> OCRResult:
        """
        Process document with Document AI OCR

        Args:
            file_path: Path to PDF or image file

        Returns:
            OCRResult with extracted text, key-value pairs, and tables

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file type not supported
        """
        start_time = time.time()

        # Validate file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Check cache first
        cached_result = get_cached_ocr_result(file_path)
        if cached_result:
            logger.info("Returning cached OCR result", file=file_path)
            # Log cache hit to Sentry
            sentry_sdk.add_breadcrumb(
                category="ocr",
                message=f"Cache hit for {os.path.basename(file_path)}",
                level="info"
            )
            return cached_result

        # Read file
        with open(file_path, 'rb') as f:
            document_content = f.read()

        # Validate file size (max 20MB)
        file_size_mb = len(document_content) / (1024 * 1024)
        if file_size_mb > 20:
            raise DocumentAIException(
                f"Document exceeds maximum size (20MB). File size: {file_size_mb:.2f}MB"
            )

        # Detect MIME type
        mime_type = self._detect_mime_type(file_path)

        # Create Document AI request
        request = documentai.ProcessRequest(
            name=self.processor_name,
            raw_document=documentai.RawDocument(
                content=document_content,
                mime_type=mime_type
            )
        )

        # Process document with retry logic
        logger.info("Processing document with Document AI", file=file_path)
        try:
            response = self._call_document_ai_api(request)
            document = response.document
        except DocumentAIException:
            raise
        except Exception as e:
            logger.error("Unexpected error calling Document AI", error=str(e))
            sentry_sdk.capture_exception(e)
            raise DocumentAIException(
                "Document AI API unavailable. Please try again later.",
                original_error=e
            )

        # Extract data
        text = document.text
        key_value_pairs = self._extract_key_value_pairs(document)
        tables = self._extract_tables(document)
        confidence_scores = self._extract_confidence_scores(document)
        page_count = len(document.pages)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Log usage to Sentry for cost tracking
        sentry_sdk.set_measurement("document_ai_pages", page_count)
        sentry_sdk.set_measurement("document_ai_processing_ms", processing_time_ms)
        sentry_sdk.set_tag("document_ai_file", os.path.basename(file_path))
        sentry_sdk.add_breadcrumb(
            category="ocr",
            message=f"Processed {os.path.basename(file_path)} - {page_count} pages",
            level="info",
            data={
                "page_count": page_count,
                "processing_time_ms": processing_time_ms,
                "estimated_cost": page_count * 0.04
            }
        )

        logger.info(
            "Document processed successfully",
            file=file_path,
            page_count=page_count,
            processing_time_ms=processing_time_ms,
            text_length=len(text),
            estimated_cost_usd=page_count * 0.04
        )

        result = OCRResult(
            text=text,
            key_value_pairs=key_value_pairs,
            tables=tables,
            confidence_scores=confidence_scores,
            page_count=page_count,
            file_name=os.path.basename(file_path),
            processing_time_ms=processing_time_ms
        )

        # Cache the result
        cache_ocr_result(file_path, result)

        return result

    def _detect_mime_type(self, file_path: str) -> str:
        """Detect MIME type from file extension"""
        ext = os.path.splitext(file_path)[1].lower()
        mime_types = {
            '.pdf': 'application/pdf',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
        }
        if ext not in mime_types:
            raise ValueError(
                f"Unsupported file type: {ext}. "
                f"Supported formats: PDF, JPEG, PNG"
            )
        return mime_types[ext]

    def _extract_key_value_pairs(self, document: Any) -> list[KeyValuePair]:
        """Extract key-value pairs from Document AI response with page/bbox metadata"""
        pairs = []
        if hasattr(document, 'entities'):
            for entity in document.entities:
                # Extract page number and bounding box from entity
                page_num, bbox = self._extract_entity_location(entity, document)

                pairs.append(KeyValuePair(
                    key=entity.type_,
                    value=entity.mention_text,
                    confidence=entity.confidence if hasattr(entity, 'confidence') else 0.0,
                    page=page_num,
                    bbox=bbox
                ))
        return pairs

    def _extract_entity_location(self, entity: Any, document: Any) -> tuple[int | None, list[float] | None]:
        """
        Extract page number and bounding box from Document AI entity

        Returns:
            Tuple of (page_number, bbox) where bbox is [x, y, width, height] in normalized coordinates
        """
        page_num = None
        bbox = None

        # Extract page number from page_anchor
        if hasattr(entity, 'page_anchor') and entity.page_anchor:
            page_refs = entity.page_anchor.page_refs
            if page_refs and len(page_refs) > 0:
                # Use first page reference
                page_num = int(page_refs[0].page) if hasattr(page_refs[0], 'page') else None

                # Extract bounding box from bounding_poly
                if hasattr(page_refs[0], 'bounding_poly') and page_refs[0].bounding_poly:
                    bbox = self._normalize_bounding_poly(
                        page_refs[0].bounding_poly,
                        page_num,
                        document
                    )

        return page_num, bbox

    def _normalize_bounding_poly(
        self,
        bounding_poly: Any,
        page_num: int | None,
        document: Any
    ) -> list[float] | None:
        """
        Convert Document AI bounding_poly to normalized [x, y, width, height]

        Document AI returns vertices as normalized coordinates (0-1 range)
        """
        if not hasattr(bounding_poly, 'normalized_vertices'):
            return None

        vertices = bounding_poly.normalized_vertices
        if len(vertices) < 2:
            return None

        # Get min/max x and y from vertices to calculate bounding box
        x_coords = [v.x for v in vertices if hasattr(v, 'x')]
        y_coords = [v.y for v in vertices if hasattr(v, 'y')]

        if not x_coords or not y_coords:
            return None

        min_x = min(x_coords)
        min_y = min(y_coords)
        max_x = max(x_coords)
        max_y = max(y_coords)

        width = max_x - min_x
        height = max_y - min_y

        return [min_x, min_y, width, height]

    def _extract_tables(self, document: Any) -> list[Table]:
        """Extract tables from Document AI response"""
        tables = []
        for page in document.pages:
            if not hasattr(page, 'tables'):
                continue
            for table in page.tables:
                # Extract headers
                headers = []
                if hasattr(table, 'header_rows') and table.header_rows:
                    header_row = table.header_rows[0]
                    for cell in header_row.cells:
                        headers.append(self._get_text_from_layout(cell.layout, document.text))

                # Extract body rows
                rows = []
                if hasattr(table, 'body_rows'):
                    for row in table.body_rows:
                        row_data = []
                        for cell in row.cells:
                            row_data.append(self._get_text_from_layout(cell.layout, document.text))
                        rows.append(row_data)

                # Calculate average confidence
                confidence = self._calculate_table_confidence(table)

                tables.append(Table(
                    headers=headers,
                    rows=rows,
                    confidence=confidence
                ))
        return tables

    def _get_text_from_layout(self, layout: Any, full_text: str) -> str:
        """Extract text from layout using text anchors"""
        if not hasattr(layout, 'text_anchor'):
            return ""
        if not hasattr(layout.text_anchor, 'text_segments'):
            return ""

        text_segments = layout.text_anchor.text_segments
        if not text_segments:
            return ""

        # Get text from first segment
        segment = text_segments[0]
        start = int(segment.start_index) if hasattr(segment, 'start_index') else 0
        end = int(segment.end_index) if hasattr(segment, 'end_index') else len(full_text)
        return full_text[start:end].strip()

    def _calculate_table_confidence(self, table: Any) -> float:
        """Calculate average confidence for table"""
        # Document AI doesn't provide table-level confidence
        # Return default high confidence for now
        return 0.9

    def _extract_confidence_scores(self, document: Any) -> Dict[str, float]:
        """Extract confidence scores per field"""
        scores = {}
        if hasattr(document, 'entities'):
            for entity in document.entities:
                key = entity.type_
                confidence = entity.confidence if hasattr(entity, 'confidence') else 0.0
                scores[key] = confidence
        return scores

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        reraise=True
    )
    def _call_document_ai_api(self, request: documentai.ProcessRequest):
        """
        Call Document AI API with retry logic

        Retries up to 3 times with exponential backoff (1s, 2s, 4s)

        Args:
            request: Document AI process request

        Returns:
            Document AI response

        Raises:
            DocumentAIException: If API call fails after retries
        """
        try:
            return self.client.process_document(request=request)
        except google_exceptions.ResourceExhausted as e:
            logger.error("Document AI quota exceeded", error=str(e))
            sentry_sdk.capture_exception(e)
            raise DocumentAIException(
                "Document AI API quota exceeded. Please contact administrator.",
                original_error=e
            )
        except google_exceptions.InvalidArgument as e:
            logger.error("Invalid Document AI request", error=str(e))
            sentry_sdk.capture_exception(e)
            raise DocumentAIException(
                "Unsupported file type. Supported formats: PDF, JPEG, PNG.",
                original_error=e
            )
        except google_exceptions.GoogleAPIError as e:
            logger.error("Document AI API error", error=str(e))
            sentry_sdk.capture_exception(e)
            raise DocumentAIException(
                "Document AI API unavailable. Please try again later.",
                original_error=e
            )
