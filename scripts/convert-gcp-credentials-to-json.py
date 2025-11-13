#!/usr/bin/env python3
"""
Script to convert malformed GCP credentials (YAML-style) to proper JSON format
Run this on the production server
"""
import json
import re
import sys

def fix_gcp_credentials(input_file, output_file):
    """Convert malformed YAML-style GCP credentials to proper JSON"""

    print(f"Reading malformed file: {input_file}")
    with open(input_file, 'r') as f:
        content = f.read()

    print(f"Original file size: {len(content)} bytes")

    # Step 1: Fix the newlines in private key (n -> \n)
    content = content.replace('-----BEGIN PRIVATE KEY-----n', '-----BEGIN PRIVATE KEY-----\\n')
    content = content.replace('n-----END PRIVATE KEY-----', '\\n-----END PRIVATE KEY-----')
    # Replace all standalone 'n' with '\n' in the private key section
    content = re.sub(r'([A-Za-z0-9+/=])n([A-Za-z0-9+/=])', r'\1\\n\2', content)

    # Step 2: Add quotes around property names and string values
    # This is a more robust approach using regex

    # Remove trailing commas before closing brace (if any)
    content = re.sub(r',\s*}', '}', content)
    content = re.sub(r',\s*$', '', content, flags=re.MULTILINE)

    # Parse line by line and fix
    lines = content.split('\n')
    fixed_lines = []

    for line in lines:
        stripped = line.strip()

        # Skip empty lines, opening/closing braces
        if not stripped or stripped in ['{', '}', '{,', '},']:
            fixed_lines.append(line)
            continue

        # Match pattern: "  key: value," or "  key: value"
        match = re.match(r'^(\s*)([a-z_]+):\s*(.+?)(,?)$', line)
        if match:
            indent, key, value, comma = match.groups()

            # Add quotes around the key
            key = f'"{key}"'

            # Check if value needs quotes
            value = value.strip()

            # Remove trailing comma from value if present
            if value.endswith(','):
                value = value[:-1].strip()
                comma = ','

            # Add quotes if not already quoted and not a number
            if not (value.startswith('"') and value.endswith('"')):
                # Don't quote if it looks like a number
                if not value.isdigit():
                    value = f'"{value}"'

            fixed_line = f'{indent}{key}: {value}{comma}'
            fixed_lines.append(fixed_line)
        else:
            # Keep line as-is if pattern doesn't match
            fixed_lines.append(line)

    fixed_content = '\n'.join(fixed_lines)

    # Step 3: Validate the JSON
    print("\nValidating JSON...")
    try:
        parsed = json.loads(fixed_content)
        print("✓ JSON is valid!")
        print(f"  Project ID: {parsed.get('project_id', 'N/A')}")
        print(f"  Type: {parsed.get('type', 'N/A')}")
        print(f"  Client Email: {parsed.get('client_email', 'N/A')}")
    except json.JSONDecodeError as e:
        print(f"✗ JSON validation failed: {e}")
        print(f"\nFixed content preview:")
        print(fixed_content[:500])
        return False

    # Step 4: Write the fixed JSON (pretty-printed)
    print(f"\nWriting fixed JSON to: {output_file}")
    with open(output_file, 'w') as f:
        json.dump(parsed, f, indent=2)

    print(f"✓ Fixed file written successfully!")
    print(f"  New file size: {len(json.dumps(parsed, indent=2))} bytes")

    return True

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 convert-gcp-credentials-to-json.py INPUT_FILE OUTPUT_FILE")
        print("Example: python3 convert-gcp-credentials-to-json.py gcp-sa-key.json gcp-sa-key-fixed.json")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    success = fix_gcp_credentials(input_file, output_file)
    sys.exit(0 if success else 1)
