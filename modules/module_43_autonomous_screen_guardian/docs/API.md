# REST & WebSocket API Reference — Module 43 (JARVIS Screen Guardian)

Base Prefix: `/api/v1/screen-guardian`  
Standalone HUD: `/screen-guardian`  
Optional Auth Header: `X-JARVIS-Token` (enforced on mutating endpoints when `SCREEN_GUARDIAN_API_TOKEN` is set)

## Health, Metadata & Telemetry

| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/screen-guardian/health` | Module health, OCR availability, version, and contract version |
| `GET` | `/api/v1/screen-guardian/manifest` | Machine-readable `manifest.json` metadata |
| `GET` | `/api/v1/screen-guardian/status` | Full runtime status (monitoring state, OCR engine, agents, counters, telemetry) |
| `GET` | `/api/v1/screen-guardian/telemetry` | Native Linux `/proc` CPU load, RAM, disk, and network counters |

## Screen Monitoring Controls

| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/screen-guardian/monitors` | Lists available displays (`xrandr`/platform detection) and active display server |
| `POST` | `/api/v1/screen-guardian/monitor/start` | Starts monitoring. **Requires** `{"explicit_consent": true}` (returns `403 CONSENT_REQUIRED` otherwise) |
| `POST` | `/api/v1/screen-guardian/monitor/pause` | Pauses active monitoring session |
| `POST` | `/api/v1/screen-guardian/monitor/resume` | Resumes paused monitoring session |
| `POST` | `/api/v1/screen-guardian/monitor/stop` | Immediately stops monitoring and clears active capture session |
| `GET` | `/api/v1/screen-guardian/monitor/preview` | Returns metadata and base64 PNG preview of the most recent in-memory frame |

## OCR, Vision & Error Detection

| Method | Path | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/screen-guardian/analyze` | Analyzes a frame (`image_base64`, `ocr_text_override`, `source_app`, `window_title`, `use_vision_model`) via Tesseract OCR, VisionCoordinator, and ErrorDetectionEngine |
| `GET` | `/api/v1/screen-guardian/ocr/history` | Returns searchable OCR history (`?q=...&limit=50`) |
| `GET` | `/api/v1/screen-guardian/errors` | Lists detected errors (`?status=new|ongoing|resolved`) with deduplication counts |
| `GET` | `/api/v1/screen-guardian/notifications` | Lists generated alerts |
| `POST` | `/api/v1/screen-guardian/notifications/{notification_id}/action` | Performs `view`, `explain`, `prepare_fix`, `dismiss`, or `ignore_similar` |

## Coding Agents & Auto-Repair

| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/screen-guardian/agents` | Real discovery of `agy`, `codex`, `gh copilot`, and `reference_local_agent` |
| `GET` | `/api/v1/screen-guardian/repairs` | Lists all repair jobs with diffs, verification results, and outcomes |
| `POST` | `/api/v1/screen-guardian/repairs` | Creates a repair job (validates workspace boundary, protected paths, and banned CLI flags) |
| `POST` | `/api/v1/screen-guardian/repairs/{repair_id}/approve` | Approves or denies a repair (`decision: "approve" | "deny"`) |
| `POST` | `/api/v1/screen-guardian/repairs/{repair_id}/execute` | Runs the authorized repair, records unified diff, and executes focused verification tests |
| `POST` | `/api/v1/screen-guardian/repairs/{repair_id}/cancel` | Cancels an active or pending repair job and terminates its subprocess |

## Voice, Settings, Logs & WebSocket

| Method | Path | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/screen-guardian/voice/command` | Processes voice commands (`speaker_source` must be `"user_mic"`; rejects screen playback audio) |
| `GET` | `/api/v1/screen-guardian/settings` | Retrieves current runtime and privacy settings |
| `PUT` | `/api/v1/screen-guardian/settings` | Persists settings to SQLite WAL (`capture_interval_sec`, `trusted_workspaces`, `excluded_windows`, etc.) |
| `GET` | `/api/v1/screen-guardian/logs` | Returns chronological audit trail (`?limit=100`) |
| `WS` | `/api/v1/screen-guardian/ws/stream` | Live WebSocket stream emitting `ws.connected`, `error.detected`, and `ws.heartbeat` events |
