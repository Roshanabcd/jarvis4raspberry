# Changelog — Module 39: Backup & Recovery Manager

## [1.0.0] - 2026-11-20
- Initial standalone release conforming to JARVIS OS Common Module Contract `v1.0.0`.
- Added sandbox-confined real ZIP snapshot creation, SHA-256 + `testzip()` verification, and Zip-Slip-protected restore (`local_snapshot_backup_engine`, `simulated: false`) backed by SQLite WAL (`snapshots`, `restore_runs`).
- Added FastAPI REST + WebSocket routes (`/api/v1/backups/*`), standalone HUD (`/backups`), React/TypeScript/Vite/Tailwind frontend, CLI demo, and automated test suites.
