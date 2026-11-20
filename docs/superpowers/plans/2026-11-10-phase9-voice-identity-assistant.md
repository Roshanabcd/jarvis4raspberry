# JARVIS OS — Phase 9 Voice Assistant, Face Identity & Unified AI Interaction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform JARVIS OS into a coherent, voice-controlled AI assistant integrating real ReSpeaker microphone capture, adaptive VAD, speech recognition, local AI brain reasoning, neural TTS speech output, facial recognition identity, role-based governance, and voice-controlled desktop/Apps Center automation.

**Architecture:** A single authoritative voice pipeline where audio capture, wake-word detection, and VAD run without competing device locks. Recognized speech is paired with active facial biometric session context (`ADMIN`, `USER`, `GUEST`) and dispatched to the unified `JARVISBrain`. Audio synthesis supports instant barge-in interruption, while permissions and dangerous actions are strictly enforced with cryptographic PIN confirmation.

**Tech Stack:** Python 3.14 (ARM64), PipeWire 1.4.2 / WirePlumber, Seeed ReSpeaker Lite USB 2-Mic array, FastAPI, OpenCV Zoo (YuNet/SFace), Ollama (`llama3.2:1b`, `qwen3.5:4b`, `moondream:latest`), Edge-TTS / OmniVoice, HTML5/CSS/JavaScript.

**Spec:** User Phase 9 Master Prompt & `PHASE9_VOICE_ARCHITECTURE_AUDIT.md`.

## Global Constraints
- Target hardware: Raspberry Pi 5 (8 GB RAM), Debian 13 Trixie, ARM64 / aarch64.
- Exclusively single camera owner (`jarvis-camera.service` on port 8082 via Picamera2).
- Exclusively single microphone owner (`jarvis-voice.service` via PipeWire `pw-record`).
- Zero fake simulations or mocked hardware claims in production paths.
- Localhost only (`127.0.0.1`). Zero public network binding.
- Zero conversational privilege escalation ("make me admin" must be rejected).
- Sensitive admin operations require verified cryptographic PIN.
- Planned applications in Apps Center must be truthfully blocked with HTTP 400.

## Review Focus
1. User speaks while TTS is playing → Audio must halt immediately (barge-in) and switch to listening.
2. User without enrolled face uses voice assistant → Defaults safely to GUEST role without access to private files or administrative settings.
3. Voice command attempts dangerous terminal command (e.g. `rm -rf`) → Security gate intercepts and requires confirmation.
4. Voice command requests planned app (`"open document qa"`) → System truthfully explains that the app is planned and not yet available.
5. PipeWire ReSpeaker disconnected or reconnecting → Voice pipeline detects device state and recovers without crashing backend daemon.

---

### Task 1: Unified Voice & Identity Session Engine

**Files:**
- Create: `apps/voice/session_manager.py`
- Modify: `apps/api/voice_api.py`
- Test: `tests/unit/test_phase9_voice_and_identity.py`

**Interfaces:**
- Consumes: `tools.identity.user_manager.user_manager`, `tools.vision.camera_manager.camera_manager`
- Produces: `VoiceSessionManager.get_active_session() -> VoiceSession`, `VoiceSessionManager.identify_speaker_from_camera() -> Dict[str, Any]`

- [ ] **Step 1: Write unit tests for VoiceSessionManager**
- [ ] **Step 2: Run test to verify failure**
- [ ] **Step 3: Implement `apps/voice/session_manager.py`**
  - Define `VoiceSession` model with `session_id`, `user_id`, `display_name`, `role`, `confidence`, `created_at`, `expires_at`.
  - Implement face recognition binding: capture image from `http://127.0.0.1:8082/api/snapshot` and identify user via `user_manager.identify_user_from_image`.
  - Default unrecognized faces or camera failures safely to `GUEST`.
- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Commit task changes**

---

### Task 2: Authoritative Voice Pipeline & Barge-In State Machine

**Files:**
- Modify: `apps/voice/wake_word_engine.py`
- Modify: `apps/voice/service.py`
- Modify: `apps/voice/stt.py`
- Modify: `apps/voice/speech_manager.py`
- Test: `tests/unit/test_phase9_voice_and_identity.py`

