"""Runnable CLI demo for JARVIS Module 39 — Backup & Recovery Manager."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.config import BackupConfig
from backend.services.backup_engine import BackupEngine


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        ws = base / "workspace"
        (ws / "configs").mkdir(parents=True, exist_ok=True)
        (ws / "configs" / "jarvis.json").write_text('{"mode":"production"}', encoding="utf-8")
        (ws / "notes.txt").write_text("JARVIS OS Pi 5 backup test", encoding="utf-8")

        cfg = BackupConfig(
            db_path=str(base / "backups.db"),
            sandbox_root=str(ws),
            archive_dir=str(base / "archives"),
        )
        engine = BackupEngine(config=cfg)
        snap = engine.create_snapshot("Nightly Pi5 Backup", source_rel_path=".", notes="CLI demo")
        ver = engine.verify_snapshot(snap["snapshot_id"])
        rest = engine.restore_snapshot(snap["snapshot_id"], target_rel_path="restored_copy")
        print(
            json.dumps(
                {
                    "simulated": engine.is_simulated,
                    "snapshot_id": snap["snapshot_id"],
                    "file_count": snap["file_count"],
                    "verified": ver["valid"],
                    "restored_files": rest["restored_files"],
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
