#!/usr/bin/env python3
"""
One-time script to transform existing declarations' draft_data from
Vietnamese format to frontend form format
"""
import json

def transform_vietnamese_to_draft(extracted_data):
    """Transform Vietnamese declaration data to form schema"""
    importer = extracted_data.get("importer", {})
    invoice = extracted_data.get("invoice", {})
    products = extracted_data.get("products", [])
    vat = extracted_data.get("vat", {})
    import_duty = extracted_data.get("import_duty", {})

    # Transform products
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

    # Build draft data
    draft_data = {
        "company_info": {
            "importer_name": importer.get("name", ""),
            "tax_id": importer.get("tax_code", ""),
            "address": importer.get("address", ""),
            "city": "",
            "country": "VN",
            "contact_person": "",
            "contact_email": "",
            "contact_phone": importer.get("phone", "")
        },
        "shipment_details": {
            "bol_number": invoice.get("invoice_number", ""),
            "arrival_date": invoice.get("invoice_date", ""),
            "port_of_arrival": "",
            "port_of_departure": "",
            "container_numbers": [""],
            "vessel_name": ""
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


if __name__ == "__main__":
    import sys

    # Read extracted_data from stdin
    extracted_data = json.load(sys.stdin)

    # Transform and output
    draft_data = transform_vietnamese_to_draft(extracted_data)
    print(json.dumps(draft_data, ensure_ascii=False))
