#!/usr/bin/env python3
"""
Test OCR functionality with sample files

This script tests the OCR service with all sample files to verify:
- Document AI integration works
- OCR extracts text correctly
- Caching improves performance

Usage:
    python scripts/test-ocr.py
"""
import sys
import os
import time

# Add backend src to path
sys.path.insert(0, '/app')

from src.services.ocr_service import OCRService
from src.core.errors import DocumentAIException


def test_ocr_file(ocr_service: OCRService, file_path: str, expected_fields: list):
    """
    Test OCR on a single file

    Args:
        ocr_service: OCR service instance
        file_path: Path to file
        expected_fields: List of expected extracted fields
    """
    file_name = os.path.basename(file_path)
    print(f"\n{'='*60}")
    print(f"Processing {file_name}...")
    print('='*60)

    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False

    try:
        # First call - cache miss
        start_time = time.time()
        result = ocr_service.process_document_ocr(file_path)
        first_call_time = int((time.time() - start_time) * 1000)

        # Validate result
        print(f"✅ Extracted {len(result.text)} characters")
        print(f"✅ Page count: {result.page_count}")
        print(f"✅ Processing time: {result.processing_time_ms}ms")

        if result.key_value_pairs:
            print(f"✅ Extracted {len(result.key_value_pairs)} key-value pairs")
            for pair in result.key_value_pairs[:3]:  # Show first 3
                print(f"   - {pair.key}: {pair.value[:50]}... (confidence: {pair.confidence:.2f})")

        if result.tables:
            print(f"✅ Extracted {len(result.tables)} tables")
            for i, table in enumerate(result.tables[:2]):  # Show first 2
                print(f"   - Table {i+1}: {len(table.headers)} columns, {len(table.rows)} rows")

        if result.confidence_scores:
            avg_confidence = sum(result.confidence_scores.values()) / len(result.confidence_scores)
            print(f"✅ Average confidence: {avg_confidence:.2f}")

            if avg_confidence < 0.7:
                print(f"⚠️  Low confidence score: {avg_confidence:.2f}")

        # Test caching
        print(f"\nTesting cache...")
        start_time = time.time()
        cached_result = ocr_service.process_document_ocr(file_path)
        second_call_time = int((time.time() - start_time) * 1000)

        print(f"✅ Cache hit - Processing time: {second_call_time}ms")

        if second_call_time < 500:
            print(f"✅ Cache performance good (<500ms)")
        else:
            print(f"⚠️  Cache slower than expected: {second_call_time}ms")

        # Verify cached result matches
        if cached_result.text == result.text:
            print(f"✅ Cached result matches original")
        else:
            print(f"❌ Cached result differs from original")
            return False

        print(f"\n✅ {file_name} test passed!")
        return True

    except DocumentAIException as e:
        print(f"❌ Document AI error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test runner"""
    print("\n" + "="*60)
    print("Document AI OCR Test Suite")
    print("="*60)

    # Initialize OCR service
    try:
        print("\nInitializing OCR service...")
        ocr_service = OCRService()
        print("✅ OCR service initialized successfully")
    except FileNotFoundError as e:
        print(f"❌ GCP credentials not found: {e}")
        print("\nPlease ensure:")
        print("1. GCP service account key is at: ./secrets/gcp-sa-key.json")
        print("2. Environment variables are set:")
        print("   - GOOGLE_CLOUD_PROJECT_ID")
        print("   - GOOGLE_CLOUD_LOCATION")
        print("   - GOOGLE_CLOUD_PROCESSOR_ID")
        print("\nSee docs/setup-google-cloud.md for setup instructions.")
        return 1
    except Exception as e:
        print(f"❌ Failed to initialize OCR service: {e}")
        return 1

    # Test files
    test_cases = [
        {
            "file": "/app/resources/sample/1/AN.pdf",
            "expected_fields": ["vessel_name", "container_number", "arrival_date"]
        },
        {
            "file": "/app/resources/sample/1/BOL.pdf",
            "expected_fields": ["bol_number", "shipper", "consignee", "port_of_loading"]
        },
        {
            "file": "/app/resources/sample/1/CO.pdf",
            "expected_fields": ["certificate_number", "exporter", "country_of_origin"]
        },
        {
            "file": "/app/resources/sample/1/INVOICE.jpg",
            "expected_fields": ["invoice_number", "invoice_date", "total_amount"]
        }
    ]

    # Run tests
    results = []
    for test_case in test_cases:
        success = test_ocr_file(
            ocr_service,
            test_case["file"],
            test_case["expected_fields"]
        )
        results.append((os.path.basename(test_case["file"]), success))

    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for file_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {file_name}")

    print("-"*60)
    print(f"Total: {passed}/{total} tests passed")
    print("="*60)

    if passed == total:
        print("\n🎉 All tests passed! Document AI is configured correctly.")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
