# API Specification — JARVIS Module 20 (`v1.0.0`)

Base URL: `/api/v1/conversational-ai`

- `GET /health`, `GET /manifest`, `GET /status`, `GET /personas`, `PUT /provider`
- `GET /sessions`, `POST /sessions`, `GET /sessions/{id}/messages`, `DELETE /sessions/{id}/messages`, `DELETE /sessions/{id}`
- `POST /chat`, `POST /sessions/{id}/interrupt`
- `WS /ws/chat` — Send `{"type": "chat", "session_id": "...", "content": "...", "persona": "aria"}` or `{"type": "interrupt", "session_id": "..."}`
