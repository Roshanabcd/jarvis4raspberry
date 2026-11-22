"""Integration tests for mounting Module 39 inside a host JARVIS OS FastAPI app."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from modules.module_39_backup_recovery_manager.backend.app.config import BackupConfig
from modules.module_39_backup_recovery_manager.backend.app.main import mount_module
from modules.module_39_backup_recovery_manager.backend.services.backup_engine import BackupEngine


class TestModule39Integration(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        ws = base / "workspace"
        ws.mkdir(parents=True, exist_ok=True)
        (ws / "state.json").write_text('{"ok":true}', encoding="utf-8")
        cfg = BackupConfig(
            db_path=str(base / "host_backups.db"),
            sandbox_root=str(ws),
            archive_dir=str(base / "archives"),
        )
        self.engine = BackupEngine(config=cfg)
        self.host_app = FastAPI(title="JARVIS OS Host")
        mount_module(self.host_app, engine=self.engine, include_root_ui=False)
        self.client = TestClient(self.host_app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_host_app_state_and_route_mounting(self) -> None:
        self.assertIs(self.host_app.state.backups, self.engine)
        status = self.client.get("/api/v1/backups/status")
        self.assertEqual(status.status_code, 200)
        self.assertEqual(status.json()["adapter"], "local_snapshot_backup_engine")
        self.assertFalse(status.json()["simulated"])

    def test_end_to_end_snapshot_and_restore_history(self) -> None:
        snap = self.client.post(
            "/api/v1/backups/snapshots",
            json={"name": "Host Snap", "source_rel_path": "."},
        ).json()
        self.client.post(
            f"/api/v1/backups/snapshots/{snap['snapshot_id']}/restore",
            json={"target_rel_path": "restore_host"},
        )

        snaps = self.client.get("/api/v1/backups/snapshots")
        self.assertEqual(snaps.status_code, 200)
        self.assertEqual(snaps.json()["count"], 1)

        restores = self.client.get(f"/api/v1/backups/restores?snapshot_id={snap['snapshot_id']}")
        self.assertEqual(restores.status_code, 200)
        self.assertEqual(restores.json()["count"], 1)


if __name__ == "__main__":
    unittest.main()
