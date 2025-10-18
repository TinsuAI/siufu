"""
Mock fixtures for Google Cloud Document AI responses
"""
from unittest.mock import MagicMock
from typing import List


def _create_mock_entity(entity_type: str, mention_text: str, confidence: float):
    """Create mock Document AI entity"""
    entity = MagicMock()
    entity.type_ = entity_type
    entity.mention_text = mention_text
    entity.confidence = confidence
    return entity


def _create_mock_cell(text: str, start_idx: int, end_idx: int):
    """Create mock Document AI table cell"""
    cell = MagicMock()
    cell.layout.text_anchor.text_segments = [MagicMock()]
    cell.layout.text_anchor.text_segments[0].start_index = start_idx
    cell.layout.text_anchor.text_segments[0].end_index = end_idx
    return cell


def _create_mock_row(cells: List[MagicMock]):
    """Create mock Document AI table row"""
    row = MagicMock()
    row.cells = cells
    return row


def _create_mock_table(headers: List[str], rows: List[List[str]], text: str):
    """Create mock Document AI table"""
    table = MagicMock()

    # Track position in text
    pos = 0

    # Create header row
    header_cells = []
    for header in headers:
        start = pos
        end = pos + len(header)
        header_cells.append(_create_mock_cell(header, start, end))
        pos = end + 1

    table.header_rows = [_create_mock_row(header_cells)]

    # Create body rows
    body_rows = []
    for row in rows:
        row_cells = []
        for cell_text in row:
            start = pos
            end = pos + len(cell_text)
            row_cells.append(_create_mock_cell(cell_text, start, end))
            pos = end + 1
        body_rows.append(_create_mock_row(row_cells))

    table.body_rows = body_rows
    return table


def mock_document_ai_response_an():
    """Mock Document AI response for AN.pdf (Arrival Notice)"""
    response = MagicMock()
    document = MagicMock()

    # Full text
    document.text = """ARRIVAL NOTICE
Vessel: MSC GEMMA
Voyage: 2025001E
Container No: MSCU1234567
Size: 40'
Weight: 20,000 kg
Port of Discharge: HO CHI MINH
Arrival Date: 2025-01-15
Notify Party: ABC IMPORT EXPORT CO"""

    # Entities (key-value pairs)
    document.entities = [
        _create_mock_entity("vessel_name", "MSC GEMMA", 0.95),
        _create_mock_entity("voyage", "2025001E", 0.92),
        _create_mock_entity("container_number", "MSCU1234567", 0.98),
        _create_mock_entity("port_of_discharge", "HO CHI MINH", 0.89),
        _create_mock_entity("arrival_date", "2025-01-15", 0.94),
    ]

    # Pages with tables
    page = MagicMock()
    table = _create_mock_table(
        headers=["Container No", "Size", "Weight"],
        rows=[["MSCU1234567", "40'", "20,000 kg"]],
        text=document.text
    )
    page.tables = [table]
    document.pages = [page]

    response.document = document
    return response


def mock_document_ai_response_bol():
    """Mock Document AI response for BOL.pdf (Bill of Lading)"""
    response = MagicMock()
    document = MagicMock()

    document.text = """BILL OF LADING
B/L No: MSCU20250115001
Shipper: XYZ EXPORT CO LTD
Consignee: ABC IMPORT CO
Port of Loading: SHANGHAI
Port of Discharge: HO CHI MINH
Container: MSCU1234567
Commodity: Electronic Equipment
Total Packages: 500 CTNS"""

    document.entities = [
        _create_mock_entity("bol_number", "MSCU20250115001", 0.96),
        _create_mock_entity("shipper", "XYZ EXPORT CO LTD", 0.91),
        _create_mock_entity("consignee", "ABC IMPORT CO", 0.93),
        _create_mock_entity("port_of_loading", "SHANGHAI", 0.95),
        _create_mock_entity("port_of_discharge", "HO CHI MINH", 0.89),
        _create_mock_entity("container", "MSCU1234567", 0.98),
    ]

    page = MagicMock()
    page.tables = []
    document.pages = [page]

    response.document = document
    return response


def mock_document_ai_response_co():
    """Mock Document AI response for CO.pdf (Certificate of Origin)"""
    response = MagicMock()
    document = MagicMock()

    document.text = """CERTIFICATE OF ORIGIN
Certificate No: CO-2025-0001
Exporter: XYZ EXPORT CO LTD
Importer: ABC IMPORT CO
Country of Origin: CHINA

Product No    Description              HS Code     Quantity
1             Laptop Computer          8471.30     200 PCS
2             Computer Monitor         8528.49     300 PCS"""

    document.entities = [
        _create_mock_entity("certificate_number", "CO-2025-0001", 0.97),
        _create_mock_entity("exporter", "XYZ EXPORT CO LTD", 0.91),
        _create_mock_entity("importer", "ABC IMPORT CO", 0.93),
        _create_mock_entity("country_of_origin", "CHINA", 0.95),
    ]

    page = MagicMock()
    table = _create_mock_table(
        headers=["Product No", "Description", "HS Code", "Quantity"],
        rows=[
            ["1", "Laptop Computer", "8471.30", "200 PCS"],
            ["2", "Computer Monitor", "8528.49", "300 PCS"]
        ],
        text=document.text
    )
    page.tables = [table]
    document.pages = [page]

    response.document = document
    return response


def mock_document_ai_response_invoice():
    """Mock Document AI response for INVOICE.jpg (Commercial Invoice)"""
    response = MagicMock()
    document = MagicMock()

    document.text = """COMMERCIAL INVOICE
Invoice No: INV-2025-0001
Invoice Date: 2025-01-10
Seller: XYZ EXPORT CO LTD
Buyer: ABC IMPORT CO

Item    Description         Qty     Unit Price    Amount
1       Laptop Computer     200     $500.00       $100,000.00
2       Computer Monitor    300     $200.00       $60,000.00

Total Amount: $160,000.00
Currency: USD"""

    document.entities = [
        _create_mock_entity("invoice_number", "INV-2025-0001", 0.96),
        _create_mock_entity("invoice_date", "2025-01-10", 0.94),
        _create_mock_entity("seller", "XYZ EXPORT CO LTD", 0.91),
        _create_mock_entity("buyer", "ABC IMPORT CO", 0.93),
        _create_mock_entity("total_amount", "$160,000.00", 0.97),
        _create_mock_entity("currency", "USD", 0.99),
    ]

    page = MagicMock()
    table = _create_mock_table(
        headers=["Item", "Description", "Qty", "Unit Price", "Amount"],
        rows=[
            ["1", "Laptop Computer", "200", "$500.00", "$100,000.00"],
            ["2", "Computer Monitor", "300", "$200.00", "$60,000.00"]
        ],
        text=document.text
    )
    page.tables = [table]
    document.pages = [page]

    response.document = document
    return response
