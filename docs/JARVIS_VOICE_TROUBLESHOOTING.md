# JARVIS OS — Voice Subsystem Troubleshooting & Operations Guide

**Version:** 1.0.0  
**Target Architecture:** Raspberry Pi 5 ARM64  
**Operating System:** Debian GNU/Linux 13 (Trixie)  
**Audio Stack:** PipeWire 1.4.2 / WirePlumber 0.5.8 / ALSA  

This comprehensive guide details symptoms, root causes, diagnostic terminal commands, and step-by-step remediation procedures for all voice, audio, and avatar components in JARVIS OS.

---

## 1. Microphone Access & Hardware Detection

### Symptom:
Microphone displays "STANDBY" or "OFFLINE" in the dashboard, or voice recordings yield 0 bytes (silence).

### Root Causes:
1. ReSpeaker Lite USB microphone array disconnected or enumerated on a different ALSA card index.
2. User account lacks `audio` group membership.
3. PipeWire input node suspended or muted by system policy.

### Diagnostic Commands:
```bash
# 1. Check physical USB hardware connection
lsusb | grep -i seeed
# Expected: Bus 001 Device 004: ID 2886:0018 Seeed Technology Co., Ltd. ReSpeaker Lite

# 2. Check ALSA soundcards
arecord -l
# Check for "card 2: Lite [ReSpeaker Lite]" or similar

# 3. Check PipeWire sources
wpctl status | grep -A 8 "Audio -> Sources"

# 4. Test direct 2-second capture via PipeWire
pw-record --rate 16000 --channels 1 /tmp/test_mic.wav && ls -lh /tmp/test_mic.wav
```

### Remediation:
- **Set Default PipeWire Audio Source:**
  ```bash
  # Find node ID from wpctl status (e.g. 68)
  wpctl set-default 68
  wpctl set-volume 68 1.0
  wpctl set-mute 68 0
  ```
- **Fix User Permissions:**
  ```bash
  sudo usermod -aG audio,video $USER
  ```

---

## 2. TigerVNC Remote Audio & Browser Microphone Routing

### Symptom:
When accessing the JARVIS dashboard via a web browser inside a TigerVNC session (`localhost:5901`), clicking the microphone button or speaking does not capture the user's laptop microphone.

### Root Cause:
The standard RFB (VNC) protocol only transmits video framebuffer updates and keyboard/mouse input; it does **not** forward client audio or microphone input to the remote X11 server.

### Solution & Recommended Workflow:
JARVIS OS provides a dual-capture architecture:
1. **Direct Web Browser Access (Recommended for remote laptops):**
   Open Chrome, Firefox, or Safari on your client laptop and navigate directly to:
   `http://<RASPBERRY_PI_IP>:8000/`
   This grants the browser native access to your laptop's local microphone via the standard HTML5 `MediaRecorder` API. The audio is streamed securely over HTTP/WebSocket directly to `POST /api/voice/transcribe`.
2. **Local Physical Raspberry Pi Session:**
   When seated at the physical Raspberry Pi 5 with the ReSpeaker Lite USB microphone connected, both the browser push-to-talk button and the background `jarvis-voice.service` wake daemon capture the hardware microphone array.

---

## 3. Browser Audio Autoplay Restrictions & Avatar Lip-Sync

### Symptom:
JARVIS generates speech audio (`audio_url` is returned), but no sound plays through the browser speakers and the avatar mouth does not move.

### Root Cause:
Modern browsers enforce strict **Autoplay Policies** preventing audio playback until the user has performed an explicit gesture (click or tap) on the page. In addition, the Web Audio `AudioContext` initializes in a `suspended` state.

### Remediation:
1. **User Gesture Initialization:**
   Click anywhere on the dashboard or press the microphone / speaker test button. The `JarvisAvatar` controller automatically executes:
   ```javascript
   if (window.jarvisAudioContext && window.jarvisAudioContext.state === 'suspended') {
     window.jarvisAudioContext.resume();
   }
   ```
2. **Verify Audio Player Element:**
   Ensure `<audio id="jarvis-audio-player">` exists in the DOM and is unmuted.
3. **Browser Permission Settings:**
   In your browser's address bar, click the site settings padlock icon:
   - **Sound:** Allow
   - **Microphone:** Allow

---

## 4. Wake-Word Engine Tuning & Sensitivity

### Symptom:
The assistant either triggers repeatedly when nobody said "Jarvis" (false positive) or fails to trigger unless shouted at directly into the microphone (false negative).

### Root Cause:
Wake-word activation threshold requires acoustic calibration to match the room acoustics, reverberation, and background noise.

