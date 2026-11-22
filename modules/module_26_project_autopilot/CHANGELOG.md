# Changelog

## [1.0.0] - 2026-11-20
### Added
- Initial release of JARVIS OS Module 26 — Project Autopilot (`jarvis-module-26-project-autopilot`).
- Isolated SQLite WAL persistence for `projects`, `milestones`, `tasks`, and `execution_logs`.
- `ProjectPlannerAdapter` contract and deterministic `LocalProjectPlannerAdapter` (`simulated: true`).
- `ProjectAutopilotEngine` with goal-to-milestone decomposition, dependency-graph task advancement, human approval checkpoints, dry-run mode, sandboxed starter workspace scaffolding, and Markdown blueprint export.
- FastAPI REST + WebSocket API under `/api/v1/project-autopilot` and standalone JARVIS Control UI at `/project-autopilot`.
- React/TypeScript/Vite/Tailwind frontend scaffold in `frontend/`.
- Automated Python backend, API, and integration tests plus runnable CLI demo.
