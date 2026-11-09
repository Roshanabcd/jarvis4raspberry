# JARVIS OS — PipeWire Audio Stream Routing and Volume Protection

## 1. Overview

YouTube playback in JARVIS OS must route audio strictly through Google Chrome's native PipeWire stream to the physical audio output (ReSpeaker Lite Analog Stereo). It must NEVER start separate background audio streamers (`mpv`, `ffplay`, `pw-play`) for YouTube video requests, and it must keep the master hardware volume strictly protected.

---

## 2. Audio Topology on Raspberry Pi 5

```
+----------------------------------------------------------------------+
|                     Raspberry Pi 5 PipeWire Audio                     |
+----------------------------------------------------------------------+
                                  │
         ┌────────────────────────┴────────────────────────┐
         │                                                 │
+------------------+                              +------------------+
|  Chrome Browser  |                              | FreeTube Stream  |
|  YouTube Tab     |                              | Background Music |
|  (Stream: vol%)  |                              | (Stream: 100%)   |
+------------------+                              +------------------+
         │                                                 │
         └────────────────────────┬────────────────────────┘
                                  ▼
               +-------------------------------------+
               | Master Sink 112: ReSpeaker Lite     |
               | Analog Stereo (Hardware Volume 65%) |
               +-------------------------------------+
                                  │
                                  ▼
                     Physical Speaker Output
```

---

## 3. Audio Protection Rules

1. **Separation of Video Playback and Audio Streaming:**
   - YouTube video selections are opened exclusively in Google Chrome.
   - Chrome manages its own audio stream (`Google Chrome input` / `Chromium input` in PipeWire).
   - `media_player.py` is guarded: it will never download, extract, or stream audio for YouTube selection queries.
2. **Master Sink Volume Protection:**
   - Master Sink 112 (ReSpeaker Lite Analog Stereo) is maintained at 65% (`0.65`).
   - YouTube video volume commands (`"Set video volume to 80%"`) adjust ONLY the Chrome application stream volume via `audio_stream_manager.set_app_volume("chrome", 80)`.
   - The master hardware sink volume is never overridden by YouTube playback.
3. **Background Stream Non-Interference:**
   - Any background music streams (such as FreeTube at 100%) remain playing and are not killed or unlinked during YouTube video selection.
