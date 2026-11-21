#!/usr/bin/env bash
set -euo pipefail
exec uvicorn backend.app.main:app --host "${JARVIS_M19_HOST:-0.0.0.0}" --port "${JARVIS_M19_PORT:-8119}"
