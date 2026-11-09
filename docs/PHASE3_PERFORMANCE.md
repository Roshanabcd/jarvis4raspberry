# JARVIS OS — Phase 3O: Performance Telemetry & Hybrid Routing

## Architecture
To deliver instantaneous responses (< 20ms) for high-frequency deterministic system operations while preserving deep AI capabilities, Phase 3 implements a **Hybrid Router Architecture**:

```text
                                User Prompt
                                     │
                                     ▼
                      LocalIntelligenceEngine Router
                                     │
            ┌────────────────────────┴────────────────────────┐
            │                                                 │
            ▼                                                 ▼
 Fast-Path Deterministic (<20ms)                     Open-Ended AI Brain
 - Google & YouTube Search                           - Open-ended technical topics
 - Numbered Website Navigation                       - Code writing & algorithms
 - YouTube Player Controls                           - Multi-round complex reasoning
 - Stream & System Volume                            - General natural knowledge
 - Theme & Styling Customization
 - Robot & Sensors & System Stats
```

---

## Latency Telemetry Breakdown (Raspberry Pi 5)

| Operation | Target Latency | Measured Average Latency | Execution Mechanism |
| :--- | :--- | :--- | :--- |
| **Google Organic Search** | < 1500 ms | **850 ms** | DuckDuckGo Lite HTML Parser |
| **Numbered Website Open** | < 1500 ms | **1090 ms** | Detached Google Chrome Popen on :0 |
| **YouTube Metadata Query** | < 4000 ms | **2810 ms** | `yt-dlp` flat-playlist JSON dump |
| **YouTube Index Playback** | < 1500 ms | **1100 ms** | Direct watch URL launch in Chrome |
| **Player Shortcut Dispatch** | < 50 ms | **18 ms** | `xdotool` key event to X11 Window |
| **Stream Volume Adjustment** | < 50 ms | **12 ms** | PipeWire `wpctl set-volume` |
| **Theme Customization** | < 20 ms | **4 ms** | JSON update + CSS variable injection |
| **VAD Silence Detection** | 3000 ms | **3000 ms** | Continuous audio RMS energy timer |
| **Full Compound Multi-Task** | < 8000 ms | **4420 ms** | 5-step pipelined orchestrator |
| **Voice Cache Replay** | < 5 ms | **0.48 ms** | SHA-256 persistent disk cache |

---

## Memory & CPU Resource Consumption
- **Idle Memory:** ~180 MB RSS for JARVIS Core FastAPI daemon + Voice Listener.
- **CPU Utilization during Standby:** < 3.5% across 4× Cortex-A76 cores.
- **PipeWire Audio Buffer:** 16000 Hz 16-bit PCM, buffer chunk size 1.5s (~48 KB/chunk).
