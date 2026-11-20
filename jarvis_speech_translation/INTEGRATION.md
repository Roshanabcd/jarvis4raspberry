# Integrating Real-Time Speech Translation into JARVIS OS

This package is **strictly additive** — it does not modify or overwrite any existing JARVIS OS files.

## 1. Copy the Package
Copy `jarvis_speech_translation/` into your JARVIS OS repository (e.g. `~/.gemini/antigravity/scratch/jarvis-os/jarvis_speech_translation/`).

## 2. Mount the Router in Your JARVIS FastAPI App
```python
from jarvis_speech_translation import SpeechTranslationConfig, create_router

app.include_router(create_router(SpeechTranslationConfig()))
```

## 3. Environment Variables (Optional)
- `JARVIS_TRANSLATE_DB_PATH`: SQLite WAL database path (default: `.jarvis_speech_translation/speech_translation.db`).
- `OPENROUTER_API_KEY` / `JARVIS_TRANSLATE_MODEL`: Optional OpenRouter LLM translation when `use_llm=true`.
- `JARVIS_TRANSLATE_LIBRE_URL`: Optional self-hosted LibreTranslate base URL (e.g. `http://localhost:5000`).
- `JARVIS_TRANSLATE_PORT`: Standalone server port (default: `8024`).

## 4. Endpoints Added
- `GET /speech-translation` — Interactive live bilingual translator dashboard
- `GET /api/speech-translation/health` — Supported languages, local TTS check, and counts
- `POST /api/speech-translation/sessions` & `GET /api/speech-translation/sessions/{session_id}` — Bilingual session & transcript management
- `POST /api/speech-translation/translate` — REST translation with auto-detection and glossary overrides
- `POST /api/speech-translation/glossary` & `GET /api/speech-translation/glossary` — Custom terminology overrides
- `WS /api/speech-translation/ws/{session_id}` — Real-time WebSocket utterance translation stream

## 5. Dashboard Card Update
Once mounted, update the **Real-Time Speech Translation** card in your JARVIS OS dashboard from `PLANNED` to `AVAILABLE` and point its **Open** button to `/speech-translation`.
