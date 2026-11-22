# Changelog — JARVIS Module 42 (`v1.0.0`)

## [1.0.0] - 2026-11-21
### Added
- Safe read-only `ModuleArchiveScanner` with path traversal, symlink, zip-bomb, file-count, and CRC integrity enforcement.
- `CompatibilityAnalyzer` with ARM64/Pi 5 package checks and cross-module port/prefix/dependency conflict detection.
- SQLite WAL `ExtensionRegistryDB`, `InstallationPlanner` (dry-run + approval gate), and async `ModuleHealthMonitor`.
- Versioned Shared Integration SDK (`sdk/jarvis_sdk` `v1.0.0`), typed async `EventBus` with retry & dead-letter tracking, `ReferenceHostAdapter`, and `sample_extension`.
- Futuristic JARVIS Extension Management HUD (`/extensions`) and React/TypeScript/Vite/Tailwind frontend (`frontend/`).
- Automated test suites covering all 18 required test categories using synthetic ZIP fixtures.
