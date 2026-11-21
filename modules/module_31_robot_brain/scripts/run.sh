#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ -f .venv/bin/activate ]; then
  source .venv/bin/activate
fi

HOST="${JARVIS_M31_HOST:-0.0.0.0}"
PORT="${JARVIS_M31_PORT:-8131}"

exec python3 -m uvicorn backend.app.main:app --host "$HOST" --port "$PORT"
