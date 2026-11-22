"""Runnable CLI demonstration for JARVIS Module 25 — AI Meeting Assistant."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.config import MeetingAssistantConfig
from backend.services.meeting_engine import MeetingAssistantEngine


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        cfg = MeetingAssistantConfig(db_path=os.path.join(tmp, "demo_meeting.db"))
        engine = MeetingAssistantEngine(config=cfg)

        meeting = engine.create_meeting(
            {
                "title": "JARVIS OS Q4 Architecture Sync",
                "meeting_date": "2026-11-20",
                "participants": ["Roshan", "Maya", "Dev"],
                "agenda": "Review Module 25 rollout and Raspberry Pi 5 latency targets",
            }
        )
        raw = "\n".join(
            [
                "Roshan: We agreed to ship Module 25 with isolated SQLite WAL storage.",
                "Maya: Action: I will prepare the integration guide and API tests by Friday.",
                "Dev: There is a risk of memory pressure if background jobs overlap on Pi 5.",
                "Roshan: Please follow up with benchmark numbers by tomorrow.",
            ]
        )
        ingested = engine.ingest_bulk_transcript(meeting["meeting_id"], raw)
        analysis = engine.analyze_meeting(meeting["meeting_id"])
        md = engine.export_markdown_minutes(meeting["meeting_id"])

        print(f"Meeting Created : {meeting['meeting_id']} ({meeting['title']})")
        print(f"Segments Loaded : {ingested['ingested_count']}")
        print(f"Decisions Found : {len(analysis['summary']['decisions'])}")
        print(f"Risks Found     : {len(analysis['summary']['risks'])}")
        print(f"Action Items    : {len(analysis['action_items'])}")
        print("\n--- Generated Markdown Minutes ---\n")
        print(md)


if __name__ == "__main__":
    main()
