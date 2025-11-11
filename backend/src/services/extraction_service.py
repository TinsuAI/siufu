"""
Extraction service for mapping extracted data to source document locations
"""
from typing import Any, Dict

from src.schemas.ocr import OCRResult


class ExtractionService:
    """
    Service for creating source metadata mappings

    Maps extracted field values to their source document locations (page, bbox)
    by matching values against OCR entities.
    """

    @staticmethod
    def build_source_metadata(
        extracted_data: Dict[str, Any],
        ocr_results: Dict[str, OCRResult],
        file_type_mapping: Dict[str, str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Build source metadata by matching extracted values to OCR entities

        Args:
            extracted_data: Nested dict of extracted field values
            ocr_results: Dict mapping document type (AN, BOL, CO, INVOICE) to OCRResult
            file_type_mapping: Dict mapping field paths to likely source document types

        Returns:
            Dict mapping field_path to {source, page, bbox}

        Example:
            {
                "company_info.importer_name": {
                    "source": "INVOICE",
                    "page": 1,
                    "bbox": [0.1, 0.2, 0.3, 0.05]
                }
            }
        """
        source_metadata = {}

        # Flatten extracted_data to field paths
        flat_data = ExtractionService._flatten_dict(extracted_data)

        # For each field, try to find matching OCR entity
        for field_path, value in flat_data.items():
            if value is None or value == "":
                continue

            # Try to find this value in OCR results
            source_info = ExtractionService._find_value_in_ocr(
                str(value),
                ocr_results,
                field_type_mapping=file_type_mapping.get(field_path)
            )

            if source_info:
                source_metadata[field_path] = source_info

        return source_metadata

    @staticmethod
    def _flatten_dict(data: Dict[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
        """
        Flatten nested dictionary to dot-notation paths

        Example:
            {"company": {"name": "ABC"}} -> {"company.name": "ABC"}
        """
        items = []
        for k, v in data.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k

            if isinstance(v, dict):
                items.extend(ExtractionService._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                # Handle lists by indexing
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        items.extend(
                            ExtractionService._flatten_dict(item, f"{new_key}.{i}", sep=sep).items()
                        )
                    else:
                        items.append((f"{new_key}.{i}", item))
            else:
                items.append((new_key, v))

        return dict(items)

    @staticmethod
    def _find_value_in_ocr(
        value: str,
        ocr_results: Dict[str, OCRResult],
        field_type_mapping: str | None = None
    ) -> Dict[str, Any] | None:
        """
        Find a value in OCR entities and return its source location

        Args:
            value: The value to search for
            ocr_results: OCR results to search in
            field_type_mapping: Preferred document type to search first (optimization)

        Returns:
            Dict with {source, page, bbox} or None if not found
        """
        # Normalize value for comparison (case-insensitive, strip whitespace)
        normalized_value = value.strip().lower()

        # Try preferred document type first if provided
        search_order = []
        if field_type_mapping and field_type_mapping in ocr_results:
            search_order.append(field_type_mapping)

        # Add remaining document types
        for doc_type in ["AN", "BOL", "CO", "INVOICE"]:
            if doc_type not in search_order and doc_type in ocr_results:
                search_order.append(doc_type)

        # Search through OCR results in order
        for doc_type in search_order:
            ocr_result = ocr_results[doc_type]

            # Search in key-value pairs
            for kv_pair in ocr_result.key_value_pairs:
                if not kv_pair.value:
                    continue

                normalized_ocr_value = kv_pair.value.strip().lower()

                # Check for exact match or substring match
                if normalized_value in normalized_ocr_value or normalized_ocr_value in normalized_value:
                    # Found a match!
                    if kv_pair.page is not None and kv_pair.bbox is not None:
                        return {
                            "source": doc_type,
                            "page": kv_pair.page,
                            "bbox": kv_pair.bbox
                        }

        # Not found in any OCR result
        return None

    @staticmethod
    def get_default_field_type_mapping() -> Dict[str, str]:
        """
        Get default mapping of field paths to likely source document types

        This is a heuristic to optimize search order when matching values.
        """
        return {
            # Company info typically from invoice
            "company_info.importer_name": "INVOICE",
            "company_info.exporter_name": "INVOICE",
            "shipper.name": "INVOICE",
            "consignee.name": "INVOICE",

            # Container info from BOL or AN
            "containers": "BOL",
            "container_number": "BOL",

            # Origin info from CO
            "origin_country": "CO",
            "certificate_number": "CO",

            # Invoice-specific fields
            "invoice_number": "INVOICE",
            "invoice_total": "INVOICE",
            "invoice_date": "INVOICE",

            # BOL-specific fields
            "bol_number": "BOL",
            "bol_date": "BOL",

            # Arrival notice fields
            "vessel_name": "AN",
            "arrival_date": "AN",
        }
