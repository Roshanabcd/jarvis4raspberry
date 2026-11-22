# JARVIS OS — Feature #7: Autonomous Web Scraping Agent

Strictly additive, Raspberry Pi 5-friendly Research & Knowledge module for **JARVIS OS**:
- **Policy-Compliant Fetching** (`robots.txt` verification, SSRF private/loopback IP blocking, per-domain rate limiting, transparent User-Agent)
- **Pure-Stdlib HTML Structure Parsing** (titles, meta descriptions, headings, absolute links, HTML tables, targeted tags, and SHA-256 content hashes — works on live URLs or raw HTML)
- **Scheduled Change Monitoring & Unified Diffs** stored in SQLite (WAL mode)
- **One-Click JSON Export** + **JARVIS OS Dark Cyber Web UI** at `/web-scraper`

## Quick Start (Standalone on Raspberry Pi 5)

```bash
cd ~/.gemini/antigravity/scratch/jarvis-os
unzip /path/to/jarvis_web_scraping_agent.zip -d features/
cd features

uvicorn jarvis_web_scraping_agent.app:app --host 127.0.0.1 --port 8017
```

Open `http://127.0.0.1:8017/web-scraper`.

## Run Tests

```bash
python3 -m unittest discover -s jarvis_web_scraping_agent/tests -v
# or with pytest:
pytest jarvis_web_scraping_agent/tests -v
```
