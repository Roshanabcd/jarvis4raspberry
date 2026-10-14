#!/bin/bash
echo "Updating JARVIS OS..."
cd /opt/jarvis-os
git pull origin main || echo "Not a git repo or no network, skipping pull."
./venv/bin/pip install -e .
echo "Restarting service (Simulated)..."
# systemctl restart jarvis-core.service
echo "Update complete."
