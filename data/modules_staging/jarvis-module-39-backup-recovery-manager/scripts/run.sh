#!/usr/bin/env bash
set -euo pipefail
PORT="${JARVIS_M39_PORT:-8139}"
HOST="${JARVIS_M39_HOST:-0.0.0.0}"
exec python3 -m uvicorn backend.app.main:app --host "$HOST" --port "$PORT"
