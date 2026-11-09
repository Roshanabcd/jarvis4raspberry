# JARVIS OS — Phase 2 Performance & Response Timing Benchmark

**Platform:** Raspberry Pi 5 (8 GB RAM, Broadcom BCM2712 Quad-Core Cortex-A76 @ 2.4 GHz)  
**OS:** Debian GNU/Linux 13 (Trixie) ARM64  
**Desktop Environment:** Native X11 (`DISPLAY=:0`, Openbox, 1360x768)  
**Audio Hardware:** Seeed Studio ReSpeaker Lite USB (Card 2, Device 0)  
**Date:** 2026-11-09  
**Timing Instrumentation:** `time.perf_counter()` monotonic nanosecond clock  

---

## 1. System Response Timing Matrix

| Operation Category | Specific Operation / Target | Metric Measured | Latency (ms) | Total Duration (ms) | Verifiable Ground-Truth Result |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **Local LLM Reasoning** | Ollama `llama3.2:1b` (1.2B Q8_0) | Time To First Token (TTFT) | **598.16 ms** | 8,972.29 ms | 46 tokens generated (~5.1 tokens/sec CPU) |
| **Desktop Launch** | Google Chrome (`/usr/bin/google-chrome`) | Launch & Window Map | **498.83 ms** | 498.83 ms | PID: 53550, State: `WINDOW_VISIBLE` |
| **Desktop Launch** | Visual Studio Code (`/home/roshan/.local/bin/code`) | Launch & Window Map | **609.90 ms** | 609.90 ms | PID: 53569, State: `WINDOW_VISIBLE` |
| **Terminal Subprocess** | `python3 --version` | Bash Subprocess Execution | **201.55 ms** | 201.55 ms | Exit Code: 0, Output: `Python 3.14.6` |
| **Terminal Internal** | `pwd` | Session State Resolution | **4.77 ms** | 4.77 ms | Exit Code: 0, CWD: `/home/roshan` |
| **Filesystem Search** | Bounded Filename (`*.py` in `~/UnityGameWorkspace`) | Traversal & Filter | **46.52 ms** | 46.52 ms | Found 2 files (`controller.py`, `build.py`) |
| **Filesystem Grep** | Content Search (`database` in `~/UnityGameWorkspace`) | Subprocess Grep & Fallback | **40.83 ms** | 40.83 ms | Found 6 occurrences across source files |
| **Audio Capture** | 1.000s Microphone Sample | PipeWire `pw-record` Capture | **1,006.30 ms** | 1,006.30 ms | Non-silent capture (RMS 5,256, 16kHz mono) |
| **Speech Synthesis** | Neural TTS Synthesis (`edge-tts` Ryan) | Audio Staging & Validation | **8,685.21 ms** | 8,685.21 ms | Audio ID: `audio_d8fa4abc4b48`, 24kHz mono |

---

## 2. Latency Decoupling & Text-First Architecture Analysis

On embedded ARM64 hardware (Raspberry Pi 5):
1. **Chat Display Speed:**
   - Text chat and streaming responses start in **< 600 ms** (via Ollama TTFT) or **< 20 ms** (via deterministic fast-path / compound orchestrator).
   - Chat tokens are delivered to the UI immediately without waiting for neural TTS synthesis.
2. **Speech Synthesis Decoupling:**
   - Neural TTS synthesis (~3s - 8s depending on sentence length and network) runs asynchronously in the background.
   - The UI displays an `Audio Staging` badge with playback controls once ready, without causing frame drops or freezing the chat console.
3. **Desktop Interaction Performance:**
   - Native application launches (Chrome, VS Code, Firefox) complete and register top-level X11 windows in **400 ms – 650 ms**.
   - Persistent terminal commands execute in **4 ms – 200 ms**, providing instantaneous CLI control.
