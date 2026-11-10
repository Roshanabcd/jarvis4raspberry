# JARVIS OS — Phase 6 Baseline Architecture & Pre-Modification Audit

**Date:** 2026-11-10  
**Target Hardware:** Raspberry Pi 5 (8 GB RAM LPDDR4X, Quad-Core Cortex-A76 @ 2.4 GHz)  
**Operating System:** Debian 13 Trixie (ARM64 / AArch64, Kernel 6.12, X11 Display `:0`, 1360 × 768)  
**Active User:** `roshan`  
**Audio Architecture:** PipeWire 1.4.2 + WirePlumber + ALSA  
**Git Branch:** `feat/jarvis-phase6-desktop-voice-repair`  

---

## 1. Executive Summary

Phase 6 audits the transition of JARVIS OS from a browser-accessed web dashboard into a standalone Linux desktop application (`JARVIS OS`) with an overhauled, fully functional, and verified voice pipeline.

Historically, JARVIS suffered from four key defects:
1. **Desktop Shell Absence:** JARVIS required the user to open Google Chrome and manually navigate to `http://localhost:8000/`.
2. **Spurious "Simulated Transcription":** Root configuration (`config/config.yaml`) had `simulation_mode: true` enabled by default, causing `SpeechToText.transcribe` and `TextToSpeech.speak` to bypass hardware and return simulated strings.
3. **Broken Wake-Word Engine Callback:** In `apps/voice/wake_word_engine.py`, the command execution callback attempted `from ai.brain import jarvis_brain` which raised an `ImportError` because `ai.brain` exports `get_brain()`, causing wake-word recognition to crash into state `ERROR`.
4. **OmniVoice Tunnel Expiration & Unclear Fallback:** Remote Google Colab Gradio live tunnels (`*.gradio.live`) expire after 72 hours. When offline, JARVIS did not consistently provide manual URL entry or transparently label the active TTS provider.

---

## 2. Hardware Device Discovery (Actual Verified State)

### Audio Devices (ALSA & PipeWire 1.4.2)
- **USB Microphone Array:** Seeed Studio ReSpeaker Lite USB 2-Mic Array
  - USB ID: `Bus 001 Device 002: ID 2886:0019 Seeed Technology Co., Ltd. ReSpeaker Lite`
  - ALSA Capture: `card 2: Lite [ReSpeaker Lite], device 0: USB Audio`
  - PipeWire Source: `Node 55: ReSpeaker Lite Analog Stereo` (Default Source `*`, volume `0.94`)
  - Capture Test: Verified real 16 kHz mono 16-bit PCM recording via `pw-record` with active RMS energy (>40.0).
- **Speaker Output:**
  - ALSA Playback: `card 2: Lite [ReSpeaker Lite], device 0: USB Audio` (Integrated USB 3.5mm DAC)
  - PipeWire Sink: `Node 54: ReSpeaker Lite Analog Stereo` (Default Sink `*`, volume `0.65`)
  - Playback Test: Verified test tone and MP3 playback via `pw-play` with zero exit errors.
- **HDMI Outputs:** `card 0: vc4hdmi0`, `card 1: vc4hdmi1` (Muted/Standby).

### Cloned Voice Reference Audio Assets
- `/home/roshan/Downloads/myvoice_clean.wav`: RIFF PCM 16-bit mono 24000 Hz, SHA256 `fb1422b0...` (Clean, validated).
- `/home/roshan/Downloads/myvoice.mp3`: MPEG ADTS Layer III, 64 kbps, 48 kHz stereo.
- `/home/roshan/Downloads/myvoice.mpeg`: MPEG ADTS Layer III, 320 kbps, 48 kHz joint stereo.
- `data/voice_samples/myvoice_ref_clean.wav`: Identical to `/home/roshan/Downloads/myvoice_clean.wav` (3.2 seconds duration, optimal for OmniVoice prompt conditioning).

### Local AI Models (Ollama)
- Daemon: `http://127.0.0.1:11434` (Active)
- Installed Models: `llama3.2:1b` (fast local default), `qwen3.5:4b` (reasoning agent).

---

## 3. Desktop Application Architecture Plan

### Framework Selection: Standalone Chromium App Shell with Native Desktop Wrapper
1. **Lightweight & High-Performance:** Google Chrome 157.0 is already installed on Debian 13 ARM64 with full GPU acceleration, WebRTC audio support, and WebSocket integration.
2. **Native Window Presentation:** Running `google-chrome --app=http://127.0.0.1:8000 --class=jarvis-os --name=jarvis-os --window-size=1360,768` creates a dedicated frameless application window with no browser tabs, search bar, or navigation buttons.
3. **Dedicated Launcher & Process Management (`apps/desktop/launcher.py`):**
   - Single-instance mutex (prevents duplicate windows or multiple backend processes).
   - Automatic backend health check: boots backend automatically if not already active.
   - High-resolution SVG and PNG application icon.
   - Desktop entry files in `~/.local/share/applications/jarvis-os.desktop` and `/home/roshan/Desktop/jarvis-os.desktop`.
   - Global command: `jarvis` accessible from any terminal.

---

## 4. Voice Pipeline Overhaul Plan

1. **Disable Global `simulation_mode` for Voice:** Ensure voice components default to real hardware execution.
2. **Fix `wake_word_engine.py`:** Update Brain dispatch to use `get_brain().chat()`, handle exceptions gracefully, and broadcast to the dashboard via WebSocket.
3. **True 3-Second Silence Detection:** Implement continuous rolling audio recording with RMS energy tracking; finalize after 3.0 seconds of silence post-speech.
4. **Transparent TTS Labelling:**
   - When OmniVoice Colab URL is online and reachable: `OmniVoice (Personal Cloned Voice)`.
   - When OmniVoice is offline: Fallback to `Neural Fallback (Edge-TTS Ryan)` with explicit visual badge and text notification.
   - Enable user to enter new Gradio URL dynamically via Settings or REST endpoint `/api/voice/register_colab`.
5. **Preserve Background Audio:** Keep PipeWire stream ducking non-destructive; never alter master sink volume or kill external audio streams.
