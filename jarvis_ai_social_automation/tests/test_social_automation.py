"""Automated tests for JARVIS OS — AI Social Media Automation (unittest & pytest compatible)."""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from jarvis_ai_social_automation.app import create_app
from jarvis_ai_social_automation.config import SocialAutomationConfig


class TestAISocialMediaAutomation(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmp.name) / "social_automation.db"
        self.export_dir = Path(self._tmp.name) / "exports"
        self.config = SocialAutomationConfig(
            db_path=self.db_path,
            manual_export_dir=self.export_dir,
            provider="offline",
        )
        self.app = create_app(config=self.config)
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_health_and_ui(self) -> None:
        res = self.client.get("/api/social-automation/health")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["feature"], "AI Social Media Automation")
        self.assertEqual(body["publish_mode"], "manual-export-fallback")

        ui = self.client.get("/social-automation")
        self.assertEqual(ui.status_code, 200)
        self.assertIn("JARVIS OS — AI SOCIAL MEDIA AUTOMATION", ui.text)

    def test_plan_schedule_publish_and_analytics(self) -> None:
        past_start = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        plan = self.client.post(
            "/api/social-automation/plan",
            json={
                "campaign_name": "JARVIS Pi 5 Launch",
                "topic": "Autonomous AI Modules on Raspberry Pi 5",
                "platforms": ["LinkedIn", "X"],
                "days": 2,
                "start_iso_utc": past_start,
            },
        )
        self.assertEqual(plan.status_code, 200)
        p_body = plan.json()
        self.assertEqual(p_body["posts_created"], 4)
        for post in p_body["posts"]:
            if post["platform"] == "X":
                self.assertLessEqual(post["character_count"], 280)

        first_id = p_body["posts"][0]["id"]

        # Dry-run publish keeps status scheduled
        dry = self.client.post(
            f"/api/social-automation/posts/{first_id}/publish",
            json={"dry_run": True},
        )
        self.assertEqual(dry.status_code, 200)
        self.assertTrue(dry.json()["dry_run"])

        # Live publish exports manual packet cleanly
        live = self.client.post(
            f"/api/social-automation/posts/{first_id}/publish",
            json={"dry_run": False},
        )
        self.assertEqual(live.status_code, 200)
        l_body = live.json()
        self.assertEqual(l_body["status"], "published")
        self.assertTrue(Path(l_body["export_path"]).exists())

        # Run due queue (dry-run) should find remaining past-due posts
        due = self.client.post("/api/social-automation/scheduler/run-due", params={"dry_run": "true"})
        self.assertEqual(due.status_code, 200)
        self.assertGreaterEqual(due.json()["due_count"], 1)

        # Log engagement metrics and verify analytics math
        metrics = self.client.post(
            f"/api/social-automation/posts/{first_id}/metrics",
            json={"impressions": 1000, "likes": 80, "comments": 10, "shares": 5, "clicks": 25},
        )
        self.assertEqual(metrics.status_code, 200)

        ana = self.client.get("/api/social-automation/analytics")
        self.assertEqual(ana.status_code, 200)
        a_body = ana.json()
        self.assertEqual(a_body["total_posts"], 4)
        self.assertEqual(a_body["published_count"], 1)
        self.assertEqual(a_body["total_impressions"], 1000)
        self.assertEqual(a_body["total_engagements"], 120)
        self.assertAlmostEqual(a_body["overall_engagement_rate_pct"], 12.0, places=2)
        self.assertAlmostEqual(a_body["overall_ctr_pct"], 2.5, places=2)


if __name__ == "__main__":
    unittest.main()
