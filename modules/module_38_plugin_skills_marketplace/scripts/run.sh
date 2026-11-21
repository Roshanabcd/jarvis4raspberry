#!/usr/bin/env bash
set -euo pipefail
PORT="${JARVIS_M38_PORT:-8138}"
HOST="${JARVIS_M38_HOST:-0.0.0.0}"
exec python3 -m uvicorn backend.app.main:app --host "$HOST" --port "$PORT"
