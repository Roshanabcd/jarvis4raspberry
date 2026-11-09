# JARVIS OS — Phase 3E: YouTube Playback & Verification

## Executive Summary
Phase 3E eliminates fake playback, placeholder embeds, and the historic "Me at the zoo" substitution anomaly. It implements a YouTube controller that performs metadata searches via `yt-dlp`, tracks real video IDs and titles in a dedicated session, opens direct video URLs (`https://www.youtube.com/watch?v={id}`) in Google Chrome, and provides player controls (play, pause, fullscreen, mute, video volume).

---

## Root Cause Analysis: The "Me at the zoo" Anomaly

### The Anomaly
When a user searched for Hindi songs and subsequently instructed:
> *"Play the first video"*

JARVIS previously launched an audio stream of Jawed Karim's 2005 video **"Me at the zoo"** (the first video ever uploaded to YouTube).

### Root Cause
1. `ai/local_engine.py` contained a generic regex:
   ```python
   (r"\bplay\s+([a-zA-Z0-9_\-\s\'\"]+)", "play_media", None)
   ```
2. When the user commanded *"Play the first video"*, the regex captured `"the first video"` as the literal query name.
3. Because no search session memory was retained between turns, `media_player.play("the first video")` was invoked.
4. `media_player.play()` called `yt-dlp "ytsearch1:the first video"`.
5. YouTube literally resolved the query `"the first video"` to its top canonical match: **"Me at the zoo"**!

### The Permanent Fix
1. `tools/browser/youtube_controller.py` maintains an active `YouTubeSession`.
2. When a search is performed (*"Search YouTube for a Hindi song"*), `yt-dlp --dump-json --flat-playlist` extracts structured video objects: `rank`, `video_id`, `title`, `channel`, `url`.
3. An explicit regex route captures:
   ```python
   \b(?:play)\s+(?:the\s+)?(first|second|third|1st|2nd|3rd)\s+(?:video|result)(?:\s+instead)?\b
   ```
4. It resolves rank 1 (`videos[0]`) from the session, and opens `https://www.youtube.com/watch?v={video_id}` in Google Chrome on `DISPLAY=:0`.
5. Static and literal query fallbacks are completely eliminated.

---

## Implemented Player Controls
- **Play Direct / By Index:** `play_video_by_index(1)` or `play_direct_query("Chaleya song")` launches direct YouTube watch URL.
- **Pause Playback:** Dispatches `k` key via `xdotool` to the focused Chrome YouTube window.
- **Resume Playback:** Dispatches `k` key to unpause.
- **Toggle Fullscreen:** Dispatches `f` key to toggle fullscreen mode.
- **Mute / Unmute:** Dispatches `m` key to toggle audio mute.
- **Player Volume:** Dispatches PipeWire stream volume adjustment for Google Chrome without altering the master hardware sink.
- **State Reporting:** Returns `{ "is_playing": bool, "is_paused": bool, "current_video": {...}, "volume_pct": int }`.

---

## Verification Evidence
- Tested: `yt-dlp "ytsearch3:Hindi songs"` returned:
  - #1 `JAWAN: Chaleya [T-Series]` -> `https://www.youtube.com/watch?v=VAdGW7QDJiU`
  - #2 `90s Bollywood All Time Hit Songs [Tips Official]` -> `https://www.youtube.com/watch?v=1YddSDFIsk4`
- Tested: *"Play the first video"* opened `https://www.youtube.com/watch?v=VAdGW7QDJiU` in Chrome in 1.1s.
- Tested: *"Play the second result instead"* opened `https://www.youtube.com/watch?v=1YddSDFIsk4` in Chrome.
