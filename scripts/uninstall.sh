#!/usr/bin/env bash
# ==============================================================================
# JARVIS OS — Safe Uninstallation Script
# Stops and disables systemd services and cleans up system hooks.
# Preserves user data and database by default.
# ==============================================================================

set -euo pipefail

SERVICE_FILE="/etc/systemd/system/jarvis-core.service"

echo "Stopping JARVIS OS service if running..."
if systemctl is-active --quiet jarvis-core 2>/dev/null; then
    sudo systemctl stop jarvis-core
    echo "✓ Service stopped."
fi

if [ -f "$SERVICE_FILE" ]; then
    sudo systemctl disable jarvis-core 2>/dev/null || true
    sudo rm -f "$SERVICE_FILE"
    sudo systemctl daemon-reload
    echo "✓ Service unit removed."
fi

echo ""
echo "JARVIS OS service uninstalled successfully."
echo "Your project code and database (jarvis_memory.db) have been preserved."
