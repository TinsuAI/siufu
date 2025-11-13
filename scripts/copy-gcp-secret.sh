#!/bin/bash
# Script to display the exact content to copy into GitHub secret

echo "=============================================="
echo "COPY EVERYTHING BETWEEN THE LINES BELOW"
echo "=============================================="
cat secrets/gcp-sa-key.json
echo ""
echo "=============================================="
echo "STOP COPYING HERE"
echo "=============================================="
echo ""
echo "Instructions:"
echo "1. Select and copy ALL the text between the lines above"
echo "2. Go to: https://github.com/gabenidolcs-creator/siufu/settings/secrets/actions"
echo "3. Click 'GCP_SA_KEY_JSON' to edit it"
echo "4. Delete the current value"
echo "5. Paste the copied content (Ctrl+V or Cmd+V)"
echo "6. Click 'Update secret'"
echo ""
echo "IMPORTANT: Copy from the opening { to the closing }"
echo "The private_key field should have \\n (not actual line breaks)"
