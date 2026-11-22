# JARVIS OS — Product Requirements Document (PRD) & Task Master

## Project Overview
Transform JARVIS OS into a robust, high-performance, edge-first AI operating environment and physical robot platform on Raspberry Pi 5.

---

## Master Phase Checklist (Ralph Loop Tracker)

- [x] **PHASE 0: Backup, System Inspection & Diagnostics**
  - [x] Host discovery (Debian 13 Trixie, aarch64, Pi 5 8GB, NVMe SSD)
  - [x] Hardware verification (IMX708 Camera, Seeed ReSpeaker Lite USB, Simulation mode for unpinned I2C/Serial)
  - [x] Ollama daemon inspection (port 11434, llama3.2:1b and qwen3.5:4b models detected)
  - [x] Write `docs/JARVIS_PHASE0_DIAGNOSTIC.md` and `IMPLEMENTATION_PROGRESS.md`

- [x] **PHASE 1: Fix AI Chat Engine & Multi-Provider Architecture**
  - [x] Dynamic Ollama connection, streaming chat API (SSE/WebSocket), model switching (`llama3.2:1b` vs `qwen3.5:4b`)
  - [x] Multi-provider registry (Ollama, Gemini, OpenAI, Anthropic, NVIDIA NIM, OpenAI-compatible)
  - [x] Provider routing, fallback logic, telemetry (TTFT, tokens/sec)
  - [x] Chat UI repair (streaming responses, markdown/code rendering, model selector, cancel/retry)

- [x] **PHASE 2: Agent Tool Registry & Autonomous Execution**
  - [x] Typed tool registry with JSON Schema and validation
  - [x] System, Robot, Sensor, Vision, Memory, Productivity, Research, Application tool suites
  - [x] Autonomous tool calling loop with multi-round execution & error recovery

- [x] **PHASE 3: ReSpeaker Lite Audio Capture & Wake-Word Engine**
  - [x] PipeWire/ALSA low-latency audio capture via Seeed ReSpeaker Lite
  - [x] Wake-word detector ("JARVIS") without device locking conflicts
  - [x] Local & cloud speech-to-text (STT) pipeline with fallback

- [x] **PHASE 4: OmniVoice Cloned Speech & Voice Pipeline**
  - [x] OmniVoice Hugging Face Space & Gradio client adapter
  - [x] Local reference voice (`data/voice_samples/myvoice.wav`) binding
  - [x] SHA-256 caching and neural fallback (`edge-tts` / `en-GB-RyanNeural`)

- [x] **PHASE 5: Real-Time Full-Duplex Audio & Voice Conversation Loop**
  - [x] Audio playback through ReSpeaker Lite speaker via PipeWire
  - [x] Barge-in / interruption handling & audio ducking
  - [x] Unified voice interaction loop (Wake Word -> STT -> Agent Brain -> Cloned TTS -> Speaker)

- [x] **PHASE 6: 14-App JARVIS Suite Implementation**
  - [x] App 1: Home / Command Center
  - [x] App 2: AI Chat
  - [x] App 3: Voice Center
  - [x] App 4: AI Studio
  - [x] App 5: Vision Center
  - [x] App 6: Robot Control
  - [x] App 7: Sensors Center
  - [x] App 8: Memory & Knowledge
  - [x] App 9: Automations & Workflows
  - [x] App 10: Tools & Skills
  - [x] App 11: Integrations
  - [x] App 12: System Monitor
  - [x] App 13: Logs & Diagnostics
  - [x] App 14: Settings Center

- [x] **PHASE 7: Interactive Settings Center (Categories A–P)**
  - [x] Complete UI & API endpoints for Categories A through P
  - [x] Persistent storage in `config/config.yaml` and `.env` with atomic writes & schema validation

- [x] **PHASE 8: Backend API & Database Hardening**
  - [x] Full REST & WebSocket API coverage
  - [x] SQLite WAL database optimizations & schema migrations

- [x] **PHASE 9: Futuristic Responsive Frontend Redesign**
  - [x] Dark navy & neon cyan aesthetic, responsive grid, zero UI lockups

- [x] **PHASE 10: Document Question Answering System (JARVIS Document AI)**
  - [x] Grounded RAG architecture: File validation, multi-format extraction, text normalization, chunking, hybrid search index, context retrieval, citations.
  - [x] Multi-format support: PDF (`pypdf` + `pdftotext`), DOCX (`python-docx`), Markdown, TXT, CSV.
  - [x] Structure-aware sentence-boundary chunking with configurable target words and sliding overlap.
  - [x] Sub-millisecond hybrid retrieval combining BM25 keyword frequency and TF-IDF cosine vector similarity (< 5ms on RPi5 ARM64).
  - [x] Grounded Q&A assistant with prompt injection quarantine and truthful ungrounded fallback (`"I could not find sufficient supporting information in the uploaded documents."`).
  - [x] Summarization studio with 4 format modes (`executive`, `key_takeaways`, `comprehensive`, `structured_outline`) and deterministic fallback.
  - [x] SQLite WAL database with foreign key cascading deletes, collections, and multi-tenant user isolation.
  - [x] 10 REST API endpoints mounted at `/api/document-qa` with RBAC GUEST restrictions.
  - [x] Frontend UI: Full Document AI suite in both classic dashboard (`static/index.html`) and futuristic operations hub.
  - [x] Comprehensive automated test suite (`tests/test_phase10_document_qa.py`) with 21/21 passed tests (100%).

