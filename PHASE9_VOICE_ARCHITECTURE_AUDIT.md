# JARVIS OS — Phase 9 Voice & Identity Architecture Audit
## Baseline System Inspection, Hardware Mapping & Architecture Roadmap

**Audit Date:** November 10, 2026  
**Target Hardware:** Raspberry Pi 5 (8 GB RAM), Debian 13 Trixie, ARM64 / aarch64  
**Project Workspace:** `/home/roshan/.gemini/antigravity/scratch/jarvis-os`  
**Git Branch:** `feat/jarvis-phase9-voice-identity-assistant`  

---

## 1. Executive Summary

This architecture audit evaluates the complete voice, speech, audio hardware, face biometric identity, and conversation pipeline in JARVIS OS.

The Raspberry Pi 5 hardware environment features:
- **Audio Server:** PipeWire 1.4.2 with WirePlumber session manager.
- **Microphone Array:** Seeed Studio ReSpeaker Lite USB 2-Mic Array (Alsa card 2, PipeWire Source Node 55, volume 0.94).
- **Physical Speaker:** USB-powered 3.5mm stereo speaker attached to ReSpeaker Lite audio jack (Alsa card 2, PipeWire Sink Node 54, volume 0.65).
- **Camera Sensor:** Raspberry Pi Camera Module 3 (Sony IMX708 autofocus sensor, 120° FoV) owned by `jarvis-camera.service` on loopback `http://127.0.0.1:8082`.
- **Local AI Provider:** Local Ollama running on `127.0.0.1:11434` with `llama3.2:1b`, `qwen3.5:4b`, and `moondream:latest`.
- **Apps Platform:** Phase 8 JARVIS Apps Center operational with 20 registered applications (3 Available, 17 Planned).

---

## 2. Audio Hardware & PipeWire Diagnostic Evidence

Executing native PipeWire diagnostic inspection (`wpctl status` and `wpctl inspect`):

```text
Audio
 ├─ Devices:
 │      48. ReSpeaker Lite                      [alsa]
 │      49. Built-in Audio                      [alsa]
 │      50. Built-in Audio                      [alsa]
 │  
 ├─ Sinks:
 │  *   54. ReSpeaker Lite Analog Stereo        [vol: 0.65]
 │      76. Built-in Audio Digital Stereo (HDMI) [vol: 1.00 MUTED]
 │  
 ├─ Sources:
 │  *   55. ReSpeaker Lite Analog Stereo        [vol: 0.94]
```

### Detailed Node Inspection
- **Default Audio Sink (ID 54):**
  - Node Name: `alsa_output.usb-Seeed_Studio_ReSpeaker_Lite_0000000001-00.analog-stereo`
  - Device API: ALSA (`front:2`), Card: `2`, Device: `0`
  - Playback channels: 2 (FL, FR), Status: Operational, Vol: 0.65.
- **Default Audio Source (ID 55):**
  - Node Name: `alsa_input.usb-Seeed_Studio_ReSpeaker_Lite_0000000001-00.analog-stereo`
  - Device API: ALSA (`front:2`), Card: `2`, Device: `0`
  - Capture channels: 2, Status: Operational, Vol: 0.94.

> [!IMPORTANT]
> The Seeed Studio ReSpeaker Lite is operating as both the authoritative system recording source and the authoritative playback sink. PipeWire dynamic discovery correctly detects it across reboots without hardcoded node IDs.

---

## 3. Running Services & Daemon Ownership

Inspecting active systemd user services via `systemctl --user list-units --type=service`:
- **`jarvis-voice.service` (Active / Running, PID 1233):**
  - ExecStart: `/home/roshan/miniconda3/bin/python3 -m apps.voice.wake_word_engine`
  - Manages continuous wake-word listening, VAD energy thresholding, and silence detection.
  - Exclusively owns the background recording stream via PipeWire (`pw-record`).
- **`jarvis-camera.service` (Active / Running, PID 28546):**
  - ExecStart: `/home/roshan/jarvis_camera_venv/bin/python /home/roshan/camera.py --headless --web --host 127.0.0.1 --port 8082`
  - Exclusively owns physical camera sensor `/dev/media0` via Picamera2.
  - Serves live HTTP endpoints: `/api/snapshot`, `/api/detections`, `/api/health`.
- **`jarvis-core` (Uvicorn Daemon, Port 8000):**
  - Core FastAPI application hosting UI dashboard, Brain, Identity, Desktop, and Apps Center APIs.

---

## 4. Current Voice & Identity Pipeline Component Analysis

### A. Microphone Capture & Single Ownership
- **Implementation:** `WakeWordEngine._record_audio_chunk` in `apps/voice/wake_word_engine.py` invokes `pw-record --rate=16000 --channels=1 --format=s16 <path>`.
- **Single Ownership:** `apps/core/main.py` checks `is_voice_service_daemon_running()`. When the systemd daemon is active, the core backend refrains from spawning competing in-process recording threads.

### B. Wake-Word Engine
- **Implementation:** Acoustic keyword detection regexes (`"JARVIS"`, `"Hey JARVIS"`, `"Hello JARVIS"`, `"Wake up JARVIS"`).
- **12-State Machine:**
  `DISABLED` → `STANDBY_LISTENING` → `WAKE_DETECTED` → `LISTENING_SPEECH` → `STREAMING_TRANSCRIPTION` → `SILENCE_COUNTDOWN` → `COMMAND_SUBMITTED` → `PROCESSING_AGENT` → `SPEAKING_RESPONSE` → `FOLLOW_UP_STANDBY` → `MUTED` → `ERROR`.
