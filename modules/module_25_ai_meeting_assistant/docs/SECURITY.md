# Security & Privacy — Module 25: AI Meeting Assistant

- **Local-First Persistence**: All meeting metadata, transcripts, and action items remain in a local SQLite WAL file (`JARVIS_M25_DB_PATH`). No transcript text is sent to external cloud APIs by default.
- **Explicit Simulation Disclosure**: The default `LocalMeetingSynthesisAdapter` reports `simulated: true` on `/health`, `/status`, and generated summaries so operators always know whether deterministic local synthesis or an external LLM provider is active.
- **Parameterized SQL Queries**: Every SQLite read/write uses `?` bind parameters, preventing SQL injection across transcript ingestion and full-text search queries.
- **Input Validation**: All request payloads are validated through Pydantic schemas (`backend/models/schemas.py`) with length bounds and strict status literals (`open` / `done`).
- **Secrets Hygiene**: No hardcoded API keys or credentials exist in the codebase. Future live STT/LLM adapters must load credentials exclusively from environment variables (`.env`).
- **CORS & Host Binding**: Configure `JARVIS_M25_CORS_ORIGINS` to restrict origins when deploying beyond `localhost`.
