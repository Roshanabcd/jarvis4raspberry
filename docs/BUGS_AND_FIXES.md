# JARVIS OS — Defects, Root Causes & Fixes Register

This document records all software defects identified, root-cause analyzed, and repaired during the project audit.

---

## Defect Summary by Severity

| Severity Level | Count Identified | Count Repaired | Regression Tested |
| :--- | :---: | :---: | :---: |
| **CRITICAL** | 3 | 3 | **100% PASS** |
| **HIGH** | 4 | 4 | **100% PASS** |
| **MEDIUM** | 3 | 3 | **100% PASS** |
| **LOW** | 2 | 2 | **100% PASS** |
| **TOTAL** | **12** | **12** | **100% PASS** |

---

## 1. Critical Defects

### BUG-01: Actuators Booted in Armed State with Unlatched Emergency Stop
- **Severity:** **CRITICAL**
- **Affected File:** `tools/robotics/controller.py`
- **Root Cause:** Motors and servos booted up with `armed=True` or no armed flag at all. Any motion call (`forward()`) would immediately execute without safety gate verification. Furthermore, an emergency stop could be inadvertently cleared simply by sending another motion command.
- **Fix Applied:** Implemented a formal safety gate. The robot now boots strictly in a `DISARMED` state (`self.armed = False`). Calling `emergency_stop()` sets a persistent latch `_emergency_stopped = True` and disarms the robot. All subsequent motion commands are rejected with an explicit error unless `clear_emergency_stop()` is called first and the robot is re-armed.
- **Verification:** Unit tests `test_boot_in_disarmed_state`, `test_motion_blocked_when_disarmed`, and `test_emergency_stop_lockout` in `tests/hardware/test_actuator_safety.py`. Verified live via `/api/robot/forward` returning HTTP 400.

### BUG-02: Missing Robot Safety Control Endpoints in Core API
- **Severity:** **CRITICAL**
- **Affected File:** `apps/api/robot_api.py`
- **Root Cause:** The FastAPI robot router only exposed directional endpoints (`/forward`, `/backward`) without `/arm`, `/disarm`, or `/clear_estop`. Clients had no way to clear a latched emergency stop or safely arm the system via REST.
- **Fix Applied:** Added `/api/robot/arm`, `/api/robot/disarm`, and `/api/robot/clear_estop` endpoints with proper HTTP status codes and state reporting.
- **Verification:** Live curl tests and automated API integration tests in `tests/unit/test_core.py`.

### BUG-03: Python 3.14 picamera2 Extension Failure Causing Camera Fallback
- **Severity:** **CRITICAL**
- **Affected File:** `apps/vision/service.py`
- **Root Cause:** The system's installed `python3-picamera2` package was compiled against Python 3.13 (`_libcamera.cpython-313.so`), failing to import under Python 3.14. The vision service caught the `ImportError` and immediately dropped into simulation mode, completely ignoring the connected physical Camera Module 3.
- **Fix Applied:** Implemented native subprocess integration with `/usr/bin/rpicam-still` and `/usr/bin/rpicam-jpeg`. When `picamera2` C-bindings fail, the service automatically detects the native ARM64 `rpicam-still` binary and executes high-speed capture.
- **Verification:** Test `test_hardware_rpicam_capture_if_available` in `tests/vision/test_vision.py` passes and captures an authentic 36.8 KB JPEG frame from the physical IMX708 sensor.

---

## 2. High Severity Defects

### BUG-04: Expired Gradio Voice Cloning Share URL Resulting in Unhandled Failures
- **Severity:** **HIGH**
- **Affected File:** `apps/voice/gradio_tts.py`
- **Root Cause:** The user-provided voice cloning URL (`https://13f7044a4e78090fd2.gradio.live/`) had expired (returning HTTP 404). Without proper client abstraction, voice synthesis attempts raised unhandled connection exceptions.
- **Fix Applied:** Built `GradioVoiceCloner` wrapping `gradio_client.Client`. It dynamically queries `client.view_api()`, caches synthesized phrases using SHA256 hashes in `~/.cache/jarvis_voice_cache/`, validates audio file headers (WAV/MP3/RIFF), and catches network/HTTP errors to seamlessly fall back to local TextToSpeech.
- **Verification:** 6 unit tests in `tests/voice/test_gradio_tts.py` all passing. Verified clean synthesis via fallback engine when URL is unreachable.

### BUG-05: Missing Serial Module Import Guard Breaking Simulation & Test Suite
- **Severity:** **HIGH**
- **Affected File:** `hardware/esp32/serial_comm.py`
- **Root Cause:** `import serial` occurred at the top level of `serial_comm.py`. When running on machines or environments without `pyserial`, importing the robot controller crashed with `ModuleNotFoundError`, which in turn caused FastAPI's `_include()` to skip the entire robot router (returning 405 Method Not Allowed).
- **Fix Applied:** Moved `import serial as _serial` inside the non-simulated hardware connection branch. Installed `pyserial 3.5` in the environment for physical UART support.
- **Verification:** `tests/unit/test_brain.py` and `tests/unit/test_core.py` pass cleanly.

