#!/bin/bash
#
# Master Backup Script
# Runs database backup, file volumes backup, and syncs to remote server
#

set -e  # Exit on error

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Timestamp for logging
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

echo ""
echo -e "${CYAN}======================================================${NC}"
echo -e "${CYAN}  LOGAI PRODUCTION BACKUP${NC}"
echo -e "${CYAN}  $TIMESTAMP${NC}"
echo -e "${CYAN}======================================================${NC}"
echo ""

cd "$PROJECT_DIR"

# Track overall status
OVERALL_STATUS=0

# Step 1: Database Backup
echo -e "${YELLOW}[1/3] Database Backup${NC}"
echo "----------------------------------------"
if "$SCRIPT_DIR/backup-db.sh"; then
    echo -e "${GREEN}Database backup: SUCCESS${NC}"
else
    echo -e "${RED}Database backup: FAILED${NC}"
    OVERALL_STATUS=1
fi
echo ""

# Step 2: File Volumes Backup
echo -e "${YELLOW}[2/3] File Volumes Backup${NC}"
echo "----------------------------------------"
if "$SCRIPT_DIR/backup-files.sh"; then
    echo -e "${GREEN}File volumes backup: SUCCESS${NC}"
else
    echo -e "${RED}File volumes backup: FAILED${NC}"
    OVERALL_STATUS=1
fi
echo ""

# Step 3: Sync to Remote Server
echo -e "${YELLOW}[3/3] Remote Sync${NC}"
echo "----------------------------------------"
# Only sync if BACKUP_HOST is configured (not the default placeholder)
if [ "${BACKUP_HOST:-your-backup-server}" != "your-backup-server.tail12345.ts.net" ] && [ -n "$BACKUP_HOST" ]; then
    if "$SCRIPT_DIR/backup-sync.sh"; then
        echo -e "${GREEN}Remote sync: SUCCESS${NC}"
    else
        echo -e "${RED}Remote sync: FAILED${NC}"
        OVERALL_STATUS=1
    fi
else
    echo -e "${YELLOW}Skipping remote sync (BACKUP_HOST not configured)${NC}"
    echo "Set BACKUP_HOST environment variable to enable remote sync"
fi
echo ""

# Summary
echo "========================================================"
if [ $OVERALL_STATUS -eq 0 ]; then
    echo -e "${GREEN}BACKUP COMPLETED SUCCESSFULLY${NC}"
else
    echo -e "${RED}BACKUP COMPLETED WITH ERRORS${NC}"
fi
echo "========================================================"
echo ""

# List recent backups
echo "Recent backups:"
echo "  Database:"
ls -lh ./backups/customs_db_*.sql 2>/dev/null | tail -3 | awk '{print "    " $9 " (" $5 ")"}'
echo "  Files:"
ls -lh ./backups/files/*.tar.gz 2>/dev/null | tail -3 | awk '{print "    " $9 " (" $5 ")"}'

exit $OVERALL_STATUS
