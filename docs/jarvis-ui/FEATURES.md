# JARVIS OS: Existing User-Visible Feature Checklist (FEATURES.md)

This document serves as the **regression oracle** for the JARVIS UI upgrade on branch `feature/jarvis-ui`.  
**Rule:** Never remove, disable, downgrade, or replace working functionality. The new UI ships behind a parallel route or feature flag (`/futuristic/`); the existing UI stays reachable.

---

## Feature Checklist & Verification Procedures

| # | Feature / Destination | Tab ID | Backend Endpoint / Route | Verification Procedure | Verified Baseline |
|---|---|---|---|---|---|
| 1 | **Home Control Center** | `tab-home` | `/api/health`, `/api/sensors` | Click "Home" in nav; verify CPU, RAM, Disk, Temp, and Network cards update with real values. | [x] |
| 2 | **Apps Center** | `tab-apps` | `/api/apps-center/list` | Click "Apps" in nav; verify app registry displays installed apps with category filters. | [x] |
| 3 | **Conversational AI Chat** | `tab-chat` | `/api/chat`, `/api/chat/stream` | Send message in chat input; verify streaming text tokens and model indicator appear. | [x] |
| 4 | **Voice Assistant & Speech**| `tab-voice` | `/api/voice`, `/api/voice/status` | Verify microphone status indicator, speech reply queue, and test tone button. | [x] |
| 5 | **AI Studio** | `tab-aistudio` | `/api/chat/models` | Test prompt generation in AI studio with local Ollama models. | [x] |
| 6 | **Vision & Face Recognition**| `tab-vision`| `/api/vision/capture` | Click capture frame; verify single camera owner serves snapshot and object bounding boxes. | [x] |
| 7 | **Robot & Actuator Control**| `tab-robot` | `/api/robot/status`, `/api/robot/emergency_stop` | Verify actuators boot DISARMED; test Emergency Stop button latches safely. | [x] |
| 8 | **Environmental Sensors** | `tab-sensors`| `/api/sensors/data` | Click refresh; verify temperature and I2C sensor readouts update. | [x] |
| 9 | **Memory & Semantic Search**| `tab-memory` | `/api/memory/search` | Enter query in memory search; verify retrieved semantic conversation facts display. | [x] |
| 10 | **Automations & Cron** | `tab-automations`| `/api/scheduler/jobs` | Verify scheduled background automation list and trigger times. | [x] |
| 11 | **Tool Registry** | `tab-tools` | `/api/tools/list` | Verify registered system, identity, and robotic tools with permission toggles. | [x] |
| 12 | **Cloud AI Integrations** | `tab-integrations`| `/api/settings/integrations` | Verify password-masked API keys for 7 providers; save requires admin PIN. | [x] |
| 13 | **System Hardware Specs** | `tab-system` | `/api/health/system` | Verify OS version, kernel (`6.18.60`), and hardware architecture render accurately. | [x] |
| 14 | **Audit & Security Logs** | `tab-logs` | `/api/logs/recent` | Verify security audit entries and command execution timestamps render. | [x] |
| 15 | **Active Desktop Launcher**| `tab-desktop`| `/api/active-desktop/status` | Verify running X11 window hierarchy and application launcher shortcuts. | [x] |
| 16 | **Computer Use Automation** | `tab-computer`| `/api/computer/status` | Verify screen preview, OCR bounding boxes, and action plan controls. | [x] |
| 17 | **AI Agents Orchestrator** | `tab-agents` | `/api/agents/roster` | Verify multi-agent roster cards, task status, and execution timeline. | [x] |
| 18 | **Developer Hub** | `tab-developer`| `/api/developer/status` | Verify Git worktree list, task queue, and agent CLI runner panel. | [x] |
| 19 | **YouTube AI Assistant** | `tab-youtube` | `/api/youtube/index` | Paste YouTube URL; verify video indexing, transcript tabs, and Q&A interface. | [x] |
| 20 | **Research Assistant** | `tab-research`| `/api/research/query` | Submit research prompt; verify evidence linking, web citations, and synthesis. | [x] |
| 21 | **Settings & Admin Profile** | `tab-settings`| `/api/settings/profile` | Verify admin PIN entry, theme selection, and system backup export. | [x] |

---

## Automated Smoke Verification Suite
Automatable items are verified via:
- `npm run test:desktop` (`tests/frontend/*.test.cjs`)
- `tests/browser/browser_verification.cjs` (Playwright Chromium)
- `pytest tests/unit/`
