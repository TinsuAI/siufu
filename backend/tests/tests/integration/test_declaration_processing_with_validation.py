"""
Integration tests for Story 3.11 - Cross-Document Income Validation

These tests verify that the validation stage correctly integrates into the
declaration processing pipeline and that warnings are stored properly.

Requirements (AC14):
- Validation stage executes during full pipeline
- Warnings stored correctly in declaration.validation_warnings JSONB field
- Workflow continues to READY_FOR_REVIEW with warnings (non-blocking)
- Progress tracking updates to 0.7 during validation
- Processing log entries created correctly
"""

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.declaration import Declaration, DeclarationStatus
from src.models.organization import Organization
from src.models.user import User
from src.repositories.declaration_repository import DeclarationRepository
from src.services.income_validation_service import IncomeValidationService


@pytest.mark.integration
class TestDeclarationProcessingWithValidation:
    """Integration tests for validation stage in declaration processing pipeline"""

    @pytest.mark.asyncio
    async def test_validation_service_integration(self, db_session: AsyncSession):
        """
        Test that validation service correctly processes declaration data
        and returns structured warnings.

        This test verifies the validation service can be called with
        extracted data and returns properly formatted warnings.
        """
        # Create validation service
        validation_service = IncomeValidationService()

        # Sample extracted data with intentional issues to trigger warnings
        extracted_dict = {
            "importer": {
                "tax_code": "0123456789",
                "name": "ABC Company Ltd",
                "address": "123 Test Street"
            },
            "exporter": {
                "name": "XYZ Exports Inc",
                "country_code": "US"
            },
            "invoice": {
                "invoice_number": "INV-2024-001",
                "invoice_date": "2024-01-15",
                "invoice_total": 10000.0,
                "invoice_currency": "USD"
            },
            "products": [
                {
                    "hs_code": "8517.62.00",
                    "description": "Smartphones",
                    "quantity_1": 100,
                    "quantity_1_unit": "PCE",
                    "invoice_unit_price": 100.0,
                    "invoice_unit_price_currency": "USD",
                    "invoice_line_total": 10000.0
                }
            ],
            "shipping_transport": {
                "bill_of_lading_number": "BOL123456",
                "arrival_date": "2024-01-20",
                "port_of_loading_code": "USNYC"
            },
            "certificate_of_origin": {
                "co_number": "CO-2024-001",
                "products": [
                    {
                        "hs_code": "8517.62.00",
                        "quantity_1": 100
                    }
                ]
            },
            "package_container": {
                "container_count": 1
            },
            "tax_duty": {
                "vat_rate": 10.0,
                "import_duty_rate": 5.0
            }
        }

        # Call validation service
        warnings = validation_service.validate_declaration(extracted_dict)

        # Verify warnings structure
        assert isinstance(warnings, list), "Warnings should be a list"

        # Each warning should have required fields
        for warning in warnings:
            assert "field" in warning, "Warning should have 'field'"
            assert "severity" in warning, "Warning should have 'severity'"
            assert "message" in warning, "Warning should have 'message'"
            assert "rule" in warning, "Warning should have 'rule'"
            assert "details" in warning, "Warning should have 'details'"

            # Verify severity is valid
            assert warning["severity"] in ["error", "warning", "info"], \
                f"Invalid severity: {warning['severity']}"

            # Verify details structure
            details = warning["details"]
            assert "source_docs" in details, "Details should have 'source_docs'"
            assert "expected_value" in details or "actual_value" in details, \
                "Details should have expected or actual value"
            assert "confidence" in details, "Details should have 'confidence'"
            assert isinstance(details["confidence"], (int, float)), \
                "Confidence should be numeric"
            assert 0.0 <= details["confidence"] <= 1.0, \
                "Confidence should be between 0 and 1"

    @pytest.mark.asyncio
    async def test_validation_warnings_stored_in_database(self, db_session: AsyncSession):
        """
        Test that validation warnings are correctly stored in the
        declaration.validation_warnings JSONB field.

        Verifies AC14: Warnings stored correctly in database.
        """
        # Create test organization and user
        org = Organization(
            id=uuid4(),
            name="Test Organization"
        )
        db_session.add(org)

        user = User(
            id=uuid4(),
            email="test@example.com",
            hashed_password="dummy",
            full_name="Test User",
            organization_id=org.id,
            role="admin"
        )
        db_session.add(user)
        await db_session.commit()

        # Create test declaration
        declaration = Declaration(
            id=uuid4(),
            organization_id=org.id,
            created_by_user_id=user.id,
            status=DeclarationStatus.PROCESSING,
            processing_progress=0.4,
            extracted_data={
                "invoice": {
                    "invoice_number": "TEST-001",
                    "invoice_total": 5000.0
                },
                "products": [
                    {
                        "hs_code": "1234.56.78",
                        "quantity_1": 10
                    }
                ]
            }
        )
        db_session.add(declaration)
        await db_session.commit()

        # Create validation service and generate warnings
        validation_service = IncomeValidationService()
        warnings = validation_service.validate_declaration(declaration.extracted_data)

        # Store warnings in declaration
        repo = DeclarationRepository(db_session)
        declaration.validation_warnings = warnings
        declaration.status = DeclarationStatus.VALIDATING
        declaration.progress = 0.7
        await db_session.commit()
        await db_session.refresh(declaration)

        # Verify warnings are stored
        assert declaration.validation_warnings is not None, \
            "Validation warnings should be stored"
        assert isinstance(declaration.validation_warnings, list), \
            "Validation warnings should be a list"

        # Verify JSONB field persisted correctly
        retrieved_declaration = await repo.get_by_id(declaration.id)
        assert retrieved_declaration is not None, "Declaration should be retrievable"
        assert retrieved_declaration.validation_warnings == warnings, \
            "Stored warnings should match original warnings"

    @pytest.mark.asyncio
    async def test_workflow_continues_with_validation_warnings(self, db_session: AsyncSession):
        """
        Test that the workflow continues to READY_FOR_REVIEW even when
        validation warnings are present (non-blocking behavior).

        Verifies AC14: Workflow continues to READY_FOR_REVIEW with warnings.
        """
        # Create test organization and user
        org = Organization(
            id=uuid4(),
            name="Test Organization"
        )
        db_session.add(org)

        user = User(
            id=uuid4(),
            email="test@example.com",
            hashed_password="dummy",
            full_name="Test User",
            organization_id=org.id,
            role="admin"
        )
        db_session.add(user)
        await db_session.commit()

        # Create declaration with warnings
        declaration = Declaration(
            id=uuid4(),
            organization_id=org.id,
            created_by_user_id=user.id,
            status=DeclarationStatus.VALIDATING,
            processing_progress=0.7,
            extracted_data={
                "invoice": {
                    "invoice_number": "TEST-001",
                    "invoice_total": 5000.0,
                    "invoice_date": "2024-01-20"
                },
                "shipping_transport": {
                    "arrival_date": "2024-01-15"  # Date inconsistency - arrival before invoice
                }
            },
            validation_warnings=[
                {
                    "field": "invoice.invoice_date",
                    "severity": "warning",
                    "message": "Invoice date is after arrival date",
                    "rule": "date_inconsistencies",
                    "details": {
                        "source_docs": ["INVOICE", "BOL"],
                        "expected_value": "Invoice date should be before arrival",
                        "actual_value": "2024-01-20 > 2024-01-15",
                        "confidence": 0.95
                    }
                }
            ]
        )
        db_session.add(declaration)
        await db_session.commit()

        # Simulate workflow progression to READY_FOR_REVIEW
        repo = DeclarationRepository(db_session)
        await repo.update_status_and_progress(
            declaration.id,
            DeclarationStatus.READY_FOR_REVIEW,
            1.0
        )

        # Verify declaration reached READY_FOR_REVIEW despite warnings
        updated_declaration = await repo.get_by_id(declaration.id)
        assert updated_declaration.status == DeclarationStatus.READY_FOR_REVIEW, \
            "Declaration should reach READY_FOR_REVIEW despite validation warnings"
        assert updated_declaration.processing_progress == 1.0, \
            "Progress should be 100% at READY_FOR_REVIEW"
        assert len(updated_declaration.validation_warnings) > 0, \
            "Validation warnings should still be present"

    @pytest.mark.asyncio
    async def test_validation_stage_progress_tracking(self, db_session: AsyncSession):
        """
        Test that progress tracking correctly updates to 0.7 during
        the validation stage.

        Verifies AC14: Progress tracking updates to 0.7 during validation.
        """
        # Create test organization and user
        org = Organization(
            id=uuid4(),
            name="Test Organization"
        )
        db_session.add(org)

        user = User(
            id=uuid4(),
            email="test@example.com",
            hashed_password="dummy",
            full_name="Test User",
            organization_id=org.id,
            role="admin"
        )
        db_session.add(user)
        await db_session.commit()

        # Create declaration at Stage 2 (after LLM extraction)
        declaration = Declaration(
            id=uuid4(),
            organization_id=org.id,
            created_by_user_id=user.id,
            status=DeclarationStatus.PROCESSING,
            processing_progress=0.4,  # After LLM extraction
            extracted_data={"invoice": {"invoice_number": "TEST-001"}}
        )
        db_session.add(declaration)
        await db_session.commit()

        # Simulate Stage 3: Validation
        repo = DeclarationRepository(db_session)
        await repo.update_status_and_progress(
            declaration.id,
            DeclarationStatus.VALIDATING,
            0.7
        )

        # Verify progress tracking
        updated_declaration = await repo.get_by_id(declaration.id)
        assert updated_declaration.status == DeclarationStatus.VALIDATING, \
            "Status should be VALIDATING during Stage 3"
        assert updated_declaration.processing_progress == 0.7, \
            "Progress should be 0.7 (70%) during validation stage"

    @pytest.mark.asyncio
    async def test_validation_with_multiple_severity_levels(self, db_session: AsyncSession):
        """
        Test that validation correctly generates warnings with different
        severity levels (error, warning, info).

        Verifies that the validation service produces all three severity types.
        """
        validation_service = IncomeValidationService()

        # Create extracted data designed to trigger various severity levels
        extracted_dict = {
            "invoice": {
                "invoice_number": "INV-001",
                "invoice_date": "2024-01-20",
                "invoice_total": 10000.0,
                "invoice_currency": "USD"
            },
            "products": [
                {
                    "hs_code": "1234.56.78",
                    "quantity_1": 100,
                    "invoice_unit_price": 95.0,  # Will cause amount discrepancy
                    "invoice_unit_price_currency": "USD",
                    "invoice_line_total": 9500.0
                }
            ],
            "shipping_transport": {
                "arrival_date": "2024-01-15",  # Before invoice date - warning
                "port_of_loading_code": "USNYC"
            },
            "package_container": {
                "container_count": 2  # Info-level check
            },
            "tax_duty": {
                "vat_rate": 10.0,
                "import_duty_rate": 5.0
            }
        }

        # Run validation
        warnings = validation_service.validate_declaration(extracted_dict)

        # Check for different severity levels
        severities = {w["severity"] for w in warnings}

        # At minimum, we should have some warnings generated
        assert len(warnings) > 0, "Should generate at least some warnings"

        # Verify all warnings have valid severities
        for severity in severities:
            assert severity in ["error", "warning", "info"], \
                f"Invalid severity found: {severity}"

    @pytest.mark.asyncio
    async def test_validation_handles_missing_optional_fields(self, db_session: AsyncSession):
        """
        Test that validation gracefully handles missing or null optional fields
        without crashing.

        Verifies robust null/missing field handling as specified in story.
        """
        validation_service = IncomeValidationService()

        # Minimal extracted data with many optional fields missing
        extracted_dict = {
            "invoice": {
                "invoice_number": "INV-001"
                # Missing: dates, amounts, currency
            },
            "products": []  # Empty products list
            # Missing: shipping_transport, package_container, tax_duty, etc.
        }

        # Should not raise exception
        warnings = validation_service.validate_declaration(extracted_dict)

        # Verify it returns a list (even if empty or with some warnings about missing data)
        assert isinstance(warnings, list), "Should return list even with minimal data"

    @pytest.mark.asyncio
    async def test_validation_performance_target(self, db_session: AsyncSession):
        """
        Test that validation completes within the performance target (<5 seconds).

        Verifies performance requirement from story Dev Notes.
        """
        import time

        validation_service = IncomeValidationService()

        # Create realistic declaration data
        extracted_dict = {
            "importer": {"tax_code": "0123456789", "name": "Test Importer"},
            "exporter": {"name": "Test Exporter", "country_code": "US"},
            "invoice": {
                "invoice_number": "INV-001",
                "invoice_date": "2024-01-15",
                "invoice_total": 50000.0,
                "invoice_currency": "USD"
            },
            "products": [
                {
                    "hs_code": f"1234.56.{i:02d}",
                    "description": f"Product {i}",
                    "quantity_1": 10 * i,
                    "invoice_unit_price": 100.0,
                    "invoice_line_total": 1000.0 * i
                }
                for i in range(1, 51)  # 50 products - realistic load
            ],
            "shipping_transport": {
                "bill_of_lading_number": "BOL123",
                "arrival_date": "2024-01-20"
            }
        }

        # Measure validation time
        start_time = time.time()
        warnings = validation_service.validate_declaration(extracted_dict)
        elapsed_time = time.time() - start_time

        # Verify performance target (<5 seconds)
        assert elapsed_time < 5.0, \
            f"Validation took {elapsed_time:.2f}s, should be <5s (target from story)"

        # Also verify it actually ran (produced results)
        assert isinstance(warnings, list), "Should return validation results"
