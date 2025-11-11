#!/usr/bin/env python3
"""
Fetch results from successful declaration and save to sample2_results.json
"""
import json
from pathlib import Path

import requests

BASE_URL = "http://localhost:8780"
DECLARATION_ID = "8d351ca0-85c5-429e-94b0-8890e6afbbd5"

def fetch_and_save():
    """Fetch declaration and save results"""
    url = f"{BASE_URL}/api/v1/declarations/{DECLARATION_ID}"

    try:
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()

            # Save to file
            output_file = Path("sample2_results.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"✅ Results saved to {output_file}")
            print(f"   Declaration ID: {data['id']}")
            print(f"   Status: {data['status']}")
            print(f"   Progress: {data['processing_progress']*100:.1f}%")

            # Show summary
            extracted = data.get("extracted_data", {})
            if extracted:
                print("\n📊 Summary:")
                print(f"   Overall Confidence: {extracted.get('overall_confidence', 0)*100:.1f}%")
                print(f"   Products: {len(extracted.get('products', []))}")

                perf = extracted.get("_performance_metrics", {})
                if perf:
                    print(f"   Total Processing Time: {perf.get('total_duration_seconds', 0):.1f}s")

            return True
        else:
            print(f"❌ Failed to fetch: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    fetch_and_save()
