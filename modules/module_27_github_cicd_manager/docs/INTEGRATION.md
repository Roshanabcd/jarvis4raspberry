# Integration Guide — JARVIS OS Module 27

## Standalone Mode
```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8127
```
- UI: `http://127.0.0.1:8127/github-cicd`
- Health: `http://127.0.0.1:8127/api/v1/github-cicd/health`

## Mounting Into Existing JARVIS OS FastAPI App
```python
from backend.app.main import mount_module

mount_module(app, include_root_ui=False)
```
- Registers all REST & WebSocket endpoints under `/api/v1/github-cicd/*` and UI at `/github-cicd`.
- Uses an isolated SQLite WAL database (`JARVIS_M27_DB_PATH`, default `./data/jarvis_github_cicd.db`).

## Connecting Real GitHub API / Actions
Implement `GitHubCICDAdapter` in `backend/adapters/github_adapter.py` using a GitHub App or PAT loaded from environment variables, set `is_simulated = False`, and inject it into `GitHubCICDEngine(adapter=YourGitHubAdapter())`.