### BUG-06: Database Relative Path Failure Under Systemd Service
- **Severity:** **HIGH**
- **Affected File:** `memory/long_term/database.py`, `services/jarvis-core.service`, `.env`
- **Root Cause:** `_db_path` defaulted to relative `"jarvis_memory.db"`, and `.env` contained hardcoded `/home/pi/jarvis-os/jarvis_memory.db` copied from an example template. When the service ran under user `roshan`, SQLite failed with `"ERROR: unable to open database file"`.
- **Fix Applied:** Updated `database.py` to calculate an absolute path relative to `__file__`, corrected `services/jarvis-core.service` to run as user `roshan` with `WorkingDirectory=/home/roshan/.gemini/antigravity/scratch/jarvis-os`, and updated `.env` paths.
- **Verification:** `curl http://localhost:8000/api/health` reports `"db": "OK"`.

### BUG-07: Unframed ESP32 Serial Protocol Lacking Communication Watchdog
- **Severity:** **HIGH**
- **Affected File:** `hardware/esp32/serial_comm.py`, `hardware/esp32/firmware/esp32_robot_controller.ino`
- **Root Cause:** Previous serial communication transmitted raw strings without framing, sequence numbers, or checksums. A line drop could cause corrupted motor speed commands or missing emergency stops.
- **Fix Applied:** Implemented robust `$CMD:<seq>:<cmd>*<crc>` packet framing with CRC8 checksumming in Python, and authored the corresponding Arduino C++ firmware sketch featuring a 500ms safety watchdog that automatically cuts all motor PWM if packets stop.
- **Verification:** 8 protocol tests in `tests/hardware/test_esp32_protocol.py` all passing.

---

## 3. Medium Severity Defects

### BUG-08: Frontend/Backend Memory Search Query Parameter Mismatch
- **Severity:** **MEDIUM**
- **Affected File:** `apps/api/memory_api.py`, `apps/dashboard/static/index.html`
- **Root Cause:** In `index.html`, the memory search UI called `/api/memory/search?query=...`, but `memory_api.py` only accepted `category: str = None`. FastAPI discarded the search term, resulting in empty or untargeted memory searches.
- **Fix Applied:** Updated `search_memory(query: str = "", category: Optional[str] = None, limit: int = 20)` in `apps/api/memory_api.py` to accept and properly pass keyword arguments to `db.search(query=query, category=category)`.
- **Verification:** End-to-end memory store and search verified live via REST API.

### BUG-09: Hardcoded Sensor Initialization Bypassing hardware.yaml Configuration
- **Severity:** **MEDIUM**
- **Affected File:** `hardware/sensors/sensor_manager.py`
- **Root Cause:** `SensorManager._initialize_sensors()` used hardcoded pins and addresses rather than reading settings defined in `config/hardware.yaml`.
- **Fix Applied:** Modified `_initialize_sensors()` to inspect `config.get("hardware", {}).get("sensors", {})` and apply configured I2C buses, hex addresses, and GPIO pins.
- **Verification:** `test_sensor_manager_initialization` in `tests/hardware/test_sensors.py`.

### BUG-10: System Diagnostic Metric Key Discrepancy
- **Severity:** **MEDIUM**
- **Affected File:** `hardware/raspberry_pi/rpi_info.py`, `apps/terminal/cli.py`
- **Root Cause:** `rpi_info.py` returned keys `temp_c`, `ram_used_mb`, `ram_total_mb`, `disk_pct`, while `cli.py` expected `cpu_temp_c`, `memory_used_mb`, `memory_total_mb`, `disk_used_percent`. All metrics displayed as 0 or N/A in the CLI.
- **Fix Applied:** Added standardized metric aliases in `rpi_info.py` supporting both conventions.
- **Verification:** `test_system_status_metric_aliases` in `tests/unit/test_diagnostics.py` and live `jarvis --status` execution.

---

## 4. Low Severity Defects

### BUG-11: Temporary File Resource Leak in Code Runner Tool
- **Severity:** **LOW**
- **Affected File:** `ai/tools/executor.py`
- **Root Cause:** `_tool_run_code()` created temporary files via `NamedTemporaryFile(delete=False)` but did not delete them in a `finally` block if Python execution timed out or failed.
- **Fix Applied:** Wrapped temporary script execution in `try...finally` with explicit `os.remove(tmp_path)`.
- **Verification:** `test_run_code` in `tests/unit/test_brain.py`.

### BUG-12: Escape Sequence Warning in Terminal CLI Banner
- **Severity:** **LOW**
- **Affected File:** `apps/terminal/cli.py`
- **Root Cause:** ASCII art banner in `cli.py` used string literal with unescaped backslashes, triggering Python 3.14 `SyntaxWarning`.
- **Fix Applied:** Converted the banner string into a raw format string (`rf"""..."""`).
- **Verification:** Zero syntax warnings emitted during CLI startup.
