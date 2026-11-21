#!/usr/bin/env bash
set -euo pipefail
python3 -m compileall -q backend examples tests
python3 -m unittest discover -s tests/backend -v
python3 -m unittest discover -s tests/integration -v
python3 examples/run_notification_demo.py
