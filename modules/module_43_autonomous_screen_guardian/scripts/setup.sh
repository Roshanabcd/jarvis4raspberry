#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[Module 43] Setting up JARVIS Screen Guardian in $ROOT_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 is required." >&2
  exit 1
fi

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

if [ ! -f ".env" ] && [ -f ".env.example" ]; then
  cp .env.example .env
  echo "[Module 43] Created .env from .env.example"
fi

if ! command -v tesseract >/dev/null 2>&1; then
  echo "[Module 43] WARNING: tesseract binary not found. Install with: sudo apt install -y tesseract-ocr"
fi

echo "[Module 43] Setup complete."
