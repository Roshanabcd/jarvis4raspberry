# Changelog

## [1.0.0] - 2026-11-20
### Added
- Initial release of JARVIS OS Module 27 — GitHub & CI/CD Manager (`jarvis-module-27-github-cicd-manager`).
- Isolated SQLite WAL persistence for `repositories`, `pull_requests`, `pipeline_runs`, and `releases`.
- `GitHubCICDAdapter` contract and `SimulatedGitHubCICDAdapter` (`simulated: true`).
- `GitHubCICDEngine` with repository registration, PR merge gates, CI/CD workflow runner, release & rollback tracking, and HMAC-SHA256 webhook verification.
- FastAPI REST + WebSocket API under `/api/v1/github-cicd` and standalone JARVIS UI at `/github-cicd`.
- React/TypeScript/Vite/Tailwind frontend scaffold in `frontend/`.
- Automated Python backend, API, and integration tests plus runnable CLI demo.
