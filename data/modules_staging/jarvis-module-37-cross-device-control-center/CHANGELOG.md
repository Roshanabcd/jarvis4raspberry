# Changelog — Module 37: Cross-Device Control Center

## [1.0.0] - 2026-11-20
- Initial standalone release conforming to JARVIS OS Common Module Contract `v1.0.0`.
- Added SQLite WAL device registry (`device_nodes`), command audit log (`device_commands`), and clipboard sync bus (`clipboard_entries`) backed by `simulated_mesh_device_bridge` (`simulated: true`).
- Added FastAPI REST + WebSocket routes (`/api/v1/devices/*`), standalone HUD (`/devices`), React/TypeScript/Vite/Tailwind frontend, CLI demo, and automated test suites.
