# Changelog — Module 41: Universal Notification Center

## [1.0.0] - 2026-11-20
- Initial standalone release conforming to JARVIS OS Common Module Contract `v1.0.0`.
- Added local notification bus with priority/channel validation, DND suppression + critical override, `dedupe_key` idempotency, and ack/dismiss lifecycle (`local_notification_hub_engine`, `simulated: false`) backed by SQLite WAL.
- Added FastAPI REST + WebSocket routes (`/api/v1/notifications/*`), standalone HUD (`/notifications`), React/TypeScript/Vite/Tailwind frontend, CLI demo, and automated test suites.
