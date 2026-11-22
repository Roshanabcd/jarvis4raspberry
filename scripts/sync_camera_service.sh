#!/usr/bin/env bash
# JARVIS OS - Camera Service Sync & Verification Script
# Synchronizes the client-aware CPU-optimized camera service between the repository and the systemd unit.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_FILE="/home/roshan/camera.py"
BACKUP_FILE="/home/roshan/camera.py.bak"
SOURCE_FILE="${REPO_DIR}/deploy/camera/camera.py"

echo "=== JARVIS OS Camera Service Synchronization ==="

if [[ ! -f "${SOURCE_FILE}" ]]; then
    echo "ERROR: Source file ${SOURCE_FILE} not found in repository." >&2
    exit 1
fi

# Ensure backup exists
if [[ -f "${TARGET_FILE}" && ! -f "${BACKUP_FILE}" ]]; then
    echo "Creating backup of current ${TARGET_FILE} to ${BACKUP_FILE}..."
    cp -p "${TARGET_FILE}" "${BACKUP_FILE}"
fi

# Compare source and target
if cmp -s "${SOURCE_FILE}" "${TARGET_FILE}"; then
    echo "✔ Target ${TARGET_FILE} is already synchronized with repository source."
else
    echo "Updating ${TARGET_FILE} from repository..."
    cp -p "${TARGET_FILE}" "${BACKUP_FILE}"
    cp -p "${SOURCE_FILE}" "${TARGET_FILE}"
    echo "✔ Updated ${TARGET_FILE}."
    
    echo "Restarting jarvis-camera.service..."
    systemctl --user restart jarvis-camera.service
    sleep 2
fi

# Health check
echo "Verifying camera service health..."
if systemctl --user is-active --quiet jarvis-camera.service; then
    echo "✔ jarvis-camera.service is ACTIVE."
else
    echo "ERROR: jarvis-camera.service is NOT active." >&2
    exit 1
fi

# Query camera health endpoint
HEALTH_URL="http://127.0.0.1:8082/api/health"
if curl -s -m 3 "${HEALTH_URL}" > /dev/null; then
    echo "✔ Camera HTTP API is responding at ${HEALTH_URL}."
else
    echo "WARNING: Camera API at ${HEALTH_URL} did not respond within 3s."
fi

# Check CPU load
PID=$(pgrep -f "camera.py" | head -n 1 || true)
if [[ -n "${PID}" ]]; then
    CPU_PCT=$(ps -p "${PID}" -o %cpu= | tr -d ' ' || echo "N/A")
    echo "✔ Camera Process PID ${PID} CPU utilization: ${CPU_PCT}%"
fi

echo "=== Camera service synchronization complete. ==="
