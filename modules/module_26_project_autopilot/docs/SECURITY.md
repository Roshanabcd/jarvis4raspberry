# Security & Safety Controls — Module 26: Project Autopilot

- **Human Approval Gates**: High-impact steps (such as release/deployment tasks) require explicit operator approval (`POST /tasks/{task_id}/approval`) and automatically pause autonomous advancement until approved.
- **Dry-Run Default**: New projects default to `dry_run=True`, preventing accidental live execution during planning.
- **Sandboxed Workspace Scaffolding**: `scaffold_workspace()` normalizes project slugs and verifies that the resolved target directory remains strictly inside `JARVIS_M26_WORKSPACE_ROOT` (`root in target.parents`), blocking path traversal.
- **Isolated Persistence & Parameterized SQL**: Uses an isolated SQLite WAL database with parameterized queries across all CRUD operations.
- **Simulation Transparency**: `LocalProjectPlannerAdapter` explicitly reports `simulated: true` across `/health`, `/status`, and exported Markdown blueprints.
- **No Hardcoded Secrets**: Verified via static regex scan; external provider credentials must be supplied via environment variables only.
