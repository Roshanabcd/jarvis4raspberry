# Current verified checkpoint — 21 November 2026

Confirmed defects repaired: native-owner rejection reported as silence; duplicate playback of server-owned speech; unconditional completion text; stale polls undoing mute; two Web Audio source nodes competing for one HTML audio element. ReSpeaker Lite capture was observed through existing owner telemetry, not a new recording. Recognized human speech and audible speaker acceptance remain pending.

The earlier notes below are preserved for history; conflicting completion claims are superseded by this checkpoint.

---

# JARVIS Voice System Audit & Diagnostics Report
**Date:** 2026-11-20
**Target Environment:** Raspberry Pi 5 (8GB RAM), Debian 13 (Trixie/aarch64), Linux kernel 6.12, PipeWire 1.4.2, WirePlumber 1.4.2, TigerVNC, ReSpeaker Lite Audio USB

---

## 1. Executive Summary

This audit investigates the end-to-end voice capture, wake-word detection, speech-to-text (STT), AI dialogue processing, text-to-speech (TTS), and avatar rendering subsystems of JARVIS OS.

### Primary Symptom Investigated:
When clicking the microphone button or attempting voice input, the user observed:
> "Voice request finished. Check the conversation for the result."
> ...accompanied by silence, no speech transcription, and no audible reply from the AI avatar.

---

## 2. Root Cause Analysis

### Root Cause 1: Microphone Owner Conflict in `apps/voice/service.py`
In `apps/voice/service.py`, lines 278–281:
```python
from apps.voice.wake_word_engine import is_voice_service_daemon_running
if is_voice_service_daemon_running():
    return {
        "status": "error",
        "message": "The dedicated voice daemon owns the microphone. Use its wake word; a second capture was not started."
    }
```
**Impact:**
The background service `jarvis-voice.service` is enabled and running under systemd user units (`python -m apps.voice.wake_word_engine`, PID 51906). Whenever the frontend invokes `POST /api/voice/listen_once`, `is_voice_service_daemon_running()` evaluates to `True`, immediately rejecting the request with an error dictionary instead of recording audio.

### Root Cause 2: Hardcoded UI Fallback in `apps/dashboard/static/control-center.js`
In `apps/dashboard/static/control-center.js`, line 81:
```javascript
byId('cc-speak').addEventListener('click', async () => {
    text('cc-chat-feedback', 'Listening through the existing JARVIS microphone service…');
    await root.toggleVoiceRecord();
    text('cc-chat-feedback', 'Voice request finished. Check the conversation for the result.');
    syncConversation();
});
```
**Impact:**
Regardless of whether `toggleVoiceRecord()` succeeded, failed with a 503/400 error, timed out, or detected pure silence, line 81 unconditionally overwrote the feedback label with `'Voice request finished. Check the conversation for the result.'`. Because Root Cause 1 caused `toggleVoiceRecord()` to return an error status, no transcript was ever created, leaving the user with a confusing success-sounding message while nothing happened.

### Root Cause 3: Missing Browser-to-Backend Audio Upload Route
In `apps/api/voice_api.py`, only two voice ingestion paths existed:
1. `POST /api/voice/listen_once` — captures audio directly from the physical hardware (ReSpeaker Lite) on the host machine using PipeWire/ALSA.
2. `POST /api/voice/command` — accepts pre-transcribed text strings.

**The TigerVNC / Remote Client Gap:**
When accessing JARVIS from a laptop or remote client via TigerVNC (RFB protocol) or a remote browser:
- The RFB protocol in TigerVNC does **not** forward client microphone hardware to the VNC host by default.
- If the operator speaks into their laptop microphone, the Raspberry Pi's host audio device receives zero signal unless the client browser records via HTML5 `getUserMedia` and uploads the audio stream to the server.
- The backend lacked an endpoint such as `POST /api/voice/transcribe` to receive browser-recorded audio buffers (WAV/WebM/OGG) and transcribe them.

### Root Cause 4: Robotic Speech & Disabled Cloud Neural TTS
In `config/config.yaml`:
```yaml
voice:
  engine: espeak
  cloud_tts_enabled: false
  fallback_voice: en-GB-RyanNeural
```
**Impact:**
Because `cloud_tts_enabled` was set to `false`, high-quality neural voice synthesis via `edge-tts` was disabled. The system fell back strictly to local `espeak-ng`, which produces metallic, robotic speech with flat intonation, failing the requirement for natural, pleasant human-like voice.

