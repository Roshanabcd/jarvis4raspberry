# JARVIS OS — Personal Voice Profile Setup & Reference Audio Guide

This document details how personal voice reference profiles are managed, discovered, validated, and processed by the OmniVoice pipeline in JARVIS OS.

---

## 1. Reference Audio Search Hierarchy

When initializing or executing voice cloning, JARVIS checks candidate paths in the following priority order:

1. `reference_voice_path` parameter (explicit API or method argument)
2. `GRADIO_VOICE_SAMPLE` environment variable
3. `/home/roshan/Downloads/myvoice.mp3` (Primary authenticated user voice sample)
4. `/home/roshan/Downloads/myvoice.mpeg`
5. `/home/roshan/Downloads/myvoice.wav`
6. `/home/roshan/Music/myvoice.mpeg`
7. `/home/roshan/Music/myvoice.mp3`
8. `/home/roshan/myvoice.mp3`
9. `voice.reference_audio_path` in `config/config.yaml`
10. `data/voice_samples/myvoice.wav` (Project fallback reference)

The first candidate that exists on disk and exceeds 100 bytes is selected and cached.

---

## 2. Voice Sample Specifications

For optimal cloning results with OmniVoice:

| Attribute | Recommended | Minimum Accepted |
| :--- | :--- | :--- |
| **Duration** | 10 – 90 seconds | 5 seconds |
| **Format** | MP3, WAV, MPEG (audio container) | Any standard audio container |
| **Sample Rate** | 24,000 Hz or 48,000 Hz | 16,000 Hz |
| **Channels** | Mono or Stereo (downmixed) | Mono |
| **Content** | Clear natural speaking voice, minimal background noise | Speech without loud music |

### Current Active Voice Sample:
- **Path:** `/home/roshan/Downloads/myvoice.mp3`
- **Duration:** 83.14 seconds
- **Format:** MPEG Audio Layer 3 (stereo, 48,000 Hz, 320 kbps)
- **Size:** 2.99 MB

---

## 3. How OmniVoice Clones the Voice

When synthesis is requested:
1. JARVIS normalizes and sanitizes text (`sanitize_speech_text`) to strip code blocks, markdown tags, and emojis.
2. The reference sample is passed via `gradio_client.handle_file(...)` to the `/generate` endpoint.
3. OmniVoice extracts pitch, timbre, cadence, and acoustic embeddings from the reference sample.
4. The diffusion model iterates for 24 steps conditioned on the extracted embeddings and input text.
5. The generated WAV audio is returned, validated via RIFF header checks, saved to the local cache, and staged for playback.
