#!/usr/bin/env bash
set -euo pipefail
export JARVIS_M29_PORT="${JARVIS_M29_PORT:-8129}"
exec uvicorn backend.app.main:app --host "${JARVIS_M29_HOST:-0.0.0.0}" --port "${JARVIS_M29_PORT}"
