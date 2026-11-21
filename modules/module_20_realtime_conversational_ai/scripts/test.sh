#!/usr/bin/env bash
set -euo pipefail
python3 -m compileall -q backend examples tests
if command -v pytest >/dev/null 2>&1; then
  pytest -v tests/backend tests/integration
else
  python3 -m unittest discover -s tests/backend -v
  python3 -m unittest discover -s tests/integration -v
fi
