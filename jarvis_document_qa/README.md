# JARVIS OS — Document Question Answering

Upload, index, search, and perform grounded semantic question answering over **PDF**, **Markdown**, and **plain text** documents on **Raspberry Pi 5 (8GB)**.

## Features
- **Multi-Format Parser (`parser.py`)**: Extracts text from `.pdf` (via `pypdf` with a built-in pure-Python fallback), `.md`/`.markdown`, and `.txt` files from pasted text or base64 uploads.
- **Section-Aware Overlapping Chunker (`chunker.py`)**: Preserves Markdown heading context while splitting documents into overlapping chunks.
- **Hybrid Semantic + BM25 Retriever (`retriever.py`)**: Combines 128-D L2-normalized dense embeddings with BM25 lexical scoring.
- **Grounded QA (`qa_engine.py`)**: Produces cited extractive answers locally with zero API keys required, plus optional OpenRouter synthesis when `OPENROUTER_API_KEY` is configured and `use_llm=true`.
- **SQLite WAL Persistence (`storage.py`)**: Stores documents and embedded chunks with cascading deletes.

## Quick Start (Standalone)
```bash
pip install -r requirements.txt
python3 -m jarvis_document_qa.app
# Open http://localhost:8020/doc-qa
```

## Run Tests
```bash
python3 -m unittest discover -s jarvis_document_qa/tests -v
```