- [x] **PHASE 11: YouTube Video Summarizer (JARVIS YouTube AI)**
  - [x] Application ID: `youtube-summarizer` in `data/apps/registry.json` (status: `available`)
  - [x] Strict compliance: Zero web scraping, zero media stream ripping, authorized caption and media sources only
  - [x] URL parser with comprehensive SSRF protection (private subnets, AWS metadata, non-standard ports blocked)
  - [x] Official YouTube Data API v3 integration with public oEmbed fallback
  - [x] Subtitle parsers (SRT, VTT, TXT, JSON) with speaker extraction and timestamp preservation
  - [x] Local media transcription via FFmpeg + Whisper with legal rights confirmation gate
  - [x] Timestamp-aware chunking and TF-IDF semantic search index (`TranscriptIndex`)
  - [x] 12 summary formats with prompt injection quarantine
  - [x] Video chapters (Creator vs AI) and key information extraction
  - [x] Grounded conversational "Ask This Video" assistant with cited timestamps
  - [x] User-isolated SQLite storage (`data/youtube_notes.sqlite3`) and export (MD, JSON, TXT)
  - [x] FastAPI REST API (`apps/api/youtube_api.py`) mounted at `/api/youtube/*`
  - [x] Single-page dashboard tab `#tab-youtube` with 11 functional sections
  - [x] Voice assistant intent integration in `ai/local_engine.py`
  - [x] 46 automated tests passing in `tests/test_phase11_youtube_ai.py` & `tests/test_phase11_youtube_api.py`
  - [x] 5 frontend tests passing in `tests/frontend/youtube-ai.test.cjs`
  - [x] Documentation: `PHASE11_YOUTUBE_AI_ARCHITECTURE.md`, `PHASE11_YOUTUBE_AI_BROWSER_REPORT.md`, `PHASE11_YOUTUBE_AI_IMPLEMENTATION_REPORT.md`

- [x] **PHASE 12: Autonomous AI Research Assistant (JARVIS Research AI)**
  - [x] Application ID: `research-assistant` in `data/apps/registry.json` (status: `available`, lifecycle: `active`)
  - [x] Strict compliance: Zero web scraping of anti-bot or policy-protected sites, public REST APIs only
  - [x] URL validator with comprehensive kernel-level SSRF defense (blocking loopback, private subnets, link-local, AWS metadata)
  - [x] Multi-repository search providers: DuckDuckGo Instant Answer, arXiv Atom XML, Crossref Works, OpenAlex, Europe PMC
  - [x] Content extraction: HTML text cleaner with 50k char cap, Poppler `pdftotext` for open-access PDFs, YouTube transcript reuse
  - [x] Transparent 9-tier source authority categorization and publication vs retrieval date disambiguation
  - [x] Verifiable evidence linking: pairs every factual claim with exact verbatim source quotes and offsets
  - [x] Verification engine: multi-source corroboration checker, contradiction detector, limitations compiler
  - [x] AI synthesis with strict `<research_materials>` prompt injection quarantine and deterministic grounded fallback
  - [x] Deterministic citation validator verifying `[N]` references against actual sources and purging hallucinations
  - [x] Comparative analysis with multi-dimensional matrix and pros/cons synthesizers
  - [x] Multi-format export: Markdown (`.md`), responsive dark-styled HTML (`.html`), and full JSON evidence archive (`.json`)
  - [x] Multi-step research agent orchestrating the 9-stage bounded loop with status transitions and cancellation tokens
  - [x] User-isolated SQLite WAL database (`data/research_assistant.sqlite3`)
  - [x] FastAPI REST router (`apps/api/research_api.py`) with 14 endpoints mounted at `/api/research/*`
  - [x] Single-page dashboard tab `#tab-research` with all 11 functional sections in `apps/dashboard/static/index.html`
  - [x] Voice assistant intent integration in `ai/local_engine.py` (open, investigate, compare, status, read summary, sources)
  - [x] 36 automated tests passing in `tests/test_phase12_research_assistant.py`
  - [x] 4 frontend DOM tests passing in `tests/frontend/research-assistant.test.cjs`
  - [x] Documentation: `PHASE12_RESEARCH_ASSISTANT_AUDIT.md`, `PHASE12_RESEARCH_ASSISTANT_ARCHITECTURE.md`, `PHASE12_RESEARCH_ASSISTANT_BROWSER_REPORT.md`, `PHASE12_RESEARCH_ASSISTANT_IMPLEMENTATION_REPORT.md`

- [x] **PHASE 11: Security, Privacy & Reliability**
  - [x] Watchdog daemon, resource isolation, credential sanitization

- [x] **PHASE 12: Automated Test Suite & Regression Testing**
  - [x] Pytest verification across all units, APIs, and pipelines (target: 100% pass)

- [x] **PHASE 13: Systemd Service & Auto-Recovery Setup**
  - [x] Production systemd daemon configuration, health monitoring (`jarvis-backend.service`, `jarvis-voice.service`, `jarvis-camera.service`)

- [x] **PHASE 14: Final End-to-End Acceptance Verification**
  - [x] Verification of Tests A through F

- [x] **PHASE 15: Documentation & Milestone Reports**
  - [x] Final comprehensive audit and architecture documentation
