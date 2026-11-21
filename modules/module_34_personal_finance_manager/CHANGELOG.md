# Changelog — JARVIS Module 34: Personal Finance Manager

## [1.0.0] — 2026-11-20
### Added
- Initial release of `jarvis-module-34-personal-finance-manager` implementing JARVIS Common Module Contract `v1.0.0`.
- Real local SQLite WAL ledger (`simulated: false`) for accounts, transactions, monthly budgets, and savings goals.
- Monthly cashflow summary, net worth & savings rate analytics, overdraft warning detection, and RFC 4180 CSV export.
- FastAPI REST & WebSocket APIs, `mount_module()` helper, standalone JARVIS HUD (`backend/app/static/index.html`), and React/Vite/Tailwind frontend (`frontend/`).
