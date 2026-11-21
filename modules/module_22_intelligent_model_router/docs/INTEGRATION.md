# JARVIS OS Integration Guide — Module 22

Module 22 implements the **JARVIS Common Module Contract (`v1.0.0`)** and mounts additively into an existing JARVIS OS FastAPI application.

## 1. Additive 2-Line FastAPI Mount
In `apps/core/main.py` (prior to any root `/` static catch-all):
```python
from backend.app.main import mount_module as mount_model_router
mount_model_router(app)
```

## 2. Database Isolation
- Uses its own SQLite WAL file at `JARVIS_M22_DB_PATH` (default `./data/jarvis_model_router.db`).
- Never modifies `jarvis_memory.db` or sibling module databases.

## 3. Wiring Live Model Providers (Ollama / Gemini / OpenAI / Anthropic)
Subclass `ModelProviderAdapter` in `backend/adapters/provider_adapter.py`:
- Implement `invoke(self, model, prompt, task_type)` routing by `model["provider"]` (e.g., local HTTP to `http://127.0.0.1:11434/api/generate` for Ollama, or HTTPS SDK calls for Gemini/OpenAI/Anthropic).
- Set `is_simulated = False` and pass the adapter to `IntelligentModelRouterEngine(config, adapter=YourLiveAdapter())`.
- All scoring, circuit breakers, budget guardrails, and response caching remain active automatically.
