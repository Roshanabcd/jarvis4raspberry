# JARVIS OS — Phase 1 Deterministic Tool Registry Specification

## 1. Registry Architecture & Safety Pipeline

All tools in JARVIS OS operate under a deterministic 5-stage pipeline managed by `ToolRegistry` (`tools/registry.py`):

1. **Schema Validation:** Strict type-checking against defined parameter types (`str`, `int`, `float`, `bool`, `dict`, `list`).
2. **Permission Check:** Granular role and confirmed check via `permission_manager` (`security/permissions/`).
3. **Safety Barrier:** Simulation-mode checks and range clamping (e.g., motor durations capped at 10,000 ms).
4. **Execution:** Direct invocation with timeout guards and exception isolation.
5. **Audit Logging:** Every tool execution is recorded to `security/audit/` with start time, duration, status, and error details.

---

## 2. Categorical Tool Inventory (78 Tools Total)

### A. System Telemetry & Operating System Metrics (Read-Only, Risk Level 0)
- `get_system_status` / `system_status`: Full system status (CPU %, RAM total/used/avail in GB, CPU temp °C, disk %, uptime string, robot state).
- `get_cpu_usage`: Real CPU percentage and core frequencies.
- `get_memory_usage`: Exact RAM and swap usage in GB and percentages.
- `get_uptime`: Linux OS uptime from `/proc/uptime` formatted in days, hours, minutes, seconds.
- `get_disk_usage`: Total, used, and free disk space in GB for `/` or specified mount point.
- `get_cpu_temperature`: Thermal-zone reading in °C with status classification.
- `get_network_status`: Local IP, hostname, connectivity status, and network IO counters.
- `get_application_status`: Service status for Ollama daemon, PipeWire audio, and JARVIS web server.

### B. Deterministic Mathematical Computation (Risk Level 0)
- `calculate(expression)`: Safe AST evaluator parsing arithmetic operations (`+`, `-`, `*`, `/`, `**`, `sqrt`, `abs`) and natural language math (`multiplied by`, `times`, `divided by`, `percent of`).
- `add(a, b)`: Adds two real numbers.
- `subtract(a, b)`: Subtracts b from a.
- `multiply(a, b)`: Multiplies two real numbers.
- `divide(a, b)`: Divides a by b with division-by-zero validation.
- `percentage(percent, total)`: Computes percentage of a total (e.g., 15% of 800 -> 120).

### C. Date, Time & Timezone Tools (Risk Level 0)
- `get_current_time`: Retrieves real local clock time with timezone name and ISO timestamp.
- `get_current_date`: Current calendar date, day of week, day, month, and year.
- `get_timezone`: System timezone name, UTC offset (`UTC+00:00`), and daylight saving time flag.
- `calculate_date_difference(start_date, end_date)`: Computes calendar day difference between dates.
- `format_timestamp(ts, fmt)`: Formats epoch timestamps into human-readable strings.

### D. Read-Only Robotics Diagnostics (Risk Level 0)
- `get_robot_status`: Hardware connection and simulation state without actuating motors.
- `get_motor_state`: Read-only motor speed and direction telemetry.
- `get_safety_state`: Checks whether the software or hardware emergency stop is engaged.

### E. Persistent Memory Tools (Risk Level 0 – 2)
- `memory_store`: Saves facts, preferences, and knowledge to SQLite database.
- `memory_search`: Keyword and fuzzy search over saved memories.
- `memory_recall`: Retrieves recent context by category (`USER`, `PROJECT`, `SYSTEM`, etc.).
- `memory_delete`: Removes a memory record by ID (requires confirmation).
- `memory_summarize`: Generates a high-level summary of stored memory count and categories.

### F. Filesystem, Media, & Desktop Tools
- Safe workspace file reading (`read_file`), writing (`write_file`), listing (`list_dir`), and searching (`search_files`, `search_folders`).
- Desktop folder navigation (`open_folder`, `open_folder_at`, `open_file`).
- Media player controls (`play_media`, `stop_media`, `pause_media`, `resume_media`, `set_volume`).
