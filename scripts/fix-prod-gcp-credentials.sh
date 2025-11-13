#!/bin/bash
# Script to fix production GCP credentials
# Run this on the PRODUCTION server AFTER you've placed a valid gcp-sa-key.json file

echo "=== Fixing Production GCP Credentials ==="

# Instructions
echo "IMPORTANT: Before running this script, ensure you have:"
echo "1. A valid GCP service account key JSON file"
echo "2. Place it at: /home/ubuntu/logai/secrets/gcp-sa-key.json (or wherever your secrets directory is)"
echo ""
read -p "Have you placed the valid GCP credentials file? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborting. Please place the valid GCP credentials file first."
    exit 1
fi

# 1. Validate the JSON file on the host
echo -e "\n1. Validating JSON on host..."
if ! python3 -m json.tool ~/logai/secrets/gcp-sa-key.json > /dev/null 2>&1; then
    echo "✗ ERROR: The JSON file is still invalid on the host!"
    echo "Please fix the JSON format before proceeding."
    exit 1
fi
echo "✓ JSON is valid on host"

# 2. Check file permissions (should be readable)
echo -e "\n2. Checking file permissions..."
ls -la ~/logai/secrets/gcp-sa-key.json

# 3. Restart Celery worker to pick up the new credentials
echo -e "\n3. Restarting Celery worker..."
docker restart siufu-celery-worker

# 4. Wait for worker to start
echo "Waiting for worker to start..."
sleep 5

# 5. Verify the worker can read the credentials
echo -e "\n4. Verifying worker can read credentials..."
docker exec siufu-celery-worker python3 -c "
import json
try:
    with open('/app/secrets/gcp-sa-key.json', 'r') as f:
        creds = json.load(f)
        print(f'✓ Credentials loaded successfully')
        print(f'  Project ID: {creds.get(\"project_id\", \"N/A\")}')
        print(f'  Type: {creds.get(\"type\", \"N/A\")}')
except Exception as e:
    print(f'✗ Error: {e}')
"

# 6. Check worker logs
echo -e "\n5. Recent worker logs:"
docker logs siufu-celery-worker --tail 20

echo -e "\n=== Fix Complete ==="
echo "The Celery worker should now be able to process declarations."
echo "Try uploading a declaration to test."
