# JARVIS UI Upgrade: Phase 0 Repository Audit (AUDIT.md)

**Date:** 2026-11-20  
**Branch:** `feature/jarvis-ui`  
**Baseline Commit:** `3522f43c2f11a1fac50b686f1466f8d3ac929d65`  
**Target Environment:** Raspberry Pi 5 (8 GB RAM, aarch64 Debian 13 trixie) & Laptop  
**Audit Status:** `COMPLETE — AWAITING OPERATOR APPROVAL`

---

## 1. Stack, Versions, and Verified Execution Commands

Every command listed below has been executed in the environment and its real output recorded in `docs/jarvis-ui/evidence/phase-0/`:

### Environment & Toolchain
- **Operating System:** Debian GNU/Linux 13 (trixie) aarch64 (`Linux raspberrypi 6.18.60+rpt-rpi-v8 #1 SMP PREEMPT`)
  - *Evidence:* `docs/jarvis-ui/evidence/phase-0/system_info.txt`
- **Python:** `Python 3.14.6` (system and `./venv/bin/python`)
  - *Evidence:* `docs/jarvis-ui/evidence/phase-0/system_info.txt`
- **Node.js & npm:** Node `v26.13.1`, npm `12.2.0`
  - *Evidence:* `docs/jarvis-ui/evidence/phase-0/system_info.txt`
- **Frontend Stack:** Vanilla HTML5, CSS3 Custom Properties, and modular ES JavaScript (`apps/dashboard/static/index.html`, `active-desktop.js`, `background-tasks.js`, `provider-settings.js`). No frontend bundler or React in the existing production dashboard.
- **Backend Stack:** FastAPI `0.141.1`, Uvicorn, asyncio, aiohttp `3.14.5`, SQLite3, PipeWire audio (`pw-play`).

### Commands & Verified Results
- **Install Python Dependencies:**
  ```bash
  ./venv/bin/pip install -e .
  ```
  *(Status: 28+ packages active in venv; see `docs/jarvis-ui/evidence/phase-0/pip_list.txt`)*
- **Install Frontend Dependencies:**
  ```bash
  npm install
  ```
  *(Status: `playwright@1.65.1`, `windsurf-agent-cli@1.2.2` installed; see `docs/jarvis-ui/evidence/phase-0/npm_list.txt`)*
- **Run Backend Core:**
  ```bash
  ./venv/bin/python -m uvicorn apps.core.main:app --host 127.0.0.1 --port 8000
  ```
- **Run Voice Service:**
  ```bash
  ./scripts/jarvis-run voice
  # or systemd: systemctl --user start jarvis-voice.service
  ```
- **Run Frontend Unit Tests:**
  ```bash
  npm run test:desktop
  ```
  *Result:* **63 passed, 0 failed in 637.9ms** (`docs/jarvis-ui/evidence/phase-0/npm_test_desktop.txt`).
- **Run Python Unit Test Suite:**
  ```bash
  ./venv/bin/pytest tests/unit/ -q
  ```
  *Result:* **596 passed, 34 failed, 1 warning in 326.62s** (`docs/jarvis-ui/evidence/phase-0/pytest_unit.txt`).

---

## 2. Architecture Map

### Entry Points
- **Backend Server:** `apps/core/main.py` (FastAPI bootstrap, lifespan lifecycle, signal handling)
- **App Factory:** `apps/core/app_factory.py:create_app()` (modular router mounting, CORS, static file mount)
- **Service daemons:** `services/jarvis-core.service`, `services/jarvis-voice.service`
- **Script launcher:** `scripts/jarvis-run`

### Static Frontend Mount
- Route: `/` mounts `apps/dashboard/static/` via FastAPI `StaticFiles(directory=static_dir, html=True)`.
- Main Dashboard: `apps/dashboard/static/index.html` (7,855 lines, 21 tabs).
- Client Scripts: `active-desktop.js`, `background-tasks.js`, `provider-settings.js`.

