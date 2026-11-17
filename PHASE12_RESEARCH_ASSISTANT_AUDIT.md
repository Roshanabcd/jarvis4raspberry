# JARVIS OS — PHASE 12: AI RESEARCH ASSISTANT ARCHITECTURE AUDIT

**Date:** 2026-11-17  
**Host Environment:** Raspberry Pi 5 (8GB RAM), Debian 13 Trixie, aarch64  
**Project Root:** `/home/roshan/.gemini/antigravity/scratch/jarvis-os`  
**Active Git Branch:** `feat/provider-adapter-dev-automation`  
**Status:** AUDIT COMPLETE — READY FOR IMPLEMENTATION  

---

## 1. Executive Summary & Existing Infrastructure

Phase 12 introduces **JARVIS AI Research Assistant** (`research-assistant`), an autonomous multi-step research agent capable of query decomposition, academic paper discovery, web research, transparent credibility scoring, cross-source fact checking, conflicting claim detection, AI synthesis, deterministic citation validation, and structured report generation on Raspberry Pi 5.

### 1.1 Core Subsystems Audited:
1. **Backend Framework:** FastAPI running on `127.0.0.1:8000`. Modular router mounts under `/api/*` managed by `create_app()` in `apps/core/app_factory.py`.
2. **Frontend Framework:** Single-page dashboard in `apps/dashboard/static/index.html` with vanilla JavaScript, CSS custom properties (dark navy/neon cyan palette), WCAG accessibility landmarks, and tab navigation (`showTab`).
3. **JARVIS Apps Center:**
   - Catalog registry in `data/apps/registry.json`. Entry `research-assistant` exists in category `research_knowledge` with initial status `planned`.
   - `AppTaskManager` in `apps/apps_center/task_manager.py`: Thread-safe background jobs with cancellation tokens and admission control via `resource_manager.py`.
   - `AppsDatabase` in `apps/apps_center/database.py`: SQLite WAL persistence in `data/apps_center.sqlite3`.
   - `apps_permissions` in `apps/apps_center/permissions.py`: RBAC enforcing `ADMIN`, `USER`, and `GUEST` roles.
4. **AI Brain & Provider Architecture:**
   - `SharedAIService` in `apps/apps_center/ai_service.py` (`shared_ai`) and `JARVISBrain` in `ai/brain.py`.
   - Providers: Local Ollama (`127.0.0.1:11434`, models `llama3.2:1b`, `qwen3.5:4b`, `moondream:latest`), Google Gemini, OpenAI, Anthropic Claude, Groq, NVIDIA NIM.
   - Credentials resolved safely via `ai/providers/credentials.py` without leaking keys to logs or frontend.
5. **Search & Browser Infrastructure:**
   - `WebSearcher` in `tools/web_search/searcher.py`: DuckDuckGo Instant Answer API integration, connectivity checks (`is_online`), and HTML-to-plain-text extraction with size caps (50KB) to prevent Pi 5 OOM.
   - `SearchManager` in `tools/browser/search_manager.py`: Search session state and organic result ranking.
6. **Academic & Document Processing:**
   - Linux system tool `/usr/bin/pdftotext` (poppler-utils) is installed and operational, allowing rapid text extraction from academic PDF papers without heavy Python dependencies.
   - Phase 10 Document AI is currently listed as `planned` in the registry. A self-contained document extractor leveraging `/usr/bin/pdftotext` will handle uploaded papers and PDFs cleanly.
7. **Phase 11 YouTube AI Integration:**
   - Operational in `apps/youtube/`. Provides authorized video metadata, subtitle parsers (SRT, VTT, TXT, JSON), timestamped chapters, and transcript search index (`TranscriptIndex`). Research tasks can incorporate authorized video transcripts as a rich multimodal evidence source.
8. **Memory & Retrieval:**
   - `SemanticMemorySearch` in `memory/vector/semantic_search.py` providing TF-IDF vectorization and cosine similarity over tokenized chunks.

---

## 2. Available Search Providers & Academic Repositories

