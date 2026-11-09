# JARVIS OS — Phase 3 Known Limitations & System Boundaries

## Overview
This document specifies the architectural boundaries, system prerequisites, hardware-dependent constraints, and deliberate design decisions governing JARVIS OS Phase 3 on Raspberry Pi 5 (8 GB RAM, ARM64, Debian 13 Trixie).

---

## 1. Desktop & Window Automation Subsystem

### 1.1 Native X11 Dependency for Window Management
- **Implementation Mechanism**: Active tab manipulation, window focus switching, and browser navigation keyboard shortcuts (`alt+Left`, `ctrl+r`, `ctrl+w`, `ctrl+1..9`, `Page_Down`) rely on `xdotool` and `wmctrl` communicating via the X11 socket on `DISPLAY=:0`.
- **Limitation**: In pure Wayland environments (e.g., default Wayfire or Labwc without XWayland permissions enabled for non-root users), synthetic key event injection requires either Wayland-native protocols (`ydotool` / `wtype` with appropriate uinput permissions) or direct CDP browser automation.
- **Handling**: `BrowserAgent` verifies `DISPLAY` environment variables and falls back to URL-based tab re-opening if `xdotool` synthetic keystroke dispatch returns non-zero exit codes.

### 1.2 Chrome Window Mapping & Cold Launch Latency
- **Behavior**: When launching Google Chrome cold with the full persistent user profile (`/home/roshan/.config/google-chrome`), profile initialization and GPU sandbox validation on Raspberry Pi 5 take between 400ms and 1,200ms.
- **Mitigation**: `BrowserAgent.open_url` and `YouTubeController.play_video_by_index` implement asynchronous launch with `stdin=subprocess.DEVNULL`, `start_new_session=True`, and 0.5s settling intervals before issuing focus commands, preventing TTY deadlocks and race conditions.

---

## 2. Web Search & Parsing Limits

### 2.1 DuckDuckGo Lite Rate Limiting
- **Implementation**: `SearchManager` utilizes DuckDuckGo Lite HTML endpoints parsed via standard library regex patterns without heavy headless browser or Selenium overhead.
- **Limitation**: Burst requests exceeding 20 queries within a 60-second window from a single IP may temporarily encounter DuckDuckGo rate limiting or CAPTCHA challenges.
- **Mitigation**: User-Agent randomization is included, and conversational search sessions cache ordered results in memory (`SearchSession`), minimizing repeat queries for pagination and numbered result lookups.

### 2.2 Deep Dynamic Single-Page Applications (SPAs)
- **Behavior**: Fast organic text extraction handles server-rendered and structured HTML pages. Sites heavily obfuscated behind multi-step client-side JavaScript hydration (e.g., complex React/Vue dashboards requiring CAPTCHAs or logins) are opened directly in the user's interactive Chrome window rather than being scraped headlessly.

---

## 3. YouTube Playback & Media Stream Management

### 3.1 Metadata Extraction Latency via `yt-dlp`
- **Measurement**: Video title, thumbnail, and stream metadata retrieval via `yt-dlp --flat-playlist` averages 1.8 to 2.8 seconds on ARM64 under typical Wi-Fi connections.
- **Limitation**: Network jitter or DNS resolution delays directly impact initial search result display time.
- **Mitigation**: The hybrid router sends a fast-path streaming text notice to the frontend immediately upon intent detection, preventing the user interface from appearing frozen while `yt-dlp` collects structured candidates.

### 3.2 Dynamic In-Stream Advertisements
- **Behavior**: Chrome plays YouTube videos within the authenticated user profile (`/home/roshan/.config/google-chrome`). If the profile has ad-blocking extensions or YouTube Premium active, playback begins without ads. If not, standard pre-roll advertisements are played by YouTube's web player.
- **Player Controls**: Mute, pause, resume, and volume shortcuts operate on the active Chrome window stream; they interact with the active media element regardless of whether pre-roll or target content is rendering.