### Root Cause 5: Static Avatar Illustration on Home Dashboard
In `apps/dashboard/static/control-center.css`, line 48:
```css
.cc-avatar {
    position: relative;
    width: 100%;
    aspect-ratio: 1.9;
    overflow: hidden;
    border-radius: 30%;
    background-image: url('/assets/jarvis-design-reference.png');
    background-size: 304% auto;
    background-position: 52.2% 27%;
}
```
**Impact:**
The central AI character on the main control center was a static raster PNG (`jarvis-design-reference.png`). It lacked facial rigs, vector geometry, or mouth layer separation. While the futuristic dashboard (`apps/dashboard/futuristic/avatar.js`) possessed a rigged `Svg2DRenderer` with ARIA and ATLAS characters and 5 mouth visemes (`rest`, `A`, `E`, `O`, `U`), it was never integrated into the primary `/` dashboard.

---

## 3. Subsystem Audit Matrix

| Subsystem | Component | Status | Verified Findings |
| :--- | :--- | :--- | :--- |
| **Audio In** | ReSpeaker Lite USB | ✅ Active | Configured as default PipeWire source (Node 80, 16kHz, S16LE, volume 73%). Captures cleanly via `pw-record`. |
| **Audio In** | TigerVNC / Browser | ⚠️ Missing Route | RFB does not forward laptop mic. Needs browser `MediaRecorder` + backend `/api/voice/transcribe`. |
| **Wake Word** | `wake_word_engine.py` | ✅ Active (Daemon) | PID 51906, systemd user unit. 12-state machine, VAD with adaptive RMS floor. Matches 'jarvis', 'hey jarvis', 'wake up jarvis'. |
| **Push-to-Talk**| `listen_once` | ❌ Blocked | Rejected whenever daemon was running. Needs inter-process coordination (`send_daemon_command('mute')`). |
| **STT** | Google Web Speech / Whisper | ✅ Ready | `speech_recognition` fast Google cloud STT + local Whisper `tiny` CPU fallback. |
| **AI Brain** | `ai/brain.py` | ✅ Operational | Ollama (`llama3.2:1b`, `moondream`), Nvidia NIM, OpenRouter. Full tool calling verified. |
| **TTS** | `edge-tts` / `espeak-ng` | ⚠️ Misconfigured | `edge-tts` 7.3.1 installed. Tested `en-US-AriaNeural` & `en-US-GuyNeural` in 1.5s. `cloud_tts_enabled` was false. |
| **Audio Out** | System Speaker (pw-play) | ✅ Active | ReSpeaker Lite Analog Stereo (Sink Node 79, volume 65%). `/usr/bin/pw-play` operational. |
| **Audio Out** | HTML5 Browser Audio | ⚠️ Muted by autoplay | Audio element needs unlocked AudioContext on first gesture. |
| **Avatar** | Digital Human / Visemes | ⚠️ Isolated | Full SVG viseme engine existed only in `/futuristic/`. Main dashboard had static PNG. |

---

## 4. Remediation Architecture

```
[User Spoken Audio]
       │
       ├──► (A) Raspberry Pi Physical Mic (ReSpeaker Lite)
       │        └─► WakeWordEngine (Background Daemon)
       │              ├─► Standby Listening (1.5s VAD chunks)
       │              ├─► Wake Word Matched ("Jarvis") ─► Speak "Yes?"
       │              ├─► Command Listening (until 3s silence)
       │              └─► Brain.chat() ─► Edge-TTS ─► pw-play & Browser Stream
       │
       └──► (B) Browser / Laptop Microphone (Remote over TigerVNC)
                └─► HTML5 getUserMedia + MediaRecorder
                      └─► POST /api/voice/transcribe
                            └─► Brain.chat() ─► Edge-TTS ─► Audio Stream & Visemes
```

---

## 5. Next Steps
Proceed immediately with Phase 2 implementation:
1. Enable inter-process muting in `apps/voice/service.py` for push-to-talk.
2. Implement `POST /api/voice/transcribe` in `apps/api/voice_api.py`.
3. Enable `cloud_tts_enabled: true` and configure Aria/Atlas voices.
4. Mount the dynamic SVG Avatar and Character Studio onto the primary dashboard.
