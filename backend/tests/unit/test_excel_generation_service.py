"""
Unit tests for ExcelGenerationService

Tests cover:
- AC 1: Template-based Excel generation using openpyxl
- AC 2, 3: Cell mapping (header, product, tax summary)
- AC 4: Number formatting (currency, dates)
- AC 5: Vietnamese label preservation
- AC 9: Structure validation against template
- Edge cases: Missing fields, multiple products, template errors
"""

from datetime import datetime
from pathlib import Path
from uuid import uuid4

import pytest
from openpyxl import load_workbook

from src.services.excel_generation_service import ExcelGenerationService


@pytest.fixture
def sample_declaration_id():
    """Sample declaration UUID"""
    return uuid4()


@pytest.fixture
def sample_draft_data():
    """
    Sample draft_data with all required fields
    Based on Story 2.4 tax calculation output
    """
    return {
        "consignee": {
            "name": "ABC Import Company Ltd",
            "address": "123 Main Street, District 1, Ho Chi Minh City",
            "tax_id": "0123456789",
            "postal_code": "700000",
            "phone": "+84-28-1234567"
        },
        "declaration_date": "2025-10-23",
        "products": [
            {
                "description": "Adult diapers, brand: Ipaly, size M-XL, disposable",
                "hs_code": "96190014",
                "quantity": 307.7,
                "unit_price": 0.076,
                "invoice_value": 23385.2,
                "origin_country": "China",
                "import_duty": 0.0,
                "vat": 49071.50,
                "total_product_tax": 49071.50
            }
        ],
        "total_invoice_value": 23385.2,
        "total_import_duty": 0.0,
        "total_vat": 49071.50,
        "total_payable": 72456.70
    }


@pytest.fixture
def minimal_draft_data():
    """Minimal draft_data with only required fields"""
    return {
        "consignee": {
            "name": "Test Company",
            "address": "Test Address",
            "tax_id": "1234567890"
        },
        "declaration_date": "2025-10-23",
        "products": [
            {
                "description": "Test Product",
                "hs_code": "12345678",
                "quantity": 100,
                "unit_price": 10.0,
                "invoice_value": 1000.0,
                "origin_country": "CN"
            }
        ],
        "total_invoice_value": 1000.0,
        "total_vat": 80.0,
        "total_payable": 1080.0
    }


@pytest.fixture
def excel_service():
    """ExcelGenerationService instance"""
    return ExcelGenerationService()


@pytest.fixture
def export_directory(tmp_path, sample_declaration_id):
    """Create temporary export directory"""
    export_dir = tmp_path / "data" / "exports" / str(sample_declaration_id)
    export_dir.mkdir(parents=True, exist_ok=True)
    return export_dir


