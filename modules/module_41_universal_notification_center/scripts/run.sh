#!/usr/bin/env bash
set -euo pipefail
PORT="${JARVIS_M41_PORT:-8141}"
HOST="${JARVIS_M41_HOST:-0.0.0.0}"
exec python3 -m uvicorn backend.app.main:app --host "$HOST" --port "$PORT"
