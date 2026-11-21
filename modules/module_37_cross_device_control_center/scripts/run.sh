#!/usr/bin/env bash
set -euo pipefail
PORT="${JARVIS_M37_PORT:-8137}"
HOST="${JARVIS_M37_HOST:-0.0.0.0}"
exec python3 -m uvicorn backend.app.main:app --host "$HOST" --port "$PORT"
