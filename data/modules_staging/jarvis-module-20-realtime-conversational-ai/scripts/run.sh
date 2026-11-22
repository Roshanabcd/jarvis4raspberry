#!/usr/bin/env bash
set -euo pipefail
exec uvicorn backend.app.main:app --host "${JARVIS_M20_HOST:-0.0.0.0}" --port "${JARVIS_M20_PORT:-8120}"
