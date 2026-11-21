"""Tests 16 & 17: FastAPI REST/WebSocket Integration, Host Mount, and Startup/Shutdown Lifecycle."""

from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from modules.module_42_unified_extension_manager.backend.app.config import ExtensionManagerConfig
from modules.module_42_unified_extension_manager.backend.app.main import create_app, mount_module
from modules.module_42_unified_extension_manager.backend.services.extension_manager import ExtensionManager


class TestApiAndHostIntegration(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.archives_dir = self.root / "archives"
        self.archives_dir.mkdir()
        with zipfile.ZipFile(self.archives_dir / "mod_sample.zip", "w") as zf:
            zf.writestr(
                "sample/manifest.json",
                json.dumps(
                    {
                        "module_id": "jarvis-synthetic-int",
                        "name": "Synthetic Integration Module",
                        "version": "1.0.0",
                        "category": "testing",
                        "compatible_api_version": "1.0.0",
                        "entrypoints": {"api_prefix": "/api/v1/synth", "default_port": 8299},
                        "required_permissions": ["synth.read"],
                    }
                ),
            )
            zf.writestr("sample/README.md", "# Synth")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_16_and_17_startup_shutdown_scan_plan_approvals_ws_and_mount(self) -> None:
        db_path = str(self.root / "host.db")
        host_app = FastAPI(title="JARVIS Core Host")
        mgr = mount_module(
            host_app,
            manager=ExtensionManager(config=ExtensionManagerConfig(db_path=db_path)),
            include_root_ui=False,
        )

        # Using context manager verifies FastAPI startup & shutdown lifecycle hooks cleanly
        with TestClient(host_app) as client:
            self.assertIs(host_app.state.extension_manager, mgr)

            h = client.get("/api/v1/extensions/health")
            self.assertEqual(h.status_code, 200)
            self.assertFalse(h.json()["simulated"])
            self.assertEqual(h.json()["sdk_version"], "1.0.0")

            m = client.get("/api/v1/extensions/manifest")
            self.assertEqual(m.status_code, 200)
            self.assertEqual(m.json()["entrypoints"]["default_port"], 8142)

            hud = client.get("/extensions")
            self.assertEqual(hud.status_code, 200)
            self.assertIn("UNIFIED EXTENSION MANAGER", hud.text)

            scan = client.post(
                "/api/v1/extensions/scan",
                json={"folder_path": str(self.archives_dir), "register_discovered": True, "target_arch": "arm64"},
            )
            self.assertEqual(scan.status_code, 200)
            self.assertEqual(scan.json()["valid_count"], 1)

            plan = client.post("/api/v1/extensions/plan", json={"module_ids": ["jarvis-synthetic-int"]})
            self.assertEqual(plan.status_code, 200)
            self.assertTrue(plan.json()["dry_run"])
            self.assertTrue(plan.json()["ready_for_approval"])

            apr = client.post(
                "/api/v1/extensions/approvals",
                json={"module_id": "jarvis-synthetic-int", "action": "install", "summary": "Approve install"},
            )
            self.assertEqual(apr.status_code, 201)
            dec = client.post(
                f"/api/v1/extensions/approvals/{apr.json()['request_id']}/decide",
                json={"decision": "approve", "reviewer": "roshan"},
            )
            self.assertEqual(dec.status_code, 200)
            self.assertEqual(dec.json()["status"], "approved")

            with client.websocket_connect("/api/v1/extensions/ws/events") as ws:
                msg = ws.receive_json()
                self.assertEqual(msg["event_type"], "ws.connected")

    def test_auth_token_guard_on_standalone_app(self) -> None:
        cfg = ExtensionManagerConfig(db_path=str(self.root / "auth.db"), api_token="m42-secret")
        with TestClient(create_app(config=cfg)) as client:
            unauth = client.post("/api/v1/extensions/scan", json={"folder_path": str(self.archives_dir)})
            self.assertEqual(unauth.status_code, 401)
            ok = client.post(
                "/api/v1/extensions/scan",
                headers={"X-JARVIS-Token": "m42-secret"},
                json={"folder_path": str(self.archives_dir)},
            )
            self.assertEqual(ok.status_code, 200)


if __name__ == "__main__":
    unittest.main()