### API Routes & Endpoints
Mounted via `apps/core/app_factory.py`:
1. `/` — Core health and root router (`apps.api.router`)
2. `/api/robot` — Actuators, arm/disarm, emergency stop, servos, motors (`apps.api.robot_api`)
3. `/api/memory` — Semantic memory query, facts, conversation history (`apps.api.memory_api`)
4. `/api/voice` — Speech output status, speech jobs, test tone, audio serving (`apps.api.voice_api`)
5. `/api/omnivoice` — Cloned voice status, HF space registration (`apps.api.omnivoice_api`)
6. `/api/vision` — Camera frames, YOLOv8 object detection, face recognition (`apps.api.vision_api`)
7. `/api/sensors` — I2C/SPI telemetry, temperature, humidity (`apps.api.sensors_api`)
8. `/api/active-desktop` — Screen capture, active desktop sessions (`apps.api.active_desktop_api`)
9. `/api/chat` — Conversational AI, SSE stream, model selection (`apps.api.chat_api`)
10. `/api/task-jobs` — Background async tasks (`apps.api.task_jobs_api`)
11. `/api/logs` — Security and system audit events (`apps.api.logs_api`)
12. `/api/settings` — Configuration management, provider keys (`apps.api.settings_api`)
13. `/api/tools` — Tool registry and permissions (`apps.api.tools_api`)
14. `/api/scheduler` — Cron and scheduled automations (`apps.api.scheduler_api`)
15. `/api/health` — Subsystem health checks (`apps.api.health_api`)
16. `/api/diagnostics` — Hardware diagnostics (`apps.api.diagnostics_api`)
17. `/api/desktop` — X11 window management, app launcher (`apps.api.desktop_api`)
18. `/api/terminal` — Sandboxed terminal execution (`apps.api.terminal_api`)
19. `/api/identity` — User authentication, PIN verification, admin sessions (`apps.api.identity_api`)
20. `/api/apps-center` — Modular app store and permissions (`apps.api.apps_center_api`)
21. `/api/browser_media` — Browser automation and media playback (`apps.api.browser_media_api`)
22. `/api/agents` — Multi-agent orchestration and task queue (`apps.api.agent_orchestrator_api`)
23. `/api/developer` — Developer Hub, worktrees, coding agent runner (`apps.api.hybrid_developer_api`)
24. `/api/youtube` — Video indexing, chapter summaries, Q&A (`apps.api.youtube_api`)
25. `/api/research` — Autonomous AI research assistant (`apps.api.research_api`)
26. `/api/computer` — Computer use, OCR, mouse/keyboard control (`apps.api.computer_api`)
27. `/ws` — WebSocket real-time telemetry (`apps.api.websocket_api`)

### Streaming Channels
- **Chat SSE:** `GET /api/chat/stream?request_id=...` (streams tokens, status updates, tool outputs)
- **Developer Hub SSE:** `GET /api/developer/events` (streams worktree status and agent progress)
- **WebSocket:** `/ws` (telemetry broadcast)

---

## 3. Voice Pipeline & Audio Architecture

### STT (Speech-To-Text)
- **Engine:** `apps/voice/stt.py` using `speech_recognition` library.
- **Wake Word Engine:** `apps/voice/wake_word_engine.py` (listens for wake phrase "Hey Jarvis" / "Jarvis").
- **Hardware Management:** Single microphone owner enforced by `jarvis-voice.service`.

### TTS (Text-To-Speech)
- **Primary Voice:** OmniVoice dynamic registration (`apps/voice/gradio_tts.py` connecting to Hugging Face Space or Colab with reference audio `myvoice.wav`).
- **Neural Fallback:** `edge-tts` (generates high-quality MP3 audio staged in `data/audio_stage/`).
- **Local Fallback:** `espeak` / `pyttsx3` for offline synthesis.
- **Audio Output Routing:**
  - Physical Speaker: PipeWire `pw-play` on the Raspberry Pi host.
  - Browser Playback: Staged audio served via HTTP at `/api/voice/audio/{audio_id}` for HTML5 `<audio>` playback.

