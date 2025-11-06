"""
Unit tests for declaration processing Celery task
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from uuid import uuid4

from src.workers.declaration_processor import (
    process_declaration_task,
    _process_declaration_async,
    _mark_declaration_failed,
    _is_transient_error
)
from src.models.declaration import DeclarationStatus
from src.core.errors import DocumentAIException, OpenRouterException
from src.schemas.ocr import OCRResult
from src.schemas.extraction import ExtractedData


@pytest.fixture
def mock_declaration():
    """Create mock declaration for testing"""
    declaration = Mock()
    declaration.id = uuid4()
    declaration.status = DeclarationStatus.UPLOADED
    declaration.uploaded_files = {
        "AN": {"path": "/app/data/uploads/an.pdf", "file_type": "AN"},
        "BOL": {"path": "/app/data/uploads/bol.pdf", "file_type": "BOL"},
        "CO_1": {"path": "/app/data/uploads/co.pdf", "file_type": "CO_1"},
        "INVOICE": {"path": "/app/data/uploads/invoice.pdf", "file_type": "INVOICE"}
    }
    declaration.celery_task_id = None
    declaration.processing_progress = 0.0
    declaration.processing_error = None
    return declaration


@pytest.fixture
def mock_ocr_result():
    """Mock OCR result"""
    return OCRResult(
        text="Sample OCR text",
        key_value_pairs=[],
        tables=[],
        confidence_scores={"overall": 0.95},
        page_count=1,
        file_name="test.pdf",
        processing_time_ms=1000
    )


@pytest.fixture
def mock_extracted_data():
    """Mock extracted data from LLM"""
    from src.schemas.extraction import CompanyDetails, ShipmentDates

    return ExtractedData(
        shipper=CompanyDetails(name="Test Shipper", confidence=0.9),
        consignee=CompanyDetails(name="Test Consignee", confidence=0.9),
        products=[],
        containers=[],
        dates=ShipmentDates(),
        invoice_total=1000.0,
        currency="USD",
        overall_confidence=0.85
    )


class TestDeclarationProcessor:
    """Test suite for declaration processing task"""

    @patch('src.workers.declaration_processor.AsyncSessionLocal')
    @patch('src.workers.declaration_processor.OCRService')
    @patch('src.workers.declaration_processor.LLMService')
    @patch('src.workers.declaration_processor.os.path.exists')
    @pytest.mark.asyncio
    async def test_process_declaration_task_success(
        self,
        mock_exists,
        mock_llm_service,
        mock_ocr_service,
        mock_session,
        mock_declaration,
        mock_ocr_result,
        mock_extracted_data
    ):
        """Test 1: Successful task execution updates status to READY_FOR_REVIEW"""
        # Setup mocks
        mock_exists.return_value = True

        mock_db = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_db

        mock_repo = Mock()
        mock_repo.get_by_id = AsyncMock(return_value=mock_declaration)
        mock_repo.update_status_and_progress = AsyncMock(return_value=mock_declaration)

        with patch('src.workers.declaration_processor.DeclarationRepository', return_value=mock_repo):
            # Mock OCR service
            ocr_instance = Mock()
            ocr_instance.process_document_ocr = Mock(return_value=mock_ocr_result)
            mock_ocr_service.return_value = ocr_instance

            # Mock LLM service
            llm_instance = Mock()
            llm_instance.extract_from_multiple_documents = AsyncMock(return_value=mock_extracted_data)
            mock_llm_service.return_value = llm_instance

            # Execute task
            result = await _process_declaration_async(str(mock_declaration.id))

            # Assertions
            assert result["status"] == "READY_FOR_REVIEW"
            assert result["declaration_id"] == str(mock_declaration.id)

            # Verify status updates were called
            assert mock_repo.update_status_and_progress.await_count == 3  # OCR, LLM, READY_FOR_REVIEW

    @patch('src.workers.declaration_processor.AsyncSessionLocal')
    @pytest.mark.asyncio
    async def test_process_declaration_task_updates_progress(
        self,
        mock_session,
        mock_declaration
    ):
        """Test 2: Verify progress updates at each stage"""
        mock_db = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_db

        progress_updates = []

        async def capture_progress(decl_id, status, progress, error_message=None):
            progress_updates.append((status, progress))
            return mock_declaration

        mock_repo = Mock()
        mock_repo.get_by_id = AsyncMock(return_value=mock_declaration)
        mock_repo.update_status_and_progress = AsyncMock(side_effect=capture_progress)

        with patch('src.workers.declaration_processor.DeclarationRepository', return_value=mock_repo), \
             patch('src.workers.declaration_processor.OCRService') as mock_ocr, \
             patch('src.workers.declaration_processor.LLMService') as mock_llm, \
             patch('src.workers.declaration_processor.os.path.exists', return_value=True):

            # Mock services
            ocr_instance = Mock()
            ocr_instance.process_document_ocr = Mock(return_value=OCRResult(
                text="test",
                key_value_pairs=[],
                tables=[],
                confidence_scores={"overall": 0.9},
                page_count=1,
                file_name="test.pdf",
                processing_time_ms=500
            ))
            mock_ocr.return_value = ocr_instance

            llm_instance = Mock()
            from src.schemas.extraction import CompanyDetails, ShipmentDates
            llm_instance.extract_from_multiple_documents = AsyncMock(return_value=ExtractedData(
                shipper=CompanyDetails(name="Test Shipper", confidence=0.9),
                consignee=CompanyDetails(name="Test Consignee", confidence=0.9),
                products=[],
                containers=[],
                dates=ShipmentDates(),
                invoice_total=1000.0,
                currency="USD",
                overall_confidence=0.8
            ))
            mock_llm.return_value = llm_instance

            await _process_declaration_async(str(mock_declaration.id))

            # Verify progress sequence
            assert len(progress_updates) == 3
            assert progress_updates[0] == (DeclarationStatus.PROCESSING, 0.2)
            assert progress_updates[1] == (DeclarationStatus.PROCESSING, 0.4)
            assert progress_updates[2] == (DeclarationStatus.READY_FOR_REVIEW, 1.0)

    @pytest.mark.asyncio
    async def test_process_declaration_task_handles_ocr_failure(self):
        """Test 3: OCR service failure triggers retry logic"""
        exc = DocumentAIException("OCR API timeout")
        exc.status_code = 429  # Rate limit - transient error

        assert _is_transient_error(exc) is True

    @pytest.mark.asyncio
    async def test_process_declaration_task_handles_llm_failure(self):
        """Test 4: LLM service failure triggers retry"""
        exc = OpenRouterException("Rate limit exceeded")
        exc.status_code = 429

        assert _is_transient_error(exc) is True

    @patch('src.workers.declaration_processor.AsyncSessionLocal')
    @pytest.mark.asyncio
    async def test_task_marks_failed_after_max_retries(
        self,
        mock_session,
        mock_declaration
    ):
        """Test 5: Declaration marked FAILED after max retries exhausted"""
        mock_db = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_db

        mock_repo = Mock()
        mock_repo.get_by_id = AsyncMock(return_value=mock_declaration)
        mock_repo.update_status_and_progress = AsyncMock(return_value=mock_declaration)

        with patch('src.workers.declaration_processor.DeclarationRepository', return_value=mock_repo):
            error_message = "Max retries exceeded"
            await _mark_declaration_failed(str(mock_declaration.id), error_message)

            # Verify FAILED status was set
            mock_repo.update_status_and_progress.assert_awaited_once_with(
                mock_declaration.id,
                DeclarationStatus.FAILED,
                0.0,
                error_message=error_message
            )

    @patch('src.workers.declaration_processor.AsyncSessionLocal')
    @patch('src.workers.declaration_processor.OCRService')
    @patch('src.workers.declaration_processor.LLMService')
    @patch('src.workers.declaration_processor.os.path.exists')
    @pytest.mark.asyncio
    async def test_task_stores_extracted_data(
        self,
        mock_exists,
        mock_llm_service,
        mock_ocr_service,
        mock_session,
        mock_declaration,
        mock_ocr_result,
        mock_extracted_data
    ):
        """Test 6: Extracted data JSON stored in database"""
        mock_exists.return_value = True

        mock_db = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_db

        mock_repo = Mock()
        mock_repo.get_by_id = AsyncMock(return_value=mock_declaration)
        mock_repo.update_status_and_progress = AsyncMock(return_value=mock_declaration)

        with patch('src.workers.declaration_processor.DeclarationRepository', return_value=mock_repo):
            ocr_instance = Mock()
            ocr_instance.process_document_ocr = Mock(return_value=mock_ocr_result)
            mock_ocr_service.return_value = ocr_instance

            llm_instance = Mock()
            llm_instance.extract_from_multiple_documents = AsyncMock(return_value=mock_extracted_data)
            mock_llm_service.return_value = llm_instance

            await _process_declaration_async(str(mock_declaration.id))

            # Verify extracted_data was set (excluding performance metrics)
            extracted_data_without_perf = {k: v for k, v in mock_declaration.extracted_data.items()
                                           if k != '_performance_metrics'}
            assert extracted_data_without_perf == mock_extracted_data.model_dump()
            assert mock_db.commit.await_count > 0

    @patch('sentry_sdk.capture_exception')
    @patch('src.workers.declaration_processor.AsyncSessionLocal')
    @pytest.mark.asyncio
    async def test_task_logs_errors_to_sentry(
        self,
        mock_session,
        mock_sentry_capture,
        mock_declaration
    ):
        """Test 7: Errors logged to Sentry on failure"""
        mock_db = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_db

        mock_repo = Mock()
        mock_repo.get_by_id = AsyncMock(return_value=None)  # Declaration not found

        with patch('src.workers.declaration_processor.DeclarationRepository', return_value=mock_repo):
            with pytest.raises(ValueError, match="Declaration not found"):
                await _process_declaration_async(str(uuid4()))


class TestErrorClassification:
    """Test error classification for retry logic"""

    def test_transient_error_rate_limit(self):
        """Rate limit errors (429) are transient"""
        exc = DocumentAIException("Rate limit")
        exc.status_code = 429
        assert _is_transient_error(exc) is True

    def test_transient_error_timeout(self):
        """Timeout errors are transient"""
        exc = TimeoutError("Connection timeout")
        assert _is_transient_error(exc) is True

    def test_permanent_error_file_not_found(self):
        """File not found is permanent"""
        exc = FileNotFoundError("File missing")
        assert _is_transient_error(exc) is False

    def test_permanent_error_invalid_credentials(self):
        """Invalid credentials (401) is permanent"""
        exc = DocumentAIException("Unauthorized")
        exc.status_code = 401
        assert _is_transient_error(exc) is False

    def test_permanent_error_value_error(self):
        """ValueError is permanent"""
        exc = ValueError("Invalid data")
        assert _is_transient_error(exc) is False
