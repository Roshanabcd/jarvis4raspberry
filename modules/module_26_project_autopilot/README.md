# JARVIS OS — Module 26: Project Autopilot (`v1.0.0`)

An independent, portable, integration-ready autonomous project planning and execution module for JARVIS OS. Decomposes high-level engineering goals into ordered milestones and dependency-linked tasks, enforces human approval checkpoints before high-impact steps, logs every execution step in an isolated SQLite WAL database, scaffolds starter project workspaces inside a confined sandbox root, and exports Markdown blueprints.

## Core Capabilities
- **Goal-to-Milestone Decomposition**: Automatically generates structured milestones and dependency-ordered tasks from a project goal and tech stack.
- **Dependency-Aware Task Execution**: Advances ready tasks whose upstream dependencies are completed, supporting `dry_run` mode and step-by-step execution (`max_steps`).
- **Human Approval Checkpoints**: Tasks marked `requires_approval=True` pause in `awaiting_approval` until an operator explicitly approves or rejects them.
- **Sandboxed Starter Scaffolding**: Safely generates starter `README.md`, `src/main.py`, and `tests/test_smoke.py` inside `JARVIS_M26_WORKSPACE_ROOT` with path-traversal protection.
- **Blueprint Export**: Downloadable Markdown plan via `GET /api/v1/project-autopilot/projects/{id}/blueprint.md`.
- **Pluggable Planner Adapter**: Ships with `LocalProjectPlannerAdapter` (`simulated: true`) behind `ProjectPlannerAdapter` so live LLM/agentic runners can be plugged in without modifying core routes.

## Quick Start
```bash
bash scripts/setup.sh
bash scripts/run.sh
```
Open `http://127.0.0.1:8126/project-autopilot` for the built-in zero-build JARVIS Control UI.

## Running Tests & Demo
```bash
bash scripts/test.sh
python3 examples/run_autopilot_demo.py
```

## Integrating Into JARVIS OS
```python
from backend.app.main import mount_module
mount_module(app)  # Mounts /api/v1/project-autopilot/* and /project-autopilot
```
See `docs/API.md`, `docs/INTEGRATION.md`, `docs/SECURITY.md`, and `docs/TEST_REPORT.md` for full details.
