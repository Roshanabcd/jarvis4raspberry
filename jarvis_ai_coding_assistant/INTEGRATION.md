# Integrating AI Coding Assistant into JARVIS OS (Strictly Additive)

This package does **not** modify or overwrite any existing `jarvis-os` files automatically. Follow these 3 steps to wire it into your existing FastAPI backend and dashboard.

## Step 1 — Place the Module Inside Your JARVIS OS Repo

```bash
mkdir -p ~/.gemini/antigravity/scratch/jarvis-os/features
unzip jarvis_ai_coding_assistant.zip -d ~/.gemini/antigravity/scratch/jarvis-os/features/
```

## Step 2 — Mount the FastAPI Router in Your Existing JARVIS Backend

Add these 2 lines to your existing FastAPI backend entry point (where `app = FastAPI(...)` is defined):

```python
from features.jarvis_ai_coding_assistant import create_router as create_coding_assistant_router

app.include_router(create_coding_assistant_router())
```

That exposes:
- **Web UI**: `GET /coding-assistant`
- **API Base**: `/api/coding-assistant/{health, workspace/files, workspace/file, generate, refactor, analyze, tests/synthesize, workspace/apply, history}`

## Step 3 — Enable the Card on Your JARVIS OS Dashboard

In your JARVIS OS dashboard app registry (where the **AI Coding Assistant** card is currently marked `PLANNED` with the `Roadmap` button):
1. Change its status from `PLANNED` to `AVAILABLE`.
2. Point the **Open** button URL to `/coding-assistant` (or `http://127.0.0.1:8011/coding-assistant` if running standalone).

## Environment Variables (All Optional)

| Variable | Default | Purpose |
|---|---|---|
| `JARVIS_CODE_WORKSPACE` | `~/.gemini/antigravity/scratch/jarvis-os` (or CWD) | Sandboxed workspace root |
| `JARVIS_CODING_PROVIDER` | `auto` | `auto`, `openrouter`, `ollama`, or `offline` |
| `OPENROUTER_API_KEY` | `""` | Enables OpenRouter LLM calls |
| `OPENROUTER_MODEL` | `openrouter/free` | OpenRouter model ID |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Local Ollama endpoint |
| `OLLAMA_MODEL` | `qwen2.5-coder:3b` | Local Ollama coding model |
| `JARVIS_CODING_DB_PATH` | `.jarvis_coding_assistant/coding_assistant.db` | SQLite WAL database path |
| `JARVIS_CODING_ALLOW_WRITES` | `true` | Set `false` for strict read-only mode |
