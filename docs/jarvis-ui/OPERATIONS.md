# JARVIS OS: Operations & Deployment Guide (OPERATIONS.md)

**Branch:** `feature/jarvis-ui`  
**Route:** `http://127.0.0.1:8000/futuristic/`  
**Safe Delivery Oracle:** Baseline UI remains fully active at `http://127.0.0.1:8000/`  

---

## 1. System Architecture & Delivery Model

JARVIS OS delivers a futuristic, dark-glassmorphism AI operating system alongside the existing baseline application:
- **Parallel ASGI Mounting:** The upgraded dashboard is served under the `/futuristic/` parallel route by FastAPI (`apps/core/app_factory.py`).
- **Regression Isolation:** The baseline dashboard at `/` is completely untouched and continues to serve existing features as verified in `docs/jarvis-ui/FEATURES.md`.
- **Honest Telemetry:** Zero mock metrics or simulated percentages in production code. Unsupported or disconnected sensors render `Unavailable`.
- **Hardware Safety:** Actuators boot in `DISARMED` status. Motion controls are locked behind Admin PIN verification and immediate physical Emergency Stop latches.

---

## 2. Requirements & Prerequisites

- **Host OS:** Linux (tested on Raspberry Pi 5 Debian 13 aarch64 and Linux x86_64)
- **Python:** Python 3.14+ with local virtual environment (`./venv`)
- **Node.js:** Node.js v20+ / v26+ with npm v10+
- **Audio Subsystem:** PipeWire / PulseAudio / ALSA (`pw-play`, `arecord`)
- **Local AI Provider:** Ollama (`llama3.2:1b`) or configured cloud provider (OpenRouter, NVIDIA NIM, Anthropic)

---

## 3. Installation & Setup

```bash
# 1. Clone repository & switch to feature branch
git checkout feature/jarvis-ui

# 2. Activate Python environment & install backend package
./venv/bin/pip install -e .

# 3. Install frontend testing & accessibility packages
npm install
```

---

## 4. Starting the JARVIS OS Daemon

### A. FastAPI Backend Core (Port 8000)
```bash
./venv/bin/python -m uvicorn apps.core.main:app --host 127.0.0.1 --port 8000 --log-level info
```
Verify backend health:
```bash
curl -s http://127.0.0.1:8000/api/health | jq
```

### B. Background Voice Daemon (Optional for Wake-Word)
```bash
./scripts/jarvis-run voice
# or via user systemd daemon:
systemctl --user start jarvis-voice.service
```

---

## 5. Operating the Futuristic Interface

Open your web browser and navigate to:
```
http://127.0.0.1:8000/futuristic/
```

### Core Destinations:
1. **Dashboard (`#dashboard`):** Real-time hardware telemetry (CPU, RAM, Disk, Temperature, Network), system health chips, and prominent digital human avatar stage.
2. **AI Chat (`#chat`):** Real SSE streaming dialogue with token-by-token output, syntax-highlighted code blocks with one-click copy, stop cancellation, retry/regenerate, search filter, history clearing, and Markdown/JSON export.
3. **Voice Assistant (`#voice`):** Microphone hardware telemetry, push-to-talk, emergency barge-in (< 300ms cancel), live subtitles (`👤 YOU` / `🤖 JARVIS`), tone/mic diagnostics, and audio parameter tuning.
4. **Digital Human Avatar:** Switch between **ARIA** (female holographic assistant) and **ATLAS** (male tactical avatar). Supports 9 emotional/operational states (`idle`, `listening`, `thinking`, `speaking`, `happy`, `concerned`, `error`, `offline`, `muted`), audio-reactive mouth modulation, periodic blinking, and micro-gaze tracking.
5. **AI Agents (`#agents`):** Agent cards with Class A (API), Class B (Headless CLI), and Class C (IDE-only) classifications. Multi-agent dispatch with worktree isolation.
6. **Developer Workspace (`#workspace`):** Real git status, active worktrees list, task diff viewer, and quality gates status.
7. **Secure Terminal (`#terminal`):** Sandboxed shell runner with command history and mandatory confirmation modal for destructive commands (`rm -rf`, `sudo`, `dd`).
8. **Operations Hub (`#tasks`, `#automation`, `#calendar`, `#memory`, `#knowledge`):**
   - **Tasks:** Multi-agent background jobs with cancel/retry and worktree diff viewer.
   - **Automation:** Scheduled workflows supporting timezone expressions (`HH:MM UTC`, `HH:MM America/New_York`) and manual "Trigger Due" execution.
   - **Calendar:** Chronological agenda with interactive timezone switching.
   - **Memory & Knowledge:** SQLite memory explorer with category filters, search, inline editing (`PUT /api/memory/{id}`), and safe deletion.
9. **Integrations & Apps (`#integrations`, `#apps`):** Real provider grid with password-masked keys and Admin PIN protection.
10. **Connected Devices & Safe Robotics (`#devices`, `#sensors`, `#robot`):**
    - **Devices:** Host Pi 5, ESP32-S3 serial bus, camera IMX708, ReSpeaker Lite audio, and I2C bus scan.
    - **Sensors:** BME280, BH1750, VL53L0X, HC-SR04, and HC-SR501 with distinct visual state indicators.
    - **Robot:** Enforced safe disarmed default, simulation labeling, emergency stop latch, PIN-protected arming, velocity limiter, and safety audit log ledger.
11. **Eco & Accessibility Toggles (Header):**
    - **⚡ Eco Mode:** Halts decorative canvas ring spins, throttles avatar FPS, relaxes polling to 10s.
    - **⏸ Reduced Motion:** Suppresses transitions and halts gaze micro-movements.

---

## 6. Verification & Automated Test Suites

Run the full verification suite anytime using the following commands:

```bash
# 1. Frontend Unit Tests (63 tests)
npm run test:desktop

# 2. Phase 1 Smoke Suite (26 regression tests covering all 21 FEATURES.md destinations)
npm run test:smoke

# 3. Phase 2 Shell & Design Suite (9 tests: Axe accessibility, keyboard nav, responsive viewports)
npm run test:shell

# 4. Phase 10 Accessibility & Responsive Suite (10 tests: 4 viewports, Eco mode, Axe AA audit)
node --test tests/browser/phase10_responsive_accessibility.cjs

# 5. Phase 11 Full Verification & Delivery Suite (18-route console sweep, offline transition, secret scan, licenses)
node --test tests/browser/phase11_full_verification.cjs

# 6. Backend ASGI Safe Delivery Mounting
./venv/bin/pytest tests/unit/test_phase1_safe_delivery.py
```

---

## 7. Troubleshooting & Recovery

| Symptom | Cause | Resolution |
|---|---|---|
| `Core: OFFLINE` banner visible | Backend Uvicorn server is stopped or restarted | Start backend: `./venv/bin/python -m uvicorn apps.core.main:app --host 127.0.0.1 --port 8000`. Dashboard will automatically reconnect. |
| Microphone permission denied | Browser blocked audio capture | Click browser URL bar lock icon, allow Microphone permission, and click "Retry Access". |
| Destructive command blocked in terminal | Security intercept activated | An explicit confirmation token modal appears. Confirm execution or cancel to abort. |
| Robot actuation disabled | Safety latch engaged | Actuation requires manual Admin PIN entry to ARM. Emergency Stop can be triggered at any time without a password. |
