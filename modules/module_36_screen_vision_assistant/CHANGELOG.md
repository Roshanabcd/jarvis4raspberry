# Changelog — Module 36: Screen Vision Assistant

## [1.0.0] - 2026-11-20
- Initial standalone release conforming to JARVIS OS Common Module Contract `v1.0.0`.
- Added local PNG/BMP/JPEG binary header inspector, SHA-256 fingerprinting, bounding-box validation, spatial hit-testing, and grounded screen Q&A engine (`local_screen_vision_engine`, `simulated: false`).
- Added SQLite WAL persistence (`captures`, `vision_queries`), FastAPI REST + WebSocket endpoints (`/api/v1/vision/*`), standalone SVG HUD (`/vision`), React/TypeScript/Vite/Tailwind frontend, CLI demo, and automated test suites.
