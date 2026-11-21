"""Runnable CLI demonstration for JARVIS Module 29 — Advanced File Manager."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.module_29_advanced_file_manager.backend.app.config import FileManagerConfig
from modules.module_29_advanced_file_manager.backend.services.file_engine import FileManagerEngine


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        cfg = FileManagerConfig(
            db_path=os.path.join(tmp, "demo_m29.db"),
            root_dir=os.path.join(tmp, "managed_files"),
        )
        engine = FileManagerEngine(config=cfg)

        engine.write_file("notes.md", "# JARVIS Notes\nDeploy Module 29 on Raspberry Pi 5.")
        engine.write_file("notes_copy.md", "# JARVIS Notes\nDeploy Module 29 on Raspberry Pi 5.")
        engine.write_file("metrics.csv", "day,cpu\nmon,24\n")
        engine.write_file("helper.py", "print('hello jarvis')\n")

        dups = engine.find_duplicates()
        dry = engine.organize_root(dry_run=True)
        real = engine.organize_root(dry_run=False)
        hits = engine.search_files("Raspberry")

        print(f"Duplicate Groups  : {dups['groups_count']} (reclaimable={dups['reclaimable_bytes']} bytes)")
        print(f"Dry-Run Plan      : {dry['count']} move(s)")
        print(f"Organized Files   : {real['count']} moved into category folders")
        print(f"Search 'Raspberry': {hits['count']} match(es) -> {[h['rel_path'] for h in hits['results']]}")


if __name__ == "__main__":
    main()
