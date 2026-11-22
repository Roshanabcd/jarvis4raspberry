"""AI Meeting Assistant Engine (Module 25).

Provides:
- Meeting session management & live/bulk speaker-diarized transcript ingestion
- Speaker talk-share analytics (word counts & percentage share)
- Deterministic extraction of action items, decisions, and risks/blockers
- Full-text transcript search across meetings
- Shareable Markdown meeting minutes export
"""

from __future__ import annotations

import re
import time
import uuid
from typing import Any, Dict, List, Optional

from modules.module_25_ai_meeting_assistant.backend.adapters.meeting_adapter import LocalMeetingSynthesisAdapter, MeetingSynthesisAdapter
from modules.module_25_ai_meeting_assistant.backend.app.config import MeetingAssistantConfig
from modules.module_25_ai_meeting_assistant.backend.models.database import MeetingAssistantDB, utc_now_iso


class MeetingAssistantError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


ACTION_CUES = ("action:", "todo:", " will ", "needs to", "please ", "follow up", "i'll ", "assign ")
DECISION_CUES = ("decided", "agreed", "approved", "we will go with", "finalized", "confirmed")
RISK_CUES = ("risk", "blocker", "blocked by", "concern", "delay", "bottleneck")
DUE_RE = re.compile(r"\b(by\s+(?:monday|tuesday|wednesday|thursday|friday|tomorrow|eod|\d{4}-\d{2}-\d{2}))\b", re.IGNORECASE)


