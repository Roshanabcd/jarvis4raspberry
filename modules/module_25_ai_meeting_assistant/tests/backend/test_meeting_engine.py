"""Unit tests for MeetingAssistantEngine (Module 25)."""

from __future__ import annotations

import os
import tempfile
import unittest

from modules.module_25_ai_meeting_assistant.backend.app.config import MeetingAssistantConfig
from modules.module_25_ai_meeting_assistant.backend.services.meeting_engine import MeetingAssistantEngine, MeetingAssistantError


class TestMeetingAssistantEngine(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = MeetingAssistantConfig(db_path=os.path.join(self._tmp.name, "test_m25.db"))
        self.engine = MeetingAssistantEngine(config=cfg)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_create_ingest_analyze_and_export(self) -> None:
        m = self.engine.create_meeting(
            {
                "title": "Architecture Review",
                "meeting_date": "2026-11-20",
                "participants": ["Roshan", "Maya"],
                "agenda": "Module 25 rollout",
            }
        )
        raw = (
            "Roshan: We agreed to deploy isolated SQLite WAL storage.\n"
            "Maya: Action: I will finalize API tests by Friday.\n"
            "Maya: There is a risk of CPU spikes during bulk indexing.\n"
        )
        ing = self.engine.ingest_bulk_transcript(m["meeting_id"], raw)
        self.assertEqual(ing["ingested_count"], 3)

        result = self.engine.analyze_meeting(m["meeting_id"])
        summary = result["summary"]
        self.assertTrue(summary["simulated_synthesis"])
        self.assertEqual(len(summary["decisions"]), 1)
        self.assertEqual(len(summary["risks"]), 1)
        self.assertEqual(len(result["action_items"]), 1)
        self.assertEqual(result["action_items"][0]["due_hint"], "by Friday")
        self.assertEqual(len(summary["speaker_stats"]), 2)
        self.assertAlmostEqual(sum(s["share_pct"] for s in summary["speaker_stats"]), 100.0, delta=0.5)

        md = self.engine.export_markdown_minutes(m["meeting_id"])
        self.assertIn("# Meeting Minutes: Architecture Review", md)
        self.assertIn("## Key Decisions", md)
        self.assertIn("by Friday", md)

    def test_action_item_status_and_search(self) -> None:
        m = self.engine.create_meeting({"title": "Ops Sync", "meeting_date": "2026-11-20"})
        self.engine.add_segment(m["meeting_id"], "Dev", "Action: Please follow up on Raspberry Pi thermals by tomorrow.", 30)
        res = self.engine.analyze_meeting(m["meeting_id"])
        item_id = res["action_items"][0]["item_id"]

        updated = self.engine.update_action_item(item_id, "done")
        self.assertEqual(updated["status"], "done")

        hits = self.engine.db.search_transcripts("thermals")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["speaker"], "Dev")

    def test_missing_meeting_raises_404_error(self) -> None:
        with self.assertRaises(MeetingAssistantError) as ctx:
            self.engine.analyze_meeting("mtg_does_not_exist")
        self.assertEqual(ctx.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
