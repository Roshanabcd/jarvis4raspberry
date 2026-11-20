# JARVIS OS — End-to-End AI Search Engine

Unified semantic indexing and neural hybrid search across **local documents**, **terminal logs**, **codebases**, and **web knowledge** for **Raspberry Pi 5 (8GB)**.

## Features
- **Source-Aware Indexing (`indexer.py`)**: Chunks codebases by function/class definitions with line ranges, terminal logs with severity tagging (`ERROR`/`WARN`/`INFO`), and documents/web knowledge by Markdown sections.
- **Guarded Local Directory Crawler**: Safely indexes workspace directories restricted to `JARVIS_SEARCH_ALLOWED_ROOTS`.
- **Hybrid 128-D Dense + BM25 RRF Search (`hybrid_search.py`)**: Combines 128-D L2-normalized semantic embeddings with BM25 lexical scoring via Reciprocal Rank Fusion (RRF), source-type filtering, and snippet highlighting.
- **Multi-Source Answer Synthesis (`engine.py`)**: Produces a synthesized summary with `[source_type: title]` citations locally, or via OpenRouter when `OPENROUTER_API_KEY` is configured and `synthesize_with_llm=true`.
- **SQLite WAL Persistence (`storage.py`)**: Stores indexed sources, chunk vectors, and query latency history.

## Quick Start (Standalone)
```bash
pip install -r requirements.txt
python3 -m jarvis_ai_search_engine.app
# Open http://localhost:8021/ai-search
```

## Run Tests
```bash
python3 -m unittest discover -s jarvis_ai_search_engine/tests -v
```
