#!/usr/bin/env bash
set -euo pipefail
HOST="${JARVIS_M18_HOST:-0.0.0.0}"
PORT="${JARVIS_M18_PORT:-8118}"
exec uvicorn backend.app.main:app --host "$HOST" --port "$PORT"
