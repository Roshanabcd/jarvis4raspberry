#!/usr/bin/env bash
# ==============================================================================
# JARVIS OS — Software Update Script
# Updates project dependencies and refreshes editable package bindings.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Updating JARVIS OS in $SCRIPT_DIR..."
cd "$SCRIPT_DIR"

if [ -d ".git" ]; then
    echo "Checking for git updates..."
    git pull origin master 2>/dev/null || git pull origin main 2>/dev/null || echo "Git pull skipped (working offline or detached head)."
fi

if [ -f "venv/bin/pip" ]; then
    echo "Updating Python package bindings..."
    venv/bin/pip install -e . --no-deps -q
fi

echo "✓ Update complete."
