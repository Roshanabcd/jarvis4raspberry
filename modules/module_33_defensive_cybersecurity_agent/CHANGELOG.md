# Changelog — JARVIS Module 33: Defensive Cybersecurity Agent

## [1.0.0] — 2026-11-20
### Added
- Initial release of `jarvis-module-33-defensive-cybersecurity-agent` implementing JARVIS Common Module Contract `v1.0.0`.
- Real `LocalDefensiveScanner` (`simulated: false`) with automatic secret redaction, world-writable permission checks, SHA-256 FIM baseline/drift verification, and SSH/sudo/HTTP log anomaly detection.
- Sandboxed path resolution (`403 PATH_OUTSIDE_SANDBOX`) preventing traversal outside `JARVIS_M33_SCAN_ROOT`.
- SQLite WAL persistence, FastAPI REST & WebSocket APIs, `mount_module()` helper, standalone JARVIS HUD (`backend/app/static/index.html`), and React/Vite/Tailwind frontend (`frontend/`).
