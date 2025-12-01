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
from datetime import UTC, datetime
from typing import Any, Dict, Optional
from uuid import UUID

import sentry_sdk
from celery import Task
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.celery_app import celery_app
from src.core.config import settings
from src.core.errors import DocumentAIException, OpenRouterException
from src.models.declaration import Declaration, DeclarationStatus
from src.repositories.declaration_repository import DeclarationRepository
from src.services import master_data_service
from src.services.income_validation_service import IncomeValidationService
from src.services.llm_service import LLMService
from src.services.ocr_service import process_document_ocr_sync

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


def transform_vietnamese_to_draft(extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    **DEPRECATED**: This function is no longer used. Frontend now uses Vietnamese schema directly.

    Transform Vietnamese declaration data structure to match OLD frontend form schema.

    Converts from LLM extraction format (importer, exporter, products, vat, invoice)
    to OLD frontend form format (company_info, shipment_details, products, tax_calculations)

    This function is kept for backward compatibility with existing test data only.
    New declarations should use Vietnamese schema directly.
    """
    importer = extracted_data.get("importer", {})
    invoice = extracted_data.get("invoice", {})
    products = extracted_data.get("products", [])
    vat = extracted_data.get("vat", {})
    import_duty = extracted_data.get("import_duty", {})

    # Transform products array
    transformed_products = []
    for product in products:
        transformed_products.append({
            "description": product.get("product_description", ""),
            "hs_code": product.get("hs_code", ""),
            "quantity": product.get("quantity_1", 0),
            "unit": product.get("quantity_unit_1", ""),
            "unit_price": product.get("invoice_unit_price", 0),
            "total_price": product.get("invoice_line_total", 0),
            "origin_country": product.get("country_of_origin_code", "")
        })

    # Calculate tax totals
    vat_amount = vat.get("amount", 0)
    import_duty_amount = import_duty.get("amount", 0)
    total_tax = vat_amount + import_duty_amount
    invoice_total = invoice.get("invoice_total", 0)
    grand_total = invoice_total + total_tax

    # Build draft data in form schema format
    draft_data = {
        "company_info": {
            "importer_name": importer.get("name", ""),
            "tax_id": importer.get("tax_code", ""),
            "address": importer.get("address", ""),
            "city": "",  # Not in Vietnamese format, leave empty
            "country": "VN",  # Default to Vietnam
            "contact_person": "",  # Not in Vietnamese format
            "contact_email": "",  # Not in Vietnamese format
            "contact_phone": importer.get("phone", "")
        },
        "shipment_details": {
            "bol_number": invoice.get("invoice_number", ""),
            "arrival_date": invoice.get("invoice_date", ""),
            "port_of_arrival": "",  # Not in Vietnamese format
            "port_of_departure": "",  # Not in Vietnamese format
            "container_numbers": [""],  # Not in Vietnamese format
            "vessel_name": ""  # Not in Vietnamese format
        },
        "products": transformed_products if transformed_products else [{
            "description": "",
            "hs_code": "",
            "quantity": 0,
            "unit": "",
            "unit_price": 0,
            "total_price": 0,
            "origin_country": ""
        }],
        "tax_calculations": {
            "subtotal": invoice_total,
            "vat_rate": vat.get("rate", 0),
            "vat_amount": vat_amount,
            "import_duty_rate": import_duty.get("rate", 0),
            "import_duty_amount": import_duty_amount,
            "total_tax": total_tax,
            "grand_total": grand_total
        }
    }

    return draft_data


async def add_processing_log(
    db: AsyncSession,
    declaration_id: UUID,
    level: str,
    message: str,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Add entry to declaration processing_log

    Args:
        db: Database session
        declaration_id: Declaration UUID
        level: Log level (info, success, warning, error)
        message: Log message
        details: Optional additional details
    """
    log_entry = {
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "level": level,
        "message": message,
    }
    if details:
        log_entry["details"] = details

    # Fetch current log, append new entry, update
    result = await db.execute(
        select(Declaration.processing_log).where(Declaration.id == declaration_id)
    )
    current_log = result.scalar_one_or_none() or []
    current_log.append(log_entry)

    await db.execute(
        update(Declaration)
        .where(Declaration.id == declaration_id)
        .values(processing_log=current_log)
    )
    await db.commit()


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
    1. PROCESSING (progress: 0.2) - OCR extraction from PDFs
    2. PROCESSING (progress: 0.4) - LLM data extraction
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
            "Declaration processing completed successfully",
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
                "Permanent error occurred, marking declaration as FAILED",
                extra={
                    "declaration_id": declaration_id,
                    "error": str(exc),
                    "error_type": type(exc).__name__
                }
            )

            # Log the failure (database update will be handled by Celery retry/failure handlers)
            logger.error(
                "Marking declaration as FAILED due to permanent error",
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
            "Unexpected error during declaration processing",
            extra={"declaration_id": declaration_id}
        )

        # Log unexpected error
        logger.error(
            "Marking declaration as FAILED due to unexpected error",
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
    _ = time.time()  # Reserved for future timing metrics

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

        # Stage 1: Update to PROCESSING status (OCR stage)
        logger.info("Stage 1: Starting OCR processing", extra={"declaration_id": declaration_id})
        await repo.update_status_and_progress(
            UUID(declaration_id),
            DeclarationStatus.PROCESSING,
            0.2
        )
        sentry_sdk.set_tag("processing_stage", "OCR")

        # Log OCR start
        await add_processing_log(
            db,
            UUID(declaration_id),
            "info",
            "Starting OCR processing",
            {"stage": "OCR", "files_to_process": len(list(uploaded_files.keys()))}
        )

        # Track OCR stage start time
        stage_start = time.time()

        # Process all PDFs through OCR in parallel using Gemini Vision via OpenRouter
        # Updated in Story 3.3.1: Handle multiple CO files (CO_1, CO_2, etc.)
        ocr_tasks = []

        # Process single-file documents
        for doc_type in required_single_docs:
            if doc_type not in uploaded_files:
                raise ValueError(f"Missing required document: {doc_type}")

            file_path = uploaded_files[doc_type].get("path")
            if not file_path or not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found for {doc_type}: {file_path}")

            # Create async task for OCR processing (using sync wrapper in executor)
            loop = asyncio.get_event_loop()
            ocr_task = loop.run_in_executor(None, process_document_ocr_sync, file_path)
            ocr_tasks.append((doc_type, ocr_task))

        # Process all CO files (CO_1, CO_2, ..., CO_N)
        co_files = {k: v for k, v in uploaded_files.items() if k.startswith("CO_")}
        if not co_files:
            raise ValueError("Missing required document: CO (Certificate of Origin)")

        for doc_type, file_metadata in co_files.items():
            file_path = file_metadata.get("path")
            if not file_path or not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found for {doc_type}: {file_path}")

            # Create async task for OCR processing (using sync wrapper in executor)
            loop = asyncio.get_event_loop()
            ocr_task = loop.run_in_executor(None, process_document_ocr_sync, file_path)
            ocr_tasks.append((doc_type, ocr_task))

        # Wait for all OCR tasks to complete
        ocr_results = {}
        for doc_type, task in ocr_tasks:
            ocr_results[doc_type] = await task

        ocr_duration = time.time() - stage_start
        logger.info(
            "OCR processing complete",
            extra={
                "declaration_id": declaration_id,
                "duration_seconds": ocr_duration,
                "documents_processed": len(ocr_results)
            }
        )

        # Log OCR complete
        await add_processing_log(
            db,
            UUID(declaration_id),
            "success",
            "OCR processing complete",
            {"documents_processed": len(ocr_results), "duration_seconds": round(ocr_duration, 2)}
        )

        # Stage 2: Continue PROCESSING status (LLM stage)
        stage_start = time.time()
        logger.info("Stage 2: Starting LLM extraction", extra={"declaration_id": declaration_id})
        await repo.update_status_and_progress(
            UUID(declaration_id),
            DeclarationStatus.PROCESSING,
            0.4
        )
        sentry_sdk.set_tag("processing_stage", "LLM")

        # Log LLM start
        await add_processing_log(
            db,
            UUID(declaration_id),
            "info",
            "Starting LLM data extraction",
            {"stage": "LLM"}
        )

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
            "LLM extraction complete",
            extra={
                "declaration_id": declaration_id,
                "duration_seconds": llm_duration,
                "overall_confidence": extracted_data.overall_confidence
            }
        )

        # Log LLM complete
        await add_processing_log(
            db,
            UUID(declaration_id),
            "success",
            "LLM data extraction complete",
            {
                "duration_seconds": round(llm_duration, 2),
                "overall_confidence": round(extracted_data.overall_confidence, 2)
            }
        )

        # Build source metadata mapping (Story 3.7)
        from src.services.extraction_service import ExtractionService
        extraction_service = ExtractionService()

        # Map OCR results to document types (exclude multi-CO results, use combined)
        ocr_by_type = {
            "AN": ocr_results.get("AN"),
            "BOL": ocr_results.get("BOL"),
            "CO": co_ocr_combined,  # Use combined CO OCR
            "INVOICE": ocr_results.get("INVOICE")
        }
        # Remove None values
        ocr_by_type = {k: v for k, v in ocr_by_type.items() if v is not None}

        source_metadata = extraction_service.build_source_metadata(
            extracted_data=extracted_data.model_dump(),
            ocr_results=ocr_by_type,
            file_type_mapping=extraction_service.get_default_field_type_mapping()
        )

        logger.info(
            "Source metadata generated",
            extra={
                "declaration_id": declaration_id,
                "metadata_field_count": len(source_metadata)
            }
        )

        # Stage 3: Cross-document validation (Story 3.11)
        validation_start = time.time()
        logger.info("Stage 3: Running cross-document validation", extra={"declaration_id": declaration_id})

        # Update progress to VALIDATING status
        await repo.update_status_and_progress(
            UUID(declaration_id),
            DeclarationStatus.VALIDATING,
            0.7
        )
        sentry_sdk.set_tag("processing_stage", "VALIDATING")

        # Run validation service
        validation_service = IncomeValidationService()
        extracted_dict = extracted_data.model_dump()
        validation_warnings = validation_service.validate_declaration(extracted_dict)

        # Log validation results
        validation_duration = time.time() - validation_start
        await add_processing_log(
            db,
            UUID(declaration_id),
            "info",
            f"Cross-document validation complete - {len(validation_warnings)} warnings found",
            {
                "duration_seconds": round(validation_duration, 2),
                "warning_count": len(validation_warnings),
                "error_count": len([w for w in validation_warnings if w["severity"] == "error"]),
                "warning_severity_count": len([w for w in validation_warnings if w["severity"] == "warning"]),
                "info_count": len([w for w in validation_warnings if w["severity"] == "info"])
            }
        )

        logger.info(
            "Validation complete",
            extra={
                "declaration_id": declaration_id,
                "duration_seconds": validation_duration,
                "warning_count": len(validation_warnings)
            }
        )

        # Stage 3a: Store extracted data in database
        stage_start = time.time()
        logger.info("Stage 3a: Matching master data and storing extracted data", extra={"declaration_id": declaration_id})

        # Store extracted data and confidence scores in declaration
        declaration = await repo.get_by_id(UUID(declaration_id))

        # Story 3.10: Match importer against master data
        extracted_dict = extracted_data.model_dump()
        importer_data = extracted_dict.get("importer", {})

        if importer_data:
            matched_importer = await master_data_service.match_importer(
                extracted_tax_code=importer_data.get("tax_code"),
                extracted_name=importer_data.get("name"),
                organization_id=declaration.organization_id,
                db=db
            )

            if matched_importer:
                logger.info(
                    "Matched importer from master data",
                    extra={
                        "declaration_id": declaration_id,
                        "importer_id": str(matched_importer.id),
                        "importer_name": matched_importer.name
                    }
                )

                # Replace extracted data with master data
                extracted_dict["importer"] = {
                    "tax_code": matched_importer.tax_code,
                    "name": matched_importer.name,
                    "postal_code": matched_importer.postal_code,
                    "address": matched_importer.address,
                    "phone": matched_importer.phone
                }

                # Set confidence scores to 1.0 for master data fields
                if "confidence_scores" not in extracted_dict:
                    extracted_dict["confidence_scores"] = {}
                extracted_dict["confidence_scores"]["importer_tax_code"] = 1.0
                extracted_dict["confidence_scores"]["importer_name"] = 1.0
                extracted_dict["confidence_scores"]["importer_address"] = 1.0

                # Link declaration to importer
                declaration.importer_id = matched_importer.id

                # Update importer statistics
                matched_importer.declaration_count += 1
                matched_importer.last_seen_declaration_id = declaration.id

        # Story 3.10: Match exporter against master data
        exporter_data = extracted_dict.get("exporter", {})

        if exporter_data:
            matched_exporter = await master_data_service.match_exporter(
                extracted_name=exporter_data.get("name"),
                extracted_country_code=exporter_data.get("country_code"),
                organization_id=declaration.organization_id,
                db=db
            )

            if matched_exporter:
                logger.info(
                    "Matched exporter from master data",
                    extra={
                        "declaration_id": declaration_id,
                        "exporter_id": str(matched_exporter.id),
                        "exporter_name": matched_exporter.name
                    }
                )

                # Replace extracted data with master data
                extracted_dict["exporter"] = {
                    "name": matched_exporter.name,
                    "country_code": matched_exporter.country_code,
                    "address_line1": matched_exporter.address_line1,
                    "address_line2": matched_exporter.address_line2,
                    "address_line3": matched_exporter.address_line3
                }

                # Set confidence scores to 1.0 for master data fields
                if "confidence_scores" not in extracted_dict:
                    extracted_dict["confidence_scores"] = {}
                extracted_dict["confidence_scores"]["exporter_name"] = 1.0
                extracted_dict["confidence_scores"]["exporter_country"] = 1.0
                extracted_dict["confidence_scores"]["exporter_address"] = 1.0

                # Link declaration to exporter
                declaration.exporter_id = matched_exporter.id

                # Update exporter statistics
                matched_exporter.declaration_count += 1
                matched_exporter.last_seen_declaration_id = declaration.id

        declaration.extracted_data = extracted_dict

        # Store validation warnings (Story 3.11)
        declaration.validation_warnings = validation_warnings

        # Build confidence scores dict from extracted data
        confidence_scores = {
            "overall": extracted_data.overall_confidence
        }

        # Add shipper/consignee confidence if available
        if hasattr(extracted_data, 'shipper') and extracted_data.shipper:
            confidence_scores["shipper"] = extracted_data.shipper.confidence
        if hasattr(extracted_data, 'consignee') and extracted_data.consignee:
            confidence_scores["consignee"] = extracted_data.consignee.confidence

        # Add date confidence scores if available
        if hasattr(extracted_data, 'dates') and extracted_data.dates and hasattr(extracted_data.dates, 'confidence_scores') and extracted_data.dates.confidence_scores:
            for key, value in extracted_data.dates.confidence_scores.items():
                confidence_scores[f"date_{key}"] = value

        # Add product confidence scores
        if hasattr(extracted_data, 'products') and extracted_data.products:
            for idx, product in enumerate(extracted_data.products):
                if hasattr(product, 'confidence_scores') and product.confidence_scores:
                    for key, value in product.confidence_scores.items():
                        confidence_scores[f"product_{idx}_{key}"] = value

        # Add container confidence scores
        if hasattr(extracted_data, 'containers') and extracted_data.containers:
            for idx, container in enumerate(extracted_data.containers):
                if hasattr(container, 'confidence'):
                    confidence_scores[f"container_{idx}"] = container.confidence

        declaration.confidence_scores = confidence_scores
        declaration.source_metadata = source_metadata  # Store source metadata (Story 3.7)

        # Store extracted data directly as draft_data (Vietnamese schema)
        # Frontend now uses Vietnamese schema (declaration_header, importer, exporter, etc.)
        # Note: extracted_dict was already created above for master data matching
        declaration.draft_data = extracted_dict  # No longer transform to old schema
        await db.commit()

        storage_duration = time.time() - stage_start
        logger.info(
            "Data storage complete",
            extra={
                "declaration_id": declaration_id,
                "duration_seconds": storage_duration,
                "overall_confidence": extracted_data.overall_confidence,
                "product_count": len(extracted_data.products)
            }
        )

        # Stage 4: Update to READY_FOR_REVIEW status
        logger.info("Stage 4: Marking as ready for review", extra={"declaration_id": declaration_id})
        await repo.update_status_and_progress(
            UUID(declaration_id),
            DeclarationStatus.READY_FOR_REVIEW,
            1.0
        )
        sentry_sdk.set_tag("processing_stage", "READY_FOR_REVIEW")

        # Log completion
        total_duration = ocr_duration + llm_duration + validation_duration + storage_duration
        await add_processing_log(
            db,
            UUID(declaration_id),
            "success",
            "Declaration processing complete - Ready for review",
            {
                "total_duration_seconds": round(total_duration, 2),
                "product_count": len(extracted_data.products)
            }
        )

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
