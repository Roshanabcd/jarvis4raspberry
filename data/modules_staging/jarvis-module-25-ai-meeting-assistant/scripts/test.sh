#!/usr/bin/env bash
set -euo pipefail
python3 -m unittest discover -s tests/backend -v
python3 -m unittest discover -s tests/integration -v
