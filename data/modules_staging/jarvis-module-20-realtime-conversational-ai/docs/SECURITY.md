# Security & Privacy — Module 20 (`v1.0.0`)

- External provider API keys are loaded solely via `JARVIS_M20_PROVIDER_API_KEY` environment variable and never stored in SQLite or packaged archives.
- Browser microphone access requires explicit user permission via standard browser Web Speech API prompts.
- Standalone mode does not enforce operator auth on `/api/v1/conversational-ai/*`; protect behind JARVIS Core / Module 40 before exposing externally.
