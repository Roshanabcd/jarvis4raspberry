# JARVIS OS — Phase 10: Document AI Pre-Implementation Audit & Verification

## Executive Summary
This document records the architectural audit, resource constraints, existing service integration points, and security requirements prior to implementing **Phase 10: JARVIS Document AI** on Raspberry Pi 5.

---

## 1. Target Hardware & Operational Environment
- **Platform:** Raspberry Pi 5 (8 GB LPDDR4X RAM, Broadcom BCM2712 Quad-Core Cortex-A76 @ 2.4 GHz)
- **Architecture:** `aarch64` (ARM64)
- **Operating System:** Debian 13 Trixie (Kernel 6.12+)
- **Storage:** High-speed NVMe SSD backing `/home/roshan/.gemini/antigravity/scratch/jarvis-os`
- **Audio Subsystem:** Seeed ReSpeaker Lite USB 2-Mic Array + dynamic VAD engine
- **Camera Subsystem:** Raspberry Pi Camera Module 3 (Sony IMX708)
- **Backend Endpoints:**
  - JARVIS Core Service: `http://127.0.0.1:8000` (FastAPI / Uvicorn)
  - Ollama Local LLM: `http://127.0.0.1:11434`
  - Camera Streaming Service: `http://127.0.0.1:8082`

---

## 2. Resource Considerations on ARM64 Edge Architecture
Heavy vector databases (e.g. Milvus, Qdrant, ChromaDB, Weaviate) introduce significant background thread overhead, C++ JNI/gRPC bindings, and excessive resident memory usage (typically 500MB–1.5GB RAM).
To maintain peak edge performance on Raspberry Pi 5 alongside active voice processing and computer vision, Phase 10 requires:
1. **Lightweight Hybrid Search Engine:**
   - In-memory pure Python TF-IDF cosine similarity vector engine paired with BM25 inverted keyword index.
   - Resident RAM footprint: < 10 MB for up to 10,000 document chunks.
   - Query latency: < 5 ms per query on Cortex-A76 CPU cores.
2. **Deterministic SQLite WAL Storage:**
   - SQLite 3 with Write-Ahead Logging (WAL) and foreign-key cascading deletes.
   - Database location: `data/document_qa.sqlite3`.
   - Multi-tenant tenant scoping keyed by `user_id`.

---

## 3. Supported File Formats & Extractor Toolchain
- **PDF (.pdf):** Page-by-page text extraction via `pypdf` with fallback to system `/usr/bin/pdftotext`.
- **Word (.docx):** Semantic structural extraction of paragraph styles (headings 1–3) and tabular structures via `python-docx`.
- **Markdown (.md):** Hierarchical header tree parsing (`#`, `##`, `###`) preserving section contexts.
- **Plain Text (.txt):** Normalized whitespace, preserved paragraphs, line-boundary normalization.
- **Tabular Data (.csv):** Structured row-by-row translation transforming raw comma-separated records into semantically descriptive key-value sentences.

---

## 4. Security & Guardrails
- **Directory Traversal Protection:** All filenames sanitized with `sanitize_filename` stripping `..`, slashes, backslashes, and dangerous non-alphanumeric characters.
- **Prompt Injection Defense:** Untrusted document text quarantined within explicit XML `<document_context>` wrappers with strict system directives instructing the AI brain to ignore instruction overrides contained in extracted document chunks.
- **Truthful Ungrounded Fallback:** If search retrieval yields confidence below the relevance threshold (score < 0.04), return truthful fallback (`"I could not find sufficient supporting information in the uploaded documents."`) rather than generating hallucinated assertions.
- **Role-Based Access Control (RBAC):** GUEST sessions can query status and perform read-only searches if public collections exist, but upload and document deletion strictly require authenticated USER or ADMIN roles.
