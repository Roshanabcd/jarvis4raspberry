# Changelog — JARVIS Module 35: Visual Workflow Builder

## [1.0.0] — 2026-11-20
### Added
- Initial release of `jarvis-module-35-visual-workflow-builder` implementing JARVIS Common Module Contract `v1.0.0`.
- Kahn's topological DAG validator with cycle & invalid edge detection (`422 WORKFLOW_CYCLE_DETECTED` / `422 INVALID_EDGE_REFERENCE`).
- Deterministic execution engine (`simulated: false`) supporting `trigger`, `transform`, `condition`, `math`, and `notify` nodes with conditional branch skipping and per-node timing traces.
- SQLite WAL persistence, FastAPI REST & WebSocket APIs, `mount_module()` helper, SVG visual graph HUD (`backend/app/static/index.html`), and React/Vite/Tailwind frontend (`frontend/`).
