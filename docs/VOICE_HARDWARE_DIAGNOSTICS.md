# JARVIS OS — Voice Hardware & Audio Environment Diagnostics
**Target SBC:** Raspberry Pi 5 (8 GB LPDDR4X, Broadcom BCM2712, Debian 13 Trixie aarch64)  
**Kernel:** Linux `6.18.60+rpt-rpi-v8`  
**Execution Date:** November 8, 2026  
**Auditor:** Principal Voice AI & Audio Embedded Systems Engineer  

---

## 1. Executive Summary & Diagnostic Findings

1. **Physical Microphone Device:**
   - **Hardware:** Seeed Studio ReSpeaker Lite USB (`ID 2886:0019`).
   - **ALSA Identifier:** `card 2: Lite [ReSpeaker Lite], device 0: USB Audio`.
   - **PipeWire Source Node:** ID `55`, `ReSpeaker Lite Analog Stereo` (configured as **Default System Source**, volume: 0.94).
   - **Verification:** Successfully recorded 16-bit PCM mono 16 kHz audio directly via PipeWire (`pw-record`) and ALSA plug format (`plughw:2,0`). Non-empty audio confirmed (14,990 frames, 0.94s, 30 KB).

2. **Physical Speaker / Output Device:**
   - **Hardware:** Seeed Studio ReSpeaker Lite USB Audio Playback.
   - **ALSA Identifier:** `card 2, device 0`.
   - **PipeWire Sink Node:** ID `54`, `ReSpeaker Lite Analog Stereo` (configured as **Default System Sink**, volume: 1.00).
   - **Alternative Sink:** ID `76`, `Built-in Audio Digital Stereo (HDMI)` (currently MUTED).
   - **Verification:** Successfully played test MP3/WAV audio via `pw-play` without errors (exit code 0).

3. **Audio Routing Daemon & Contention:**
   - **Active Daemon:** PipeWire `1.4.2` with WirePlumber `1.4.2` session manager.
   - **Contention Cause:** Direct hardware access (`hw:2,0`) fails with `Device or resource busy` because PipeWire holds the hardware file descriptor.
   - **Resolution:** Use PipeWire native routing (`pw-record` / `pw-play`) or format-converting ALSA plug (`plughw:2,0`). Both allow seamless software multiplexing and sample rate conversion.

4. **Permissions & User Group:**
   - User `roshan` belongs to the `audio` group (`gid 29`).
   - Device node permissions on `/dev/snd/*` allow read/write (`crw-rw----+ root audio`).

---

## 2. Command Output Summaries

### 2.1 ALSA Cards (`cat /proc/asound/cards`)
```text
 0 [vc4hdmi0       ]: vc4-hdmi - vc4-hdmi-0 (HDMI Audio 0)
 1 [vc4hdmi1       ]: vc4-hdmi - vc4-hdmi-1 (HDMI Audio 1)
 2 [Lite           ]: USB-Audio - ReSpeaker Lite (Seeed Studio ReSpeaker Lite at usb-xhci-hcd.0-1, high speed)
```

### 2.2 Capture Devices (`arecord -l`)
```text
**** List of CAPTURE Hardware Devices ****
card 2: Lite [ReSpeaker Lite], device 0: USB Audio [USB Audio]
  Subdevices: 1/1
  Subdevice #0: subdevice #0
```

### 2.3 Playback Devices (`aplay -l`)
```text
**** List of PLAYBACK Hardware Devices ****
card 0: vc4hdmi0 [vc4-hdmi-0], device 0: MAI PCM i2s-hifi-0
card 1: vc4hdmi1 [vc4-hdmi-1], device 0: MAI PCM i2s-hifi-0
card 2: Lite [ReSpeaker Lite], device 0: USB Audio [USB Audio]
```

### 2.4 PipeWire & WirePlumber Topology (`wpctl status`)
```text
PipeWire 'pipewire-0' [1.4.2, roshan@raspberrypi]
Audio
 ├─ Devices:
 │      48. ReSpeaker Lite                      [alsa]
 │      49. Built-in Audio (HDMI 0)             [alsa]
 │      50. Built-in Audio (HDMI 1)             [alsa]
 │  
 ├─ Sinks:
 │  *   54. ReSpeaker Lite Analog Stereo        [vol: 1.00]  <-- DEFAULT SYSTEM OUTPUT
 │      76. Built-in Audio Digital Stereo (HDMI)[vol: 1.00 MUTED]
 │  
 ├─ Sources:
 │  *   55. ReSpeaker Lite Analog Stereo        [vol: 0.94]  <-- DEFAULT SYSTEM INPUT
```

---

## 3. Reference Voice Sample Validation

- **Path:** `/home/roshan/.gemini/antigravity/scratch/jarvis-os/data/voice_samples/myvoice.wav`
- **File Format:** RIFF (little-endian) data, WAVE audio, Microsoft PCM, 16 bit
- **Channels:** 1 (Mono)
- **Sample Rate:** 24,000 Hz
- **Total Frames:** 1,994,688
- **Duration:** 83.11 seconds
- **File Size:** 3,989,454 bytes (~3.99 MB)
- **Status:** **VALID & VERIFIED**

---

## 4. Root Causes of Current Defects

1. **Defect 1: "Simulated transcription" returned instead of real microphone input:**
   - In `apps/voice/stt.py:95-97`, `SpeechToText.transcribe()` checked `if self.simulation_mode: return self.transcribe_simulated()`.
   - In `apps/voice/service.py:41`, `VoiceService` defaulted its `simulation_mode` to `config.get("simulation_mode", True)`.
   - Because `simulation_mode: true` was enabled globally in `config.yaml` to run unpinned robot motors safely, it inadvertently forced the voice engine, microphone recorder, and speech-to-text into simulation mode as well.

2. **Defect 2: Responses displayed as text but never spoken aloud:**
   - In `apps/api/chat_api.py`, `POST /api/chat` and `POST /api/chat/stream` only generated LLM text responses and never invoked speech synthesis or returned audio payloads.
   - In `apps/dashboard/static/index.html`, `sendChat()` rendered text bubbles without triggering audio playback.

3. **Defect 3: Cloned Voice Status:**
   - The configured Hugging Face Space URL (`https://roshan-omnivoice-jarvis.hf.space`) currently returns HTTP 404 (Offline/Unreachable).
   - When the remote space is offline, the system must clearly indicate `OMNIVOICE OFFLINE — FALLBACK VOICE ACTIVE` and use the local `edge-tts` engine without claiming it is cloned.