| Provider / API | Endpoint | Auth Required | Purpose in Phase 12 | Status |
| :--- | :--- | :--- | :--- | :--- |
| **DuckDuckGo API** | `https://api.duckduckgo.com/` | None | Public web queries, definitions, entity overviews | Available |
| **arXiv REST API** | `http://export.arxiv.org/api/query` | None | Computer Science, Physics, AI academic preprints & abstracts | Available |
| **Crossref REST API** | `https://api.crossref.org/works` | None | Peer-reviewed journal publications, DOIs, publisher metadata | Available |
| **OpenAlex API** | `https://api.openalex.org/works` | None | Open access metadata, citations, abstracts, institutions | Available |
| **Europe PMC API** | `https://www.ebi.ac.uk/europepmc/webservices/rest/search` | None | Life sciences, biomedical, open-access research | Available |
| **Google Custom Search** | `https://www.googleapis.com/customsearch/v1` | Optional (`GOOGLE_API_KEY` + `GOOGLE_CSE_ID`) | Targeted commercial web search if configured | Optional Fallback |
| **JARVIS YouTube AI** | Internal (`apps/youtube/`) | Internal | Authorized video transcripts as multimodal research sources | Available |

---

## 3. Strict Compliance, Safety & Security Boundaries

1. **Zero Unauthorized Scraping:**
   - Uses documented REST APIs (DuckDuckGo, arXiv, Crossref, OpenAlex, Europe PMC).
   - Only opens allowed public web pages conforming to standard HTTP/HTTPS schemes.
   - If a page blocks access or returns an anti-bot challenge (Cloudflare, CAPTCHA), the system truthfully records `ACCESS_BLOCKED` and never attempts bypasses.
2. **SSRF & Network Defenses:**
   - URL validator blocks loopback (`127.0.0.0/8`), private subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), AWS metadata (`169.254.169.254`), non-standard ports, and non-HTTP schemes (`file://`, `gopher://`).
3. **Prompt Injection Quarantine:**
   - All retrieved web content, abstracts, and papers are treated as untrusted user data.
   - Data is enclosed within `<research_materials>` tags with strict directives forbidding LLMs from following commands, role changes, or instructions embedded within source texts.
4. **Truthful Source & Citation Integrity:**
   - Never fabricates authors, dates, titles, URLs, or DOIs.
   - Clearly flags abstract-only citations: `"Abstract-Only Source"`.
   - Distinguishes publication date vs event date vs retrieval date.
   - Deterministic citation validation verifies all cited source IDs before marking a report complete.

---

## 4. Architectural Modules to Implement

1. `apps/research/models.py`: Data models (`ResearchTask`, `ResearchPlan`, `ResearchQuery`, `ResearchSource`, `EvidenceRecord`, `ContradictionRecord`, `CitationRecord`, `ResearchReport`).
2. `apps/research/planner.py`: Autonomous query decomposition and structured research plan generation.
3. `apps/research/search_providers.py`: Multi-provider search engine integrating DuckDuckGo, arXiv, Crossref, OpenAlex, and Europe PMC.
4. `apps/research/extractor.py`: Safe content extraction for HTML pages, PDF papers (`/usr/bin/pdftotext`), and YouTube transcripts.
5. `apps/research/credibility.py`: Transparent source quality categorization and publication date disambiguation.
6. `apps/research/evidence.py`: Evidence store linking factual claims directly to source passages.
7. `apps/research/verification.py`: Cross-source fact checking, contradiction detection, and research limitations synthesis.
8. `apps/research/synthesizer.py`: Grounded AI report synthesis with prompt injection quarantine and deterministic fallback.
9. `apps/research/citations.py`: Deterministic citation validation ensuring 100% genuine sources.
10. `apps/research/reports.py`: Multi-format report builder (Markdown, HTML, JSON evidence archive).
11. `apps/research/comparative.py`: Structured feature-by-feature comparative matrix generator.
12. `apps/research/agent.py`: Multi-step bounded research orchestrator with cancellation tokens and restart recovery.
13. `apps/research/database.py`: SQLite WAL persistence in `data/research_assistant.sqlite3` with user isolation.
14. `apps/api/research_api.py`: FastAPI endpoints mounted at `/api/research/*`.
15. `apps/dashboard/static/index.html`: Dashboard tab `#tab-research` with all 11 required sections.
16. `ai/local_engine.py`: Voice assistant intent integration for natural research queries.
17. `tests/test_phase12_research_assistant.py`: Automated Pytest suite covering all test groups.

---

## 5. Audit Conclusion

The environment is verified. All required tools (FastAPI, SQLite, Python 3.14, `/usr/bin/pdftotext`, `requests`, `urllib3`, `SharedAIService`, `WebSearcher`) are available. No external blocking dependencies exist. Ready to proceed to Stage B.
