# JARVIS OS — Phase 2 Defect Log & Targeted Software Repairs

This document catalogs every defect identified during the Phase 2 Independent Verification on Raspberry Pi 5, detailing the root cause, exact code modifications, and reproduction/verification test results.

---

## 1. Defect Catalog & Repair Summaries

### Defect 1: Missing `file_name` key in `file_search.search_content()`
- **Severity:** Medium (Caused `KeyError: 'file_name'` in content grep callers)
- **Root Cause:** `DesktopFileSearch.search_content()` populated dictionaries with `file`, `line`, and `content`, but omitted the convenience basename key `file_name`.
- **Affected File:** `tools/desktop/file_search.py`
- **Fix Applied:** Injected `"file_name": os.path.basename(fpath)` into both the primary `grep -rnI` parser and the secondary Python fallback walker.
- **Verification:** Re-ran `search_content("database", "~/UnityGameWorkspace")` — succeeded without KeyError, returned 6 matches.

---

### Defect 2: Desktop Lifecycle State Distinction (`PROCESS_STARTED` -> `WINDOW_VISIBLE` -> `TARGET_PROJECT_OPENED`)
- **Severity:** High (Required for deterministic desktop automation audits)
- **Root Cause:** `DesktopAppLauncher.launch_app()` previously returned an undifferentiated `"opened"` status based only on PID liveness, without polling X11 window mapping or confirming target project loading.
- **Affected File:** `tools/desktop/app_launcher.py`
- **Fix Applied:** Implemented `get_lifecycle_status()` with bounded X11 `wmctrl -l -p` polling loop. Classifies transitions through `PROCESS_STARTED`, `WINDOW_VISIBLE` (with window ID and title), and `TARGET_PROJECT_OPENED` (when project directory is loaded into the IDE).
- **Verification:** Tested `launch_app("code", target="~/UnityGameWorkspace/GameProject")` — returned transitions `['PROCESS_STARTED', 'WINDOW_VISIBLE', 'TARGET_PROJECT_OPENED']` and Window ID `0x02800003` (`Welcome - GameProject - Visual Studio Code`).

---

### Defect 3: Missing `get_job(job_id)` in `DesktopProgramRunner`
- **Severity:** Medium (Caused `AttributeError` when querying individual background jobs)
- **Root Cause:** `DesktopProgramRunner` implemented `list_jobs()` and `stop_job()` but lacked a direct single-job lookup method `get_job()`.
- **Affected File:** `tools/desktop/program_runner.py`
- **Fix Applied:** Added `get_job(self, job_id: str) -> Optional[Dict[str, Any]]` updating process liveness via `os.kill(pid, 0)`.
- **Verification:** Re-ran background execution test with `/home/roshan/UnityGameWorkspace/GameProject/build.py` — returned valid job descriptor with PID and status `running`.

---

### Defect 4: Compound Orchestrator Fallthrough on Desktop & Media Sub-Tasks
- **Severity:** High (Caused compound tasks like "Open Chrome and search YouTube..." to stall for 90s generating LLM essays)
- **Root Cause:** `CompoundTaskOrchestrator` only recognized calculator math, system RAM, and project opening. Any sub-task mentioning YouTube search, URL navigation, or terminal commands fell through to open-ended LLM text generation.
- **Affected File:** `ai/agents/task_orchestrator.py`
- **Fix Applied:** Added dedicated regex matchers and action handlers for:
  1. YouTube search via `browser_controller.search_youtube()`
  2. Terminal command execution via `terminal_engine.execute_command()`
  3. Direct URL navigation via `browser_controller.open_url()`
  4. System telemetry via `get_system_status()`
- **Verification:** Ran `Open Chrome and search YouTube for ROS2 robotics tutorials.` — executed in 498 ms, opening Chrome to encoded YouTube search URL without calling LLM text generation.

---

### Defect 5: Multi-Turn Context Continuity for Voice & Desktop Operations
- **Severity:** High (Required for natural conversational multi-turn workflows)
- **Root Cause:** When a user established context in Turn 1 (e.g. "For my next desktop command, use Google Chrome" or "I am working on ~/UnityGameWorkspace/GameProject"), subsequent voice commands in Turn 2 ("Open that project in VS Code") failed to resolve "that project".
- **Affected File:** `ai/agents/task_orchestrator.py`
- **Fix Applied:** Connected `execute_compound` to SQLite conversation history via `db.get_session_messages(sid)`. Extracts project paths, workspace names, and browser preferences from prior turns to bind pronouns like "that project", "the project", and "it".
- **Verification:** Tested 2-turn sequence:
  - Turn 1: "I am working on /home/roshan/UnityGameWorkspace/GameProject"
  - Turn 2: "Open that project in VS Code and find its Python files"
  - Result: Resolved `GameProject`, launched VS Code (PID 52558), and returned `controller.py` and `build.py`.