class TestExcelGeneration:
    """Test suite for Excel file generation"""

    def test_generate_cd_file_creates_valid_xlsx(
        self, excel_service, sample_declaration_id, sample_draft_data, tmp_path, monkeypatch
    ):
        """
        Test 1: Verify Excel file is created and is valid .xlsx
        AC 1: Uses openpyxl to create .xlsx file
        """
        # Mock export directory to use tmp_path
        def mock_ensure_export_directory(self, declaration_id):
            export_dir = tmp_path / "data" / "exports" / str(declaration_id)
            export_dir.mkdir(parents=True, exist_ok=True)
            return export_dir

        monkeypatch.setattr(
            ExcelGenerationService,
            "_ensure_export_directory",
            mock_ensure_export_directory
        )

        # Generate Excel file
        file_path = excel_service.generate_cd_file(
            sample_declaration_id,
            sample_draft_data
        )

        # Verify file exists
        assert Path(file_path).exists()
        assert file_path.endswith(".xlsx")

        # Verify it's a valid Excel file by loading it
        workbook = load_workbook(file_path)
        assert workbook is not None
        assert workbook.active is not None

        # Cleanup
        Path(file_path).unlink()

    def test_header_section_mapping(
        self, excel_service, sample_declaration_id, sample_draft_data, tmp_path, monkeypatch
    ):
        """
        Test 2: Verify header section fields mapped correctly
        AC 2, 3: Header section includes importer name, address, tax ID, date
        """
        # Mock export directory
        def mock_ensure_export_directory(self, declaration_id):
            export_dir = tmp_path / "data" / "exports" / str(declaration_id)
            export_dir.mkdir(parents=True, exist_ok=True)
            return export_dir

        monkeypatch.setattr(
            ExcelGenerationService,
            "_ensure_export_directory",
            mock_ensure_export_directory
        )

        # Generate Excel file
        file_path = excel_service.generate_cd_file(
            sample_declaration_id,
            sample_draft_data
        )

        # Load generated file
        workbook = load_workbook(file_path)
        worksheet = workbook.active

        # Verify header mappings (based on Task 1 analysis)
        assert worksheet["H10"].value == sample_draft_data["consignee"]["tax_id"]
        assert worksheet["H11"].value == sample_draft_data["consignee"]["name"]
        assert worksheet["H14"].value == sample_draft_data["consignee"]["address"]
        assert worksheet["H13"].value == sample_draft_data["consignee"]["postal_code"]
        assert worksheet["H16"].value == sample_draft_data["consignee"]["phone"]

        # Verify date is datetime object with DD/MM/YYYY format
        date_cell = worksheet["G8"]
        assert isinstance(date_cell.value, datetime)
        assert date_cell.number_format == "DD/MM/YYYY"

        # Cleanup
        Path(file_path).unlink()

    def test_product_table_mapping(
        self, excel_service, sample_declaration_id, sample_draft_data, tmp_path, monkeypatch
    ):
        """
        Test 3: Verify product table fields mapped correctly
        AC 2, 3: Product table includes description, HS code, quantity, prices, origin
        """
        # Mock export directory
        def mock_ensure_export_directory(self, declaration_id):
            export_dir = tmp_path / "data" / "exports" / str(declaration_id)
            export_dir.mkdir(parents=True, exist_ok=True)
            return export_dir

        monkeypatch.setattr(
            ExcelGenerationService,
            "_ensure_export_directory",
            mock_ensure_export_directory
        )

        # Generate Excel file
        file_path = excel_service.generate_cd_file(
            sample_declaration_id,
            sample_draft_data
        )

        # Load generated file
        workbook = load_workbook(file_path)
        worksheet = workbook.active

        product = sample_draft_data["products"][0]

        # Verify product mappings (row 160+)
        assert worksheet["G160"].value == product["hs_code"]
        assert worksheet["G161"].value == product["description"]
        assert worksheet["V164"].value == product["quantity"]
        assert worksheet["V166"].value == product["unit_price"]
        assert worksheet["I166"].value == product["invoice_value"]

        # Verify origin country
        cell_value = str(worksheet["X171"].value)
        assert "CN" in cell_value or "CHINA" in cell_value.upper()
        assert "CHINA" in str(worksheet["Z171"].value).upper()

        # Verify VAT amount
        assert worksheet["I181"].value == product["vat"]

        # Cleanup
        Path(file_path).unlink()

    def test_tax_summary_mapping(
        self, excel_service, sample_declaration_id, sample_draft_data, tmp_path, monkeypatch
    ):
        """
        Test 4: Verify tax summary fields mapped correctly
        AC 2, 3: Tax summary includes total VAT and total payable
        """
        # Mock export directory
        def mock_ensure_export_directory(self, declaration_id):
            export_dir = tmp_path / "data" / "exports" / str(declaration_id)
            export_dir.mkdir(parents=True, exist_ok=True)
            return export_dir

        monkeypatch.setattr(
            ExcelGenerationService,
            "_ensure_export_directory",
            mock_ensure_export_directory
        )

        # Generate Excel file
        file_path = excel_service.generate_cd_file(
            sample_declaration_id,
            sample_draft_data
        )

        # Load generated file
        workbook = load_workbook(file_path)
        worksheet = workbook.active

        # Verify tax summary mappings
        assert worksheet["H67"].value == sample_draft_data["total_vat"]
        assert worksheet["R68"].value == sample_draft_data["total_payable"]

        # Cleanup
        Path(file_path).unlink()

    def test_number_formatting(
        self, excel_service, sample_declaration_id, sample_draft_data, tmp_path, monkeypatch
    ):
        """
        Test 5: Verify number formatting matches requirements
        AC 4: Currency cells use #,##0.00, Date cells use DD/MM/YYYY
        """
        # Mock export directory
        def mock_ensure_export_directory(self, declaration_id):
            export_dir = tmp_path / "data" / "exports" / str(declaration_id)
            export_dir.mkdir(parents=True, exist_ok=True)
            return export_dir

        monkeypatch.setattr(
            ExcelGenerationService,
            "_ensure_export_directory",
            mock_ensure_export_directory
        )

        # Generate Excel file
        file_path = excel_service.generate_cd_file(
            sample_declaration_id,
            sample_draft_data
        )

        # Load generated file
        workbook = load_workbook(file_path)
        worksheet = workbook.active

        # Verify date format
        assert worksheet["G8"].number_format == "DD/MM/YYYY"

        # Verify currency formats (should have comma separators and decimals)
        currency_cells = ["V164", "I166", "I181", "H67", "R68"]
        for cell_ref in currency_cells:
            cell_format = worksheet[cell_ref].number_format
            # Check for comma-separated format patterns
            assert "#,##0" in cell_format or "FORMAT_NUMBER" in str(cell_format)

        # Verify unit price format (3 decimals)
        assert "0.000" in worksheet["V166"].number_format

        # Cleanup
        Path(file_path).unlink()

    def test_vietnamese_labels_preserved(
        self, excel_service, sample_declaration_id, minimal_draft_data, tmp_path, monkeypatch
    ):
        """
        Test 6: Verify Vietnamese static labels are not overwritten
        AC 5: Vietnamese language headers and labels preserved
        """
        # Mock export directory
        def mock_ensure_export_directory(self, declaration_id):
            export_dir = tmp_path / "data" / "exports" / str(declaration_id)
            export_dir.mkdir(parents=True, exist_ok=True)
            return export_dir

        monkeypatch.setattr(
            ExcelGenerationService,
            "_ensure_export_directory",
            mock_ensure_export_directory
        )

        # Load original template to check labels
        original_template = load_workbook("resources/sample/2/CD.xlsx")
        original_ws = original_template.active

        # Generate Excel file
        file_path = excel_service.generate_cd_file(
            sample_declaration_id,
            minimal_draft_data
        )

        # Load generated file
        generated_wb = load_workbook(file_path)
        generated_ws = generated_wb.active

        # Verify key Vietnamese labels are preserved
        vietnamese_label_cells = [
            "C9",   # "Người nhập khẩu"
            "D10",  # "Mã"
            "D11",  # "Tên"
            "D14",  # "Địa chỉ"
            "C160", # "Mã số hàng hóa"
            "C161", # "Mô tả hàng hóa"
            "S164", # "Số lượng (1)"
            "C166", # "Trị giá hóa đơn"
            "S166", # "Đơn giá hóa đơn"
        ]

        for cell_ref in vietnamese_label_cells:
            original_value = original_ws[cell_ref].value
            generated_value = generated_ws[cell_ref].value

            # Labels should be identical (not overwritten)
            error_msg = (
                f"Label at {cell_ref} was modified. "
                f"Expected: {original_value}, Got: {generated_value}"
            )
            assert original_value == generated_value, error_msg

        # Cleanup
        Path(file_path).unlink()

    def test_multiple_products_export(
        self, excel_service, sample_declaration_id, sample_draft_data, tmp_path, monkeypatch
    ):
        """
        Test 7: Verify handling of multiple products (2 products)
        Multi-product support: Each product mapped to sequential sections
        """
        # Mock export directory
        def mock_ensure_export_directory(self, declaration_id):
            export_dir = tmp_path / "data" / "exports" / str(declaration_id)
            export_dir.mkdir(parents=True, exist_ok=True)
            return export_dir

        monkeypatch.setattr(
            ExcelGenerationService,
            "_ensure_export_directory",
            mock_ensure_export_directory
        )

        # Add second product
        multi_product_data = sample_draft_data.copy()
        multi_product_data["products"] = [
            sample_draft_data["products"][0],
            {
                "description": "Second Product - Clothing",
                "hs_code": "87654321",
                "quantity": 50,
                "unit_price": 20.0,
                "invoice_value": 1000.0,
                "origin_country": "Vietnam",
                "vat": 80.0
            }
        ]

        # Generate Excel file
        file_path = excel_service.generate_cd_file(
            sample_declaration_id,
            multi_product_data
        )

        # Verify file was created
        assert Path(file_path).exists()

        # Load and verify BOTH products were exported
        workbook = load_workbook(file_path)
        worksheet = workbook.active

        # First product at row 160
        assert worksheet["G160"].value == multi_product_data["products"][0]["hs_code"]
        assert worksheet["G161"].value == multi_product_data["products"][0]["description"]

        # Second product at row 202 (160 + 42)
        assert worksheet["G202"].value == multi_product_data["products"][1]["hs_code"]
        assert worksheet["G203"].value == multi_product_data["products"][1]["description"]

        # Cleanup
        Path(file_path).unlink()

    def test_five_products_export(
        self, excel_service, sample_declaration_id, sample_draft_data, tmp_path, monkeypatch
    ):
        """
        Test 7b: Verify handling of 5 products
        Multi-product support: Sequential product sections
        """
        # Mock export directory
        def mock_ensure_export_directory(self, declaration_id):
            export_dir = tmp_path / "data" / "exports" / str(declaration_id)
            export_dir.mkdir(parents=True, exist_ok=True)
            return export_dir

        monkeypatch.setattr(
            ExcelGenerationService,
            "_ensure_export_directory",
            mock_ensure_export_directory
        )

        # Create 5 products
        multi_product_data = sample_draft_data.copy()
        multi_product_data["products"] = [
            {
                "description": f"Product {i+1}",
                "hs_code": f"1234567{i}",
                "quantity": 100 * (i + 1),
                "unit_price": 10.0 + i,
                "invoice_value": 1000.0 * (i + 1),
                "origin_country": "China",
                "vat": 80.0 * (i + 1)
            }
            for i in range(5)
        ]

        # Generate Excel file
        file_path = excel_service.generate_cd_file(
            sample_declaration_id,
            multi_product_data
        )

        # Verify file was created
        assert Path(file_path).exists()

        # Load and verify all 5 products
        workbook = load_workbook(file_path)
        worksheet = workbook.active

        # Verify each product at correct row offset
        for i in range(5):
            base_row = 160 + (i * 42)
            expected_hs_code = f"1234567{i}"
            error_msg = f"Product {i+1} HS code mismatch"
            assert worksheet[f"G{base_row}"].value == expected_hs_code, error_msg

        # Cleanup
        Path(file_path).unlink()

    def test_twenty_products_performance(
        self, excel_service, sample_declaration_id, sample_draft_data, tmp_path, monkeypatch
    ):
        """
        Test 7c: Performance validation with 20 products
        Target: <3-5 seconds generation time
        """
        import time

        # Mock export directory
        def mock_ensure_export_directory(self, declaration_id):
            export_dir = tmp_path / "data" / "exports" / str(declaration_id)
            export_dir.mkdir(parents=True, exist_ok=True)
            return export_dir

        monkeypatch.setattr(
            ExcelGenerationService,
            "_ensure_export_directory",
            mock_ensure_export_directory
        )

        # Create 20 products
        multi_product_data = sample_draft_data.copy()
        multi_product_data["products"] = [
            {
                "description": f"Product {i+1} - Performance Test Item",
                "hs_code": f"9999{i:04d}",
                "quantity": 100,
                "unit_price": 10.0,
                "invoice_value": 1000.0,
                "origin_country": "China",
                "vat": 80.0
            }
            for i in range(20)
        ]

        # Measure generation time
        start_time = time.time()
        file_path = excel_service.generate_cd_file(
            sample_declaration_id,
            multi_product_data
        )
        generation_time = time.time() - start_time

        # Verify file was created
        assert Path(file_path).exists()

        # Performance assertion: Should complete in <5 seconds
        assert generation_time < 5.0, f"Generation took {generation_time:.2f}s (target: <5s)"

        # Verify file is valid Excel
        workbook = load_workbook(file_path)
        worksheet = workbook.active

        # Spot check: First and last products
        assert worksheet["G160"].value == "99990000"  # First product
        assert worksheet["G958"].value == "99990019"  # Last product (160 + 19*42 = 958)

        # Cleanup
        Path(file_path).unlink()

    def test_missing_draft_data_fields(self, excel_service, sample_declaration_id):
        """
        Test 8: Verify validation error when required fields missing
        Error handling: Missing required fields
        """
        # Missing consignee
        incomplete_data_1 = {
            "declaration_date": "2025-10-23",
            "products": [],
            "total_invoice_value": 0,
            "total_vat": 0,
            "total_payable": 0
        }

        with pytest.raises(ValueError, match="Missing required field"):
            excel_service.generate_cd_file(sample_declaration_id, incomplete_data_1)

        # Missing products
        incomplete_data_2 = {
            "consignee": {"name": "Test", "address": "Test", "tax_id": "123"},
            "declaration_date": "2025-10-23",
            "total_invoice_value": 0,
            "total_vat": 0,
            "total_payable": 0
        }

        with pytest.raises(ValueError, match="Missing required field"):
            excel_service.generate_cd_file(sample_declaration_id, incomplete_data_2)

        # Empty products array
        incomplete_data_3 = {
            "consignee": {"name": "Test", "address": "Test", "tax_id": "123"},
            "declaration_date": "2025-10-23",
            "products": [],
            "total_invoice_value": 0,
            "total_vat": 0,
            "total_payable": 0
        }

        with pytest.raises(ValueError, match="non-empty array"):
            excel_service.generate_cd_file(sample_declaration_id, incomplete_data_3)

    def test_template_file_not_found(self, sample_declaration_id, sample_draft_data):
        """
        Test 9: Verify error handling when template file not found
        Error handling: Template file missing
        """
        # Should raise FileNotFoundError during initialization
        with pytest.raises(FileNotFoundError, match="Excel template not found"):
            # Create service with invalid template path - this should raise immediately
            invalid_service = ExcelGenerationService(template_path="nonexistent/template.xlsx")

    def test_export_directory_creation(
        self, excel_service, sample_declaration_id, sample_draft_data, tmp_path, monkeypatch
    ):
        """
        Test: Verify export directory is created if it doesn't exist
        AC 6: Generated file saved to ./data/exports/{declaration_id}/CD.xlsx
        """
        # Mock export directory to use tmp_path
        def mock_ensure_export_directory(self, declaration_id):
            export_dir = tmp_path / "data" / "exports" / str(declaration_id)
            export_dir.mkdir(parents=True, exist_ok=True)
            return export_dir

        monkeypatch.setattr(
            ExcelGenerationService,
            "_ensure_export_directory",
            mock_ensure_export_directory
        )

        # Directory should not exist initially
        export_dir = tmp_path / "data" / "exports" / str(sample_declaration_id)
        if export_dir.exists():
            import shutil
            shutil.rmtree(export_dir)

        # Generate Excel file
        file_path = excel_service.generate_cd_file(
            sample_declaration_id,
            sample_draft_data
        )

        # Verify directory was created
        assert export_dir.exists()
        assert Path(file_path).parent == export_dir

        # Cleanup
        Path(file_path).unlink()

    def test_delete_export_file(
        self, excel_service, sample_declaration_id, sample_draft_data, tmp_path, monkeypatch
    ):
        """
        Test: Verify delete_export_file() cleanup method
        Task 4: Cleanup method for future use
        """
        # Mock export directory to use tmp_path
        def mock_path_new(cls, *args):
            if args[0] == "./data/exports":
                return tmp_path / "data" / "exports"
            return Path(*args)

        monkeypatch.setattr(Path, "__new__", mock_path_new)

        def mock_ensure_export_directory(self, declaration_id):
            export_dir = tmp_path / "data" / "exports" / str(declaration_id)
            export_dir.mkdir(parents=True, exist_ok=True)
            return export_dir

        monkeypatch.setattr(
            ExcelGenerationService,
            "_ensure_export_directory",
            mock_ensure_export_directory
        )

        # Generate Excel file first
        file_path = excel_service.generate_cd_file(
            sample_declaration_id,
            sample_draft_data
        )

        assert Path(file_path).exists()

        # Delete file
        result = excel_service.delete_export_file(sample_declaration_id)

        # File should be deleted
        assert result is True
        assert not Path(file_path).exists()

        # Trying to delete again should return False
        result = excel_service.delete_export_file(sample_declaration_id)
        assert result is False
