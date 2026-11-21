#!/usr/bin/env bash
set -euo pipefail
PORT="${JARVIS_M40_PORT:-8140}"
HOST="${JARVIS_M40_HOST:-0.0.0.0}"
exec python3 -m uvicorn backend.app.main:app --host "$HOST" --port "$PORT"
