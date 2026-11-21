#!/usr/bin/env bash
set -euo pipefail
python3 -m compileall -q backend sdk sample_extension examples tests
python3 -m unittest discover -s tests/backend -p "test_*.py" -v
python3 -m unittest discover -s tests/integration -p "test_*.py" -v
python3 examples/run_extension_manager_demo.py
