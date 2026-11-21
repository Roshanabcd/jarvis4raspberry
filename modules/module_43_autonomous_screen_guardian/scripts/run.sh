#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ -f ".venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

export PYTHONPATH="$ROOT_DIR${PYTHONPATH:+:$PYTHONPATH}"
HOST="${SCREEN_GUARDIAN_HOST:-127.0.0.1}"
PORT="${SCREEN_GUARDIAN_PORT:-8143}"

echo "[Module 43] Starting JARVIS Screen Guardian on http://${HOST}:${PORT}/screen-guardian"
exec python3 -m uvicorn backend.app.main:app --host "$HOST" --port "$PORT"
