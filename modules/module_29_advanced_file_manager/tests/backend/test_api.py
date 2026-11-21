"""REST & WebSocket API tests for JARVIS Module 29 — Advanced File Manager."""

from __future__ import annotations

import os
import tempfile
import unittest

from fastapi.testclient import TestClient

from modules.module_29_advanced_file_manager.backend.app.config import FileManagerConfig
from modules.module_29_advanced_file_manager.backend.app.main import create_app


class TestFileManagerAPI(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = FileManagerConfig(
            db_path=os.path.join(self._tmp.name, "api_m29.db"),
            root_dir=os.path.join(self._tmp.name, "managed_files"),
        )
        self.app = create_app(config=cfg)
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_health_manifest_and_ui(self) -> None:
        r_h = self.client.get("/api/v1/file-manager/health")
        self.assertEqual(r_h.status_code, 200)
        self.assertEqual(r_h.json()["module_id"], "jarvis-module-29-advanced-file-manager")
        self.assertFalse(r_h.json()["simulated"])

        r_m = self.client.get("/api/v1/file-manager/manifest")
        self.assertEqual(r_m.status_code, 200)
        self.assertEqual(r_m.json()["version"], "1.0.0")

        r_ui = self.client.get("/file-manager")
        self.assertEqual(r_ui.status_code, 200)
        self.assertIn("Advanced File Manager", r_ui.text)

    def test_full_rest_workflow(self) -> None:
        w1 = self.client.post("/api/v1/file-manager/files", json={"rel_path": "readme.md", "content": "JARVIS file"})
        self.assertEqual(w1.status_code, 201)
        w2 = self.client.post("/api/v1/file-manager/files", json={"rel_path": "dup.md", "content": "JARVIS file"})
        self.assertEqual(w2.status_code, 201)

        bad = self.client.post("/api/v1/file-manager/files", json={"rel_path": "../bad.txt", "content": "x"})
        self.assertEqual(bad.status_code, 403)

        tag_r = self.client.post("/api/v1/file-manager/tags", json={"rel_path": "readme.md", "tags": ["Important", "Docs"]})
        self.assertEqual(tag_r.status_code, 200)
        self.assertEqual(tag_r.json()["tags"], ["docs", "important"])

        dups = self.client.get("/api/v1/file-manager/duplicates")
        self.assertEqual(dups.status_code, 200)
        self.assertEqual(dups.json()["groups_count"], 1)

        d_res = self.client.delete("/api/v1/file-manager/files", params={"path": "dup.md"})
        self.assertEqual(d_res.status_code, 200)
        tid = d_res.json()["trash_id"]

        res_r = self.client.post(f"/api/v1/file-manager/trash/{tid}/restore")
        self.assertEqual(res_r.status_code, 200)

        org = self.client.post("/api/v1/file-manager/organize", json={"dry_run": False})
        self.assertEqual(org.status_code, 200)
        self.assertEqual(org.json()["count"], 2)

        srch = self.client.get("/api/v1/file-manager/search", params={"q": "JARVIS"})
        self.assertEqual(srch.status_code, 200)
        self.assertEqual(srch.json()["count"], 2)

    def test_websocket_connects(self) -> None:
        with self.client.websocket_connect("/api/v1/file-manager/ws/events") as ws:
            msg = ws.receive_json()
            self.assertEqual(msg["event_type"], "ws.connected")
            self.assertIn("status", msg)


if __name__ == "__main__":
    unittest.main()