**Interfaces:**
- Consumes: `SpeechOutputManager.stop()`, `SpeechToText.transcribe()`, `PipeWire`
- Produces: `WakeWordEngine.barge_in()`, `WakeWordEngine.get_status()`, `SpeechToText.set_language()`

- [ ] **Step 1: Write unit tests for barge-in and state transitions**
- [ ] **Step 2: Run test to verify failure**
- [ ] **Step 3: Implement barge-in interruption & dynamic recovery**
  - Implement `barge_in()` terminating current `pw-play` subprocess immediately.
  - Implement multi-language preparation in `SpeechToText` (`en-US`, `hi-IN`, `ne-NP`).
  - Add device disconnect and recovery detection in `WakeWordEngine`.
- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Commit task changes**

---

### Task 3: Permission-Governed Voice Intent & Apps Center Routing

**Files:**
- Modify: `ai/brain.py`
- Modify: `ai/local_engine.py`
- Modify: `apps/voice/service.py`
- Test: `tests/unit/test_phase9_voice_and_identity.py`

**Interfaces:**
- Consumes: `app_registry`, `apps_permissions`, `VoiceSessionManager`
- Produces: `JARVISBrain.chat(..., session_context=...)`, `LocalIntelligenceEngine.execute_voice_command()`

- [ ] **Step 1: Write unit tests for voice intent permissions & Apps Center routing**
- [ ] **Step 2: Run test to verify failure**
- [ ] **Step 3: Implement voice intent routing with role checks**
  - Block planned applications with truthful roadmap responses.
  - Reject conversational privilege escalation attempts.
  - Integrate desktop application opening (`Firefox`, `Chrome`, `VS Code`, `Antigravity`).
  - Require PIN verification for administrative actions.
- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Commit task changes**

---

### Task 4: Interactive Desktop Voice Assistant UI & Telemetry HUD

**Files:**
- Modify: `apps/dashboard/static/index.html`
- Test: Manual UI inspection & DOM validation tests

**Interfaces:**
- Consumes: `/api/voice/status`, `/api/voice/session`, `/api/voice/interrupt`
- Produces: Reactive visual status pill, wave animation, transcript bubble, push-to-talk, interrupt button

- [ ] **Step 1: Update `apps/dashboard/static/index.html`**
  - Add 12-state visual ring indicator with real-time text label.
  - Add Active User Identity Pill (`👤 Roshan (USER)` / `👤 Guest`).
  - Add instant `[⏹️ Interrupt]` barge-in button.
  - Add `[🎤 Push-to-Talk]` manual trigger button.
  - Add real-time transcript and response display.
- [ ] **Step 2: Verify responsive rendering on 1360×768 resolution**
- [ ] **Step 3: Commit task changes**

---

### Task 5: Comprehensive 27-Item Automated Test Suite & Regression Verification

**Files:**
- Create: `tests/unit/test_phase9_voice_and_identity.py`
- Test: Full monorepo unit test suites (Phase 7, 7.1, 8, 9)

- [ ] **Step 1: Author 27 automated test cases covering all Phase 9 requirements**
- [ ] **Step 2: Run Phase 9 test suite and confirm 27/27 PASS**
- [ ] **Step 3: Run Phase 7 & 7.1 camera regression suite (25/25 PASS)**
- [ ] **Step 4: Run Phase 8 Apps Center test suite (25/25 PASS)**
- [ ] **Step 5: Commit task changes**

---

### Task 6: Documentation, Physical Hardware Acceptance & Final Handoff

**Files:**
- Create: `PHASE9_VOICE_ARCHITECTURE.md`
- Create: `PHASE9_VOICE_IDENTITY_IMPLEMENTATION_REPORT.md`
- Modify: `tasks.md`

- [ ] **Step 1: Author `PHASE9_VOICE_ARCHITECTURE.md` developer guide**
- [ ] **Step 2: Author `PHASE9_VOICE_IDENTITY_IMPLEMENTATION_REPORT.md` with explicit "MY NEXT MANUAL TESTS"**
- [ ] **Step 3: Verify all daemons and restart `jarvis-voice.service` and uvicorn**
- [ ] **Step 4: Final atomic git commit**
