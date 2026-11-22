#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_ZIP="${1:-${ROOT_DIR}/../JARVIS_Module_43_Autonomous_Screen_Guardian_v1.0.0.zip}"

python3 - "$ROOT_DIR" "$OUT_ZIP" <<'PY'
import os
import sys
import zipfile
from pathlib import Path

root = Path(sys.argv[1]).resolve()
out_zip = Path(sys.argv[2]).resolve()
out_zip.parent.mkdir(parents=True, exist_ok=True)

EXCLUDE_DIRS = {".git", ".venv", "__pycache__", "node_modules", ".pytest_cache", "dist", "build"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".db", ".db-wal", ".db-shm"}

count = 0
with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in EXCLUDE_DIRS)
        for fname in sorted(filenames):
            if fname.endswith(tuple(EXCLUDE_SUFFIXES)) or fname == ".env":
                continue
            full = Path(dirpath) / fname
            rel = full.relative_to(root)
            zf.write(full, arcname=str(Path(root.name) / rel))
            count += 1

with zipfile.ZipFile(out_zip, "r") as zf:
    bad = zf.testzip()
    if bad is not None:
        raise SystemExit(f"Corrupt ZIP member: {bad}")

print(f"Packaged {count} files -> {out_zip} ({out_zip.stat().st_size} bytes)")
PY
