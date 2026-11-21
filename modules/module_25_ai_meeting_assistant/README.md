# JARVIS OS — Module 25: AI Meeting Assistant (`v1.0.0`)

An independent, portable, integration-ready AI Meeting Assistant module for JARVIS OS. Captures live or bulk speaker-diarized transcripts, computes speaker talk-share analytics, extracts decisions, risks/blockers, and action items with due-date hints, supports cross-meeting transcript search, and exports shareable Markdown meeting minutes.

## Core Capabilities
- **Meeting Session Lifecycle**: Create and manage meeting sessions with participants, dates, agendas, and persisted summaries in an isolated SQLite WAL database (`./data/jarvis_meeting_assistant.db`).
- **Live & Bulk Transcript Ingestion**: Append single speaker segments or ingest multi-line `Speaker: message` transcripts in one call.
- **Deterministic Extraction & Talk-Share Analytics**: Computes per-speaker word counts and talk-share percentages, extracts decisions, risks/blockers, and action items with owner attribution and due-date hints (`by Friday`, `by tomorrow`, `by YYYY-MM-DD`).
- **Action Item Tracking**: Track open/done action items across all meetings via REST API and UI.
- **Cross-Meeting Transcript Search**: Case-insensitive full-text search across all stored meeting transcripts.
- **Markdown Minutes Export**: Generates clean `.md` meeting minutes via `GET /api/v1/meeting-assistant/meetings/{id}/minutes.md`.
- **Pluggable Synthesis Adapter**: Ships with `LocalMeetingSynthesisAdapter` (`simulated: true`) behind the `MeetingSynthesisAdapter` ABC so you can drop in Whisper / OpenAI / Gemini / Ollama providers later without touching core routes.

## Quick Start
```bash
bash scripts/setup.sh
bash scripts/run.sh
```
Open `http://127.0.0.1:8125/meeting-assistant` for the built-in zero-build JARVIS Control UI.

## Running Tests & Demo
```bash
bash scripts/test.sh
python3 examples/run_meeting_demo.py
```

## Integrating Into JARVIS OS
```python
from backend.app.main import mount_module
mount_module(app)  # Mounts /api/v1/meeting-assistant/* and /meeting-assistant
```
See `docs/INTEGRATION.md`, `docs/API.md`, `docs/SECURITY.md`, and `docs/TEST_REPORT.md` for full specifications.
