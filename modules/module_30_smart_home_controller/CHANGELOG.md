# Changelog — JARVIS Module 30: Smart Home Controller

## [1.0.0] — 2026-11-20
### Added
- Initial release of `jarvis-module-30-smart-home-controller` implementing JARVIS Common Module Contract `v1.0.0`.
- SQLite WAL persistence (`devices`, `scenes`, `rules`, `device_events`).
- `SmartHomeBridgeAdapter` abstract contract and `SimulatedSmartHomeBridgeAdapter` (`simulated: true`).
- `SmartHomeEngine` with device registry, command dispatch, explicit `confirm_unlock=True` safety guard (`409 UNLOCK_CONFIRMATION_REQUIRED`), multi-device scene activation, sensor threshold rule evaluation, and room energy telemetry.
- FastAPI REST endpoints under `/api/v1/smart-home/*`, WebSocket event stream at `/api/v1/smart-home/ws/events`, and `mount_module()` helper for JARVIS OS embedding.
- Zero-build JARVIS HUD (`backend/app/static/index.html`) and React/TypeScript/Vite/Tailwind frontend (`frontend/`).
- Automated backend, API, and integration test suites plus runnable CLI demo.