### Viseme/Phoneme Timing vs Raw Audio
- **Phoneme/Viseme Stream:** Not exposed by `edge-tts`, `espeak`, or `pw-play`.
- **Frontend Audio Access:** The browser plays the audio file directly from `/api/voice/audio/{audio_id}`.
- **Lip-Sync Solution:** Confirmed **Tier 2: Audio-reactive mouth animation** using Web Audio API `AudioContext` and `AnalyserNode` connected to the playing `<audio>` element. Amplitude and frequency bins drive real-time mouth openness.
- **Naming Rule:** Labeled **audio-reactive**, never *phoneme lip-sync*.

---

## 4. AI Providers & Agent Orchestration

### Configured Providers & Status
Tested via `scripts/check_ai_providers.py` (see `docs/jarvis-ui/evidence/phase-0/ai_providers.json`):
- `nvidia`: Enabled, API key configured in `.env` (Model: `nvidia/nemotron-3.5-bolt-e4b`). Status: Available.
- `openrouter`: Enabled, API key configured in `.env` (Model: `openrouter/free`). Status: Available.
- `openai`: Enabled, missing API key in `.env`.
- `gemini`: Enabled, missing API key in `.env`.
- `anthropic`: Enabled, missing API key in `.env`.
- `groq`: Enabled, missing API key in `.env`.
- `together`: Enabled, missing API key in `.env`.
- `ollama` (Local LLM): Operational on `http://127.0.0.1:11434` with `moondream:latest`, `llama3.2:1b`, and `qwen3.5:4b`.

### Agent Orchestration & Worktree Isolation
- **Agent Registry:** `ai/agents/task_orchestrator.py` & `tools/hybrid-jarvis-developer/`.
- **Worktree Isolation:** `tools/hybrid-jarvis-developer/worktrees.py` isolates concurrent coding agents inside `.worktrees/{task_id}` branching off `hybrid/{task_id}`. Zero changes leak to `main` without explicit human review via `awaiting_human_review`.

---

## 5. Storage & Databases

- **`data/developer_orchestration.sqlite3`:** Developer Hub tasks, agent worktree executions.
- **`data/research_assistant.sqlite3`:** Autonomous AI research queries, evidence records, citations.
- **`data/youtube_notes.sqlite3`:** YouTube video transcripts, chapter summaries, Q&A records.
- **`jarvis_memory.db`:** Short-term and long-term conversation memory and embeddings.
- **`config/config.yaml` & `config/models.yaml`:** System and model configuration managed by thread-safe `ConfigManager`.
- **`tools/identity/user_manager.py`:** Local PIN-authenticated user accounts (`admin` / `guest`).

---

## 6. Robot Backend & Safety Limits

- **Controller:** `tools/robotics/controller.py` & `apps/api/robot_api.py`.
- **Safety Guarantees:**
  - Actuators boot in **DISARMED** state (`self.armed = False`).
  - Emergency stop immediately cuts motor power and latches locked state.
  - Hard speed limits: Safe clamping (default 50, max 100).
  - Channel & angle bounds: PCA9685 servo channels 0-15 validated within 0-180°.
  - Simulation Mode: Active when physical hardware is absent; clearly rendered in UI.

---

## 7. Baseline Test Results

- **Frontend Desktop Tests (`npm run test:desktop`):**
  - **63 Passed, 0 Failed** (Duration: 637.9ms)
  - Coverage: Active desktop session, background tasks, developer hub, PIN authentication, provider settings, real-time chat, UI feedback, voice jobs, YouTube AI.
- **Python Unit Tests (`pytest tests/unit/ -q`):**
  - **596 Passed, 34 Failed** (Duration: 326.62s)
  - Failures relate to mock expectations in legacy tests (e.g., PCA9685 simulation fixture in test_core.py, Ollama mock in test_ai_system.py).
- **Browser Verification (`npm run test:browser`):**
  - 1 failure due to legacy button text selector `button:has-text("Save Keys to .env")` (button in HTML is labeled `💾 Save API keys`).

---

## 8. Integration Capability Matrix