### Configuration Adjustment:
Edit `config/config.yaml`:
```yaml
voice:
  wake_word:
    engine: "openwakeword"
    wake_words: ["jarvis", "hey jarvis"]
    sensitivity: 0.50             # Range: 0.30 (more sensitive) to 0.80 (strict)
    cooldown_seconds: 2.0        # Minimum time between successive triggers
    history_frames: 10
    verification_mode: "hybrid"  # Verifies energy burst before deep inference
```
- **For noisy environments:** Increase `sensitivity` to `0.65` or `0.70`.
- **For quiet rooms or distant microphones:** Decrease `sensitivity` to `0.40`.

### Restart Voice Daemon:
```bash
sudo systemctl restart jarvis-voice.service
journalctl -u jarvis-voice.service -f
```

---

## 5. Voice Daemon vs. Push-to-Talk IPC Conflict

### Symptom:
Push-to-talk returns: `"The dedicated voice daemon owns the microphone. Use the daemon for voice interactions."`

### Root Cause:
In earlier legacy releases, the background `jarvis-voice.service` held an exclusive ALSA lock on the recording hardware, refusing API listen requests.

### Solution (Resolved in current build):
The updated `apps/voice/service.py` coordinates seamlessly with the wake daemon via UNIX socket IPC (`apps/voice/daemon_control.py`). When the web dashboard initiates push-to-talk:
1. `service.py` issues a `mute` command to the daemon to temporarily pause wake monitoring.
2. The user utterance is recorded and processed.
3. `service.py` issues an `unmute` command, returning the daemon to `STANDBY_LISTENING`.

To manually control or inspect daemon state:
```bash
# Check daemon socket
ls -l /tmp/jarvis_voice_daemon.sock

# Mute daemon via curl
curl -X POST http://localhost:8000/api/voice/daemon/mute

# Unmute daemon via curl
curl -X POST http://localhost:8000/api/voice/daemon/unmute
```

---

## 6. Text-to-Speech (TTS) Failures & Offline Fallback

### Symptom:
Voice replies sound like a robotic synthesizer (`espeak-ng`) instead of natural neural speech (ARIA or ATLAS).

### Root Causes & Fixes:
1. **Network Connectivity / DNS Outage:**
   Microsoft Edge-TTS relies on HTTPS access to `speech.platform.bing.com`. If the Raspberry Pi loses internet access, the system safely falls back to local `espeak-ng`.
   - Test connectivity:
     ```bash
     curl -I https://speech.platform.bing.com
     ```
2. **Cloud TTS Disabled in Configuration:**
   Verify `config/config.yaml`:
   ```yaml
   voice:
     cloud_tts_enabled: true
     fallback_voice: "en-US-AriaNeural"
     neural_voice: "en-US-AriaNeural"
   ```
3. **Verify edge-tts CLI tool:**
   ```bash
   ./venv/bin/edge-tts --voice en-US-AriaNeural --text "System diagnostic complete." --write-media /tmp/test_speech.mp3
   mpv /tmp/test_speech.mp3 || pw-play /tmp/test_speech.mp3
   ```

---

## 7. Avatar Viseme Animation Freezing

### Symptom:
Audio plays correctly, but the avatar mouth remains in `REST` position or freezes mid-sentence.

### Root Causes:
1. **Cross-Origin Audio Restriction:**
   If the audio file is served from a different origin or protocol without `crossOrigin="anonymous"`, the Web Audio `createMediaElementSource` node is silenced for security reasons.
2. **Missing MediaElementSource Connection:**
   The `AudioContext` was connected after the audio finished playing.

### Verification in Web Console (F12):
```javascript
// Check avatar driver state
console.log(window.jarvisAvatar);
console.log(window.jarvisLipSyncDriver);

// Manually trigger visemes to verify DOM binding
window.jarvisAvatar.setViseme('A'); // Mouth should open
window.jarvisAvatar.setViseme('O'); // Mouth should round
window.jarvisAvatar.setViseme('REST'); // Mouth returns to neutral
```

---

## 8. Service Management Quick Reference

| Service | Description | Command |
|---|---|---|
| `jarvis-backend.service` | Core FastAPI server (Port 8000) | `sudo systemctl restart jarvis-backend.service` |
| `jarvis-voice.service` | Real-time wake daemon & audio listener | `sudo systemctl restart jarvis-voice.service` |
| `jarvis-camera.service` | IMX708 RTSP/HTTP camera streamer | `sudo systemctl restart jarvis-camera.service` |
| `pipewire.service` | PipeWire audio subsystem | `systemctl --user restart pipewire pipewire-pulse` |

To inspect all JARVIS systemd unit logs simultaneously:
```bash
journalctl -u jarvis-backend.service -u jarvis-voice.service -f
```
