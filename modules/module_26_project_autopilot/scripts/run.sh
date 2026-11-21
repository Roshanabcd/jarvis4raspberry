#!/usr/bin/env bash
set -euo pipefail
export JARVIS_M26_PORT="${JARVIS_M26_PORT:-8126}"
exec uvicorn backend.app.main:app --host "${JARVIS_M26_HOST:-0.0.0.0}" --port "${JARVIS_M26_PORT}"
