#!/bin/bash
# Wedding Organizer - Database Backup Script
#
# Usage:
#   ./scripts/backup.sh                    # Backup to ./backups/
#   ./scripts/backup.sh /path/to/backups   # Backup to custom directory
#   ./scripts/backup.sh --restore latest   # Restore most recent backup
#   ./scripts/backup.sh --restore FILE     # Restore specific backup
#
# Automate with cron (daily at 2am):
#   0 2 * * * /path/to/wedding-organizer/scripts/backup.sh

set -euo pipefail

# Configuration
DB_PATH="./instance/wedding_organizer.db"
BACKUP_DIR="${1:-./backups}"
MAX_BACKUPS=30  # Keep last 30 backups
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/wedding_organizer_${TIMESTAMP}.db"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# Restore mode
if [[ "${1:-}" == "--restore" ]]; then
    RESTORE_FILE="${2:-latest}"

    if [[ "$RESTORE_FILE" == "latest" ]]; then
        RESTORE_FILE=$(ls -t ./backups/wedding_organizer_*.db 2>/dev/null | head -1)
        [[ -z "$RESTORE_FILE" ]] && error "No backups found in ./backups/"
    fi

    [[ ! -f "$RESTORE_FILE" ]] && error "Backup file not found: $RESTORE_FILE"

    info "Restoring from: $RESTORE_FILE"

    # Safety backup of current database before restore
    if [[ -f "$DB_PATH" ]]; then
        SAFETY="./backups/wedding_organizer_pre_restore_${TIMESTAMP}.db"
        mkdir -p ./backups
        cp "$DB_PATH" "$SAFETY"
        info "Current database backed up to: $SAFETY"
    fi

    cp "$RESTORE_FILE" "$DB_PATH"
    info "Database restored successfully!"
    info "Restart the container: docker-compose restart"
    exit 0
fi

# Backup mode
[[ ! -f "$DB_PATH" ]] && error "Database not found at $DB_PATH"

mkdir -p "$BACKUP_DIR"

# Use SQLite backup command if available (safer for running databases)
if command -v sqlite3 &>/dev/null; then
    sqlite3 "$DB_PATH" ".backup '$BACKUP_FILE'"
else
    cp "$DB_PATH" "$BACKUP_FILE"
fi

# Verify backup
if [[ -f "$BACKUP_FILE" ]] && [[ -s "$BACKUP_FILE" ]]; then
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    info "Backup created: $BACKUP_FILE ($SIZE)"
else
    error "Backup failed!"
fi

# Cleanup old backups
BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/wedding_organizer_*.db 2>/dev/null | wc -l)
if [[ "$BACKUP_COUNT" -gt "$MAX_BACKUPS" ]]; then
    REMOVE_COUNT=$((BACKUP_COUNT - MAX_BACKUPS))
    ls -1t "$BACKUP_DIR"/wedding_organizer_*.db | tail -n "$REMOVE_COUNT" | xargs rm -f
    info "Cleaned up $REMOVE_COUNT old backup(s), keeping last $MAX_BACKUPS"
fi

info "Backup complete!"
