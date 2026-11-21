# Security & Privacy — Module 23: Personal Executive Assistant

- **Local-First Storage**: All goals, tasks, schedules, habit logs, and follow-ups remain in the local SQLite WAL file (`JARVIS_M23_DB_PATH`).
- **Zero External Telemetry**: No outbound network requests are made by default.
- **Input Validation**: All request payloads and `HH:MM` schedule ranges are strictly validated via Pydantic schemas and overlap checks before persistence.
