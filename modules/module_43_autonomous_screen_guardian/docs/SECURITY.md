# Security & Privacy Architecture — Module 43 (JARVIS Screen Guardian)

## 1. Core Privacy Guarantees (Secure by Default)

Module 43 is designed for continuous desktop awareness **without** covert surveillance or uncontrolled automation.

| Control | Default Value | Enforcement Layer |
| :--- | :--- | :--- |
| Explicit monitoring consent | Required (`consent_confirmed=true`) | `ScreenCaptureService.start()` returns `403 CONSENT_REQUIRED` if missing |
| Auto-start on boot | `false` | `ScreenGuardianConfig.auto_start_on_boot` |
| Raw screenshot persistence | `false` (in-memory only) | `ScreenCaptureService` holds latest preview frame in RAM only |
| Remote vision upload | `false` (local heuristic default) | `VisionCoordinator` blocks remote provider unless explicitly enabled |
| Visible status & persistent stop | Always visible in HUD + `POST /monitor/stop` | Standalone HUD & React dashboard |
| Window & region exclusions | Supported (`excluded_windows`, `excluded_regions`) | Redacted via Pillow black-box mask before OCR/vision |

## 2. Prompt-Injection Defense (Untrusted Screen Data)

Visible screen content (webpages, terminal logs, chat messages, PDFs, error dialogs) is **strictly untrusted data**.

- `ErrorDetectionEngine` scans extracted text for prompt-injection markers (e.g., `"ignore previous instructions"`, `"run rm -rf"`, `"--dangerously-skip-permissions"`, `"execute shell"`, `"curl | bash"`).
- Detected prompt-injection text is flagged (`prompt_injection_detected=true`), sanitized before being passed to any vision or coding-agent prompt, and **never** executed as a shell command or coding-agent directive.
- Voice commands only accept `speaker_source="user_mic"`. Audio coming from screen playback (`speaker_source="system_audio"` or `"unknown"`) is ignored.

## 3. Coding Agent & Repair Safety Boundaries

### Four Permission Modes

1. `observe_only` — Detects and explains errors; blocks all repair execution.
2. `suggest_fix` — Generates diagnosis and suggested fix plans without writing files.
3. `assisted_repair` — Prepares repair jobs and **requires explicit user approval** (`POST /repairs/{id}/approve`) before any file modification or test execution.
4. `trusted_workspace_autopilot` — Permits automated repair **only** inside explicitly configured `trusted_workspaces` directories and still enforces full diff logging, focused test verification, and live cancellation.

### Hard-Blocked CLI Flags

The coding-agent adapter (`backend/adapters/coding_agents.py`) permanently rejects dangerous autonomous bypass flags, including:
- `--dangerously-skip-permissions`
- `--dangerously-bypass-approvals-and-sandbox`
- `--yolo`
- `--no-sandbox`
- `--allow-all-paths`

### Protected System Paths

`AutoRepairEngine` resolves real canonical paths (`Path.resolve()`) and rejects any repair target inside protected OS directories (`/`, `/etc`, `/usr`, `/bin`, `/sbin`, `/boot`, `/root`, `/var`, `/sys`, `/proc`, `/dev`) or outside configured `trusted_workspaces` with HTTP `403`.

## 4. Honest Verification Policy

- A detected error is **never** marked `resolved` simply because a coding agent exited with code `0` or edited a file.
- `AutoRepairEngine` runs focused verification commands via `asyncio.create_subprocess_exec` (no `shell=True`) and records exact stdout/stderr, exit code, and unified diff.
- Only when verification tests actually pass does the repair outcome become `verified_fixed` and the linked error transition to `resolved`. Unverified or failing repairs are honestly recorded as `not_fixed`, `verification_incomplete`, or `execution_failed`.

## 5. Audit Trail & Secret Hygiene

- Every monitoring state change, privacy toggle, notification action, repair creation, approval/denial, cancellation, and test result is logged in SQLite WAL (`audit_logs` table).
- No API keys, tokens, or credentials are committed in source code. External vision keys (e.g., `GEMINI_API_KEY`) are read only from environment variables when remote vision is explicitly opted in.