class MeetingAssistantEngine:
    def __init__(
        self,
        config: Optional[MeetingAssistantConfig] = None,
        db: Optional[MeetingAssistantDB] = None,
        adapter: Optional[MeetingSynthesisAdapter] = None,
    ) -> None:
        self.config = config or MeetingAssistantConfig.from_env()
        self.config.ensure_dirs()
        self.db = db or MeetingAssistantDB(self.config.db_path)
        self.adapter = adapter or LocalMeetingSynthesisAdapter()
        self._started_at = time.monotonic()

    def create_meeting(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        now = utc_now_iso()
        return self.db.create_meeting(
            {
                "meeting_id": f"mtg_{uuid.uuid4().hex[:10]}",
                "title": payload["title"],
                "meeting_date": payload.get("meeting_date", "2026-11-20"),
                "participants": list(payload.get("participants", [])),
                "agenda": payload.get("agenda", ""),
                "status": "live",
                "created_at": now,
                "updated_at": now,
            }
        )

    def _require_meeting(self, meeting_id: str) -> Dict[str, Any]:
        m = self.db.get_meeting(meeting_id)
        if not m:
            raise MeetingAssistantError("MEETING_NOT_FOUND", f"Meeting '{meeting_id}' not found.", 404)
        return m

    def add_segment(self, meeting_id: str, speaker: str, text: str, timestamp_sec: int = 0) -> Dict[str, Any]:
        self._require_meeting(meeting_id)
        return self.db.add_segment(
            {
                "segment_id": f"seg_{uuid.uuid4().hex[:10]}",
                "meeting_id": meeting_id,
                "speaker": speaker.strip(),
                "text": text.strip(),
                "timestamp_sec": timestamp_sec,
                "created_at": utc_now_iso(),
            }
        )

    def ingest_bulk_transcript(self, meeting_id: str, raw_transcript: str) -> Dict[str, Any]:
        self._require_meeting(meeting_id)
        added: List[Dict[str, Any]] = []
        ts = len(self.db.list_segments(meeting_id)) * 15
        for line in raw_transcript.splitlines():
            clean = line.strip()
            if not clean:
                continue
            if ":" in clean:
                spk, body = clean.split(":", 1)
                speaker = spk.strip()[:80] or "Speaker"
                text = body.strip()
            else:
                speaker = "Speaker"
                text = clean
            if text:
                added.append(self.add_segment(meeting_id, speaker, text, timestamp_sec=ts))
                ts += 15
        return {"meeting_id": meeting_id, "ingested_count": len(added), "segments": added}

    def analyze_meeting(self, meeting_id: str) -> Dict[str, Any]:
        meeting = self._require_meeting(meeting_id)
        segments = self.db.list_segments(meeting_id)

        # Speaker talk-share analytics
        word_counts: Dict[str, int] = {}
        total_words = 0
        decisions: List[str] = []
        risks: List[str] = []
        extracted_actions: List[Dict[str, Any]] = []
        now = utc_now_iso()

        for seg in segments:
            spk = seg["speaker"]
            txt = seg["text"]
            wc = len(txt.split())
            word_counts[spk] = word_counts.get(spk, 0) + wc
            total_words += wc

            low = f" {txt.lower()} "
            if any(c in low for c in DECISION_CUES):
                decisions.append(f"{spk}: {txt}")
            if any(c in low for c in RISK_CUES):
                risks.append(f"{spk}: {txt}")
            if any(c in low for c in ACTION_CUES):
                due_m = DUE_RE.search(txt)
                extracted_actions.append(
                    {
                        "item_id": f"act_{uuid.uuid4().hex[:10]}",
                        "owner": spk,
                        "description": txt,
                        "due_hint": due_m.group(1) if due_m else None,
                        "status": "open",
                        "created_at": now,
                        "updated_at": now,
                    }
                )

        speaker_stats = [
            {
                "speaker": spk,
                "word_count": wc,
                "share_pct": round((wc / total_words) * 100.0, 1) if total_words else 0.0,
            }
            for spk, wc in sorted(word_counts.items(), key=lambda kv: kv[1], reverse=True)
        ]

        saved_actions = self.db.replace_action_items(meeting_id, extracted_actions)
        overview = self.adapter.generate_executive_overview(meeting, segments, decisions, saved_actions, risks)
        summary = {
            "simulated_synthesis": self.adapter.is_simulated,
            "executive_overview": overview,
            "decisions": decisions,
            "risks": risks,
            "speaker_stats": speaker_stats,
            "action_items_count": len(saved_actions),
            "analyzed_at": utc_now_iso(),
        }
        updated = self.db.save_meeting_summary(meeting_id, summary, status="completed")
        return {"meeting": updated, "summary": summary, "action_items": saved_actions}

    def update_action_item(self, item_id: str, status: str) -> Dict[str, Any]:
        updated = self.db.update_action_item(item_id, status)
        if not updated:
            raise MeetingAssistantError("ACTION_ITEM_NOT_FOUND", f"Action item '{item_id}' not found.", 404)
        return updated

    def export_markdown_minutes(self, meeting_id: str) -> str:
        meeting = self._require_meeting(meeting_id)
        if not meeting.get("summary"):
            self.analyze_meeting(meeting_id)
            meeting = self._require_meeting(meeting_id)
        s = meeting["summary"]
        actions = self.db.list_action_items(meeting_id=meeting_id)

        lines = [
            f"# Meeting Minutes: {meeting['title']}",
            f"- **Date**: {meeting['meeting_date']}",
            f"- **Participants**: {', '.join(meeting['participants']) or 'Recorded in transcript'}",
            f"- **Agenda**: {meeting['agenda'] or 'General sync'}",
            "",
            "## Executive Overview",
            s["executive_overview"],
            "",
            "## Key Decisions",
        ]
        lines.extend([f"- {d}" for d in s["decisions"]] or ["- None recorded."])
        lines.append("")
        lines.append("## Action Items")
        lines.extend(
            [f"- [{ 'x' if a['status']=='done' else ' ' }] **{a['owner']}**: {a['description']}" + (f" ({a['due_hint']})" if a.get("due_hint") else "") for a in actions]
            or ["- None extracted."]
        )
        lines.append("")
        lines.append("## Risks & Blockers")
        lines.extend([f"- {r}" for r in s["risks"]] or ["- None recorded."])
        return "\n".join(lines) + "\n"

    def get_status(self) -> Dict[str, Any]:
        meetings = self.db.list_meetings()
        actions = self.db.list_action_items()
        return {
            "adapter": self.adapter.adapter_name,
            "simulated": self.adapter.is_simulated,
            "meetings_count": len(meetings),
            "open_action_items": sum(1 for a in actions if a["status"] == "open"),
            "completed_action_items": sum(1 for a in actions if a["status"] == "done"),
            "uptime_seconds": round(time.monotonic() - self._started_at, 2),
        }
