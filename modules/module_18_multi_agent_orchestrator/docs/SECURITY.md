# Security & Safety Architecture — Module 18 (`v1.0.0`)

## Implemented Controls
- **Zero Hardcoded Credentials**: All runtime configuration is read from environment variables (`.env.example`).
- **SQL Injection Protection**: Every SQLite query uses parameterized placeholders (`?`) with `PRAGMA foreign_keys=ON` and WAL mode.
- **Bounded Resource Usage**: Global concurrency (`1..32`) and per-agent concurrency (`1..16`) plus strict `asyncio.wait_for` per-task timeouts prevent runaway tasks on Raspberry Pi 5.
- **Human-in-the-Loop Approval Checkpoints**: High-impact tasks (`requires_approval=true`) cannot execute until explicitly approved; rejection automatically cancels downstream dependents.
- **Safe Reference Agents**: Default reference agents never execute arbitrary shell commands, never call external paid APIs, and visibly flag simulated operations.

## Known Security Limitations (Standalone Mode)
- **Authentication / RBAC**: Standalone mode does not enforce JWT/OAuth operator authentication on `/api/v1/orchestrator/*` endpoints. Before exposing Module 18 beyond `localhost` or a trusted LAN, protect it behind JARVIS Core authentication (or Module 40 Permissions & Approval Center) and restrict `JARVIS_M18_CORS_ORIGINS`.
- **Custom Python Handlers**: Handlers registered via `register_handler()` execute in-process; only register trusted code.
