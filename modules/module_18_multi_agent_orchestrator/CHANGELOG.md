# Changelog — Module 18: Multi-Agent Task Orchestrator

## [1.0.0] - 2026-11-20
### Added
- Core async `MultiAgentOrchestrator` engine with SQLite WAL persistence and restart recovery.
- Agent registry, capability routing, global and per-agent concurrency limits.
- DAG dependency graph validation with DFS cycle detection and automatic downstream failure/cancel propagation.
- Priority scheduling (`CRITICAL` > `HIGH` > `NORMAL` > `LOW`), exponential retry backoff, and per-task timeout enforcement.
- Human approval checkpoints (`awaiting_approval` -> approve/reject workflow).
- Inter-agent messaging bus, execution audit logs, workflow result aggregation, and WebSocket event stream.
- Versioned JARVIS Common Module Contract (`v1.0.0`) adapter interfaces and standalone compatibility harness.
- Futuristic JARVIS-themed React/TypeScript/Vite/Tailwind frontend and zero-build FastAPI standalone Control Dashboard.
- Automated backend, API, integration, frontend (Vitest/RTL), and E2E (Playwright) test suites.
