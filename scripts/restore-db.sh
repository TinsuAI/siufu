#!/bin/bash
#
# PostgreSQL Database Restore Script
# Restores the customs_db database from a SQL backup file
#
# Usage: ./restore-db.sh <backup_file.sql>
#

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check arguments
if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup_file.sql>"
    echo ""
    echo "Available backups:"
    ls -lh ./backups/customs_db_*.sql 2>/dev/null | awk '{print "  " $9 " (" $5 ", " $6 " " $7 ")"}'
    exit 1
fi

BACKUP_FILE="$1"

# Validate backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}Error: Backup file not found: $BACKUP_FILE${NC}"
    exit 1
fi

echo "================================================"
echo "  PostgreSQL Database Restore"
echo "================================================"
echo "Backup file: $BACKUP_FILE"
echo "File size: $(du -h "$BACKUP_FILE" | cut -f1)"
echo ""

# Confirm restore
echo -e "${YELLOW}WARNING: This will DROP the existing database and restore from backup!${NC}"
echo -e "${YELLOW}All current data will be LOST!${NC}"
echo ""
read -p "Are you sure you want to continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

echo ""
echo "Stopping backend services to prevent database connections..."

# Stop services that use the database (optional - makes restore cleaner)
docker compose stop backend celery-worker 2>/dev/null || true

echo ""
echo "Restoring database..."

# Drop existing connections and database, then restore
docker compose exec -T postgres psql -U postgres -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'customs_db' AND pid <> pg_backend_pid();
" 2>/dev/null || true

docker compose exec -T postgres psql -U postgres -c "DROP DATABASE IF EXISTS customs_db;"
docker compose exec -T postgres psql -U postgres -c "CREATE DATABASE customs_db;"

# Restore from backup
docker compose exec -T postgres psql -U postgres -d customs_db < "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}Database restored successfully!${NC}"
    echo ""

    # Show table count as verification
    TABLE_COUNT=$(docker compose exec -T postgres psql -U postgres -d customs_db -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';")
    echo "Tables restored: $TABLE_COUNT"

    # Restart services
    echo ""
    echo "Restarting services..."
    docker compose up -d backend celery-worker

    echo ""
    echo -e "${GREEN}Restore complete!${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}Database restore failed!${NC}"

    # Try to restart services anyway
    docker compose up -d backend celery-worker 2>/dev/null || true

    exit 1
fi
