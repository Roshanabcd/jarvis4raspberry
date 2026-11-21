#!/usr/bin/env bash
set -euo pipefail
export JARVIS_M27_PORT="${JARVIS_M27_PORT:-8127}"
exec uvicorn backend.app.main:app --host "${JARVIS_M27_HOST:-0.0.0.0}" --port "${JARVIS_M27_PORT}"
