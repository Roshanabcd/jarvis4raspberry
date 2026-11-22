# Changelog

## [1.0.0] — Initial Release
### Added
- `ExecutiveAssistantDB` SQLite WAL persistence (`goals`, `tasks`, `time_blocks`, `habits`, `habit_checkins`, `follow_ups`).
- `PersonalExecutiveEngine` with Eisenhower quadrant classification, overlap-checked time blocking, smart workday auto-planner, habit streak calculation, overdue follow-up detection, and Daily Executive Briefing generation.
- `ExecutiveSynthesisAdapter` contract and offline `LocalRuleExecutiveAdapter`.
- FastAPI REST (`/api/v1/executive-assistant/*`), WebSocket (`/api/v1/executive-assistant/ws/events`), and `mount_module(app)` integration hook.
- Standalone JARVIS-themed Control UI (`backend/app/static/index.html`) and React/TypeScript/Vite/Tailwind frontend (`frontend/`).
- Automated backend, API, integration, frontend, and E2E test suites plus runnable CLI demo.