---

## 4. PipeWire Per-Stream Audio Subsystem

### 4.1 Transient Stream Identifiers
- **Mechanism**: PipeWire assigns dynamic sink input IDs (e.g., Stream 110 for FreeTube, Stream 114 for Chrome) whenever an audio application opens an output node.
- **Limitation**: When a video or song is stopped or closed, PipeWire destroys the stream node. If a user issues "lower YouTube volume" while the video is paused and before audio frames have been dispatched, `wpctl status` will not list an active sink-input for that application.
- **Handling**: `AudioStreamManager.set_app_volume` gracefully detects missing streams, logs an informational notice without raising unhandled exceptions, and updates the application's target volume preference so subsequent streams are leveled appropriately.

### 4.2 Hardware Master Sink Isolation
- **Rule**: Sink 119 (`alsa_output.usb-Seeed_Seeed_ReSpeaker_Lite_...`) master volume is strictly quarantined from application volume adjustments.
- **Limitation**: Commands specifying "lower video volume" will NOT alter the speaker's hardware amplifier volume. To change physical speaker output level, the user must explicitly say "system volume", "master volume", or "speaker volume".

---

## 5. Wake-Word Engine & Voice Pipeline

### 5.1 Continuous Silence Detection in High-Noise Environments
- **Mechanism**: The 12-state wake word machine uses an RMS-based Voice Activity Detector (VAD) with a 3.0-second continuous silence threshold to auto-submit user commands.
- **Limitation**: In acoustic environments where continuous ambient background noise exceeds 78–82 dB SPL (e.g., loud machinery or direct speaker feedback aimed at the microphone), the RMS calculation may stay above the silence threshold.
- **Mitigation**: Audio auto-ducking reduces active background music to 20% while listening and speaking. If background noise remains high, the manual push-to-talk button or Enter key in the UI overrides the silence counter.

### 5.2 Hardware Physical Mute Switch
- **Behavior**: The Seeed ReSpeaker Lite USB features a physical push-button mute switch with LED indicators.
- **Limitation**: When muted at the hardware level, the USB audio stream produces digital zeros (RMS = 0.00). Software cannot programmatically unmute the physical microphone hardware.
- **Handling**: The wake engine reports microphone silence state without crashing, and the dashboard status center indicates audio capture readiness.

---

## 6. On-Device LLM Inference (Raspberry Pi 5 ARM64)

### 6.1 Inference Speed vs Fast-Path Routing
- **Latency Profile**:
  - Deterministic fast-path regex router: < 15ms
  - Hybrid router intent classification: 20–45ms
  - On-device Ollama CPU inference (`qwen2.5:3b` / `llama3.2:3b`): 8–14 tokens per second on Cortex-A76 cores.
- **Design Decision**: All Phase 3 desktop, media, search, and volume commands are routed through the deterministic fast-path executor, completely bypassing the LLM when explicit intent signatures match. LLM invocation is reserved solely for complex multi-turn reasoning and conversational queries.

---

## Summary Matrix

| Subsystem | Primary Constraint | Mitigation / Workaround | Status |
| :--- | :--- | :--- | :--- |
| **X11 Desktop** | Requires `DISPLAY=:0` for `xdotool` | Verified active on native X11 session | Protected |
| **DuckDuckGo** | Rate limits on burst scraping | Memory search session & caching | Protected |
| **YouTube Metadata** | 1.8–2.8s `yt-dlp` extraction time | Fast text ACK & flat-playlist query | Protected |
| **PipeWire Streams** | Transient stream IDs when paused | Graceful detection & stream-level isolation | Protected |
| **Master Sink** | Physical volume overwrite risk | Strict domain separation & sink quarantine | Enforced |
| **VAD Silence** | High ambient acoustic noise floor | Intelligent 20% music ducking & UI override | Protected |
| **LLM Generation** | 8–14 tok/s CPU generation speed | Hybrid router fast-path (< 15ms) | Optimized |
