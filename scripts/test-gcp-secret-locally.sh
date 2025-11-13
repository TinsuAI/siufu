#!/bin/bash
# Test script to verify GCP secret will work in GitHub Actions
# This simulates what the workflow does

echo "=== Testing GCP Secret for GitHub Actions ==="

# Check if the local file exists
if [ ! -f "secrets/gcp-sa-key.json" ]; then
    echo "✗ File not found: secrets/gcp-sa-key.json"
    exit 1
fi

echo -e "\n1. Original file validation:"
python3 -m json.tool secrets/gcp-sa-key.json > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ Original file is valid JSON"
else
    echo "✗ Original file is NOT valid JSON"
    exit 1
fi

# Simulate what GitHub Actions does
echo -e "\n2. Simulating GitHub Actions transfer (base64):"

# Read the file content (this simulates the GitHub secret)
SECRET_CONTENT=$(cat secrets/gcp-sa-key.json)

# Encode to base64 (simulating: echo "$SECRET" | base64)
ENCODED=$(echo "$SECRET_CONTENT" | base64 -w 0)
echo "  Encoded length: ${#ENCODED} characters"

# Decode from base64 (simulating: base64 -d > file)
DECODED=$(echo "$ENCODED" | base64 -d)

# Write to temp file
echo "$DECODED" > /tmp/gcp-test-decoded.json

# Validate the decoded file
echo -e "\n3. Validating decoded file:"
python3 << 'PYEOF'
import json
import sys

try:
    with open('/tmp/gcp-test-decoded.json', 'r') as f:
        creds = json.load(f)

    # Validate required fields
    required_fields = ['type', 'project_id', 'private_key_id', 'private_key',
                      'client_email', 'client_id', 'auth_uri', 'token_uri']

    missing_fields = [field for field in required_fields if field not in creds]

    if missing_fields:
        print(f"✗ Missing required fields: {', '.join(missing_fields)}")
        sys.exit(1)

    # Validate formats
    if creds.get('type') != 'service_account':
        print(f"✗ Invalid type: {creds.get('type')}")
        sys.exit(1)

    if not creds.get('private_key', '').startswith('-----BEGIN PRIVATE KEY-----'):
        print("✗ Invalid private_key format")
        sys.exit(1)

    if '\\n' not in creds.get('private_key', ''):
        print("✗ Private key missing escaped newlines")
        sys.exit(1)

    print("✓ Decoded file is valid!")
    print(f"  Project ID: {creds['project_id']}")
    print(f"  Service Account: {creds['client_email']}")
    print(f"  Private Key: {len(creds['private_key'])} characters")

except json.JSONDecodeError as e:
    print(f"✗ Invalid JSON after decoding: {e}")
    print("\nFirst 200 chars of decoded content:")
    with open('/tmp/gcp-test-decoded.json', 'r') as f:
        print(f.read()[:200])
    sys.exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)
PYEOF

if [ $? -eq 0 ]; then
    echo -e "\n=== SUCCESS ==="
    echo "✓ Your local GCP credentials file will work with GitHub Actions!"
    echo "  The file survived base64 encoding/decoding correctly."
else
    echo -e "\n=== FAILURE ==="
    echo "✗ The GitHub secret transfer simulation failed."
    echo "  This means there's an issue with the file format."
fi

# Cleanup
rm -f /tmp/gcp-test-decoded.json