- **Follow-up Window:** 15.0 seconds of conversation follow-up without repeating the wake word.

### C. Voice Activity Detection (VAD)
- **Algorithm:** Root-Mean-Square (RMS) amplitude calculation over 16-bit PCM frames.
- **Adaptive Calibration:** Ambient noise floor tracked smoothly (`noise_floor = noise_floor * 0.85 + rms * 0.15`).
- **Dynamic Energy Threshold:** Minimum 90.0 RMS, maximum 350.0 RMS, clamped to 2.0x noise floor.
- **Silence Window:** 3.0 seconds continuous silence triggers command finalization.

### D. Speech-to-Text (STT)
- **Implementation:** `SpeechToText` in `apps/voice/stt.py`.
- **Engine Priority:**
  1. SpeechRecognition (`recognize_google`, en-US).
  2. Local Whisper model fallback if loaded.
- **Anti-Simulation:** Near-silent audio (<8.0 RMS) is rejected immediately with an empty string rather than simulated transcripts.

### E. Speech Synthesis (TTS) & Barge-In
- **Implementation:** `SpeechOutputManager` in `apps/voice/speech_manager.py`.
- **Engine Priority:**
  1. Cloned OmniVoice if Colab tunnel is online.
  2. Neural Fallback (Edge-TTS `en-GB-RyanNeural`) with truthful provider label.
- **Acoustic Feedback Guard:** During active system speaker playback (`pw-play`), microphone VAD is suppressed to eliminate self-trigger feedback loops.
- **Barge-In:** `stop_playback()` terminates `_current_player` (`SIGTERM`/`kill`) immediately.

### F. Face Recognition & Role-Based Identity
- **Face Detection:** OpenCV Zoo YuNet (<90ms on Cortex-A76).
- **Feature Extraction:** OpenCV Zoo SFace (128-D embedding vector).
- **Matching:** Cosine similarity threshold (0.363).
- **Roles:** `ADMIN`, `USER`, `GUEST` stored in `data/identity/users.json`.
- **Security:** Conversational elevation ("make me admin") is strictly rejected; administrator actions require cryptographic PIN verification.

### G. Phase 8 Apps Center Integration
- Verified present on branch `feat/jarvis-phase9-voice-identity-assistant`!
- 20 registered applications in `data/apps/registry.json`.
- 3 Available (`voice-assistant`, `face-recognition`, `multi-agent-automation`) and 17 Planned.

---

## 5. Identified Gaps & Planned Phase 9 Upgrades

1. **Unified Authenticated Voice Session:**
   - Currently, voice commands run under a generic `"voice-session"` context.
   - *Phase 9 Solution:* Connect voice processing directly to active facial recognition session. When the user in front of the camera is recognized (e.g. `roshan`), the voice turn inherits that user's identity, role, and favorites. If unrecognized or camera disabled, fallback to `GUEST`.
2. **Strict Conversational Security Gate:**
   - Voice commands must not be allowed to bypass backend permissions or trigger sensitive actions (such as deleting files or adding administrators) without explicit PIN challenge.
3. **Enhanced Barge-In & State Transitions:**
   - When the user speaks or clicks "Interrupt" while JARVIS is speaking, cancel the audio playback instantly and transition directly to `LISTENING_SPEECH` to capture the new command without queue collision.
4. **ReSpeaker Dynamic Disconnection & Recovery:**
   - Detect PipeWire device dropouts and recover gracefully without crashing background loops or logging uncontrolled traceback loops.
5. **Interactive Voice Assistant Dashboard HUD:**
   - Provide a real-time visual voice assistant interface in the desktop dashboard showing:
     - Live 12-state visual indicator (Standby, Wake Detected, Listening, Transcribing, Thinking, Speaking, Error).
     - Active User Identity & Role pill (`👤 Roshan (USER)` or `👤 Guest`).
     - Real-time recognized transcript & AI response streaming.
     - Push-to-Talk button, Mute toggle, and Instant Interrupt button.
     - Dynamic audio device selectors & volume sliders.

---

## 6. Architecture Roadmap & Next Execution Stages

- **Stage B:** Single Authoritative Voice Pipeline Engine with unified session manager.
- **Stage C & D:** Wake-word & VAD tuning with dynamic sensitivity controls.
- **Stage E:** STT engine hardening with multi-language readiness (English, Hindi, Nepali).
- **Stage F & G:** Seamless integration of Brain reasoning, Camera snapshot face recognition, and user session context.
- **Stage H & I:** Voice-controlled permission governance, desktop automation, and Apps Center routing.
- **Stage J & K:** Dual TTS synthesis, speech queue pruning, and instant barge-in.
- **Stage L & M:** ReSpeaker audio management panel and Desktop Voice UI HUD.
- **Stage N & O:** REST/WebSocket API endpoints and RPi5 resource management.
- **Stage P:** 27-item automated test suite + hardware verification.
- **Stage Q & R:** Security audit & systemd service optimization.
- **Stage S:** Final implementation reports and documentation.
