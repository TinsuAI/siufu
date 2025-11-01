"""
Declaration processing Celery task

Orchestrates full customs declaration processing pipeline:
1. OCR processing of PDF documents (AN, BOL, CO (1-20 files), INVOICE)
2. LLM extraction of structured data
3. Validation of extracted data

Updated in Story 3.3.1: Certificate of Origin now supports 1-20 files
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
# Use NullPool to avoid connection pooling issues in forked processes
from sqlalchemy.pool import NullPool

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    poolclass=NullPool  # Disable pooling for celery workers to avoid connection sharing
)
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


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

        # Log successful completion with performance metrics
        total_duration = time.time() - task_start_time
        logger.info(
            f"Declaration processing completed successfully",
            extra={
                "declaration_id": declaration_id,
                "total_duration_seconds": total_duration,
                "ocr_duration_seconds": result.get("ocr_duration", 0),
                "llm_duration_seconds": result.get("llm_duration", 0),
                "storage_duration_seconds": result.get("storage_duration", 0),
                "status": result["status"]
            }
        )

        # Log performance metrics to Sentry
        sentry_sdk.set_measurement("task_total_duration_seconds", total_duration)
        sentry_sdk.set_measurement("task_ocr_duration_seconds", result.get("ocr_duration", 0))
        sentry_sdk.set_measurement("task_llm_duration_seconds", result.get("llm_duration", 0))
        sentry_sdk.set_measurement("task_storage_duration_seconds", result.get("storage_duration", 0))

        # Alert if processing exceeds 90 seconds (NFR1 violation)
        if total_duration > 90:
            sentry_sdk.capture_message(
                f"Processing duration exceeded 90s target: {total_duration:.1f}s",
                level="warning"
            )

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

            # Log the failure (database update will be handled by Celery retry/failure handlers)
            logger.error(
                f"Marking declaration as FAILED due to permanent error",
                extra={
                    "declaration_id": declaration_id,
                    "error_message": str(exc)
                }
            )

            sentry_sdk.capture_exception(exc)
            # Let Celery handle the task failure
            raise

    except Exception as exc:
        # Unexpected error - log and fail
        logger.exception(
            f"Unexpected error during declaration processing",
            extra={"declaration_id": declaration_id}
        )

        # Log unexpected error
        logger.error(
            f"Marking declaration as FAILED due to unexpected error",
            extra={
                "declaration_id": declaration_id,
                "error_message": f"{type(exc).__name__}: {str(exc)}"
            }
        )

        sentry_sdk.capture_exception(exc)
        # Let Celery handle the task failure
        raise


async def _process_declaration_async(declaration_id: str) -> Dict[str, Any]:
    """
    Async implementation of declaration processing pipeline

    Args:
        declaration_id: UUID string of declaration

    Returns:
        dict with status, declaration_id, and timing metrics
    """
    ocr_start = time.time()

    async with AsyncSessionLocal() as db:
        repo = DeclarationRepository(db)

        # Load declaration
        declaration = await repo.get_by_id(UUID(declaration_id))
        if not declaration:
            raise ValueError(f"Declaration not found: {declaration_id}")

        # Validate uploaded_files structure
        if not declaration.uploaded_files:
            raise ValueError("No uploaded files found in declaration")

        # Convert uploaded_files list to dict keyed by file_type
        uploaded_files_list = declaration.uploaded_files
        uploaded_files = {}

        # Handle both list format (from Story 1.6) and dict format
        if isinstance(uploaded_files_list, list):
            for file_metadata in uploaded_files_list:
                file_type = file_metadata.get("file_type")
                if file_type:
                    uploaded_files[file_type] = file_metadata
        elif isinstance(uploaded_files_list, dict):
            uploaded_files = uploaded_files_list
        else:
            raise ValueError(f"Invalid uploaded_files structure: {type(uploaded_files_list)}")

        # Required single-file docs (Updated in Story 3.3.1: CO is now multi-file)
        required_single_docs = ["AN", "BOL", "INVOICE"]

        # Stage 1: Update to PROCESSING_OCR status
        logger.info(f"Stage 1: Starting OCR processing", extra={"declaration_id": declaration_id})
        await repo.update_status_and_progress(
            UUID(declaration_id),
            DeclarationStatus.PROCESSING_OCR,
            0.2
        )
        sentry_sdk.set_tag("processing_stage", "PROCESSING_OCR")

        # Track OCR stage start time
        stage_start = time.time()

        # Process all PDFs through OCR in parallel
        # Updated in Story 3.3.1: Handle multiple CO files (CO_1, CO_2, etc.)
        ocr_service = OCRService()
        ocr_tasks = []

        # Process single-file documents
        for doc_type in required_single_docs:
            if doc_type not in uploaded_files:
                raise ValueError(f"Missing required document: {doc_type}")

            file_path = uploaded_files[doc_type].get("path")
            if not file_path or not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found for {doc_type}: {file_path}")

            # Create async task for OCR processing
            loop = asyncio.get_event_loop()
            ocr_task = loop.run_in_executor(None, ocr_service.process_document_ocr, file_path)
            ocr_tasks.append((doc_type, ocr_task))

        # Process all CO files (CO_1, CO_2, ..., CO_N)
        co_files = {k: v for k, v in uploaded_files.items() if k.startswith("CO_")}
        if not co_files:
            raise ValueError("Missing required document: CO (Certificate of Origin)")

        for doc_type, file_metadata in co_files.items():
            file_path = file_metadata.get("path")
            if not file_path or not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found for {doc_type}: {file_path}")

            # Create async task for OCR processing
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

        # Combine multiple CO OCR results into one (Updated in Story 3.3.1)
        # LLM service expects single OCRResult, but we may have CO_1, CO_2, etc.
        co_ocr_combined = None
        co_results_list = sorted([
            (k, v) for k, v in ocr_results.items() if k.startswith("CO_")
        ], key=lambda x: x[0])  # Sort by key to ensure CO_1, CO_2, ... order

        if co_results_list:
            # Combine all CO OCR texts
            combined_text = "\n\n=== COMBINED CERTIFICATE OF ORIGIN FILES ===\n\n"
            combined_key_value_pairs = []
            combined_tables = []
            combined_confidence_scores = {}

            for idx, (co_key, co_result) in enumerate(co_results_list, 1):
                combined_text += f"=== FILE {idx} ({co_key}) ===\n{co_result.text}\n\n"
                combined_key_value_pairs.extend(co_result.key_value_pairs)
                combined_tables.extend(co_result.tables)
                # Prefix confidence score keys with file number to avoid conflicts
                for k, v in co_result.confidence_scores.items():
                    combined_confidence_scores[f"{co_key}_{k}"] = v

            # Create combined OCRResult
            from src.schemas.ocr import OCRResult
            co_ocr_combined = OCRResult(
                text=combined_text,
                key_value_pairs=combined_key_value_pairs,
                tables=combined_tables,
                confidence_scores=combined_confidence_scores,
                page_count=sum(r[1].page_count for r in co_results_list),
                file_name=f"COMBINED_CO_({len(co_results_list)}_files)",
                processing_time_ms=sum(r[1].processing_time_ms for r in co_results_list)
            )

        # Extract structured data using LLM
        llm_service = LLMService()
        extracted_data = await llm_service.extract_from_multiple_documents(
            ocr_an=ocr_results.get("AN"),
            ocr_bol=ocr_results.get("BOL"),
            ocr_co=co_ocr_combined,
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

        # Stage 3: Store extracted data in database
        stage_start = time.time()
        logger.info(f"Stage 3: Storing extracted data", extra={"declaration_id": declaration_id})

        # Store extracted data and confidence scores in declaration
        declaration = await repo.get_by_id(UUID(declaration_id))
        declaration.extracted_data = extracted_data.model_dump()
        declaration.confidence_scores = extracted_data.confidence_scores
        await db.commit()

        storage_duration = time.time() - stage_start
        logger.info(
            f"Data storage complete",
            extra={
                "declaration_id": declaration_id,
                "duration_seconds": storage_duration,
                "overall_confidence": extracted_data.overall_confidence,
                "product_count": len(extracted_data.products)
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

        # Store performance metrics in declaration metadata for analytics
        performance_metadata = {
            "ocr_duration_seconds": ocr_duration,
            "llm_duration_seconds": llm_duration,
            "storage_duration_seconds": storage_duration,
            "total_duration_seconds": ocr_duration + llm_duration + storage_duration
        }

        # Update declaration with performance metadata
        declaration = await repo.get_by_id(UUID(declaration_id))
        if not declaration.extracted_data:
            declaration.extracted_data = {}
        declaration.extracted_data["_performance_metrics"] = performance_metadata
        await db.commit()

        return {
            "status": "READY_FOR_REVIEW",
            "declaration_id": declaration_id,
            "ocr_duration": ocr_duration,
            "llm_duration": llm_duration,
            "storage_duration": storage_duration
        }


def _mark_declaration_failed_sync(declaration_id: str, error_message: str) -> None:
    """
    Mark declaration as FAILED with error message (synchronous version for Celery error handlers)

    Args:
        declaration_id: UUID string
        error_message: Error description
    """
    async def _do_mark_failed():
        async with AsyncSessionLocal() as db:
            repo = DeclarationRepository(db)
            await repo.update_status_and_progress(
                UUID(declaration_id),
                DeclarationStatus.FAILED,
                0.0,
                error_message=error_message
            )

    # Run in a new event loop (safe for Celery tasks)
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_do_mark_failed())
    finally:
        loop.close()


async def _mark_declaration_failed(declaration_id: str, error_message: str) -> None:
    """
    Mark declaration as FAILED with error message (async version)

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
