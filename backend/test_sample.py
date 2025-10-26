#!/usr/bin/env python3
"""
Test script for end-to-end processing with sample data

Usage:
    python3 test_sample.py [sample_dir] [timeout]

Arguments:
    sample_dir: Path to sample directory (default: ../resources/sample/2)
    timeout: Timeout in seconds for processing (default: 360)

Examples:
    python3 test_sample.py
    python3 test_sample.py ../resources/sample/1
    python3 test_sample.py ../resources/sample/2 600
"""
import requests
import time
import json
import sys
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8780"
SAMPLE_DIR = Path("../resources/sample/2")  # Default sample directory
DEFAULT_TIMEOUT = 360  # Default timeout in seconds

# Files to upload
# The API requires 4 input files:
# - AN.pdf (Arrival Notice)
# - BOL.pdf (Bill of Lading)
# - CO.pdf (Certificate of Origin)
# - INVOICE (jpg/pdf/png) - extension will be auto-detected
#
# NOTE: CD.xlsx in sample folders is the EXPECTED OUTPUT, not an input file
FILES = {
    "arrival_notice": "AN.pdf",
    "bill_of_lading": "BOL.pdf",
    "certificate_of_origin": "CO.pdf",
    "invoice": "INVOICE"  # Extension will be auto-detected
}

def upload_files(sample_dir):
    """Upload declaration files"""
    print("📤 Step 1: Uploading files...")

    url = f"{BASE_URL}/api/v1/declarations/upload"

    files_data = {}
    for field_name, filename in FILES.items():
        # Auto-detect invoice file extension
        if field_name == "invoice":
            found = False
            for ext in ['.jpg', '.jpeg', '.pdf', '.png']:
                invoice_file = sample_dir / f"{filename}{ext}"
                if invoice_file.exists():
                    file_path = invoice_file
                    found = True
                    break
            if not found:
                print(f"⚠️  Warning: Invoice file not found (tried .jpg, .jpeg, .pdf, .png)")
                return None
        else:
            file_path = sample_dir / filename
            if not file_path.exists():
                print(f"⚠️  Warning: File not found: {file_path}")
                return None

        files_data[field_name] = (file_path.name, open(file_path, 'rb'))

    try:
        response = requests.post(url, files=files_data)

        # Close all file handles
        for field_name, file_tuple in files_data.items():
            file_tuple[1].close()

        if response.status_code == 201:
            data = response.json()
            declaration_id = data["declaration_id"]
            print(f"✅ Upload successful! Declaration ID: {declaration_id}")
            print(f"   Status: {data['status']}")
            print(f"   Files uploaded: {len(data['uploaded_files'])}")
            return declaration_id
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return None

def trigger_processing(declaration_id):
    """Trigger async processing"""
    print(f"\n⚙️  Step 2: Triggering processing for {declaration_id}...")

    url = f"{BASE_URL}/api/v1/declarations/{declaration_id}/process"

    try:
        response = requests.post(url)

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Processing started!")
            print(f"   Status: {data['status']}")
            print(f"   Celery Task ID: {data['celery_task_id']}")
            return True
        else:
            print(f"❌ Processing trigger failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Processing error: {e}")
        return False

def poll_status(declaration_id, max_wait=120):
    """Poll declaration status until complete or timeout"""
    print(f"\n📊 Step 3: Polling status (max {max_wait}s)...")

    url = f"{BASE_URL}/api/v1/declarations/{declaration_id}/status"

    start_time = time.time()
    last_status = None
    last_progress = 0.0
    poll_count = 0

    while time.time() - start_time < max_wait:
        try:
            poll_count += 1
            response = requests.get(url)

            if response.status_code == 200:
                data = response.json()
                status = data["status"]
                progress = data["progress"]

                # Print status updates (always show every 10 polls to prove we're alive)
                if status != last_status or progress != last_progress or poll_count % 10 == 0:
                    elapsed = time.time() - start_time
                    print(f"   [{elapsed:5.1f}s] Poll #{poll_count:3d} | Status: {status:20s} | Progress: {progress*100:5.1f}%")

                    # Show additional details if available
                    if data.get("current_step"):
                        print(f"           Current Step: {data['current_step']}")
                    if data.get("processing_error"):
                        print(f"           ⚠️  Error: {data['processing_error']}")

                    last_status = status
                    last_progress = progress

                # Check if complete
                if status == "READY_FOR_REVIEW":
                    total_time = time.time() - start_time
                    print(f"\n✅ Processing complete in {total_time:.1f}s! (Total polls: {poll_count})")
                    return True
                elif status == "FAILED":
                    print(f"\n❌ Processing failed after {poll_count} polls!")
                    if data.get("processing_error"):
                        print(f"   Error: {data['processing_error']}")
                    return False

                # Wait before next poll
                time.sleep(2)
            else:
                print(f"❌ Status check failed: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error during polling: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected polling error: {e}")
            import traceback
            print(traceback.format_exc())
            return False

    elapsed = time.time() - start_time
    print(f"\n⏱️  Timeout after {max_wait}s ({poll_count} polls, last status: {last_status})")
    print(f"   Consider increasing timeout or checking celery worker logs:")
    print(f"   docker logs logai-focus-celery-worker")
    return False

