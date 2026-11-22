"""FastAPI REST & WebSocket API tests for JARVIS Module 39 — Backup & Recovery Manager."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.config import BackupConfig
from backend.app.main import create_app


class TestBackupAPI(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        ws = base / "workspace"
        ws.mkdir(parents=True, exist_ok=True)
        (ws / "config.ini").write_text("[jarvis]\nport=8139\n", encoding="utf-8")
        cfg = BackupConfig(
            db_path=str(base / "api_backups.db"),
            sandbox_root=str(ws),
            archive_dir=str(base / "archives"),
        )
        self.app = create_app(cfg)
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_health_manifest_and_hud(self) -> None:
        r = self.client.get("/api/v1/backups/health")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["module_id"], "jarvis-module-39-backup-recovery-manager")
        self.assertFalse(body["simulated"])

        m = self.client.get("/api/v1/backups/manifest")
        self.assertEqual(m.status_code, 200)
        self.assertEqual(m.json()["default_port"], 8139)

        hud = self.client.get("/backups")
        self.assertEqual(hud.status_code, 200)
        self.assertIn("Backup &amp; Recovery Manager", hud.text)

    def test_snapshot_verify_restore_and_traversal_endpoints(self) -> None:
        created = self.client.post(
            "/api/v1/backups/snapshots",
            json={"name": "Config Backup", "source_rel_path": ".", "notes": "api test"},
        )
        self.assertEqual(created.status_code, 201)
        snap_id = created.json()["snapshot_id"]

        ver = self.client.post(f"/api/v1/backups/snapshots/{snap_id}/verify")
        self.assertEqual(ver.status_code, 200)
        self.assertTrue(ver.json()["valid"])

        rest = self.client.post(
            f"/api/v1/backups/snapshots/{snap_id}/restore",
            json={"target_rel_path": "restored_api"},
        )
        self.assertEqual(rest.status_code, 201)
        self.assertEqual(rest.json()["restored_files"], 1)

        bad = self.client.post(
            "/api/v1/backups/snapshots",
            json={"name": "Bad Escape", "source_rel_path": "../../etc"},
        )
        self.assertEqual(bad.status_code, 403)
        self.assertEqual(bad.json()["error"]["code"], "PATH_OUTSIDE_SANDBOX")

    def test_websocket_snapshots_channel(self) -> None:
        with self.client.websocket_connect("/api/v1/backups/ws/snapshots") as ws:
            msg = ws.receive_json()
            self.assertEqual(msg["event_type"], "ws.connected")
            self.assertEqual(msg["status"]["adapter"], "local_snapshot_backup_engine")
            self.assertFalse(msg["status"]["simulated"])


if __name__ == "__main__":
    unittest.main()
