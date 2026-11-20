# JARVIS OS Voice Agent & Intelligence Upgrade: Implementation Plan
**Branch:** `feature/jarvis-ui`
**Reference Specs:** `docs/JARVIS_VOICE_SYSTEM_AUDIT.md`, `docs/jarvis-ui/SPEC.md`, `AGENTS.md`

---

## 1. Plan Overview & Objectives
Transform JARVIS OS into a responsive, voice-first digital assistant:
1. **Real Microphone Audio Ingestion:** Fix `listen_once` daemon coordination, add browser `POST /api/voice/transcribe`, and support both physical ReSpeaker Lite and remote browser laptop microphones.
2. **Reliable Wake Word Activation:** Continuous low-resource wake word detection ("Jarvis", "Hey Jarvis") with state machine: Standby -> Wake Detected ("Yes?") -> Command Listening -> Processing -> Speaking -> 15s Follow-up window.
3. **Human-like Neural AI Voice:** Edge Neural TTS (`en-US-AriaNeural` for Aria / female, `en-US-GuyNeural` for Atlas / male) with natural intonation, adjustable speed/volume, and offline fallback.
4. **Speaking AI Character & Lip-Sync:** Integrate SVG digital human renderer (ARIA and ATLAS) with 5 mouth visemes driven by real-time audio playback volume/frequencies.
5. **Character & Voice Studio:** Allow seamless switching between ARIA, ATLAS, and custom characters directly from settings/dashboard with persistent preferences.
6. **Task & Vision Execution by Voice:** Ground spoken dialogue in real tools (CPU/RAM telemetry, process inspection, vision analysis via screen capture and camera).
7. **Accurate Voice Diagnostics & Meaningful Feedback:** Eliminate ambiguous "Voice request finished" message. Display precise status chips ("Listening...", "Transcribing...", "Thinking...", "Speaking...").

---

## 2. Implementation Phases & Schedule

### Phase 1: Complete Voice System Audit & Root Cause Isolation
- **Status:** Verified (Documented in `docs/JARVIS_VOICE_SYSTEM_AUDIT.md`)
- Isolated daemon lock rejection, `control-center.js` string overwrite, missing `/api/voice/transcribe`, and `cloud_tts_enabled` flag.

### Phase 2: Fix Microphone Input & Audio Routing
- **Files Modified:**
  - `apps/voice/service.py`: Update `listen_once` to coordinate with `wake_word_engine` via `send_daemon_command('mute')` / `('unmute')` instead of rejecting with error.
  - `apps/api/voice_api.py`: Add `POST /api/voice/transcribe` endpoint accepting multipart WAV/WebM/OGG audio files for client-side recording.
  - `apps/dashboard/static/index.html`: Update `toggleVoiceRecord()` to support browser `MediaRecorder` + fallback to `/api/voice/listen_once`.
  - `apps/dashboard/static/control-center.js`: Replace unconditional "Voice request finished" message with real state tracking.
- **Verification Gate:**
  - `curl -X POST http://127.0.0.1:8000/api/voice/listen_once` captures real audio and returns without daemon lock error.
  - Browser audio test confirms audio recording and transcription.

### Phase 3: Fix Real AI Chat & Speech Output
- **Files Modified:**
  - `config/config.yaml`: Enable `cloud_tts_enabled: true`, set default voices for Aria and Atlas.
  - `apps/voice/gradio_tts.py`: Add voice selection support (`en-US-AriaNeural`, `en-US-GuyNeural`), speed/pitch adjustments, and smooth fallback to `pyttsx3`/`espeak-ng`.
  - `apps/voice/speech_manager.py`: Guarantee staged audio playback and URL delivery.
- **Verification Gate:**
  - Synthesize custom phrase; verify MP3 generation and valid headers; test playback.

### Phase 4: Implement & Enhance Wake Word Engine
- **Files Modified:**
  - `apps/voice/wake_word_engine.py`: Refine state transitions, dynamic noise floor calibration, and push-to-talk interrupt handler.
  - `apps/api/voice_api.py`: Add wake word control endpoints (`/api/voice/wake_word/toggle`, `/api/voice/wake_word/config`).
- **Verification Gate:**
  - Wake word trigger test: saying "Jarvis" transitions engine from `STANDBY_LISTENING` -> `WAKE_DETECTED` -> `LISTENING_SPEECH`.

### Phase 5: Natural Multi-Turn Conversation
- **Files Modified:**
  - `apps/voice/conversation.py`: Ensure persistent multi-turn history with context retrieval.
  - `ai/brain.py`: Ensure seamless context carry-over ("explain decorators" -> "explain that simply" -> "give me an example").
  - `apps/voice/service.py`: Connect multi-turn conversation context to brain queries.
- **Verification Gate:**
  - Execute multi-turn dialogue test verifying pronoun and topic continuity.

### Phase 6: Character Selection & Lip-Sync System
- **Files Modified:**
  - `apps/dashboard/static/index.html` & `control-center.js`: Embed `AvatarController` into `#cc-hero`, replacing static PNG with dynamic `Svg2DRenderer`.
  - `apps/dashboard/static/control-center.js`: Connect `AudioReactiveLipSyncDriver` to speech playback events.
  - Add Avatar Studio / Character Selector in dashboard and settings with ARIA / ATLAS toggle.
- **Verification Gate:**
  - Character switch test (ARIA <-> ATLAS).
  - Mouth viseme animation during audio playback verified; returns to closed at rest.

### Phase 7: Voice-Controlled Task Execution
- **Files Modified:**
  - `ai/brain.py` & `ai/tools/executor.py`: Ensure natural language system queries ("check CPU", "check system status", "list tasks") execute real tools and summarize cleanly.
- **Verification Gate:**
  - Spoken query "Jarvis, check my system status" invokes `get_system_status` and speaks real telemetry.

### Phase 8: Screen & Camera Multimodal Integration
- **Files Modified:**
  - `apps/vision/service.py` & `apps/api/active_desktop_api.py`: Connect screen/camera capture to brain multimodal context.
  - Handle voice prompts: "Jarvis, look at my screen" and "Jarvis, what can you see through the camera?".
- **Verification Gate:**
  - Test screen and camera frame capture with vision analysis.

### Phase 9: UI Redesign & Voice Diagnostics
- **Files Modified:**
  - `apps/dashboard/static/index.html` & `control-center.js`: Build dedicated Voice Diagnostics panel with live microphone level meter, STT/TTS engine status, loopback test, and speaker test.
- **Verification Gate:**
  - Verify live telemetry updates and loopback/speaker test routines.

### Phase 10: Testing, Documentation & Optimization
- **Files Created:**
  - `docs/JARVIS_WAKEWORD_ARCHITECTURE.md`
  - `docs/JARVIS_AVATAR_AND_LIPSYNC.md`
  - `docs/JARVIS_VOICE_TEST_REPORT.md`
  - `docs/JARVIS_VOICE_TROUBLESHOOTING.md`
- Run full test suite (`pytest`, browser tests, curl checks) and record evidence.
