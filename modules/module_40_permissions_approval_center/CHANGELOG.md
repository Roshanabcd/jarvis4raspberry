# Changelog — Module 40: Permissions & Approval Center

## [1.0.0] - 2026-11-20
- Initial standalone release conforming to JARVIS OS Common Module Contract `v1.0.0`.
- Added fail-closed policy engine, human-in-the-loop approval queue, TTL expiration enforcement, single-decision lock, and immutable audit trail (`local_policy_approval_engine`, `simulated: false`) backed by SQLite WAL.
- Added FastAPI REST + WebSocket routes (`/api/v1/approvals/*`), standalone HUD (`/approvals`), React/TypeScript/Vite/Tailwind frontend, CLI demo, and automated test suites.
