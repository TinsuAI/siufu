"""
Pydantic schemas for Vietnamese Customs Declaration (77 fields)

Based on field mapping specification in docs/stories/1.7-field-mapping.md
"""
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class DeclarationHeader(BaseModel):
    """Declaration header information (6 fields)"""
    declaration_number: Optional[str] = Field(None, description="System generated")
    declaration_type_code: Optional[str] = Field(None, description="Import type classification (e.g., A11 2 [4])")
    customs_office_code: Optional[str] = Field(None, description="Receiving customs office code (e.g., HQHOALAC)")
    processing_division_code: Optional[str] = Field(None, description="Processing division code")
    registration_date: Optional[str] = Field(None, description="Registration date (DD/MM/YYYY)")
    representative_hs_code: Optional[str] = Field(None, description="First 4 digits of primary HS code")


class Importer(BaseModel):
    """Importer information (5 fields)"""
    tax_code: Optional[str] = Field(None, description="Vietnamese tax ID (10 digits)")
    name: Optional[str] = Field(None, description="Full legal name")
    postal_code: Optional[str] = Field(None, description="Vietnamese postal code")
    address: Optional[str] = Field(None, description="Full address in Vietnam")
    phone: Optional[str] = Field(None, description="Contact phone number")


class Exporter(BaseModel):
    """Exporter information (5 fields)"""
    name: Optional[str] = Field(None, description="Full legal name of exporter")
    address_line1: Optional[str] = Field(None, description="Primary address line")
    address_line2: Optional[str] = Field(None, description="Additional address line")
    address_line3: Optional[str] = Field(None, description="City, province, country")
    country_code: Optional[str] = Field(None, description="ISO 3166-1 alpha-2 country code")


class ShippingTransport(BaseModel):
    """Shipping & transport information (10 fields)"""
    bill_of_lading_number: Optional[str] = Field(None, description="B/L number or AWB number")
    warehouse_code: Optional[str] = Field(None, description="Warehouse/CFS code")
    warehouse_name: Optional[str] = Field(None, description="Warehouse name")
    port_of_discharge_code: Optional[str] = Field(None, description="UN/LOCODE port code")
    port_of_discharge_name: Optional[str] = Field(None, description="Port name")
    port_of_loading_code: Optional[str] = Field(None, description="UN/LOCODE port code")
    port_of_loading_name: Optional[str] = Field(None, description="Port name")
    transport_mode_code: Optional[str] = Field(None, description="Transport mode code (9999=vessel)")
    vessel_name: Optional[str] = Field(None, description="Vessel name and voyage number")
    arrival_date: Optional[str] = Field(None, description="Date cargo arrived at port (DD/MM/YYYY)")


class PackageContainer(BaseModel):
    """Package & container information (6 fields)"""
    total_packages: Optional[float] = Field(None, description="Total number of packages")
    package_unit: Optional[str] = Field(None, description="Package unit (PK=package, CT=carton)")
    package_marks: Optional[str] = Field(None, description="Shipping marks and numbers")
    gross_weight_kg: Optional[float] = Field(None, description="Total gross weight in kg")
    gross_weight_unit: Optional[str] = Field(None, description="Weight unit (KGM=kilograms)")
    container_count: Optional[int] = Field(None, description="Number of containers")


class Invoice(BaseModel):
    """Invoice information (8 fields)"""
    invoice_number: Optional[str] = Field(None, description="Commercial invoice number")
    invoice_date: Optional[str] = Field(None, description="Invoice issue date (DD/MM/YYYY)")
    payment_method_code: Optional[str] = Field(None, description="Payment method code (KC=Letter of Credit)")
    invoice_total: Optional[float] = Field(None, description="Total invoice value")
    invoice_currency: Optional[str] = Field(None, description="ISO 4217 currency code (e.g., USD)")
    invoice_incoterm: Optional[str] = Field(None, description="Incoterms (FOB, CIF, C&F, etc.)")
    total_taxable_value_vnd: Optional[float] = Field(None, description="Total taxable value in VND (calculated)")
    exchange_rate: Optional[float] = Field(None, description="USD to VND exchange rate")


class CertificateOfOrigin(BaseModel):
    """Certificate of Origin information (3 fields)"""
    co_form_type: Optional[str] = Field(None, description="Form type (Form E, Form AK, etc.)")
    co_number: Optional[str] = Field(None, description="Certificate of Origin number")
    co_date: Optional[str] = Field(None, description="CO issue date (DD/MM/YYYY)")