| Tool / Provider | Installed | Version | Auth Status | Class | Integration Notes |
|---|---|---|---|---|---|
| **Codex** | `/home/roshan/.local/bin/codex` | `0.167.1` | Keyring authenticated | **Class B** | **PROHIBITED:** Quota exhausted per user rule 1.14. Must not be invoked. |
| **Antigravity** | `/home/roshan/.local/bin/agy` | `1.5.13` | Active CLI | **Class B** | Primary development and orchestration agent. |
| **Gemini** | CLI `/home/roshan/.npm-global/bin/gemini` & SDK | `0.68.0` | CLI OAuth missing; SDK adapter present | **Class A (SDK)** | Python adapter ready; awaiting API key in `.env`. |
| **Copilot** | `/home/roshan/.local/bin/copilot` + `gh` | `1.0.112` / gh `2.46.0` | Authenticated (`Roshanabcd`) | **Class B** | CLI available for task dispatch. |
| **OpenRouter** | `ai/providers/base.py` | Cloud API | API key active in `.env` | **Class A** | Fully functional cloud inference route. |
| **NVIDIA NIM** | `ai/providers/base.py` | Cloud API | API key active in `.env` | **Class A** | Fully functional cloud inference route. |
| **Cline** | `/home/roshan/.npm-global/bin/cline` | `3.0.74` | IDE CLI | **Class C** | IDE-only; no programmatic backend API. |
| **Ollama (Local)**| `/home/roshan/.local/bin/ollama` | `0.40.4` | Localhost (no auth required) | **Class A** | HTTP API on `127.0.0.1:11434`. Models: `moondream`, `llama3.2:1b`, `qwen3.5:4b`. |

---

## 9. Risks

1. **Raspberry Pi Resource Limits:** The target hardware is a Raspberry Pi 5 (8 GB RAM, ARM64) and laptop. Complex 3D shaders or unoptimized VRM models could cause FPS drops.
2. **Audio Feedback Loop:** Browser microphone input must be gated/suppressed while assistant TTS audio is actively playing to prevent acoustic echoes.
3. **Vanilla JS vs. React Architecture:** The Gemini prototype (`jarvis_os_futuristic_ai_interface.tsx`) is React/TSX, whereas the production JARVIS dashboard is Vanilla HTML5/CSS/JavaScript. Porting must either introduce a lightweight Vite build or cleanly transpile/render the components into the native frontend architecture.
4. **Codex Quota:** Explicitly blocked from calling OpenAI Codex CLI.

---

## 10. Confirmation of Avatar Plan

1. **Frontend Architecture Discovery:** The existing codebase does not use React; it is a lightweight Vanilla JS single-page application.
2. **Dual-Renderer Avatar Architecture:**
   - **3D VRM Renderer (`Vrm3D`):** Three.js + `@pixiv/three-vrm` (VRM 1.0) loaded dynamically when VRM assets are supplied.
   - **2D Digital Human Renderer (`Svg2D`):** High-fidelity SVG digital humans ARIA (female) and ATLAS (male) directly adapted from `jarvis_os_futuristic_ai_interface.tsx`. Features: 7 states, 5 mouth shapes, eye blinking, gaze tracking, holographic scanlines, and particle glow. Runs at 60 FPS on any hardware without external asset dependencies.
3. **Lip-Sync Tier:** Tier 2 (Audio-reactive Web Audio analyser) driving mouth openness during speech.

---

## 11. Proposed Amendments to PLAN.md

- **Phase 1:** Add Playwright smoke suite covering the 21 existing dashboard tabs and mount the new UI behind a parallel route (`/futuristic/`) so the existing `/` dashboard remains 100% accessible.
- **Phase 2 & 5:** Port the design tokens and ARIA/ATLAS avatar system from `docs/jarvis-ui/references/jarvis_os_futuristic_ai_interface.tsx` into a modular, responsive frontend package.
- **Phase 5:** Support both 2D SVG digital humans (ARIA & ATLAS) and 3D VRM 1.0 models.
