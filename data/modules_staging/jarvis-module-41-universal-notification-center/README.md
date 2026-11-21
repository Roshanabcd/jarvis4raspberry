# JARVIS OS — Module 41: Universal Notification Center (`v1.0.0`)

Local-first universal notification hub with priority routing, Do-Not-Disturb critical override, `dedupe_key` idempotency, ack/dismiss lifecycle, SQLite WAL storage, and an interactive HUD for JARVIS OS.

## Key Capabilities
- **Local Notification Bus (`simulated: false`)**: Persists alerts across `hud`, `desktop`, `voice`, `email`, and `webhook` channels in SQLite WAL (external SMTP/webhook push adapters remain optional host hooks).
- **Do-Not-Disturb with Critical Override**: Suppresses non-critical alerts to `suppressed` during DND while still delivering `critical` alerts when `allow_critical_during_dnd` is enabled.
- **Idempotent Deduplication**: Reuses existing alert records when an identical `dedupe_key` is submitted (`deduplicated: true`).
- **Standalone HUD & Host Mount**: Serves `/notifications` directly from FastAPI (`port 8141`) and mounts cleanly into JARVIS OS via `backend.app.main:mount_module`.

## Quick Start
```bash
./scripts/setup.sh
./scripts/run.sh
# Open http://localhost:8141/notifications
```
