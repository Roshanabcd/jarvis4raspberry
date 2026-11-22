#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ -f ".venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

export PYTHONPATH="$ROOT_DIR${PYTHONPATH:+:$PYTHONPATH}"

echo "[Module 43] Syntax check..."
python3 -m compileall -q backend examples tests

echo "[Module 43] Running backend & integration tests..."
python3 -m unittest discover -s tests/backend -p "test_*.py" -v
python3 -m unittest discover -s tests/integration -p "test_*.py" -v

echo "[Module 43] Running end-to-end demo script..."
python3 examples/run_screen_guardian_demo.py

echo "[Module 43] All Python verification suites passed."
