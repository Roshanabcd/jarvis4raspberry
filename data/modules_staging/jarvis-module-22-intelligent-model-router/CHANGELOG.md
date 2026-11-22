# Changelog

## [1.0.0] — Initial Release
### Added
- `ModelRouterDB` SQLite WAL persistence (`models`, `routing_logs`, `response_cache`, `router_policy`).
- `ModelProviderAdapter` contract and `SimulatedModelProviderAdapter` with outage simulation.
- `IntelligentModelRouterEngine` with task classification, 5 routing strategies, explainable candidate scoring, automatic failover, circuit breaker protection, budget-cap local downgrade, SHA-256 response cache, and multi-model benchmarking.
- FastAPI REST (`/api/v1/model-router/*`), WebSocket (`/api/v1/model-router/ws/events`), and `mount_module(app)` integration hook.
- Standalone JARVIS-themed Control UI (`backend/app/static/index.html`) and React/TypeScript/Vite/Tailwind frontend (`frontend/`).
- Automated backend, API, integration, frontend, and E2E test suites plus runnable CLI demo.
