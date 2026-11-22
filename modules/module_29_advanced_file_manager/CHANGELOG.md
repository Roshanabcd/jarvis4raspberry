# Changelog

## [1.0.0] - 2026-11-20
### Added
- Initial release of JARVIS OS Module 29 — Advanced File Manager (`jarvis-module-29-advanced-file-manager`).
- Path-traversal-safe sandboxed filesystem engine (`FileManagerEngine`) with CRUD, move/rename, soft-delete trash & restore, SHA-256 duplicate scanner, dry-run/live smart auto-organizer, and filename/content search.
- Isolated SQLite WAL persistence for `file_tags`, `trash_items`, and `audit_logs`.
- `FileClassifierAdapter` contract and `LocalRuleFileClassifierAdapter` (`simulated: false`).
- FastAPI REST + WebSocket API under `/api/v1/file-manager` and standalone JARVIS UI at `/file-manager`.
- React/TypeScript/Vite/Tailwind frontend scaffold in `frontend/`.
- Automated Python backend, API, and integration tests plus runnable CLI demo.
