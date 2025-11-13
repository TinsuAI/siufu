#!/bin/bash
# Upload GCP credentials to production server manually

echo "=========================================="
echo "Uploading GCP credentials to production"
echo "=========================================="
echo ""

# Use base64 to safely transfer the file
cat /home/tinxu-luna/logai/secrets/gcp-sa-key.json | base64 -w 0 | \
  ssh tinxu-luna@tinxudev.airplane-manta.ts.net \
  "base64 -d > /home/tinxu-luna/logai-production/secrets/gcp-sa-key.json && chmod 644 /home/tinxu-luna/logai-production/secrets/gcp-sa-key.json"

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ File uploaded successfully!"
    echo ""
    echo "Verifying on production server..."
    ssh tinxu-luna@tinxudev.airplane-manta.ts.net \
      "python3 -m json.tool /home/tinxu-luna/logai-production/secrets/gcp-sa-key.json > /dev/null 2>&1 && echo '✓ File is valid JSON on production' || echo '✗ File is invalid on production'"

    echo ""
    echo "Showing first 200 characters on production:"
    ssh tinxu-luna@tinxudev.airplane-manta.ts.net \
      "head -c 200 /home/tinxu-luna/logai-production/secrets/gcp-sa-key.json"
    echo ""
    echo ""
    echo "=========================================="
    echo "SUCCESS! GCP credentials are now on production"
    echo "=========================================="
else
    echo "✗ Upload failed"
    exit 1
fi
