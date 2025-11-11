"""
Excel Generation Service for Vietnamese Customs Declaration (CD.xlsx)

Generates Excel files from Declaration draft_data using official template.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import UUID

import structlog
from openpyxl import load_workbook
from openpyxl.styles import numbers

logger = structlog.get_logger(__name__)


class ExcelGenerationService:
    """
    Service for generating Vietnamese customs declaration Excel files.

    Uses template-based approach to preserve Vietnamese labels and formatting.
    Supports multi-product declarations with sequential product sections.
    Each product occupies ~42 rows starting at row 160.
    """

    def __init__(self, template_path: Optional[str] = None):
        """
        Initialize the Excel generation service.

        Args:
            template_path: Path to CD.xlsx template. Defaults to resources/sample/2/CD.xlsx
        """
        self.template_path = template_path or "resources/sample/2/CD.xlsx"
        self._validate_template_exists()

    def _validate_template_exists(self) -> None:
        """Validate that the template file exists."""
        if not Path(self.template_path).exists():
            raise FileNotFoundError(
                f"Excel template not found: {self.template_path}"
            )

    def generate_cd_file(self, declaration_id: UUID, draft_data: dict) -> str:
        """
        Generate CD.xlsx file from declaration draft_data.

        Args:
            declaration_id: UUID of the declaration
            draft_data: Declaration data containing consignee, products, tax totals

        Returns:
            str: Absolute path to generated Excel file

        Raises:
            ValueError: If required fields are missing from draft_data
            FileNotFoundError: If template file not found
            OSError: If file system errors occur
        """
        logger.info("generating_excel", declaration_id=str(declaration_id))

        # Validate required fields
        self._validate_draft_data(draft_data)

        # Load template
        workbook = load_workbook(self.template_path)
        worksheet = workbook.active

        # Map sections to Excel cells
        self._map_header_section(worksheet, draft_data)
        self._map_product_section(worksheet, draft_data)
        self._map_tax_summary(worksheet, draft_data)

        # Ensure export directory exists
        export_path = self._ensure_export_directory(declaration_id)
        output_file = export_path / "CD.xlsx"

        # Save workbook
        workbook.save(str(output_file))

        logger.info(
            "excel_generated",
            declaration_id=str(declaration_id),
            file_path=str(output_file)
        )

        return str(output_file)

    def _validate_draft_data(self, draft_data: dict) -> None:
        """
        Validate that all required fields are present in draft_data.

        Args:
            draft_data: Declaration data to validate

        Raises:
            ValueError: If required fields are missing
        """
        required_fields = {
            "consignee": ["name", "address", "tax_id"],
            "declaration_date": None,
            "products": ["description", "hs_code", "quantity", "unit_price",
                        "invoice_value", "origin_country"],
            "total_invoice_value": None,
            "total_vat": None,
            "total_payable": None
        }

        # Check top-level fields
        for field, subfields in required_fields.items():
            if field not in draft_data:
                raise ValueError(f"Missing required field in draft_data: {field}")

            # Check nested fields
            if subfields and isinstance(draft_data[field], dict):
                for subfield in subfields:
                    if subfield not in draft_data[field]:
                        raise ValueError(
                            f"Missing required field in draft_data.{field}: {subfield}"
                        )

            # Check product array fields
            if field == "products":
                if not isinstance(draft_data[field], list) or len(draft_data[field]) == 0:
                    raise ValueError("draft_data.products must be a non-empty array")

                for i, product in enumerate(draft_data[field]):
                    for subfield in subfields:
                        if subfield not in product:
                            raise ValueError(
                                f"Missing required field in draft_data.products[{i}]: {subfield}"
                            )

    def _map_header_section(self, worksheet, draft_data: dict) -> None:
        """
        Map header section data to Excel cells.

        Populates importer/consignee information and declaration date.

        Args:
            worksheet: openpyxl worksheet object
            draft_data: Declaration data
        """
        consignee = draft_data["consignee"]

        # Importer information (merged cells - write to top-left)
        worksheet["H10"] = consignee["tax_id"]  # Tax ID
        worksheet["H11"] = consignee["name"]  # Name (merged H11:AH12)
        worksheet["H14"] = consignee["address"]  # Address (merged H14:AH15)

        # Optional fields
        if "postal_code" in consignee:
            worksheet["H13"] = consignee["postal_code"]
        if "phone" in consignee:
            worksheet["H16"] = consignee["phone"]

        # Declaration date - convert ISO to DD/MM/YYYY
        declaration_date_str = draft_data["declaration_date"]
        if isinstance(declaration_date_str, str):
            # Parse ISO format date
            date_obj = datetime.fromisoformat(declaration_date_str.split("T")[0])
        else:
            date_obj = declaration_date_str

        worksheet["G8"] = date_obj
        worksheet["G8"].number_format = "DD/MM/YYYY"

        # Optional: Shipper/Exporter information (if available)
        if "shipper" in draft_data and draft_data["shipper"]:
            shipper = draft_data["shipper"]
            if "name" in shipper:
                worksheet["H23"] = shipper["name"]
            if "address" in shipper:
                worksheet["H25"] = shipper["address"]
            if "country" in shipper:
                worksheet["U26"] = shipper["country"]

    def _map_product_section(self, worksheet, draft_data: dict) -> None:
        """
        Map product data to Excel cells.

        Supports multiple products. Each product starts at row 160 + (index * 42).
        Product sections repeat every 42 rows (rows 160-202 per product).

        Args:
            worksheet: openpyxl worksheet object
            draft_data: Declaration data
        """
        products = draft_data["products"]
        product_row_spacing = 42  # Each product spans ~42 rows (160-202)

        logger.info(
            "mapping_products",
            count=len(products),
            message=f"Exporting {len(products)} product(s) to Excel"
        )

        # Map each product to sequential sections
        for index, product in enumerate(products):
            base_row = 160 + (index * product_row_spacing)
            self._map_single_product(worksheet, product, base_row)

    def _map_single_product(self, worksheet, product: dict, base_row: int) -> None:
        """
        Map a single product to Excel cells starting at base_row.

        Args:
            worksheet: openpyxl worksheet object
            product: Product data dictionary
            base_row: Starting row for this product (160 for first, 202 for second, etc.)
        """
        # Product details
        worksheet[f"G{base_row}"] = product["hs_code"]  # HS Code
        worksheet[f"G{base_row + 1}"] = product["description"]  # Description (merged)

        # Quantity (row offset +4 from base)
        quantity_row = base_row + 4
        worksheet[f"V{quantity_row}"] = product["quantity"]
        worksheet[f"V{quantity_row}"].number_format = numbers.FORMAT_NUMBER_COMMA_SEPARATED1

        # Quantity unit
        if "quantity_unit" in product:
            worksheet[f"AE{quantity_row}"] = product["quantity_unit"]
        else:
            worksheet[f"AE{quantity_row}"] = "PCE"  # Default unit

        # Invoice value and unit price (row offset +6 from base)
        invoice_row = base_row + 6
        worksheet[f"I{invoice_row}"] = product["invoice_value"]
        worksheet[f"I{invoice_row}"].number_format = numbers.FORMAT_NUMBER_COMMA_SEPARATED1

        worksheet[f"V{invoice_row}"] = product["unit_price"]
        worksheet[f"V{invoice_row}"].number_format = "0.000"  # 3 decimal places

        # Currency
        worksheet[f"AC{invoice_row}"] = "USD"  # Default currency

        # Tax base value (VND) (row offset +8 from base)
        tax_base_row = base_row + 8
        worksheet[f"I{tax_base_row}"] = product["invoice_value"]
        worksheet[f"I{tax_base_row}"].number_format = "#,##0"  # No decimals for VND

        # Import duty (row offset +11 from base)
        duty_row = base_row + 11
        if "import_duty" in product:
            import_duty = product["import_duty"]
            if import_duty > 0:
                worksheet[f"I{duty_row}"] = import_duty
                worksheet[f"I{duty_row}"].number_format = numbers.FORMAT_NUMBER_COMMA_SEPARATED1

        # Origin country
        origin_country = product.get("origin_country", "")

        # Map common country names to codes
        country_code_map = {
            "China": "CN",
            "Vietnam": "VN",
            "USA": "US",
            "Japan": "JP",
            "Korea": "KR",
            "Germany": "DE",
            "France": "FR"
        }

        if len(origin_country) == 2:
            # Already a country code
            worksheet[f"X{duty_row}"] = origin_country.upper()
        else:
            # Try to find code from map
            country_code = country_code_map.get(origin_country, origin_country[:2].upper())
            worksheet[f"X{duty_row}"] = country_code

        worksheet[f"Z{duty_row}"] = origin_country.upper()  # Full country name

        # VAT section (row offsets +19, +20, +21 from base)
        if "vat" in product:
            vat_base_row = base_row + 19
            vat_rate_row = base_row + 20
            vat_amount_row = base_row + 21

            # VAT base
            worksheet[f"I{vat_base_row}"] = product["invoice_value"]
            worksheet[f"I{vat_base_row}"].number_format = "#,##0"

            # VAT rate
            vat_rate = product.get("vat_rate", "8%")
            worksheet[f"I{vat_rate_row}"] = vat_rate

            # VAT amount
            worksheet[f"I{vat_amount_row}"] = product["vat"]
            worksheet[f"I{vat_amount_row}"].number_format = numbers.FORMAT_NUMBER_COMMA_SEPARATED1

    def _map_tax_summary(self, worksheet, draft_data: dict) -> None:
        """
        Map tax summary data to Excel cells.

        Populates total VAT and total payable in the summary section (rows 67-70).

        Args:
            worksheet: openpyxl worksheet object
            draft_data: Declaration data
        """
        # Total VAT
        total_vat = draft_data.get("total_vat", 0)
        worksheet["H67"] = total_vat
        worksheet["H67"].number_format = numbers.FORMAT_NUMBER_COMMA_SEPARATED1

        # Total payable
        total_payable = draft_data.get("total_payable", 0)
        worksheet["R68"] = total_payable
        worksheet["R68"].number_format = numbers.FORMAT_NUMBER_COMMA_SEPARATED1

    def _ensure_export_directory(self, declaration_id: UUID) -> Path:
        """
        Ensure export directory exists for the declaration.

        Args:
            declaration_id: UUID of the declaration

        Returns:
            Path: Absolute path to export directory

        Raises:
            OSError: If directory creation fails
        """
        export_dir = Path("./data/exports") / str(declaration_id)

        try:
            export_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error(
                "export_directory_creation_failed",
                declaration_id=str(declaration_id),
                error=str(e)
            )
            raise OSError(f"Failed to create export directory: {e}") from e

        return export_dir

    def delete_export_file(self, declaration_id: UUID) -> bool:
        """
        Delete generated Excel file for a declaration.

        Future use: Cleanup when declaration is deleted or regenerated.

        Args:
            declaration_id: UUID of the declaration

        Returns:
            bool: True if file was deleted, False if file didn't exist
        """
        export_file = Path("./data/exports") / str(declaration_id) / "CD.xlsx"

        if export_file.exists():
            export_file.unlink()
            logger.info("export_file_deleted", declaration_id=str(declaration_id))
            return True

        return False
