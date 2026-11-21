#!/usr/bin/env bash
set -euo pipefail
export JARVIS_M28_PORT="${JARVIS_M28_PORT:-8128}"
exec uvicorn backend.app.main:app --host "${JARVIS_M28_HOST:-0.0.0.0}" --port "${JARVIS_M28_PORT}"
