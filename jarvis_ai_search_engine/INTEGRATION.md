# Integrating End-to-End AI Search Engine into JARVIS OS

This package is **strictly additive** — it does not modify or overwrite any existing JARVIS OS files.

## 1. Copy the Package
Copy `jarvis_ai_search_engine/` into your JARVIS OS repository (e.g. `~/.gemini/antigravity/scratch/jarvis-os/jarvis_ai_search_engine/`).

## 2. Mount the Router in Your JARVIS FastAPI App
```python
from jarvis_ai_search_engine import AISearchConfig, create_router

app.include_router(create_router(AISearchConfig()))
```

## 3. Environment Variables (Optional)
- `JARVIS_SEARCH_DB_PATH`: SQLite WAL database path (default: `.jarvis_ai_search_engine/search_index.db`).
- `JARVIS_SEARCH_ALLOWED_ROOTS`: Colon-separated list of directories permitted for local crawling (default: current working directory).
- `JARVIS_SEARCH_EMBED_DIM`: Dense embedding dimension (default: `128`).
- `OPENROUTER_API_KEY` / `JARVIS_SEARCH_MODEL`: Optional LLM synthesis when `synthesize_with_llm=true`.
- `JARVIS_SEARCH_PORT`: Standalone server port (default: `8021`).

## 4. Endpoints Added
- `GET /ai-search` — Unified JARVIS OS AI Search web dashboard
- `GET /api/ai-search/health` — Index health and source-type breakdown
- `POST /api/ai-search/index` — Index a document, codebase file, terminal log, or web snippet
- `POST /api/ai-search/index-directory` — Safely crawl and index a local workspace directory
- `GET /api/ai-search/sources` — List all indexed sources
- `DELETE /api/ai-search/sources/{item_id}` — Delete source and cascade-delete chunks
- `POST /api/ai-search/query` — Unified hybrid RRF search with synthesized answer
- `GET /api/ai-search/history` — Recent search history and latency metrics

## 5. Dashboard Card Update
Once mounted, update the **End-to-End AI Search Engine** card in your JARVIS OS dashboard from `PLANNED` to `AVAILABLE` and point its **Open** button to `/ai-search`.
