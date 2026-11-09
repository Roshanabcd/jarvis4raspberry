# JARVIS OS — Phase 3F & 3G: Audio Stream Separation & Music Preservation

## Overview
Phase 3F and 3G fixes the audio volume jump and background music interruption defect. Previously, inspecting system state, launching Antigravity/VS Code, or adjusting volume would suddenly jump system volume to 100% or terminate ongoing audio playback (such as FreeTube, VLC, or Spotify). The new **Central Audio Stream Manager** (`tools/media/audio_stream_manager.py`) provides clear stream separation, protects the hardware master sink, and implements intelligent audio ducking.

---

## Root Cause Analysis: Audio Volume Jump & Music Interruption

### 1. Master Sink Overwriting
- Previous code in `media_player.set_volume(level)` called:
  ```python
  subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{fraction:.2f}"])
  ```
- Because `@DEFAULT_AUDIO_SINK@` represents the physical hardware DAC (Sink 119: ReSpeaker Lite Analog Stereo), every volume adjustment forcibly changed the entire system's master amplifier level.
- Furthermore, diagnostic scripts previously issued `wpctl set-volume 54 1.0`, pinning the hardware speaker to 100% volume.

### 2. Accidental Process Termination
- Diagnostic routines or application launchers using broad kill commands (`pkill -f ...`, `killall pw-play`) were inadvertently terminating external media player streams like FreeTube and background media.

---

## Architectural Solution: Central Audio Stream Manager

### 1. Four Separated Audio Domains
1. **Video Player Domain:** Adjusts player volume via Chrome shortcuts or per-app stream control.
2. **Application Stream Domain:** Adjusts volume of specific PipeWire application streams (`wpctl set-volume <stream_id> <vol>`) without touching other applications or the master sink.
3. **JARVIS Speech Domain:** Dedicated speech synthesis stream gain (`pw-play`).
4. **Master Hardware Sink:** Protected domain. Only modified when the user explicitly commands: *"Set system volume to X%"* or *"Set master volume to X%"*.

### 2. Intelligent Audio Ducking
- When JARVIS initiates speech synthesis (`SpeechOutputManager.play_system_audio`):
  1. The manager queries active playback streams (`wpctl status`).
  2. Any active background media stream (e.g., FreeTube stream 110, VLC, Spotify) has its current volume saved and ducked to **20%** (`duck_active_streams(duck_fraction=0.20)`).
  3. JARVIS speaks the response clearly through the ReSpeaker Lite physical speaker.
  4. As soon as the `pw-play` process terminates, a completion daemon hook immediately calls `restore_active_streams()`, restoring the background music smoothly to its original 100% level without interruption.

---

## Verification Evidence
- PipeWire Topology on Raspberry Pi 5:
  - Master Sink 119: ReSpeaker Lite Analog Stereo (maintained at 0.45 / 45%).
  - Active Stream 110: FreeTube playback stream.
- Per-Stream Adjustment Test:
  - `audio_stream_manager.set_stream_volume(110, 0.80)` modified FreeTube volume without changing Sink 119.
- Ducking / Restoration Test:
  - Speech playback triggered ducking on Stream 110 from 1.00 down to 0.20.
  - Process termination restored Stream 110 to 1.00 cleanly.
