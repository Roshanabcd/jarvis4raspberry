#!/usr/bin/env bash
set -euo pipefail
PORT="${JARVIS_M36_PORT:-8136}"
HOST="${JARVIS_M36_HOST:-0.0.0.0}"
exec python3 -m uvicorn backend.app.main:app --host "$HOST" --port "$PORT"