def get_results(declaration_id, sample_dir):
    """Retrieve and display extraction results"""
    print(f"\n📥 Step 4: Retrieving results...")

    url = f"{BASE_URL}/api/v1/declarations/{declaration_id}"

    try:
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()

            print(f"\n📋 Declaration Details:")
            print(f"   ID: {data['id']}")
            print(f"   Status: {data['status']}")
            print(f"   Progress: {data['processing_progress']*100:.1f}%")

            # Extract key fields
            extracted = data.get("extracted_data", {})

            if extracted:
                print(f"\n📊 Extracted Data Summary:")

                # Performance metrics
                perf = extracted.get("_performance_metrics", {})
                if perf:
                    print(f"\n   ⏱️  Performance Metrics:")
                    print(f"      OCR Duration: {perf.get('ocr_duration_seconds', 0):.1f}s")
                    print(f"      LLM Duration: {perf.get('llm_duration_seconds', 0):.1f}s")
                    print(f"      Storage Duration: {perf.get('storage_duration_seconds', 0):.1f}s")
                    print(f"      Total Duration: {perf.get('total_duration_seconds', 0):.1f}s")

                # Overall confidence
                overall_conf = extracted.get("overall_confidence", 0)
                print(f"\n   🎯 Overall Confidence: {overall_conf*100:.1f}%")

                # Importer info
                importer = extracted.get("importer", {})
                if importer:
                    print(f"\n   📦 Importer:")
                    print(f"      Tax Code: {importer.get('tax_code', 'N/A')}")
                    print(f"      Name: {importer.get('name', 'N/A')}")

                # Invoice info
                invoice = extracted.get("invoice", {})
                if invoice:
                    print(f"\n   💰 Invoice:")
                    print(f"      Number: {invoice.get('invoice_number', 'N/A')}")
                    print(f"      Date: {invoice.get('invoice_date', 'N/A')}")
                    print(f"      Total: {invoice.get('invoice_total', 0)} {invoice.get('invoice_currency', 'USD')}")

                # Products
                products = extracted.get("products", [])
                print(f"\n   📦 Products: {len(products)} items")
                for i, product in enumerate(products[:3], 1):  # Show first 3
                    print(f"      {i}. HS Code: {product.get('hs_code', 'N/A')}")
                    print(f"         Description: {product.get('product_description', 'N/A')[:80]}...")
                    print(f"         Quantity: {product.get('quantity_1', 0)} {product.get('quantity_unit_1', '')}")
                    print(f"         Unit Price: {product.get('invoice_unit_price', 0)} {product.get('invoice_unit_price_currency', 'USD')}")

                # Save full results to file in sample directory
                output_file = sample_dir / "results.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"\n   💾 Full results saved to: {output_file}")

            else:
                print("   ⚠️  No extracted data found")

            return True
        else:
            print(f"❌ Failed to retrieve results: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Retrieval error: {e}")
        return False

def main():
    """Run end-to-end test"""
    # Parse command line arguments
    if len(sys.argv) > 1:
        sample_dir = Path(sys.argv[1])
    else:
        sample_dir = SAMPLE_DIR

    if len(sys.argv) > 2:
        timeout = int(sys.argv[2])
    else:
        timeout = DEFAULT_TIMEOUT

    # Ensure sample directory exists
    if not sample_dir.exists():
        print(f"❌ Sample directory does not exist: {sample_dir}")
        return

    print(f"🚀 Starting End-to-End Test with Sample: {sample_dir}\n")
    print(f"   Timeout: {timeout}s\n")
    print("=" * 60)

    # Step 1: Upload files
    declaration_id = upload_files(sample_dir)
    if not declaration_id:
        print("\n❌ Test failed at upload stage")
        return

    # Step 2: Trigger processing
    if not trigger_processing(declaration_id):
        print("\n❌ Test failed at processing trigger stage")
        return

    # Step 3: Poll status
    if not poll_status(declaration_id, max_wait=timeout):
        print("\n❌ Test failed at polling stage")
        return

    # Step 4: Get results
    if not get_results(declaration_id, sample_dir):
        print("\n❌ Test failed at results retrieval stage")
        return

    print("\n" + "=" * 60)
    print("✅ End-to-End Test PASSED!")
    print("=" * 60)

if __name__ == "__main__":
    main()
