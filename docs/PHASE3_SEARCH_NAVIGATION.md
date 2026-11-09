# JARVIS OS — Phase 3C & 3D: Organic Search & Numbered Navigation

## Overview
Phase 3C & 3D implements genuine web search extraction and numbered conversational navigation. Users can command JARVIS to search for topics, inspect ranked organic results, and issue natural-language follow-ups such as "Open the first website", "Open the second website", "Open the third result in a new tab", or "Go back and open the second website".

---

## Technical Implementation

### 1. Organic Search Engine (`tools/browser/search_manager.py`)
- **Extraction Protocol:** Queries DuckDuckGo Lite endpoint via `POST https://lite.duckduckgo.com/lite/` using standard library HTTP components (`urllib.request`).
- **Zero Third-Party Dependencies:** Parses HTML records and snippet structures using compiled regex engines with zero external dependency friction.
- **Data Extracted per Result:**
  - `rank`: Integer 1..N
  - `title`: Decoded, sanitized page title
  - `domain`: Fully-qualified domain name (e.g., `raspberrytips.com`, `raspberrypi.com`)
  - `url`: Direct, destination URL resolved from redirect parameters (`uddg`)
  - `snippet`: Extracted contextual text snippet
- **Ad & Tracker Filtering:** Automatically filters out sponsored ads and internal redirect links.

### 2. Conversational Search Memory (`SearchSession`)
- State is preserved across multiple dialogue turns:
  ```json
  {
    "query": "Raspberry Pi robotics",
    "total_results": 10,
    "active_index": 0,
    "opened_urls": ["https://raspberrytips.com/best-raspberry-pi-robots-kits/"]
  }
  ```
- **Numbered Resolution Mapping:**
  - Natural 1-based indexing (`first` -> rank 1 -> `results[0]`, `second` -> rank 2 -> `results[1]`, `third` -> rank 3 -> `results[2]`).
  - Out-of-bounds error handling with clear human feedback.

### 3. Numbered Navigation Workflows
1. **Search Request:**
   - User: *"Search Google for Raspberry Pi robotics."*
   - JARVIS: Searches web, returns top 5 organic results with rank, domain, title, and URL, and stores active search session.
2. **First Selection:**
   - User: *"Open the first website."*
   - JARVIS: Resolves index 1 (`results[0]`), launches URL in Google Chrome on `DISPLAY=:0`.
3. **Sequential Selection:**
   - User: *"Go back and open the second website."*
   - JARVIS: Issues `Alt+Left` to Chrome window, then resolves index 2 (`results[1]`), opening the second website.
4. **Tab Isolation:**
   - User: *"Open the third result in a new tab."*
   - JARVIS: Resolves index 3 (`results[2]`), opens target URL in a new tab.

---

## REST API Integration
- `GET /api/browser/search?q={query}&max_results={n}`: Returns structured ranked results.
- `POST /api/browser/open-result`: Body `{"index": 1, "new_tab": false}` opens requested result in Chrome.
- `GET /api/browser/session`: Inspects active search context memory.
- `POST /api/browser/navigate`: Dispatches `back`, `forward`, `reload`, `scroll_down`, `scroll_up`.
