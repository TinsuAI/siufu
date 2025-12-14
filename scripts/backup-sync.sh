#!/bin/bash
#
# Backup Sync Script
# Syncs local backups to remote Tailscale server via rsync
#

set -e  # Exit on error

# ============================================================
# CONFIGURATION - Update these values for your environment
# ============================================================
BACKUP_HOST="${BACKUP_HOST:-your-backup-server.tail12345.ts.net}"
BACKUP_USER="${BACKUP_USER:-$(whoami)}"
BACKUP_PATH="${BACKUP_PATH:-~/logai-backups/}"
# ============================================================

BACKUP_DIR="./backups"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "================================================"
echo "  Backup Sync to Remote Server"
echo "================================================"
echo "Remote: ${BACKUP_USER}@${BACKUP_HOST}:${BACKUP_PATH}"
echo ""

# Check if backup directory exists
if [ ! -d "$BACKUP_DIR" ]; then
    echo -e "${RED}Error: Backup directory does not exist: $BACKUP_DIR${NC}"
    exit 1
fi

# Check if rsync is installed
if ! command -v rsync &> /dev/null; then
    echo -e "${RED}Error: rsync is not installed${NC}"
    exit 1
fi

# Check if we can reach the remote host
echo "Testing connection to $BACKUP_HOST..."
if ! ssh -o ConnectTimeout=10 -o BatchMode=yes "${BACKUP_USER}@${BACKUP_HOST}" "echo 'Connection successful'" 2>/dev/null; then
    echo -e "${RED}Error: Cannot connect to ${BACKUP_HOST}${NC}"
    echo "Please ensure:"
    echo "  1. The Tailscale server is online"
    echo "  2. SSH keys are configured"
    echo "  3. The hostname is correct"
    exit 1
fi

# Create remote backup directory if it doesn't exist
echo "Ensuring remote directory exists..."
ssh "${BACKUP_USER}@${BACKUP_HOST}" "mkdir -p ${BACKUP_PATH}"

# Sync backups
echo ""
echo "Syncing backups..."
rsync -avz --progress \
    --exclude='*.tmp' \
    "$BACKUP_DIR/" \
    "${BACKUP_USER}@${BACKUP_HOST}:${BACKUP_PATH}"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}Sync completed successfully!${NC}"

    # Show remote backup size
    REMOTE_SIZE=$(ssh "${BACKUP_USER}@${BACKUP_HOST}" "du -sh ${BACKUP_PATH} 2>/dev/null | cut -f1")
    echo "Remote backup size: $REMOTE_SIZE"

    exit 0
else
    echo ""
    echo -e "${RED}Sync failed!${NC}"
    exit 1
fi
