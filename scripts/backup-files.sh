#!/bin/bash
#
# File Volumes Backup Script
# Backs up uploaded-files, exports, and screenshots Docker volumes
#

set -e  # Exit on error

# Configuration
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_DIR="./backups/files"
RETENTION_DAYS=30

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "================================================"
echo "  File Volumes Backup"
echo "================================================"
echo "Timestamp: $TIMESTAMP"
echo ""

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Function to backup a volume
backup_volume() {
    local VOLUME_NAME=$1
    local BACKUP_NAME=$2
    local BACKUP_FILE="$BACKUP_DIR/${BACKUP_NAME}_$TIMESTAMP.tar.gz"

    echo "Backing up $VOLUME_NAME..."

    # Use a temporary container to access the volume and create a tar archive
    docker run --rm \
        -v "${VOLUME_NAME}:/data:ro" \
        -v "$(pwd)/$BACKUP_DIR:/backup" \
        alpine:3.19 \
        tar czf "/backup/${BACKUP_NAME}_$TIMESTAMP.tar.gz" -C /data .

    if [ $? -eq 0 ]; then
        FILE_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        echo -e "${GREEN}  [OK] ${BACKUP_NAME}: $FILE_SIZE${NC}"
        return 0
    else
        echo -e "${RED}  [FAIL] ${BACKUP_NAME}${NC}"
        return 1
    fi
}

# Get the Docker Compose project name (used as volume prefix)
PROJECT_NAME=$(docker compose ps --format json 2>/dev/null | head -1 | grep -o '"Project":"[^"]*"' | cut -d'"' -f4)
if [ -z "$PROJECT_NAME" ]; then
    # Fallback: try to detect from existing volumes
    PROJECT_NAME=$(docker volume ls --format '{{.Name}}' | grep 'uploaded-files' | sed 's/_uploaded-files//' | head -1)
fi

if [ -z "$PROJECT_NAME" ]; then
    echo -e "${RED}Error: Could not determine Docker Compose project name${NC}"
    echo "Make sure Docker Compose services are running or volumes exist."
    exit 1
fi

echo "Project name: $PROJECT_NAME"
echo ""

# Track success/failure
FAILED=0

# Backup each volume
backup_volume "${PROJECT_NAME}_uploaded-files" "uploads" || FAILED=1
backup_volume "${PROJECT_NAME}_exports" "exports" || FAILED=1
backup_volume "${PROJECT_NAME}_screenshots" "screenshots" || FAILED=1

echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All backups completed successfully!${NC}"
    echo ""

    # Cleanup old backups
    echo "Cleaning up backups older than $RETENTION_DAYS days..."
    find "$BACKUP_DIR" -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete
    REMAINING=$(find "$BACKUP_DIR" -name "*.tar.gz" | wc -l)
    echo "File backups remaining: $REMAINING"

    exit 0
else
    echo -e "${RED}Some backups failed!${NC}"
    exit 1
fi