class ProductLineItem(BaseModel):
    """Product line item (18 fields per product)"""
    item_number: Optional[int] = Field(None, description="Sequential line item number")
    hs_code: Optional[str] = Field(None, description="8-digit HS code")
    product_description: Optional[str] = Field(None, description="Full product description in Vietnamese")
    quantity_1: Optional[float] = Field(None, description="Primary quantity")
    quantity_unit_1: Optional[str] = Field(None, description="Primary unit (PCE, KGM, etc.)")
    quantity_2: Optional[float] = Field(None, description="Secondary quantity")
    quantity_unit_2: Optional[str] = Field(None, description="Secondary unit")
    invoice_unit_price: Optional[float] = Field(None, description="Unit price on invoice")
    invoice_unit_price_currency: Optional[str] = Field(None, description="Invoice currency (USD, EUR, etc.)")
    invoice_line_total: Optional[float] = Field(None, description="Line total (qty × unit price)")
    taxable_value_vnd: Optional[float] = Field(None, description="Taxable value in VND (calculated)")
    unit_price_vnd: Optional[float] = Field(None, description="Unit price in VND (calculated)")
    country_of_origin_code: Optional[str] = Field(None, description="ISO 3166-1 alpha-2 country code")
    country_of_origin_name: Optional[str] = Field(None, description="Country name")
    preferential_code: Optional[str] = Field(None, description="Preferential tariff code")
    manufacturer_name: Optional[str] = Field(None, description="Manufacturer name")
    brand_name: Optional[str] = Field(None, description="Brand/trademark")
    condition: Optional[str] = Field(None, description="New/used condition (e.g., Mới 100%)")


class ImportDuty(BaseModel):
    """Import duty calculation (4 fields)"""
    rate: Optional[float] = Field(None, description="Import duty rate (percentage)")
    rate_type: Optional[str] = Field(None, description="Rate type (C=Ad valorem, S=Specific, M=Mixed)")
    amount: Optional[float] = Field(None, description="Import duty amount in VND (calculated)")
    exemption_amount: Optional[float] = Field(None, description="Duty exemption amount")


class VAT(BaseModel):
    """VAT & other taxes (6 fields)"""
    name: Optional[str] = Field(None, description="Tax name (always 'Thuế GTGT' for VAT)")
    rate_code: Optional[str] = Field(None, description="VAT rate code (e.g., VB245)")
    rate: Optional[float] = Field(None, description="VAT rate (percentage)")
    taxable_value_vnd: Optional[float] = Field(None, description="VAT taxable value in VND")
    amount: Optional[float] = Field(None, description="VAT amount in VND (calculated)")
    exemption_amount: Optional[float] = Field(None, description="VAT exemption amount")


class TaxSummary(BaseModel):
    """Tax summary (4 fields)"""
    total_tax_amount_vnd: Optional[float] = Field(None, description="Total taxes payable (import duty + VAT)")
    tax_payment_deadline_code: Optional[str] = Field(None, description="Tax payment deadline code")
    taxpayer_type: Optional[str] = Field(None, description="Taxpayer type (1=Importer)")
    tax_classification: Optional[str] = Field(None, description="Tax classification code")


class Metadata(BaseModel):
    """Metadata (2 fields)"""
    total_pages: Optional[int] = Field(None, description="Total pages in declaration")
    total_line_items: Optional[int] = Field(None, description="Total product line items")


