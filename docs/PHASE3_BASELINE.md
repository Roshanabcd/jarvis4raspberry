# JARVIS OS — Phase 3 Baseline & Diagnostic Report

**Date:** 2026-11-09  
**Platform:** Raspberry Pi 5 (8 GB RAM, Broadcom BCM2712 Quad-Core Cortex-A76 @ 2.4 GHz)  
**Operating System:** Debian GNU/Linux 13 (Trixie) ARM64  
**Desktop Environment:** Native X11 (`DISPLAY=:0`), Openbox Window Manager, Resolution 1360 × 768  
**Repository Branch:** `feat/jarvis-phase3-browser-agent` (Branched from `b774c0b`)  
**Active Services:** Uvicorn on `http://localhost:8000/`, Ollama on `http://127.0.0.1:11434`  

---

## 1. Root Cause Analysis: The "Me at the zoo" Anomaly

### Observed Bug
When the user previously asked:
1. *"Search YouTube for a Hindi song."* $\rightarrow$ YouTube search page opened in browser.
2. *"Play the first video."* $\rightarrow$ JARVIS responded:
   > *"🎵 Now playing 'Me at the zoo' from online stream through the physical speaker."*

### Root Cause Discovery
Inspection of `ai/local_engine.py` and `tools/media/media_player.py` revealed:
1. **Absence of Contextual Media Session State:**
   In `ai/local_engine.py:26`, the regex pattern:
   ```python
   (r"\bplay\s+([a-zA-Z0-9_\-\s\'\"]+)", "play_media", None)
   ```
   matched the sentence `"Play the first video"`. It extracted `m_track = "the first video"` as a literal search query rather than a positional index reference to the preceding YouTube search!
2. **Literal ytsearch Execution:**
   `media_player.play("the first video")` executed yt-dlp:
   ```bash
   yt-dlp "ytsearch1:the first video" --get-title --get-url
   ```
   The first video ever uploaded to YouTube in history (uploaded April 23, 2005 by Jawed Karim) is titled **"Me at the zoo"**. YouTube's relevance algorithm literally returned "Me at the zoo" as the #1 match for the string *"the first video"*.
3. **Stream Redirection to Local Speaker:**
   Instead of launching or controlling the video in the active Chrome browser, `MediaPlayer` streamed the raw audio via `pw-play` through the Raspberry Pi's physical speaker.

### Resolution Plan for Phase 3
- Implement `BrowserSearchManager` and `YouTubePlayerController` maintaining an ordered list of search results (`SearchSession`).
- When the user commands *"Play the first video"*, resolve index 0 from the active search session, extract its actual video ID and title, navigate the browser to `https://www.youtube.com/watch?v={video_id}`, and verify video playback in the browser.

---

## 2. Root Cause Analysis: Audio Volume Jumps & Background Music Interruption

### Observed Bug
When JARVIS checks applications, runs diagnostics, or adjusts sound:
- Audio suddenly jumps to 100% or drops to 0%.
- Background music (e.g. FreeTube, VLC, Spotify, browser tabs) gets interrupted or terminated.

### Root Cause Discovery
1. **Global Master Sink Manipulation:**
   In `tools/media/media_player.py:332`:
   ```python
   def set_volume(self, level_pct: int) -> Dict[str, Any]:
       target = max(0, min(100, int(level_pct)))
       fraction = target / 100.0
       if shutil.which("wpctl"):
           subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{fraction:.2f}"])
   ```
   Any volume instruction—even *"Set YouTube volume to 50%"*—executed `wpctl set-volume @DEFAULT_AUDIO_SINK@ ...`, which forcefully overwrote the **hardware master volume** for all applications on node 106 (`ReSpeaker Lite Analog Stereo`).
2. **Hardcoded Max Volume in Diagnostics:**
   Historical troubleshooting scripts and diagnostic guides ran `wpctl set-volume 54 1.0` or `amixer set Master 100%`, blowing out the speaker to 100% during testing.
3. **Uncoordinated Playback Interruption:**
   Calling `stop_media` terminated player processes without checking if the user intended to pause an active browser video or a local audio player.

### Resolution Plan for Phase 3
- Implement `AudioStreamManager` separating volume control into four distinct layers:
  1. **HTML5 Video Player Volume:** Controlled via JavaScript/CDP inside the web page without touching system volume.
  2. **Application Stream Volume:** Controlled via PipeWire per-stream sink inputs (`wpctl set-volume <stream_id>`).
  3. **JARVIS Voice Stream Volume:** Independent software gain for assistant speech.
  4. **Master Hardware Volume:** Modified ONLY when the user explicitly commands *"Set system volume to X%"*.
- Strict non-interference policy: Zero modification of global master sink during diagnostics, app discovery, or Antigravity checks. Unrelated audio streams are never killed or suspended.

---

## 3. Audio Hardware & Stream Diagnostics

From live PipeWire 1.4.2 inspection:
- **Audio Capture Device:** Seeed Studio ReSpeaker Lite USB (`card 2: Lite`), Node 127 (Volume: 0.94)
- **Audio Playback Sink:** Seeed Studio ReSpeaker Lite USB (`card 2: Lite`), Node 106 (Volume: 0.60, Default)
- **Active Music Streams:** FreeTube / browser audio streams active without interference.

---

## 4. Browser Automation Baseline

- **Google Chrome:** Installed at `/usr/bin/google-chrome` (v157 ARM64).
- **User Profile:** Located at `/home/roshan/.config/google-chrome`. Authenticated user profiles and login cookies must be preserved without data loss.
- **Automation Approach:**
  Implement a dual-mode browser controller:
  1. Direct Chrome remote debugging interface / CDP WebSocket communication on local debugging port.
  2. Native desktop browser navigation fallback via URL management and X11 window inspection.
