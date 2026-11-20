"""Automated tests for JARVIS OS — AI Content Creation Pipeline (unittest & pytest compatible)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from jarvis_ai_content_pipeline.app import create_app
from jarvis_ai_content_pipeline.config import ContentPipelineConfig


class TestAIContentCreationPipeline(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmp.name) / "content_pipeline.db"
        self.config = ContentPipelineConfig(
            db_path=self.db_path,
            provider="offline",
        )
        self.app = create_app(config=self.config)
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_health_and_ui(self) -> None:
        res = self.client.get("/api/content-pipeline/health")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["feature"], "AI Content Creation Pipeline")
        self.assertEqual(body["provider"], "offline-template")

        ui = self.client.get("/content-pipeline")
        self.assertEqual(ui.status_code, 200)
        self.assertIn("JARVIS OS — AI CONTENT CREATION PIPELINE", ui.text)

    def test_generate_blog(self) -> None:
        res = self.client.post(
            "/api/content-pipeline/blog",
            json={
                "topic": "Modular FastAPI Services on Raspberry Pi 5",
                "key_points": ["Additive isolation", "SQLite WAL"],
                "include_code_example": True,
            },
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertIn("Modular FastAPI Services", body["title"])
        self.assertIn("```python", body["markdown"])
        self.assertGreaterEqual(body["estimated_read_minutes"], 1)
        self.assertIsNotNone(body["manual_prompt_fallback"])

    def test_generate_video_script(self) -> None:
        res = self.client.post(
            "/api/content-pipeline/video-script",
            json={
                "topic": "JARVIS Voice Assistant Pipeline",
                "platform": "YouTube Shorts",
                "duration_seconds": 45,
            },
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["duration_seconds"], 45)
        self.assertEqual(len(body["scenes"]), 5)
        self.assertIn("0:00", body["full_script_markdown"])

    def test_generate_hooks_and_captions(self) -> None:
        res = self.client.post(
            "/api/content-pipeline/hooks-captions",
            json={
                "topic": "Edge AI Robotics with Raspberry Pi 5",
                "platforms": ["YouTube", "LinkedIn", "X"],
                "hook_count": 6,
            },
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(len(body["hooks"]), 6)
        self.assertEqual(len(body["captions"]), 3)
        self.assertGreater(body["captions"][0]["character_count"], 20)

    def test_generate_carousel(self) -> None:
        res = self.client.post(
            "/api/content-pipeline/carousel",
            json={"topic": "SQLite WAL Best Practices", "slide_count": 7},
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(len(body["slides"]), 7)
        self.assertEqual(body["slides"][0]["role"], "Cover Hook")
        self.assertEqual(body["slides"][-1]["role"], "Closing CTA")

    def test_full_campaign_library_and_markdown_export(self) -> None:
        res = self.client.post(
            "/api/content-pipeline/campaign",
            json={
                "topic": "JARVIS OS AI Coding Assistant Launch",
                "video_duration_seconds": 60,
                "carousel_slides": 6,
            },
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        campaign_id = body["campaign_id"]
        self.assertIn("Full Content Campaign", body["combined_markdown"])

        hist = self.client.get("/api/content-pipeline/history")
        self.assertEqual(hist.status_code, 200)
        # 4 individual items + 1 combined campaign = 5
        self.assertEqual(hist.json()["total"], 5)

        detail = self.client.get(f"/api/content-pipeline/item/{campaign_id}")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["content_type"], "campaign")

        export = self.client.get(f"/api/content-pipeline/item/{campaign_id}/export")
        self.assertEqual(export.status_code, 200)
        self.assertIn("text/markdown", export.headers["content-type"])
        self.assertIn("JARVIS OS AI Coding Assistant Launch", export.text)


if __name__ == "__main__":
    unittest.main()
