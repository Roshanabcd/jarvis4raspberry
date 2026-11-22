# Changelog

## [1.0.0] - 2026-11-20
### Added
- Initial release of JARVIS OS Module 25 — AI Meeting Assistant (`jarvis-module-25-ai-meeting-assistant`).
- Isolated SQLite WAL persistence for `meetings`, `transcript_segments`, and `action_items`.
- `MeetingSynthesisAdapter` interface and `LocalMeetingSynthesisAdapter` (`simulated: true`).
- `MeetingAssistantEngine` with live/bulk transcript ingestion, speaker talk-share analytics, action item/decision/risk extraction, full-text search, and Markdown minutes export.
- FastAPI REST + WebSocket API under `/api/v1/meeting-assistant` and standalone JARVIS UI at `/meeting-assistant`.
- React/TypeScript/Vite/Tailwind frontend source in `frontend/`.
- Automated Python backend, API, and integration tests plus runnable CLI demo.
