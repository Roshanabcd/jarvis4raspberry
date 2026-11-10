# JARVIS OS — Phase 6 Microphone Setup & Capture Engineering

**Hardware Integration Guide for Seeed Studio ReSpeaker Lite USB 2-Mic Array**

---

## 1. Physical Device Identification

The ReSpeaker Lite USB two-microphone array is automatically detected on the Raspberry Pi 5 USB bus:

```text
Bus 001 Device 002: ID 2886:0019 Seeed Technology Co., Ltd. ReSpeaker Lite
ALSA Capture: card 2: Lite [ReSpeaker Lite], device 0: USB Audio
PipeWire Source: Node 55 [ReSpeaker Lite Analog Stereo] (Default Source *)
```

---

## 2. PipeWire Non-Blocking Capture Backend

To avoid device-lock conflicts (where ALSA `hw:2,0` is locked by a single application), JARVIS uses native PipeWire capture:

```bash
pw-record --rate=16000 --channels=1 --format=s16 /tmp/output.wav
```

### Advantages:
1. **Multi-Client Sharing:** WirePlumber multiplexes the ReSpeaker audio stream across the wake-word engine, push-to-talk, and diagnostics without conflict.
2. **Deterministic Sampling:** Enforces 16000 Hz mono 16-bit PCM suitable for both Google Web Speech API and local Whisper models.
3. **Hardware Volume Preservation:** Uses default ReSpeaker source volume (`0.94` / 94%) without altering user ALSA levels.

---

## 3. Real Energy & VAD Calibration

- **Quiet Ambient Noise RMS:** ~35.0 to 45.0
- **Normal Conversational Speech RMS:** ~200.0 to 900.0
- **Configured Energy Threshold:** `120.0` (in `config.yaml` under `voice.energy_threshold`)
- **Silence Timeout Threshold:** `3.0` seconds (resets whenever speech RMS > 120.0 is observed)
