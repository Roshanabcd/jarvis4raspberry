# API Reference — Module 27: GitHub & CI/CD Manager

Base prefix: `/api/v1/github-cicd` (default standalone port: `8127`).

## Endpoints
| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Module liveness, version, contract version, and `simulated` flag |
| `GET` | `/manifest` | Returns `manifest.json` metadata |
| `GET` | `/status` | Adapter name, `simulated` flag, repo/PR/run/release counts, uptime |
| `GET` | `/repos` | List registered repositories |
| `POST` | `/repos` | Register a repository (`full_name`, `default_branch`, `require_ci_green`, `workflows`) |
| `GET` | `/pull-requests` | List pull requests (filterable by `repo_id`, `status`) |
| `POST` | `/pull-requests` | Create a pull request |
| `POST` | `/pull-requests/{pr_id}/merge` | Merge PR (returns `409 CI_GATE_BLOCKED` if CI is not `passed`) |
| `GET` | `/pipelines` | List pipeline runs (filterable by `repo_id`) |
| `POST` | `/pipelines/trigger` | Trigger a CI/CD workflow run (updates linked PR `ci_status`) |
| `GET` | `/releases` | List releases (filterable by `repo_id`) |
| `POST` | `/releases` | Publish a release (requires passing CI when `require_ci_green=True`) |
| `POST` | `/releases/{release_id}/rollback` | Mark a published release as `rolled_back` |
| `POST` | `/webhooks/github` | Verify `X-Hub-Signature-256` HMAC-SHA256 webhook payload |
| `WS` | `/ws/events` | Real-time status stream (`ws.connected` + `ws.heartbeat`) |
