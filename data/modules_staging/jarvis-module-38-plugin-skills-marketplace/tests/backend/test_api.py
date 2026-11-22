"""FastAPI REST & WebSocket API tests for JARVIS Module 38 — Plugin & Skills Marketplace."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.config import MarketplaceConfig
from backend.app.main import create_app


class TestMarketplaceAPI(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = MarketplaceConfig(db_path=str(Path(self._tmp.name) / "api_marketplace.db"))
        self.app = create_app(cfg)
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_health_manifest_and_hud(self) -> None:
        r = self.client.get("/api/v1/marketplace/health")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["module_id"], "jarvis-module-38-plugin-skills-marketplace")
        self.assertFalse(body["simulated"])

        m = self.client.get("/api/v1/marketplace/manifest")
        self.assertEqual(m.status_code, 200)
        self.assertEqual(m.json()["default_port"], 8138)

        hud = self.client.get("/marketplace")
        self.assertEqual(hud.status_code, 200)
        self.assertIn("Plugin &amp; Skills Marketplace", hud.text)

    def test_publish_install_toggle_and_uninstall_endpoints(self) -> None:
        pub = self.client.post(
            "/api/v1/marketplace/packages",
            json={
                "slug": "weather-digest",
                "name": "Weather Digest",
                "version": "1.0.0",
                "kind": "skill",
                "permissions": ["network_read", "notifications"],
            },
        )
        self.assertEqual(pub.status_code, 201)
        pkg = pub.json()

        bad = self.client.post(
            f"/api/v1/marketplace/packages/{pkg['package_id']}/install",
            json={"expected_sha256": "deadbeef", "enabled": True},
        )
        self.assertEqual(bad.status_code, 422)
        self.assertEqual(bad.json()["error"]["code"], "CHECKSUM_MISMATCH")

        ok = self.client.post(
            f"/api/v1/marketplace/packages/{pkg['package_id']}/install",
            json={"expected_sha256": pkg["sha256"], "enabled": True},
        )
        self.assertEqual(ok.status_code, 200)
        self.assertTrue(ok.json()["installed"])

        tog = self.client.post(f"/api/v1/marketplace/packages/{pkg['package_id']}/toggle", json={"enabled": False})
        self.assertEqual(tog.status_code, 200)
        self.assertFalse(tog.json()["enabled"])

        rem = self.client.delete(f"/api/v1/marketplace/packages/{pkg['package_id']}/install")
        self.assertEqual(rem.status_code, 200)
        self.assertFalse(rem.json()["installed"])

    def test_websocket_registry_channel(self) -> None:
        with self.client.websocket_connect("/api/v1/marketplace/ws/registry") as ws:
            msg = ws.receive_json()
            self.assertEqual(msg["event_type"], "ws.connected")
            self.assertEqual(msg["status"]["adapter"], "local_plugin_registry_engine")
            self.assertFalse(msg["status"]["simulated"])


if __name__ == "__main__":
    unittest.main()
