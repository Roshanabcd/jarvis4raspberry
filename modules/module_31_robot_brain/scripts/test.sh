#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ -f .venv/bin/activate ]; then
  source .venv/bin/activate
fi

python3 -m compileall -q backend examples tests
python3 -m unittest discover -s tests/backend -p "test_*.py" -v
python3 -m unittest discover -s tests/integration -p "test_*.py" -v
python3 examples/run_robot_brain_demo.py
