# Module 41 — Security & Privacy Notes

- **Local-First Storage**: All notification payloads and DND preferences remain in local SQLite WAL storage (`JARVIS_M41_DB_PATH`) with zero external push transmissions by default.
- **Strict Validation**: Enforces priority allowlist (`low`, `normal`, `high`, `critical`) and channel allowlist (`hud`, `desktop`, `voice`, `email`, `webhook`), rejecting invalid values with `422`.
- **Anti-Flood Deduplication**: Supplying `dedupe_key` prevents duplicate alert storms from repeated module polling.
- **Production Hardening**: Restrict `JARVIS_M41_CORS_ORIGINS` and authenticate internal module publishers if exposed beyond `127.0.0.1`.
