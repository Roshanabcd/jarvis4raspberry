---
title: OmniVoice Voice Cloner for JARVIS OS
emoji: 🎙️
colorFrom: indigo
colorTo: cyan
sdk: gradio
sdk_version: 5.6.0
app_file: app.py
pinned: false
---

# OmniVoice Voice Cloner & Synthesis Server

Permanent, production-ready cloud backend for JARVIS OS voice cloning.
Extracted and enhanced from the Super Eleven Lab Lite 2.1 project with:
- ZeroGPU support (`@spaces.GPU` decorator) for fast Nvidia A100 serverless inference.
- Dual interface: Web UI for testing and interactive synthesis + dedicated `/clone_voice` API endpoint for JARVIS OS background daemon.
- Reference audio voice cloning across 600+ languages.

## API Endpoint Reference

### `/clone_voice` (Dedicated API for JARVIS OS)
- **Parameters:**
  - `text` (str): Text prompt to synthesize.
  - `ref_audio` (audio / filepath): Reference voice sample (WAV/MP3).
  - `ref_text` (str, optional): Transcript of reference voice.
  - `num_steps` (int, default 32): Diffusion steps (8 to 64).
  - `speed` (float, default 1.0): Speech speed multiplier.
- **Returns:**
  - `audio` (audio file path): Synthesized 24kHz WAV audio.
  - `status` (str): Latency and generation details.
