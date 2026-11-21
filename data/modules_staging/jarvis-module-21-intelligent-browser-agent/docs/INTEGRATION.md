# JARVIS OS Integration Guide — Module 21

Module 21 follows the **JARVIS Common Module Contract (`v1.0.0`)** so it mounts cleanly into an existing JARVIS OS FastAPI host without altering existing routes or databases.

## 1. Additive 2-Line FastAPI Mount
Place `jarvis-module-21-intelligent-browser-agent/` alongside your JARVIS OS modules and mount it in `apps/core/main.py` (before any root `/` static catch-all):

```python
from backend.app.main import mount_module as mount_browser_agent
mount_browser_agent(app)
```

If mounted as a package subfolder (e.g., `jarvis_module_21_intelligent_browser_agent`), add its directory to `sys.path` or import via your `jarvis_feature_suite_loader`.

## 2. Database & File Isolation
- SQLite WAL database defaults to `data/browser_agent.db` (configurable via `JARVIS_M21_DB_PATH`).
- Sandboxed downloads default to `data/downloads` (configurable via `JARVIS_M21_DOWNLOAD_DIR`).
- Never touches `jarvis_memory.db` or any other module's database.

## 3. Connecting a Live Browser Adapter (Playwright / Chromium)
Subclass `BrowserAutomationAdapter` in `backend/adapters/browser_adapter.py`:
- Implement `fetch_page(url)`, `submit_form(url, form_id, fields)`, `fetch_download(url)`, and `capture_and_analyze_screenshot(url, dom)`.
- Set `is_simulated = False` and pass your adapter into `IntelligentBrowserEngine(config, adapter=YourPlaywrightAdapter())`.
- All SSRF checks, domain allowlists, approval gates, and download sandboxing remain enforced by `IntelligentBrowserEngine`.
