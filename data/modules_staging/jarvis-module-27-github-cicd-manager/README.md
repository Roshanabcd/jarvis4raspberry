# JARVIS OS — Module 27: GitHub & CI/CD Manager (`v1.0.0`)

An independent, portable, integration-ready GitHub & CI/CD management module for JARVIS OS. Manages repositories, pull requests with branch-protection CI merge gates, CI/CD workflow runs with structured step logs, semantic release publishing and rollback markers, and HMAC-SHA256 GitHub webhook verification.

## Core Capabilities
- **Repository Registry**: Track `owner/repo` metadata, default branch, CI merge-gate policy, and configured workflows in an isolated SQLite WAL database (`./data/jarvis_github_cicd.db`).
- **Pull Request Merge Gates**: Enforces passing CI (`ci_status == "passed"`) before allowing merges when `require_ci_green` is enabled.
- **CI/CD Pipeline Runner**: Triggers workflows with structured step logs (`checkout`, `lint_and_typecheck`, `automated_tests`, `security_and_package`) and optional failure simulation (`simulate_failure=True`).
- **Releases & Rollbacks**: Gates semantic release publishing on at least one green CI run and supports one-click rollback state tracking.
- **Webhook Signature Verification**: Real HMAC-SHA256 `X-Hub-Signature-256` verification via `hmac.compare_digest` on `POST /api/v1/github-cicd/webhooks/github`.
- **Pluggable Provider Adapter**: Ships with `SimulatedGitHubCICDAdapter` (`simulated: true`) behind `GitHubCICDAdapter` so no live GitHub token is needed locally.

## Quick Start
```bash
bash scripts/setup.sh
bash scripts/run.sh
```
Open `http://127.0.0.1:8127/github-cicd` for the zero-build JARVIS Control UI.

## Running Tests & Demo
```bash
bash scripts/test.sh
python3 examples/run_cicd_demo.py
```

## Integrating Into JARVIS OS
```python
from backend.app.main import mount_module
mount_module(app)  # Mounts /api/v1/github-cicd/* and /github-cicd
```
