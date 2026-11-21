# Changelog — Module 19: Autonomous Computer Assistant

## [1.0.0] - 2026-11-20
### Added
- `SafeDemoDesktopAdapter` virtual desktop with Pillow PNG screenshot capture, allowlisted app discovery/launch, window focus, and virtual cursor/keyboard state.
- `ComputerAssistantEngine` with persistent E-STOP, global/per-action dry-run mode, risk-classified human approval gates, sandboxed file I/O with path-traversal protection, action replay, and diagnostics.
- FastAPI REST + WebSocket API (`/api/v1/computer-assistant/*`) and additive `mount_module(app)` hook.
- Futuristic JARVIS-themed React/TypeScript/Vite/Tailwind frontend + zero-build standalone UI at `/computer-assistant`.
- Automated backend, API, integration, frontend (Vitest/RTL), and E2E (Playwright) test suites.