class VietnameseDeclarationData(BaseModel):
    """
    Complete Vietnamese Customs Declaration Data (77 fields)

    Based on field mapping in docs/stories/1.7-field-mapping.md
    """
    declaration_header: DeclarationHeader
    importer: Importer
    exporter: Exporter
    shipping_transport: ShippingTransport
    package_container: PackageContainer
    invoice: Invoice
    certificate_of_origin: CertificateOfOrigin
    products: List[ProductLineItem] = Field(default_factory=list, description="Product line items (1-50 per declaration)")
    import_duty: ImportDuty
    vat: VAT
    tax_summary: TaxSummary
    metadata: Metadata
    confidence_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Per-field confidence scores (flat structure with dot-notation keys)"
    )
    overall_confidence: float = Field(0.0, ge=0.0, le=1.0, description="Overall extraction confidence")

    model_config = {
        "json_schema_extra": {
            "example": {
                "declaration_header": {
                    "declaration_number": None,
                    "declaration_type_code": "A11 2 [4]",
                    "customs_office_code": "HQHOALAC",
                    "processing_division_code": "00",
                    "registration_date": None,
                    "representative_hs_code": "9619"
                },
                "importer": {
                    "tax_code": "0104118221",
                    "name": "Công ty TNHH sản xuất dịch vụ và thương mại Thịnh Linh",
                    "postal_code": "100000",
                    "address": "Tràng An, phường Chương Mỹ, Thành Phố Hà Nội, Việt Nam",
                    "phone": "+24"
                },
                "exporter": {
                    "name": "QUANZHOU YOULI SANITARY PRODUCTS CO., LTD",
                    "address_line1": "ROOM A10-219, NO 936-1 LUOBAI ROAD",
                    "address_line2": "YUTOU VILLAGE, LUOYANG TOWN, HUIAN",
                    "address_line3": "QUANZHOU, FUJIAN, CHINA",
                    "country_code": "CN"
                },
                "shipping_transport": {
                    "bill_of_lading_number": "270925JJCXMHPALS53751",
                    "warehouse_code": "03CES11",
                    "warehouse_name": "CANG NAM DINH VU",
                    "port_of_discharge_code": "VNDVN",
                    "port_of_discharge_name": "CANG NAM DINH VU",
                    "port_of_loading_code": "CNXMN",
                    "port_of_loading_name": "XIAMEN",
                    "transport_mode_code": "9999",
                    "vessel_name": "GLORY SHANGHAI 2538S",
                    "arrival_date": "01/10/2025"
                },
                "package_container": {
                    "total_packages": 3077,
                    "package_unit": "PK",
                    "package_marks": "",
                    "gross_weight_kg": 19480.1,
                    "gross_weight_unit": "KGM",
                    "container_count": 2
                },
                "invoice": {
                    "invoice_number": "A - LA2025-068",
                    "invoice_date": "26/09/2025",
                    "payment_method_code": "KC",
                    "invoice_total": 23385.2,
                    "invoice_currency": "USD",
                    "invoice_incoterm": "C&F",
                    "total_taxable_value_vnd": 613393796,
                    "exchange_rate": 26230
                },
                "certificate_of_origin": {
                    "co_form_type": "Form E",
                    "co_number": "02251414210008653",
                    "co_date": "30/09/2025"
                },
                "products": [
                    {
                        "item_number": 1,
                        "hs_code": "96190014",
                        "product_description": "Bỉm quần dành cho người già, hiệu: Ipaly",
                        "quantity_1": 307700,
                        "quantity_unit_1": "PCE",
                        "quantity_2": None,
                        "quantity_unit_2": None,
                        "invoice_unit_price": 0.076,
                        "invoice_unit_price_currency": "USD",
                        "invoice_line_total": 23385.2,
                        "taxable_value_vnd": 613393796,
                        "unit_price_vnd": 1993.48,
                        "country_of_origin_code": "CN",
                        "country_of_origin_name": "CHINA",
                        "preferential_code": "B05",
                        "manufacturer_name": "FUJIAN LIAO PAPER CO., LTD",
                        "brand_name": "Ipaly",
                        "condition": "Mới 100%"
                    }
                ],
                "import_duty": {
                    "rate": 0.0,
                    "rate_type": "C",
                    "amount": 0.0,
                    "exemption_amount": 0.0
                },
                "vat": {
                    "name": "Thuế GTGT",
                    "rate_code": "VB245",
                    "rate": 8.0,
                    "taxable_value_vnd": 613393796,
                    "amount": 49071503.68,
                    "exemption_amount": 0.0
                },
                "tax_summary": {
                    "total_tax_amount_vnd": 49071504,
                    "tax_payment_deadline_code": "D",
                    "taxpayer_type": "1",
                    "tax_classification": "A"
                },
                "metadata": {
                    "total_pages": 3,
                    "total_line_items": 1
                },
                "confidence_scores": {
                    "importer.tax_code": 0.95,
                    "invoice.invoice_number": 0.98,
                    "products.0.hs_code": 0.87
                },
                "overall_confidence": 0.94
            }
        }
    }
