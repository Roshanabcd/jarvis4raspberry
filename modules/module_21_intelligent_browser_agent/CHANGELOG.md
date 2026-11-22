# Changelog

## [1.0.0] — Initial Release
### Added
- `BrowserAgentDB` SQLite WAL persistence (`browser_sessions`, `browser_tasks`, `submission_approvals`, `downloads`, `browser_logs`, `site_policy`).
- `DOMExtractorParser` real HTML DOM extraction (`title`, `headings`, `links`, `forms`, `inputs`, `text_preview`).
- `BrowserAutomationAdapter` contract and `SafeSimulatedBrowserAdapter` with local `*.jarvis.local` HTML fixtures and Pillow PNG screenshot capture & analysis.
- `IntelligentBrowserEngine` with SSRF/private-IP blocking, site allowlist/denylist enforcement, approval-gated form submissions, sandboxed downloads with SHA-256 hashing, and multi-page workflow orchestration with pause/resume and cancellation.
- FastAPI REST endpoints (`/api/v1/browser-agent/*`), WebSocket event stream (`/api/v1/browser-agent/ws/events`), and `mount_module(app)` JARVIS OS integration hook.
- Standalone JARVIS-themed Control UI (`backend/app/static/index.html`) and React/TypeScript/Vite/Tailwind frontend (`frontend/`).
- Automated backend, API, integration, frontend, and E2E test suites plus runnable CLI workflow demo.
