#!/usr/bin/env bash
set -euo pipefail
export JARVIS_M42_PORT="${JARVIS_M42_PORT:-8142}"
uvicorn backend.app.main:app --host "${JARVIS_M42_HOST:-0.0.0.0}" --port "${JARVIS_M42_PORT}"
