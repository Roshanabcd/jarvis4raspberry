# Changelog — Module 38: Plugin & Skills Marketplace

## [1.0.0] - 2026-11-20
- Initial standalone release conforming to JARVIS OS Common Module Contract `v1.0.0`.
- Added SQLite WAL plugin/skill catalog (`packages`, `installations`, `marketplace_audit`) with SemVer validation, permission allowlisting, SHA-256 checksum verification, and install/toggle/uninstall lifecycle (`local_plugin_registry_engine`, `simulated: false`).
- Added FastAPI REST + WebSocket routes (`/api/v1/marketplace/*`), standalone HUD (`/marketplace`), React/TypeScript/Vite/Tailwind frontend, CLI demo, and automated test suites.
