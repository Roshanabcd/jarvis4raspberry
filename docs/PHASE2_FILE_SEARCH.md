# JARVIS OS — Phase 2 File and Content Search Guide
## Specification and Operational Guide for Filesystem & Content Searching

### 1. Overview
The JARVIS Desktop File Search Subsystem (`tools/desktop/file_search.py`) provides safe, high-speed, bounded searching across workspace directories on Raspberry Pi 5.

### 2. Search Capabilities

#### 2.1 Filename & Extension Search (`search_files`)
- Search by exact filename or wildcard pattern (`*README*`, `controller.py`).
- Filter by file extension (`.py`, `.json`, `.toml`).
- Constrained recursion depth (default max depth: 5 levels).
- Returns structured metadata: file name, relative path, full path, file size formatted, and modification date.

#### 2.2 Content Grep Search (`search_content`)
- Searches source-code text contents using `grep -rnI -i` with Python fallback.
- Case-insensitive search with result line numbers and content snippets.
- Skips binary files and files larger than 2 MB to prevent memory exhaustion on ARM64.

### 3. Excluded Noisy Directories
To prevent expensive disk thrashing, the search engine automatically prunes:
- `.git`, `.hg`, `.svn`
- `node_modules`
- `__pycache__`, `.pytest_cache`, `.mypy_cache`
- `venv`, `.venv`
- `.cache`, `dist`, `build`, `target`
- System pseudo-filesystems (`/proc`, `/sys`, `/dev`)

### 4. Natural Language Commands Supported
* *"Find all Python files in my UnityGameWorkspace folder."*
* *"Search for controller.py in the JARVIS project."*
* *"Find all README files in Downloads."*
* *"Find all files containing the word database."*
* *"Find every file containing robot_move."*

### 5. REST API Reference

#### Search Files
`POST /api/desktop/search/files`
```json
{
  "directory": "/home/roshan/UnityGameWorkspace",
  "pattern": "*",
  "extension": ".py",
  "max_results": 50
}
```

#### Grep Content
`POST /api/desktop/search/content`
```json
{
  "query": "database",
  "directory": "/home/roshan/UnityGameWorkspace",
  "max_results": 25
}
```
