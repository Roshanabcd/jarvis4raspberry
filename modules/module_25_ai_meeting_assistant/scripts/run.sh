#!/usr/bin/env bash
set -euo pipefail
export JARVIS_M25_PORT="${JARVIS_M25_PORT:-8125}"
exec uvicorn backend.app.main:app --host "${JARVIS_M25_HOST:-0.0.0.0}" --port "${JARVIS_M25_PORT}"
