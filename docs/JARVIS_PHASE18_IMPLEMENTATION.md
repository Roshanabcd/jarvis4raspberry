# JARVIS OS — Phase 18 Implementation Guide
## Real-World Autonomous AI Assistant: Offline Wake Word, Screen Understanding, Coding Agent Bridge & Safe E-Stop Recovery

### Executive Summary
Phase 18 advances JARVIS OS from verified computer-control automation into a cohesive, production-grade autonomous conversational AI assistant on Raspberry Pi 5 (`aarch64`, 8GB RAM). Building atop Git checkpoint `b124858` and branch `feature/jarvis-ui`, Phase 18 implements:
1. **Offline Acoustic Wake-Word Detection (`openWakeWord` + ONNX Runtime)** running on ARM64 with configurable sensitivity thresholds (low 0.70, medium 0.50, high 0.35) and immediate spoken acknowledgment ("Yes, I'm listening.").
2. **Multimodal Screen Understanding & Root Cause Analysis** integrating Playwright semantic DOM extraction and `pytesseract` OCR to detect runtime errors and formulate actionable remediation plans.
3. **Coding Agent Bridge (`tools/desktop/coding_agent_bridge.py`)** discovering real CLI tools (`agy`, `codex`, `gh`) and dispatching safe repairs via `ReferenceLocalRepairAgent` in authorized workspaces without unsafe permission bypasses.
4. **Persistent Emergency-Stop Recovery & Safety Protocol** utilizing an on-disk lock file (`data/computer_estop.lock`) that survives UI reloads and service restarts, paired with safe recovery via `POST /api/computer/rearm` ("re-arm computer control").
5. **Real-Time Barge-In & Interruption** allowing verbal commands ("stop speaking", "be quiet") and REST calls (`/voice/interrupt`) to instantly halt speech synthesis and release playback leases.

---

### Key Components & Architecture

#### 1. Acoustic Wake-Word Engine (`apps/voice/wake_word_engine.py`)
- **Engine:** `openwakeword` (v0.4.0) with native ARM64 CPU Execution Provider in `onnxruntime` (v1.32.0).
- **Acoustic Model:** `hey_jarvis_v0.1.onnx` pre-bundled in the Python 3.14 virtual environment.
- **Inference Latency:** ~211ms per 1.5s audio chunk on Raspberry Pi 5 CPU.
- **Scoring Pipeline:**
  - 16 kHz 16-bit mono streaming audio fed into acoustic sliding window.
  - Multi-tier classification:
    - Tier A: Acoustic neural inference scoring (`openWakeWord.predict()`). Score threshold default `0.50`.
    - Tier B: Rolling audio boundary evaluation across consecutive frame windows.
    - Tier C: Deterministic regex and Whisper STT fallback for Push-to-Talk or ambiguous speech.
- **State Transition:** Upon wake trigger, engine transitions from `STANDBY_LISTENING` to `WAKE_DETECTED`, speaks `"Yes, I'm listening."` via the audio pipeline, and arms conversational listening.
- **REST Endpoints:**
  - `GET /api/voice/wake_word/config`: Returns active model name, threshold, and noise floor parameters.
  - `POST /api/voice/wake_word/config`: Configures wake threshold (`wake_threshold: float`) and VAD sensitivity.

#### 2. Screen Intelligence & Error Inspection (`tools/desktop/screen_intelligence.py`)
- **DOM Inspection:** Searches visible elements in active Playwright browser sessions for error banners, exception tracebacks, and HTTP status alerts.
- **OCR Inspection:** Captures active desktop window geometry via `xdotool` / `scrot` and extracts text using Tesseract OCR 5.5.0 (`/usr/bin/tesseract`).
- **Error Classifier & Explanation:** Identifies common fault classes (ZeroDivisionError, ConnectionRefused, 404 Not Found, SyntaxError, AssertionError) and provides structured root-cause explanations and suggested code guards.

#### 3. Coding Agent Bridge (`tools/desktop/coding_agent_bridge.py`)
- **Agent Discovery:** Scans system PATH for real CLI tools:
  - Google Antigravity CLI (`agy`) — v1.5.13 discovered at `/home/roshan/.gemini/antigravity/bin/agy`.
  - OpenAI Codex CLI (`codex`) — v0.171.0 discovered at `/home/roshan/miniconda3/bin/codex`.
  - GitHub Copilot CLI (`gh`) — installed at `/usr/bin/gh`.
  - `ReferenceLocalRepairAgent` — local deterministic Python patch engine.
- **Sandboxing Policy:** Enforces approved workspace boundaries (`/home/roshan/.gemini/antigravity/scratch/jarvis-os`).
- **Safety Enforcement:** Blocks unsafe flags such as `--dangerously-skip-permissions` or `--no-sandbox`.
- **Verification:** Automatically executes fast automated pytest verification suites (`test_copilot_adapter.py`) post-repair to validate syntax and test integrity before reporting diffs.

#### 4. Persistent Emergency-Stop Recovery (`tools/desktop/unified_computer_service.py`)
- **Persistent Lock File:** `data/computer_estop.lock` is written atomically upon emergency stop invocation.
- **Persistence Across Restarts:** On daemon startup, `UnifiedComputerService.__init__()` detects `computer_estop.lock` and initializes `_emergency_stopped = True`, ensuring unverified restarts cannot bypass safety locks.
- **Gating:** Any queued or incoming computer control instructions are rejected with:
  `Action blocked: Computer control is currently in EMERGENCY STOP.`
- **Safe Recovery Protocol (`rearm_session`):**
  - Releases all held keyboard keys and mouse buttons via `native_backend.release_all_inputs()`.
  - Purges any pending queued commands to guarantee cancelled actions do NOT auto-resume.
  - Safely deletes `computer_estop.lock`.
  - Sets `_emergency_stopped = False` and `_session_enabled = True`.
  - Exposed via `POST /api/computer/rearm` and natural voice command `"re-arm computer control"`.

#### 5. Real-Time Interruption & Barge-In (`apps/voice/speech_manager.py`)
- **Interruption API:** `POST /api/voice/interrupt` halts active audio player processes (`pw-play`) within <2ms.
- **Conversational Fast Path:** Intent `"stop_speech"` added to `FAST_PATH_INTENTS` in `ai/brain.py` and `ai/local_engine.py`. Verbal phrases ("stop speaking", "be quiet", "shut up", "silence") immediately trigger `speech_manager.stop()`.

---

### Preserved Performance Invariants
1. **Camera CPU Throttling:** The dedicated camera vision daemon on port 8082 maintains client-aware inference throttling. At 0 connected clients, camera remains in `standby_idle` mode at 0.0 FPS and ~3.0%–5.0% instantaneous CPU on Pi 5.
2. **Audio Hardware Integrity:** Dedicated user systemd unit `jarvis-voice.service` retains ALSA capture device ownership on `hw:2,0` (Seeed ReSpeaker Lite), avoiding PipeWire node lock contention.
