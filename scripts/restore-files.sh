#!/bin/bash
#
# File Volumes Restore Script
# Restores uploaded-files, exports, or screenshots from backup archives
#
# Usage: ./restore-files.sh <volume_type> <backup_file.tar.gz>
# Volume types: uploads, exports, screenshots, all
#

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Volume type mapping
declare -A VOLUME_MAP
VOLUME_MAP["uploads"]="uploaded-files"
VOLUME_MAP["exports"]="exports"
VOLUME_MAP["screenshots"]="screenshots"

show_usage() {
    echo "Usage: $0 <volume_type> <backup_file.tar.gz>"
    echo ""
    echo "Volume types:"
    echo "  uploads     - Restore uploaded client files"
    echo "  exports     - Restore generated exports"
    echo "  screenshots - Restore OCR screenshots"
    echo "  all         - Restore all volumes (requires 3 files in order)"
    echo ""
    echo "Examples:"
    echo "  $0 uploads ./backups/files/uploads_2025-12-13_02-00-00.tar.gz"
    echo "  $0 all uploads.tar.gz exports.tar.gz screenshots.tar.gz"
    echo ""
    echo "Available backups:"
    ls -lh ./backups/files/*.tar.gz 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
}

# Check arguments
if [ $# -lt 2 ]; then
    show_usage
    exit 1
fi

VOLUME_TYPE="$1"
shift

# Get the Docker Compose project name
PROJECT_NAME=$(docker compose ps --format json 2>/dev/null | head -1 | grep -o '"Project":"[^"]*"' | cut -d'"' -f4)
if [ -z "$PROJECT_NAME" ]; then
    PROJECT_NAME=$(docker volume ls --format '{{.Name}}' | grep 'uploaded-files' | sed 's/_uploaded-files//' | head -1)
fi

if [ -z "$PROJECT_NAME" ]; then
    echo -e "${RED}Error: Could not determine Docker Compose project name${NC}"
    exit 1
fi

# Function to restore a single volume
restore_volume() {
    local VOLUME_SUFFIX=$1
    local BACKUP_FILE=$2
    local FULL_VOLUME_NAME="${PROJECT_NAME}_${VOLUME_SUFFIX}"

    echo "Restoring $FULL_VOLUME_NAME from $BACKUP_FILE..."

    # Validate backup file exists
    if [ ! -f "$BACKUP_FILE" ]; then
        echo -e "${RED}Error: Backup file not found: $BACKUP_FILE${NC}"
        return 1
    fi

    # Use a temporary container to restore the volume
    docker run --rm \
        -v "${FULL_VOLUME_NAME}:/data" \
        -v "$(cd "$(dirname "$BACKUP_FILE")" && pwd):/backup:ro" \
        alpine:3.19 \
        sh -c "rm -rf /data/* && tar xzf /backup/$(basename "$BACKUP_FILE") -C /data"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}  [OK] Restored $VOLUME_SUFFIX${NC}"
        return 0
    else
        echo -e "${RED}  [FAIL] Failed to restore $VOLUME_SUFFIX${NC}"
        return 1
    fi
}

echo "================================================"
echo "  File Volumes Restore"
echo "================================================"
echo "Project: $PROJECT_NAME"
echo ""

# Warning
echo -e "${YELLOW}WARNING: This will OVERWRITE existing files in the selected volume(s)!${NC}"
echo ""
read -p "Are you sure you want to continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

echo ""

# Handle restore based on volume type
case "$VOLUME_TYPE" in
    uploads|exports|screenshots)
        BACKUP_FILE="$1"
        VOLUME_SUFFIX="${VOLUME_MAP[$VOLUME_TYPE]}"
        if restore_volume "$VOLUME_SUFFIX" "$BACKUP_FILE"; then
            echo ""
            echo -e "${GREEN}Restore complete!${NC}"
            exit 0
        else
            exit 1
        fi
        ;;
    all)
        if [ $# -ne 3 ]; then
            echo -e "${RED}Error: 'all' requires 3 backup files: uploads.tar.gz exports.tar.gz screenshots.tar.gz${NC}"
            show_usage
            exit 1
        fi

        FAILED=0
        restore_volume "uploaded-files" "$1" || FAILED=1
        restore_volume "exports" "$2" || FAILED=1
        restore_volume "screenshots" "$3" || FAILED=1

        echo ""
        if [ $FAILED -eq 0 ]; then
            echo -e "${GREEN}All volumes restored successfully!${NC}"
            exit 0
        else
            echo -e "${RED}Some restores failed!${NC}"
            exit 1
        fi
        ;;
    *)
        echo -e "${RED}Error: Unknown volume type: $VOLUME_TYPE${NC}"
        show_usage
        exit 1
        ;;
esac
