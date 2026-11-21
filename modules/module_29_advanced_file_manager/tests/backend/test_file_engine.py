"""Unit tests for FileManagerEngine (Module 29)."""

from __future__ import annotations

import os
import tempfile
import unittest

from modules.module_29_advanced_file_manager.backend.app.config import FileManagerConfig
from modules.module_29_advanced_file_manager.backend.services.file_engine import FileManagerEngine, FileManagerError


class TestFileManagerEngine(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = FileManagerConfig(
            db_path=os.path.join(self._tmp.name, "test_m29.db"),
            root_dir=os.path.join(self._tmp.name, "managed_files"),
        )
        self.engine = FileManagerEngine(config=cfg)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_crud_trash_restore_duplicates_and_organize(self) -> None:
        self.engine.write_file("a.md", "same content here")
        self.engine.write_file("b.md", "same content here")
        self.engine.write_file("script.py", "print('jarvis')")

        dups = self.engine.find_duplicates()
        self.assertEqual(dups["groups_count"], 1)
        self.assertGreater(dups["reclaimable_bytes"], 0)

        tr = self.engine.soft_delete("b.md")
        self.assertEqual(len(self.engine.db.list_trash()), 1)
        restored = self.engine.restore_trash(tr["trash_id"])
        self.assertEqual(restored["restored_path"], "b.md")
        self.assertEqual(self.engine.read_file("b.md")["content"], "same content here")

        dry = self.engine.organize_root(dry_run=True)
        self.assertEqual(dry["count"], 3)
        live = self.engine.organize_root(dry_run=False)
        self.assertEqual(live["count"], 3)

        hits = self.engine.search_files("jarvis")
        self.assertEqual(hits["count"], 1)
        self.assertEqual(hits["results"][0]["rel_path"], "code/script.py")

    def test_path_traversal_blocked(self) -> None:
        with self.assertRaises(FileManagerError) as ctx:
            self.engine.write_file("../../escape.txt", "nope")
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.code, "PATH_TRAVERSAL_BLOCKED")

    def test_missing_file_raises_404(self) -> None:
        with self.assertRaises(FileManagerError) as ctx:
            self.engine.read_file("nonexistent.txt")
        self.assertEqual(ctx.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
