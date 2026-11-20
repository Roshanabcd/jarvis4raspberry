# JARVIS OS — PHASE 11: YOUTUBE AI ARCHITECTURE AUDIT

**Date:** 2026-11-17  
**Host Environment:** Raspberry Pi 5 (8GB RAM), Debian 13 Trixie, aarch64  
**Project Root:** `/home/roshan/.gemini/antigravity/scratch/jarvis-os`  
**Active Git Branch:** `feat/provider-adapter-dev-automation`  
**Status:** AUDIT COMPLETE — READY FOR IMPLEMENTATION

---

## 1. Executive Summary & Existing Reusable Components

Phase 11 introduces **JARVIS YouTube AI** (`youtube-summarizer`), a full-featured video understanding and conversational assistant operating strictly within YouTube's Developer Policies and legal compliance bounds.

### Audit Findings of Existing Subsystems:
1. **Backend Framework:** FastAPI running on `127.0.0.1:8000`. Modular router mounts under `/api/*`. App factory in `apps/core/app_factory.py`.
2. **Frontend Framework:** Single-page dashboard in `apps/dashboard/static/index.html` with vanilla JavaScript, CSS custom properties (dark navy/neon cyan theme), a11y landmarks, and tab navigation (`showTab`).
3. **JARVIS Apps Center:** Implemented in `apps/apps_center/` with:
   - Registry catalog in `data/apps/registry.json` (`youtube-summarizer` currently listed as `planned`).
   - `AppTaskManager` in `apps/apps_center/task_manager.py` managing thread-safe background jobs with admission control via `resource_manager.py`.
   - `AppsDatabase` in `apps/apps_center/database.py` with SQLite WAL persistence in `data/apps_center.sqlite3`.
   - RBAC in `apps/apps_center/permissions.py` enforcing `ADMIN`, `USER`, and `GUEST` roles.
4. **AI Brain & Provider Architecture:**
   - Central router `JARVISBrain` in `ai/brain.py` and `SharedAIService` in `apps/apps_center/ai_service.py`.
   - Providers: Local Ollama (`127.0.0.1:11434`, models `llama3.2:1b`, `qwen3.5:4b`, `moondream:latest`), Gemini, OpenAI, Anthropic Claude, Groq, NVIDIA NIM, Together.
   - Credentials resolved safely via `ai/providers/credentials.py` without leaking keys to logs or frontend.
5. **Memory & Retrieval Service:**
   - `SemanticMemorySearch` in `memory/vector/semantic_search.py` providing TF-IDF vectorization and cosine similarity over tokenized chunks, degrading gracefully to keyword search.
6. **Speech & Audio Pipeline:**
   - `SpeechToText` in `apps/voice/stt.py` with local Whisper (`tiny` model on CPU) and fallback speech recognition.
   - `ffmpeg` installed at `/usr/bin/ffmpeg` for media extraction and audio conversion.
7. **YouTube Controller (Phase 3):**
   - `tools/browser/youtube_controller.py` provides organic search extraction and playback on `DISPLAY=:0`. It does NOT perform unauthorized caption scraping or audiovisual downloads.

---

## 2. Available Video / Transcript Processing Libraries

| Library / Tool | Location | Status | Permitted Application in Phase 11 |
| :--- | :--- | :--- | :--- |
| `google-api-python-client` | `venv` (v2.201.0) | Installed | Official YouTube Data API v3 public metadata lookup. |
| `google-auth` / `google-auth-httplib2` | `venv` (v2.59.1) | Installed | Documented OAuth 2.0 flow for creator-owned caption tracks. |
| `openai-whisper` | `venv` (v20250625) | Installed | Local transcription of user-uploaded media files with confirmed rights. |
| `ffmpeg` | `/usr/bin/ffmpeg` | Installed | Audio conversion (extracting 16kHz WAV from user media). |
| `re` / `xml.etree` / `json` | Python 3.14 stdlib | Built-in | Parsing user-uploaded SRT, VTT, and TXT transcript files. |

> [!IMPORTANT]
> **Policy Compliance Boundaries:**
> - Neither `yt-dlp` nor undocumented scraping libraries (e.g. Innertube scraping or browser DOM scraping) will be used to extract captions or media.
> - The application only processes:
>   1. Creator-owned captions via authorized YouTube Data API OAuth (`captions.download`).
>   2. User-provided transcript files (`.srt`, `.vtt`, `.txt`, `.json`).
>   3. User-uploaded audio/video files where the user explicitly confirms processing rights.
> - When no authorized source is available, the system honestly reports: *"Transcript access is unavailable for this video through the currently configured authorized sources."*

