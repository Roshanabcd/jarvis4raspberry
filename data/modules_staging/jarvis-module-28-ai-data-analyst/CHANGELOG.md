# Changelog

## [1.0.0] - 2026-11-20
### Added
- Initial release of JARVIS OS Module 28 — AI Data Analyst (`jarvis-module-28-ai-data-analyst`).
- Isolated SQLite WAL persistence for `datasets` and `query_history`.
- `DataInsightAdapter` contract and `LocalDataInsightAdapter` (`simulated: true`).
- `DataAnalystEngine` with CSV/JSON ingestion, descriptive statistical profiling, Z-score anomaly detection, group-by aggregations, natural-language Q&A with chart series, and Markdown report export.
- FastAPI REST + WebSocket API under `/api/v1/ai-data-analyst` and standalone JARVIS UI at `/ai-data-analyst`.
- React/TypeScript/Vite/Tailwind frontend scaffold in `frontend/`.
- Automated Python backend, API, and integration tests plus runnable CLI demo.
