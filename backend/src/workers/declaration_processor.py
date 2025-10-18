"""
Declaration processing Celery task

Orchestrates full customs declaration processing pipeline:
1. OCR processing of 4 PDF documents (AN, BOL, CO, INVOICE)
2. LLM extraction of structured data
3. Validation of extracted data
4. Progress tracking throughout

Expected duration: 52-85 seconds (within 90 second NFR1 requirement)
"""
import asyncio
import logging
import os
import time
from typing import Dict, Any
from uuid import UUID

import sentry_sdk
from celery import Task
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.core.celery_app import celery_app
from src.core.config import settings
from src.core.errors import DocumentAIException, OpenRouterException
from src.models.declaration import DeclarationStatus
from src.repositories.declaration_repository import DeclarationRepository
from src.services.ocr_service import OCRService
from src.services.llm_service import LLMService

logger = logging.getLogger(__name__)

# Create async database engine for Celery tasks
engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class DeclarationProcessingTask(Task):
    """Custom task class with error handling and retry logic"""

    # Exponential backoff: 60s, 120s, 240s
    autoretry_for = ()  # We handle retries manually for granular control
    retry_kwargs = {'max_retries': 3}
    retry_backoff = True
    retry_backoff_max = 240
    retry_jitter = False


@celery_app.task(
    bind=True,
    base=DeclarationProcessingTask,
    name="process_declaration_task",
    max_retries=3
)
def process_declaration_task(self, declaration_id: str) -> Dict[str, Any]:
    """
    Process a customs declaration through full pipeline

    Task progresses through stages:
    1. PROCESSING_OCR (progress: 0.1) - OCR extraction from PDFs
    2. PROCESSING_LLM (progress: 0.4) - LLM data extraction
    3. VALIDATING (progress: 0.7) - Data validation
    4. READY_FOR_REVIEW (progress: 1.0) - Complete

    Args:
        declaration_id: UUID of declaration to process (as string)

    Returns:
        dict: {"status": str, "declaration_id": str}

    Raises:
        Retry: For transient errors (API timeouts, rate limits)
        Ignore: For permanent errors (file not found, invalid data)
    """
    task_start_time = time.time()

    # Add Sentry context
    sentry_sdk.set_tag("task_name", "process_declaration_task")
    sentry_sdk.set_tag("declaration_id", declaration_id)
    sentry_sdk.set_tag("retry_count", self.request.retries)
    sentry_sdk.add_breadcrumb(
        category="celery",
        message=f"Task started (attempt {self.request.retries + 1}/4)",
        level="info"
    )

    try:
        # Run async processing
        result = asyncio.run(_process_declaration_async(declaration_id))

        # Log successful completion
        duration = time.time() - task_start_time
        logger.info(
            f"Declaration processing completed successfully",
            extra={
                "declaration_id": declaration_id,
                "duration_seconds": duration,
                "status": result["status"]
            }
        )
        sentry_sdk.set_measurement("task_duration_seconds", duration)

        return result

    except (DocumentAIException, OpenRouterException) as exc:
        # Check if error is transient (should retry)
        if _is_transient_error(exc):
            # Calculate backoff based on retry attempt
            countdown = min(60 * (2 ** self.request.retries), 240)

            logger.warning(
                f"Transient error occurred, retrying in {countdown}s",
                extra={
                    "declaration_id": declaration_id,
                    "error": str(exc),
                    "retry_attempt": self.request.retries + 1
                }
            )

            sentry_sdk.add_breadcrumb(
                category="celery",
                message=f"Retry attempt {self.request.retries + 1}/3",
                level="warning"
            )

            # Retry with exponential backoff
            raise self.retry(exc=exc, countdown=countdown)
        else:
            # Permanent error - fail immediately
            logger.error(
                f"Permanent error occurred, marking declaration as FAILED",
                extra={
                    "declaration_id": declaration_id,
                    "error": str(exc),
                    "error_type": type(exc).__name__
                }
            )

            # Update declaration status to FAILED
            asyncio.run(_mark_declaration_failed(declaration_id, str(exc)))

            sentry_sdk.capture_exception(exc)
            raise

    except Exception as exc:
        # Unexpected error - log and fail
        logger.exception(
            f"Unexpected error during declaration processing",
            extra={"declaration_id": declaration_id}
        )

        asyncio.run(_mark_declaration_failed(
            declaration_id,
            f"Unexpected error: {type(exc).__name__}: {str(exc)}"
        ))

        sentry_sdk.capture_exception(exc)
        raise


