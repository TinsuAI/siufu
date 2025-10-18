#!/bin/bash
#
# PostgreSQL Database Backup Script
# Backs up the customs_db database to timestamped SQL file
#

set -e  # Exit on error

# Configuration
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_DIR="./backups"
BACKUP_FILE="$BACKUP_DIR/customs_db_$TIMESTAMP.sql"
RETENTION_DAYS=30

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "================================================"
echo "  PostgreSQL Database Backup"
echo "================================================"
echo "Timestamp: $TIMESTAMP"
echo "Backup file: $BACKUP_FILE"
echo ""

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Perform backup
echo "Starting backup..."
docker-compose exec -T postgres pg_dump -U postgres -d customs_db > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    # Get file size
    FILE_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo -e "${GREEN}✓ Backup successful!${NC}"
    echo "File: $BACKUP_FILE"
    echo "Size: $FILE_SIZE"
    echo ""

    # Cleanup old backups
    echo "Cleaning up backups older than $RETENTION_DAYS days..."
    find "$BACKUP_DIR" -name "customs_db_*.sql" -mtime +$RETENTION_DAYS -delete
    REMAINING=$(find "$BACKUP_DIR" -name "customs_db_*.sql" | wc -l)
    echo "Backups remaining: $REMAINING"

    exit 0
else
    echo -e "${RED}✗ Backup failed!${NC}"
    rm -f "$BACKUP_FILE"  # Remove incomplete backup file
    exit 1
fi
