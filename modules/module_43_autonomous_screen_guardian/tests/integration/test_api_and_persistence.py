"""Tests 19-20: REST/HUD/WS/Voice/host mount_module integration and SQLite WAL restart persistence."""

from __future__ import annotations

import base64
import io
import tempfile
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from modules.module_43_autonomous_screen_guardian.backend.app.config import ScreenGuardianConfig
from modules.module_43_autonomous_screen_guardian.backend.app.main import create_app, mount_module
from modules.module_43_autonomous_screen_guardian.backend.services.guardian_service import ScreenGuardianService


def _png_b64(lines: list[str]) -> str:
    img = Image.new("RGB", (960, 240), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    y = 24
    for line in lines:
        draw.text((24, y), line, fill=(0, 0, 0))
        y += 28
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


class TestAPIAndPersistence(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="m43_test_api_")
        self.tmp_path = Path(self._tmp.name)
        self.db_path = self.tmp_path / "data" / "guardian.db"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_19_rest_hud_ws_voice_and_host_mount(self) -> None:
        config = ScreenGuardianConfig(
            db_path=str(self.db_path),
            api_token="secret-test-token",
        )
        service = ScreenGuardianService(config=config)

        # Verify host app mount preserves JARVIS core "/" route
        host_app = FastAPI(title="Mock JARVIS Core")

        @host_app.get("/")
        async def core_root():
            return {"core": "jarvis"}

        mount_module(host_app, service, include_root_ui=False)
        client = TestClient(host_app)

        self.assertEqual(client.get("/").json(), {"core": "jarvis"})
        self.assertEqual(client.get("/screen-guardian").status_code, 200)
        self.assertIn("JARVIS", client.get("/screen-guardian").text)

        health = client.get("/api/v1/screen-guardian/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["module_id"], "jarvis-module-43-autonomous-screen-guardian")

        # Token enforcement on mutating route
        unauth = client.post("/api/v1/screen-guardian/monitor/start", json={"explicit_consent": True})
        self.assertEqual(unauth.status_code, 401)

        headers = {"X-JARVIS-Token": "secret-test-token"}
        # Consent enforcement via API
        no_consent = client.post("/api/v1/screen-guardian/monitor/start", json={"explicit_consent": False}, headers=headers)
        self.assertEqual(no_consent.status_code, 403)

        started = client.post("/api/v1/screen-guardian/monitor/start", json={"explicit_consent": True}, headers=headers)
        self.assertEqual(started.status_code, 200)
        self.assertEqual(started.json()["state"], "monitoring")

        # Analyze real PNG traceback via REST + real Tesseract OCR
        analyzed = client.post(
            "/api/v1/screen-guardian/analyze",
            json={
                "image_base64": _png_b64(
                    [
                        "Traceback (most recent call last):",
                        "  File 'demo.py', line 4, in run",
                        "ZeroDivisionError: division by zero",
                    ]
                ),
                "source_app": "Terminal",
                "window_title": "bash",
            },
            headers=headers,
        )
        self.assertEqual(analyzed.status_code, 200)
        self.assertGreaterEqual(len(analyzed.json()["errors"]), 1)

        # Voice command rejects screen playback audio
        voice_ignored = client.post(
            "/api/v1/screen-guardian/voice/command",
            json={"utterance": "fix this error", "speaker_source": "screen_media"},
            headers=headers,
        )
        self.assertEqual(voice_ignored.status_code, 200)
        self.assertFalse(voice_ignored.json()["accepted"])

        # Voice command accepts user_mic
        voice_ok = client.post(
            "/api/v1/screen-guardian/voice/command",
            json={"utterance": "what is wrong on my screen?", "speaker_source": "user_mic"},
            headers=headers,
        )
        self.assertEqual(voice_ok.status_code, 200)
        self.assertTrue(voice_ok.json()["accepted"])

        # WebSocket connection & clean disconnect
        with client.websocket_connect("/api/v1/screen-guardian/ws/stream") as ws:
            hello = ws.receive_json()
            self.assertEqual(hello["event_type"], "ws.connected")

        stopped = client.post("/api/v1/screen-guardian/monitor/stop", headers=headers)
        self.assertEqual(stopped.json()["state"], "stopped")

    def test_20_backend_restart_preserves_sqlite_wal_state(self) -> None:
        config1 = ScreenGuardianConfig(db_path=str(self.db_path))
        app1 = create_app(config=config1)
        client1 = TestClient(app1)

        # Persist settings and an error
        upd = client1.put(
            "/api/v1/screen-guardian/settings",
            json={"capture_interval_sec": 3.5, "excluded_windows": ["Bitwarden"]},
        )
        self.assertEqual(upd.status_code, 200)

        client1.post(
            "/api/v1/screen-guardian/analyze",
            json={"ocr_text_override": "ModuleNotFoundError: No module named 'fastapi_xyz'", "source_app": "Terminal"},
        )

        # Simulate full backend restart with a fresh app & service instance
        config2 = ScreenGuardianConfig(db_path=str(self.db_path))
        app2 = create_app(config=config2)
        client2 = TestClient(app2)

        settings_after = client2.get("/api/v1/screen-guardian/settings").json()
        self.assertEqual(settings_after["capture_interval_sec"], 3.5)
        self.assertIn("Bitwarden", settings_after["excluded_windows"])

        errors_after = client2.get("/api/v1/screen-guardian/errors").json()
        self.assertEqual(errors_after["count"], 1)
        self.assertIn("ModuleNotFoundError", errors_after["errors"][0]["title"])


if __name__ == "__main__":
    unittest.main()