async def _process_declaration_async(declaration_id: str) -> Dict[str, Any]:
    """
    Async implementation of declaration processing pipeline

    Args:
        declaration_id: UUID string of declaration

    Returns:
        dict with status and declaration_id
    """
    stage_start = time.time()

    async with AsyncSessionLocal() as db:
        repo = DeclarationRepository(db)

        # Load declaration
        declaration = await repo.get_by_id(UUID(declaration_id))
        if not declaration:
            raise ValueError(f"Declaration not found: {declaration_id}")

        # Validate uploaded_files structure
        if not declaration.uploaded_files:
            raise ValueError("No uploaded files found in declaration")

        uploaded_files = declaration.uploaded_files
        required_docs = ["AN", "BOL", "CO", "INVOICE"]

        # Stage 1: Update to PROCESSING_OCR status
        logger.info(f"Stage 1: Starting OCR processing", extra={"declaration_id": declaration_id})
        await repo.update_status_and_progress(
            UUID(declaration_id),
            DeclarationStatus.PROCESSING_OCR,
            0.1
        )
        sentry_sdk.set_tag("processing_stage", "PROCESSING_OCR")

        # Process all 4 PDFs through OCR in parallel
        ocr_service = OCRService()
        ocr_tasks = []

        for doc_type in required_docs:
            if doc_type not in uploaded_files:
                raise ValueError(f"Missing required document: {doc_type}")

            file_path = uploaded_files[doc_type].get("path")
            if not file_path or not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found for {doc_type}: {file_path}")

            # Create async task for OCR processing
            # Note: OCRService.process_document_ocr is synchronous, so we run it in executor
            loop = asyncio.get_event_loop()
            ocr_task = loop.run_in_executor(None, ocr_service.process_document_ocr, file_path)
            ocr_tasks.append((doc_type, ocr_task))

        # Wait for all OCR tasks to complete
        ocr_results = {}
        for doc_type, task in ocr_tasks:
            ocr_results[doc_type] = await task

        ocr_duration = time.time() - stage_start
        logger.info(
            f"OCR processing complete",
            extra={
                "declaration_id": declaration_id,
                "duration_seconds": ocr_duration,
                "documents_processed": len(ocr_results)
            }
        )

        # Stage 2: Update to PROCESSING_LLM status
        stage_start = time.time()
        logger.info(f"Stage 2: Starting LLM extraction", extra={"declaration_id": declaration_id})
        await repo.update_status_and_progress(
            UUID(declaration_id),
            DeclarationStatus.PROCESSING_LLM,
            0.4
        )
        sentry_sdk.set_tag("processing_stage", "PROCESSING_LLM")

        # Extract structured data using LLM
        llm_service = LLMService()
        extracted_data = await llm_service.extract_from_multiple_documents(
            ocr_an=ocr_results.get("AN"),
            ocr_bol=ocr_results.get("BOL"),
            ocr_co=ocr_results.get("CO"),
            ocr_invoice=ocr_results.get("INVOICE")
        )

        llm_duration = time.time() - stage_start
        logger.info(
            f"LLM extraction complete",
            extra={
                "declaration_id": declaration_id,
                "duration_seconds": llm_duration,
                "overall_confidence": extracted_data.overall_confidence
            }
        )

        # Stage 3: Update to VALIDATING status
        stage_start = time.time()
        logger.info(f"Stage 3: Validating data", extra={"declaration_id": declaration_id})
        await repo.update_status_and_progress(
            UUID(declaration_id),
            DeclarationStatus.VALIDATING,
            0.7
        )
        sentry_sdk.set_tag("processing_stage", "VALIDATING")

        # Store extracted data in declaration
        declaration = await repo.get_by_id(UUID(declaration_id))
        declaration.extracted_data = extracted_data.model_dump()
        declaration.confidence_scores = {
            "overall": extracted_data.overall_confidence,
            "shipper": extracted_data.shipper.confidence if extracted_data.shipper else 0.0,
            "consignee": extracted_data.consignee.confidence if extracted_data.consignee else 0.0,
        }
        await db.commit()

        validation_duration = time.time() - stage_start
        logger.info(
            f"Validation complete",
            extra={
                "declaration_id": declaration_id,
                "duration_seconds": validation_duration
            }
        )

        # Stage 4: Update to READY_FOR_REVIEW status
        logger.info(f"Stage 4: Marking as ready for review", extra={"declaration_id": declaration_id})
        await repo.update_status_and_progress(
            UUID(declaration_id),
            DeclarationStatus.READY_FOR_REVIEW,
            1.0
        )
        sentry_sdk.set_tag("processing_stage", "READY_FOR_REVIEW")

        return {
            "status": "READY_FOR_REVIEW",
            "declaration_id": declaration_id
        }


async def _mark_declaration_failed(declaration_id: str, error_message: str) -> None:
    """
    Mark declaration as FAILED with error message

    Args:
        declaration_id: UUID string
        error_message: Error description
    """
    async with AsyncSessionLocal() as db:
        repo = DeclarationRepository(db)
        await repo.update_status_and_progress(
            UUID(declaration_id),
            DeclarationStatus.FAILED,
            0.0,
            error_message=error_message
        )


def _is_transient_error(exc: Exception) -> bool:
    """
    Determine if error is transient (should retry) or permanent (fail immediately)

    Transient errors:
    - Rate limits (429)
    - Timeouts
    - Redis connection errors

    Permanent errors:
    - File not found
    - Invalid credentials (401)
    - Invalid data (ValueError)

    Args:
        exc: Exception to classify

    Returns:
        True if transient (should retry), False if permanent
    """
    # Check for rate limit errors
    if hasattr(exc, 'status_code') and exc.status_code == 429:
        return True

    # Check for timeout errors
    if isinstance(exc, TimeoutError) or "timeout" in str(exc).lower():
        return True

    # Check for connection errors
    if "connection" in str(exc).lower() or "redis" in str(exc).lower():
        return True

    # All other errors are permanent
    return False
