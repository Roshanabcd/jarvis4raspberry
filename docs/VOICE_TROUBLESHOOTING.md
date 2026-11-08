# JARVIS OS — Voice Subsystem Troubleshooting & Failure Recovery

This document provides diagnosis procedures and solutions for common voice pipeline and OmniVoice integration issues.

---

## 1. Diagnostics Quick Check

Run the following commands on your Raspberry Pi:

```bash
# 1. Voice pipeline & hardware status
curl -s http://127.0.0.1:8000/api/voice/status

# 2. OmniVoice Colab integration status
curl -s http://127.0.0.1:8000/api/integrations/omnivoice/status

# 3. Audio hardware device detection
curl -s http://127.0.0.1:8000/api/voice/devices
```

---

## 2. Common Issues & Solutions

### Issue A: Status Displays `OMNIVOICE OFFLINE — FALLBACK VOICE ACTIVE`
- **Cause:** The Google Colab instance has terminated, timed out, or a new Gradio URL was generated without re-registering.
- **Solution:**
  1. Open Colab and run all cells in `Super_Eleven_Lab_Lite_2_1.ipynb`.
  2. Copy the new `https://<hash>.gradio.live` share URL.
  3. In JARVIS Web Dashboard, go to **Voice Center**, paste the URL into the Colab panel, and click **Connect & Register**.
  4. The status badge will immediately turn `🟢 CLONED VOICE READY`.

### Issue B: Cloned Voice Synthesis Takes Too Long (>30 seconds)
- **Cause:** High diffusion step count or GPU throttling on free tier Colab instances.
- **Solution:**
  - The default diffusion step count in JARVIS is set to 24 (balanced for speed and acoustic clarity).
  - Check GPU utilization in Colab via `!nvidia-smi`.
  - Ensure other heavy background notebooks are terminated.

### Issue C: Registration Rejected: `401 Unauthorized`
- **Cause:** The registration secret token does not match.
- **Solution:**
  - Default token: `jarvis_omnivoice_secret_2026`.
  - If changed in `.env` (`OMNIVOICE_REGISTRATION_TOKEN`), use the same token in Colab or register directly from the local Web Dashboard (`127.0.0.1`).

### Issue D: Microphone Captures Silence
- **Cause:** Microphone muted or wrong default ALSA capture source.
- **Solution:**
  - Verify Seeed ReSpeaker Lite USB is connected: `arecord -l` should show `card 2, device 0`.
  - Test raw capture: `pw-record -d 55 /tmp/test.wav` then `pw-play /tmp/test.wav`.
  - Unmute via Web Dashboard or `POST /api/voice/unmute`.

### Issue E: Audio Plays in Browser but Not on Raspberry Pi Speaker
- **Cause:** Voice routing policy set to `browser` only, or system volume muted.
- **Solution:**
  - Set `voice.routing_policy: "both"` in `config/config.yaml`.
  - Check PipeWire volume: `wpctl set-volume 54 1.0` (unmutes and sets ReSpeaker sink 54 to 100%).
