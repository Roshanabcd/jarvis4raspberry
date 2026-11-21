# Changelog — JARVIS Module 31: JARVIS Robot Brain

## [1.0.0] — 2026-11-20
### Added
- Initial release of `jarvis-module-31-robot-brain` implementing JARVIS Common Module Contract `v1.0.0`.
- SQLite WAL persistence (`robot_state`, `waypoints`, `missions`, `telemetry_events`).
- `RobotHardwareAdapter` ABC and `SimulatedRobotHardwareAdapter` (`simulated: true`).
- `RobotBrainEngine` with E-STOP interlock, confirmed E-STOP reset, velocity clamping, obstacle proximity halt, low-battery mission lockout, differential-drive kinematics, waypoint registry, and multi-step autonomous mission execution.
- FastAPI REST endpoints under `/api/v1/robot-brain/*`, WebSocket telemetry stream at `/api/v1/robot-brain/ws/telemetry`, and `mount_module()` helper.
- Zero-build JARVIS Robot Brain HUD (`backend/app/static/index.html`) and React/TypeScript/Vite/Tailwind frontend (`frontend/`).
