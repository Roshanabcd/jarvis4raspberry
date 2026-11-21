# Changelog — JARVIS Module 32: System Health & Diagnostics

## [1.0.0] — 2026-11-20
### Added
- Initial release of `jarvis-module-32-system-health-diagnostics` implementing JARVIS Common Module Contract `v1.0.0`.
- Real `LocalLinuxHostProbe` (`simulated: false`) reading CPU load, `/proc/meminfo`, disk usage, `/proc/uptime`, and Linux thermal zones.
- SQLite WAL persistence for metric snapshots, alert rules, alerts, localhost service checks, and scored diagnostic runs.
- FastAPI REST & WebSocket APIs, `mount_module()` helper, standalone JARVIS HUD (`backend/app/static/index.html`), and React/Vite/Tailwind frontend (`frontend/`).
