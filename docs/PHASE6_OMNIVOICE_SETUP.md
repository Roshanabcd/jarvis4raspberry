# JARVIS OS — Phase 6 OmniVoice Setup & Voice Cloning Guide

**Personal Voice Integration, Reference Audio Validation, and Transparent Fallback**

---

## 1. Verified Personal Voice Reference Audio

The user's original reference voice samples were audited:

| File Path | Format | Sample Rate | Channels | Duration | SHA256 Checksum | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `/home/roshan/Downloads/myvoice_clean.wav` | RIFF PCM 16-bit | 24000 Hz | 1 (Mono) | 3.2s | `fb1422b0...` | **Optimal Reference Sample** |
| `data/voice_samples/myvoice_ref_clean.wav` | RIFF PCM 16-bit | 24000 Hz | 1 (Mono) | 3.2s | `fb1422b0...` | **Verified Identical Copy** |
| `/home/roshan/Downloads/myvoice.mp3` | MPEG ADTS Layer III | 48000 Hz | 2 (Stereo) | 5.2s | `38f5d5dc...` | Secondary Sample |
| `/home/roshan/Downloads/myvoice.mpeg` | MPEG ADTS Layer III | 48000 Hz | 2 (Stereo) | 5.2s | `edd911fa...` | Secondary Sample |

JARVIS automatically uses `/home/roshan/Downloads/myvoice_clean.wav` (and `data/voice_samples/myvoice_ref_clean.wav`) as the primary prompt audio for voice cloning.

---

## 2. Remote Google Colab OmniVoice Integration

The OmniVoice architecture runs on Google Colab (`Super_Eleven_Lab_Lite_2_1.ipynb`) backed by a GPU runtime. When started, it creates a public Gradio tunnel (`https://<hash>.gradio.live`).

### Dynamic URL Registration
When a new Colab notebook starts:
1. It executes an authenticated callback:
   `POST /api/voice/register_colab` (or `/api/integrations/omnivoice/register`)
2. With payload:
   ```json
   {
     "gradio_url": "https://<new-hash>.gradio.live",
     "session_id": "roshan_colab_2026",
     "token": "jarvis_omnivoice_secret_2026",
     "verify": true
   }
   ```
3. JARVIS instantly verifies the remote endpoint and updates its active cloner URL.

### Manual Registration in Dashboard Settings
If the Raspberry Pi is running locally behind NAT, the user can paste the newly generated `https://<hash>.gradio.live` link directly into **Voice Center** -> **Connect & Register**.

---

## 3. Truthful Provider Labelling & Neural Fallback

When Google Colab is offline or expired:
- **Badge:** `OMNIVOICE OFFLINE — FALLBACK ACTIVE`
- **Active Engine:** `Neural Fallback (Edge-TTS Ryan)`
- **Behavior:** The dashboard and API explicitly state that fallback is in use. Under no circumstances does JARVIS claim that a fallback synthetic voice is the user's cloned voice.
