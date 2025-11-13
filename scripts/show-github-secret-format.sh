#!/bin/bash
# Script to show what the GitHub secret GCP_SA_KEY_JSON should look like

echo "=== GitHub Secret Format Checker ==="
echo ""

if [ ! -f "secrets/gcp-sa-key.json" ]; then
    echo "✗ File not found: secrets/gcp-sa-key.json"
    exit 1
fi

echo "Your local GCP credentials file:"
echo "================================="
cat secrets/gcp-sa-key.json
echo ""
echo "================================="
echo ""

echo "Validation:"
python3 -m json.tool secrets/gcp-sa-key.json > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ Local file is valid JSON"
else
    echo "✗ Local file is NOT valid JSON"
    exit 1
fi

echo ""
echo "=== What to put in GitHub Secret ==="
echo "1. Go to: https://github.com/gabenidolcs-creator/siufu/settings/secrets/actions"
echo "2. Edit the secret: GCP_SA_KEY_JSON"
echo "3. Copy the ENTIRE content above (between the === lines)"
echo "4. Paste it into the secret value"
echo ""
echo "IMPORTANT: Make sure you copy ALL the content including:"
echo "  - Opening and closing braces { }"
echo "  - All double quotes around keys and values"
echo "  - The \\n characters in the private_key (they should stay as \\n, not become actual newlines)"
echo ""

echo "=== Checking what GitHub currently has ==="
echo "After updating the secret, the 'First 100 chars' in CI logs should show:"
echo ""
head -c 100 secrets/gcp-sa-key.json
echo ""
echo ""
echo "If it shows 'type: service_account' (without quotes), the secret is wrong!"
echo "It should show '\"type\": \"service_account\"' (with quotes)!"
