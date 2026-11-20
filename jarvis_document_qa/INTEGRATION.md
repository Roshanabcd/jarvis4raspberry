# Integrating Document Question Answering into JARVIS OS

This package is **strictly additive** — it does not modify or overwrite any existing JARVIS OS files.

## 1. Copy the Package
Copy `jarvis_document_qa/` into your JARVIS OS repository (e.g. `~/.gemini/antigravity/scratch/jarvis-os/jarvis_document_qa/`).

## 2. Mount the Router in Your JARVIS FastAPI App
```python
from jarvis_document_qa import DocumentQAConfig, create_router

app.include_router(create_router(DocumentQAConfig()))
```

## 3. Environment Variables (Optional)
- `JARVIS_DOCQA_DB_PATH`: Custom SQLite WAL database path (default: `.jarvis_document_qa/docqa.db`).
- `JARVIS_DOCQA_EMBED_DIM`: Dense embedding dimension (default: `128`).
- `JARVIS_DOCQA_CHUNK_SIZE`: Target chunk size in characters (default: `520`).
- `JARVIS_DOCQA_CHUNK_OVERLAP`: Overlap between consecutive chunks (default: `90`).
- `OPENROUTER_API_KEY` / `JARVIS_DOCQA_MODEL`: Optional OpenRouter synthesis when `use_llm=true`.
- `JARVIS_DOCQA_PORT`: Standalone server port (default: `8020`).

## 4. Endpoints Added
- `GET /doc-qa` — Interactive JARVIS OS Document QA web dashboard
- `GET /api/doc-qa/health` — Index health and document/chunk counts
- `POST /api/doc-qa/documents` — Ingest PDF, Markdown, or text document
- `GET /api/doc-qa/documents` — List indexed documents
- `DELETE /api/doc-qa/documents/{doc_id}` — Delete document and cascade-delete its chunks
- `POST /api/doc-qa/search` — Hybrid semantic + BM25 chunk search
- `POST /api/doc-qa/ask` — Grounded question answering with chunk citations

## 5. Dashboard Card Update
Once mounted, update the **Document Question Answering** card in your JARVIS OS dashboard from `PLANNED` to `AVAILABLE` and point its **Open** button to `/doc-qa`.
