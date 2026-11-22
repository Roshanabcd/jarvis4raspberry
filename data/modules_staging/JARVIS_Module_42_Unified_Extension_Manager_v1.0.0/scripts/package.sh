#!/usr/bin/env bash
set -euo pipefail
OUT_ZIP="${1:-JARVIS_Module_42_Unified_Extension_Manager_v1.0.0.zip}"
python3 - <<'PY' "$OUT_ZIP"
import pathlib, sys, zipfile
root = pathlib.Path('.').resolve()
out = pathlib.Path(sys.argv[1]).resolve()
skip = {'__pycache__', '.pytest_cache', '.venv', 'node_modules', 'data', '.git'}
with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
    for p in sorted(root.rglob('*')):
        if p.is_file() and p != out:
            rel = p.relative_to(root)
            if any(part in skip for part in rel.parts) or p.suffix == '.pyc':
                continue
            zf.write(p, arcname=str(pathlib.Path('JARVIS_Module_42_Unified_Extension_Manager_v1.0.0') / rel))
with zipfile.ZipFile(out, 'r') as zf:
    assert zf.testzip() is None
print(f"Packaged verified archive: {out}")
PY
