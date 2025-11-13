#!/bin/bash
# Diagnostic script for production GCP credentials issue
# Run this on the PRODUCTION server

echo "=== Checking Production GCP Credentials ==="

# 1. Check if the file exists and its permissions
echo -e "\n1. GCP credentials file info:"
docker exec siufu-celery-worker ls -la /app/secrets/gcp-sa-key.json

# 2. Check the first few lines of the file (to see the malformed JSON)
echo -e "\n2. First 10 lines of GCP credentials:"
docker exec siufu-celery-worker head -10 /app/secrets/gcp-sa-key.json

# 3. Validate the JSON
echo -e "\n3. JSON validation:"
docker exec siufu-celery-worker python3 -c "
import json
try:
    with open('/app/secrets/gcp-sa-key.json', 'r') as f:
        content = f.read()
        print(f'File size: {len(content)} bytes')
        print(f'First 100 chars: {content[:100]}')
        json.loads(content)
        print('✓ JSON is valid')
except json.JSONDecodeError as e:
    print(f'✗ JSON is INVALID: {e}')
    print(f'Error at line {e.lineno}, column {e.colno}')
    # Show the problematic line
    lines = content.split('\n')
    if e.lineno <= len(lines):
        print(f'Problematic line: {lines[e.lineno-1]}')
except Exception as e:
    print(f'✗ Error: {e}')
"

echo -e "\n=== Diagnostic Complete ==="
echo "If JSON is invalid, you need to replace the file with a valid GCP service account key."
