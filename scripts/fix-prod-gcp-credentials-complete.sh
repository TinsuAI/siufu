#!/bin/bash
# Complete script to fix malformed GCP credentials on production
# This script will:
# 1. Copy the malformed file from the container
# 2. Fix the JSON format
# 3. Replace the file
# 4. Restart Celery worker

set -e  # Exit on error

echo "=== Fixing Production GCP Credentials ==="

# Step 1: Copy the malformed file from the container
echo -e "\n1. Copying malformed GCP credentials from container..."
docker cp siufu-celery-worker:/app/secrets/gcp-sa-key.json /tmp/gcp-sa-key-malformed.json
echo "✓ Copied to /tmp/gcp-sa-key-malformed.json"

# Step 2: Fix the JSON format using Python
echo -e "\n2. Converting to proper JSON format..."

python3 << 'EOF'
import json
import re

# Read the malformed file
with open('/tmp/gcp-sa-key-malformed.json', 'r') as f:
    content = f.read()

print(f"Original size: {len(content)} bytes")

# Fix newlines in private key
content = content.replace('-----BEGIN PRIVATE KEY-----n', '-----BEGIN PRIVATE KEY-----\\n')
content = content.replace('n-----END PRIVATE KEY-----', '\\n-----END PRIVATE KEY-----')
content = re.sub(r'([A-Za-z0-9+/=])n([A-Za-z0-9+/=])', r'\1\\n\2', content)

# Parse and fix each line
lines = content.split('\n')
fixed_lines = []

for line in lines:
    stripped = line.strip()

    if not stripped or stripped in ['{', '}']:
        fixed_lines.append(line)
        continue

    # Match "key: value," pattern
    match = re.match(r'^(\s*)([a-z_]+):\s*(.+?)(,?)$', line)
    if match:
        indent, key, value, comma = match.groups()

        # Remove trailing comma from value
        value = value.rstrip(',').strip()

        # Quote the key
        key = f'"{key}"'

        # Quote the value if it's not a number
        if not value.isdigit():
            value = f'"{value}"'

        # Reconstruct line
        fixed_line = f'{indent}{key}: {value}{comma}'
        fixed_lines.append(fixed_line)
    else:
        fixed_lines.append(line)

fixed_content = '\n'.join(fixed_lines)

# Parse as JSON to validate and pretty-print
try:
    parsed = json.loads(fixed_content)
    print("✓ JSON is valid")
    print(f"  Project: {parsed.get('project_id')}")
    print(f"  Email: {parsed.get('client_email')}")

    # Write the fixed JSON
    with open('/tmp/gcp-sa-key-fixed.json', 'w') as f:
        json.dump(parsed, f, indent=2)

    print(f"✓ Fixed file created: /tmp/gcp-sa-key-fixed.json")
    print(f"  New size: {len(json.dumps(parsed, indent=2))} bytes")
except json.JSONDecodeError as e:
    print(f"✗ JSON validation failed: {e}")
    print("First 500 chars of fixed content:")
    print(fixed_content[:500])
    exit(1)
EOF

# Check if Python script succeeded
if [ $? -ne 0 ]; then
    echo "✗ Failed to fix JSON format"
    exit 1
fi

# Step 3: Validate the fixed file
echo -e "\n3. Final validation..."
if ! python3 -m json.tool /tmp/gcp-sa-key-fixed.json > /dev/null; then
    echo "✗ Final validation failed"
    exit 1
fi
echo "✓ Fixed file is valid JSON"

# Step 4: Backup the old file on host
echo -e "\n4. Creating backup..."
BACKUP_FILE="$HOME/logai/secrets/gcp-sa-key.json.backup.$(date +%Y%m%d_%H%M%S)"
cp "$HOME/logai/secrets/gcp-sa-key.json" "$BACKUP_FILE" || true
echo "✓ Backup created: $BACKUP_FILE"

# Step 5: Replace the file on host
echo -e "\n5. Replacing credentials file..."
cp /tmp/gcp-sa-key-fixed.json "$HOME/logai/secrets/gcp-sa-key.json"
chmod 644 "$HOME/logai/secrets/gcp-sa-key.json"
echo "✓ File replaced"

# Step 6: Restart Celery worker
echo -e "\n6. Restarting Celery worker..."
docker restart siufu-celery-worker

echo "Waiting for worker to start..."
sleep 5

# Step 7: Verify the fix
echo -e "\n7. Verifying the fix..."
docker exec siufu-celery-worker python3 << 'EOF'
import json
try:
    with open('/app/secrets/gcp-sa-key.json', 'r') as f:
        creds = json.load(f)
    print('✓ Celery worker can read credentials!')
    print(f'  Project ID: {creds["project_id"]}')
    print(f'  Client Email: {creds["client_email"]}')
except Exception as e:
    print(f'✗ Error: {e}')
    exit(1)
EOF

# Step 8: Show recent logs
echo -e "\n8. Recent Celery worker logs:"
docker logs siufu-celery-worker --tail 10

echo -e "\n=== Fix Complete ==="
echo "✓ GCP credentials have been fixed and Celery worker restarted"
echo "✓ Try uploading a declaration to test"
echo ""
echo "Backup file location: $BACKUP_FILE"
echo "Fixed file location: /tmp/gcp-sa-key-fixed.json"
