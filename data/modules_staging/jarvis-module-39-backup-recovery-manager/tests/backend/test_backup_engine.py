"""Unit tests for Module 39 BackupEngine (real ZIP snapshots, SHA-256 tamper detection, sandbox confinement)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.app.config import BackupConfig
from backend.services.backup_engine import BackupEngine, BackupError


class TestBackupEngine(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.ws = self.base / "workspace"
        (self.ws / "sub").mkdir(parents=True, exist_ok=True)
        (self.ws / "alpha.txt").write_text("alpha-data", encoding="utf-8")
        (self.ws / "sub" / "beta.txt").write_text("beta-data", encoding="utf-8")
        cfg = BackupConfig(
            db_path=str(self.base / "backups.db"),
            sandbox_root=str(self.ws),
            archive_dir=str(self.base / "archives"),
        )
        self.engine = BackupEngine(config=cfg)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_snapshot_verify_and_restore_roundtrip(self) -> None:
        snap = self.engine.create_snapshot("Full Backup", source_rel_path=".", notes="unit test")
        self.assertEqual(snap["file_count"], 2)
        self.assertEqual(len(snap["sha256"]), 64)

        ver = self.engine.verify_snapshot(snap["snapshot_id"])
        self.assertTrue(ver["valid"])

        rest = self.engine.restore_snapshot(snap["snapshot_id"], target_rel_path="recovered")
        self.assertEqual(rest["restored_files"], 2)
        self.assertEqual((self.ws / "recovered" / "alpha.txt").read_text(encoding="utf-8"), "alpha-data")
        self.assertEqual((self.ws / "recovered" / "sub" / "beta.txt").read_text(encoding="utf-8"), "beta-data")
        self.assertFalse(self.engine.get_status()["simulated"])

    def test_tampered_archive_fails_verify_and_blocks_restore(self) -> None:
        snap = self.engine.create_snapshot("Tamper Check", source_rel_path=".")
        archive_path = self.base / "archives" / snap["archive_filename"]
        archive_path.write_bytes(archive_path.read_bytes() + b"CORRUPTED")

        ver = self.engine.verify_snapshot(snap["snapshot_id"])
        self.assertFalse(ver["valid"])
        self.assertIn("SHA-256", ver["reason"])

        with self.assertRaises(BackupError) as err:
            self.engine.restore_snapshot(snap["snapshot_id"], target_rel_path="should_not_restore")
        self.assertEqual(err.exception.code, "SNAPSHOT_CORRUPTED")
        self.assertEqual(err.exception.status_code, 409)

    def test_sandbox_traversal_blocked(self) -> None:
        with self.assertRaises(BackupError) as err1:
            self.engine.create_snapshot("Escape", source_rel_path="../outside")
        self.assertEqual(err1.exception.code, "PATH_OUTSIDE_SANDBOX")
        self.assertEqual(err1.exception.status_code, 403)

        snap = self.engine.create_snapshot("Safe", source_rel_path=".")
        with self.assertRaises(BackupError) as err2:
            self.engine.restore_snapshot(snap["snapshot_id"], target_rel_path="/tmp/escape")
        self.assertEqual(err2.exception.code, "PATH_OUTSIDE_SANDBOX")
        self.assertEqual(err2.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
