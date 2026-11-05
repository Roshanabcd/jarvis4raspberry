#!/usr/bin/env bash
# ==============================================================================
# JARVIS OS — Safe Backup Script
# Creates a compressed, timestamped archive of:
# - SQLite long-term memory (jarvis_memory.db)
# - Configuration files (config/)
# - Environment settings (.env)
# Does NOT delete or alter any existing data.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${SCRIPT_DIR}/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/jarvis_backup_${TIMESTAMP}.tar.gz"

mkdir -p "$BACKUP_DIR"

echo "Creating JARVIS OS backup to $BACKUP_FILE..."

ITEMS_TO_BACKUP=()

if [ -f "${SCRIPT_DIR}/jarvis_memory.db" ]; then
    # Safely checkpoint SQLite WAL if sqlite3 is installed
    if command -v sqlite3 >/dev/null 2>&1; then
        sqlite3 "${SCRIPT_DIR}/jarvis_memory.db" "PRAGMA wal_checkpoint(TRUNCATE);" 2>/dev/null || true
    fi
    ITEMS_TO_BACKUP+=("jarvis_memory.db")
fi

if [ -d "${SCRIPT_DIR}/config" ]; then
    ITEMS_TO_BACKUP+=("config")
fi

if [ -f "${SCRIPT_DIR}/.env" ]; then
    ITEMS_TO_BACKUP+=(".env")
fi

if [ ${#ITEMS_TO_BACKUP[@]} -eq 0 ]; then
    echo "No items found to backup."
    exit 0
fi

cd "$SCRIPT_DIR"
tar -czf "$BACKUP_FILE" "${ITEMS_TO_BACKUP[@]}"
chmod 600 "$BACKUP_FILE"

echo "✓ Backup created successfully: $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"