---

## 3. Missing Functionality to Implement

1. **YouTube URL & Video ID Parser:**
   - Parsing standard URLs, short links (`youtu.be`), embed URLs, and Shorts.
   - Robust SSRF protection (rejecting localhost, loopback, private RFC1918 subnets, AWS metadata endpoints, file schemes, and invalid video IDs).
2. **Metadata Integration Service (`apps/youtube/metadata.py`):**
   - Official YouTube Data API v3 client using Google API key from `config.yaml` / environment.
   - Fallback when API key is missing: allow user-provided title/channel/duration without fabricating metadata.
3. **Authorized Transcript Acquisition & Parser (`apps/youtube/transcripts.py`):**
   - SRT, VTT, and TXT parser preserving start/end timestamps, speaker labels, and segment IDs.
   - YouTube OAuth caption download client for creator-owned videos.
   - User-provided media audio extraction (FFmpeg -> Whisper) with explicit user consent.
4. **Timestamp-Aware Chunking & Search Engine (`apps/youtube/indexing.py`):**
   - Segments grouped into timestamp-preserving chunks (e.g. 150-300 words).
   - Keyword search and TF-IDF/semantic search (leveraging `memory/vector/semantic_search.py`).
5. **AI Summarization & Information Extraction Engine (`apps/youtube/summarizer.py`):**
   - 12 summary formats strictly grounded in transcript content: Quick, Detailed, Executive, Key Points, Chapter-Wise, Important Concepts, Action Items, Study Notes, FAQ, Revision Notes, Pros/Cons, Technical Explanation.
   - Timestamped chapter generation: clearly distinguishing `CREATOR_PROVIDED_CHAPTER` vs `AI_GENERATED_CHAPTER`.
   - Key info extraction: topics, concepts, dates/numbers, action items, brief quotes with timestamps.
6. **Conversational "Ask This Video" Service (`apps/youtube/qa.py`):**
   - Transcript-retrieval grounded Q&A returning: answer, timestamp, supporting passage, video title, source.
   - Strict adherence: returns *"I could not find sufficient supporting information in the available transcript"* if evidence is absent.
   - Prompt injection defense: treats transcripts as untrusted data; prevents instruction override.
7. **Saved Notes & History Store (`apps/youtube/database.py`):**
   - SQLite table in `data/youtube_notes.sqlite3` with user isolation, full-text search, export, and delete.
8. **FastAPI Endpoints (`apps/api/youtube_api.py`):**
   - Mounted at `/api/youtube/*` with RBAC permissions (`USER` / `ADMIN`).
9. **Frontend Dashboard Section (`apps/dashboard/static/index.html`):**
   - Full 11-section UI tab `#tab-youtube`: Overview, Video Input, Details, Transcript, Summary (12 tabs), Chapters, Key Points, Ask This Video, Saved Notes & History, Settings.
10. **Voice Assistant Intent Routing (`apps/voice/service.py` / `ai/local_engine.py`):**
    - Natural voice commands: "Summarize this YouTube video", "Read summary aloud", "What does the video say about X?".

---

## 4. Implementation Plan & Milestones

- **Milestone 1:** Architecture Audit & Phase 11 PRD tracker update (`PHASE11_YOUTUBE_AI_AUDIT.md`, `PRD.md`).
- **Milestone 2:** Apps Center Registration & Catalog Update (`data/apps/registry.json`).
- **Milestone 3:** Core Engine Modules (`apps/youtube/models.py`, `url_parser.py`, `metadata.py`, `transcripts.py`, `indexing.py`, `summarizer.py`, `qa.py`, `database.py`).
- **Milestone 4:** FastAPI Router & Background Task Pipeline (`apps/api/youtube_api.py`).
- **Milestone 5:** Dashboard Frontend UI Implementation (`apps/dashboard/static/index.html`).
- **Milestone 6:** Voice Assistant Intent Integration (`apps/voice/` & `ai/local_engine.py`).
- **Milestone 7:** Automated Pytest Test Suite (`tests/test_phase11_youtube_ai.py` with 40 required test cases).
- **Milestone 8:** Real Browser Verification & End-to-End Testing (`PHASE11_YOUTUBE_AI_BROWSER_REPORT.md`).
- **Milestone 9:** Implementation Report & Architecture Guide (`PHASE11_YOUTUBE_AI_IMPLEMENTATION_REPORT.md`, `PHASE11_YOUTUBE_AI_ARCHITECTURE.md`).
