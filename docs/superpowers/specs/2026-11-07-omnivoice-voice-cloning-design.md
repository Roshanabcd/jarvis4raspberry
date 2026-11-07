# Design Document: Permanent OmniVoice Cloud Endpoint & JARVIS OS Integration

## Intent & The Why
JARVIS OS requires custom voice cloning based on the user's "Super Eleven Lab Lite 2.1" project (which runs OmniVoice from `k2-fsa/OmniVoice`). Previously, the user ran this in Google Colab, generating temporary Gradio live URLs (e.g. `https://13f7044a4e78090fd2.gradio.live/`) that expire every 72 hours, causing JARVIS OS to lose its cloned voice and fall back to robotic offline local TTS (`espeak`).
The user wants a seamless solution so that whenever JARVIS OS starts, it can automatically access the voice cloning model, pass the desired reference audio sample, generate cloned speech, and speak to the user.

## Goals, Non-Goals, and Anti-Goals
- **Goals:**
  1. Package the exact "Super Eleven Lab Lite 2.1" OmniVoice engine into an always-on, non-expiring cloud endpoint (Hugging Face Space with Gradio SDK).
  2. Provide zero-configuration startup for JARVIS OS: the background service (`jarvis-core.service`) boots and immediately links to the permanent endpoint without manual link copying.
  3. Support reference voice cloning with optional caching on the Pi 5 to keep recurring phrase latency under 5ms.
  4. Maintain graceful offline fallback to local TTS if network connectivity is ever lost.
- **Non-Goals:**
  - Running 3–5 GB diffusion TTS models directly on the Raspberry Pi 5 CPU (which would induce 30–60 second latency per phrase).
  - Attempting to bypass Google Colab CAPTCHAs/OAuth via headless terminal scripts (which violates Colab terms of service and breaks after minutes).
- **Anti-Goals:**
  - Requiring the user to open Colab and copy-paste new URLs every 72 hours.
  - Hardcoding ephemeral URLs in source code.

## Constraints
1. **Target SBC:** Raspberry Pi 5 (Quad-Core Cortex-A76, Debian 13 Trixie, no CUDA GPU).
2. **Network/Cloud:** Free-tier Hugging Face Spaces provides free hosting with optional ZeroGPU for fast model inference.
3. **Endpoint Schema:** The Gradio application must expose clean, named API endpoints (`/generate` and `/clone_voice`) that accept `text`, `ref_audio`, and generation parameters.

## Approaches Considered
1. **Approach 1: Permanent Hugging Face Space (Chosen)**
   - *Architecture:* Deploy the extracted OmniVoice Gradio application to a dedicated Hugging Face Space. Configure JARVIS OS to connect directly to the permanent Space URL (`https://<username>-<space>.hf.space` or HF Space ID).
   - *Pros:* Never expires, 100% free, runs 24/7, optional ZeroGPU acceleration, no daily human intervention needed.
   - *Cons:* Requires one-time deployment of the Space to a Hugging Face account.
2. **Approach 2: Google Colab Webhook Sync**
   - *Architecture:* Keep running in Colab, but add a script cell that automatically posts the new Gradio live URL to JARVIS OS's local API via ngrok/tailscale webhook.
   - *Pros:* Keeps running on Google Colab GPUs.
   - *Cons:* Colab still times out after 15–30 minutes of inactivity, disconnects after a few hours, and requires constant manual re-execution in a browser.
3. **Approach 3: Local Pi 5 CPU Diffusion Inference**
   - *Architecture:* Install OmniVoice directly into the Pi 5's Python virtual environment.
   - *Pros:* Fully offline.
   - *Cons:* Severe performance bottleneck; 32 diffusion steps on 4 ARM CPU cores takes ~45 seconds per sentence, unusable for real-time conversation.

## System Architecture & Integration Details

### 1. Hugging Face Space Package (`hf_spaces/omnivoice/`)
- `app.py`: Extracted from "Super Eleven Lab Lite 2.1", optimized with `@spaces.GPU` for serverless GPU acceleration, exposing:
  - Standard interactive Gradio UI for web browser testing.
  - Named API endpoint `/clone_voice` taking `(text: str, ref_audio: filepath, num_steps: int, speed: float)`.
- `requirements.txt`: `omnivoice`, `gradio>=5.0.0`, `torch`, `torchaudio`, `spaces`.
- `README.md`: Hugging Face Space metadata block (`title`, `sdk: gradio`, `app_file: app.py`).
- `deploy_space.sh`: Interactive 1-step deployment script using `huggingface-cli` or git push to deploy to the user's HF account.

### 2. JARVIS OS Voice Pipeline Updates (`apps/voice/`)
- `apps/voice/gradio_tts.py`:
  - Enhance `_probe_gradio_client` to support both direct HTTP URLs and Hugging Face Space IDs (e.g. `username/omnivoice-cloner`).
  - Implement direct invocation of `/clone_voice` or dynamic parameter binding for OmniVoice.
  - Automatically pass the configured reference audio sample (`GRADIO_VOICE_SAMPLE` or `config.voice.reference_audio_path`).
  - Cache synthesized WAV audio locally in `~/.cache/jarvis_voice_cache/` so identical phrases play instantly.
- `config/config.yaml` & `.env`:
  - Add `GRADIO_VOICE_URL` pointing to the permanent Space.
  - Add `GRADIO_VOICE_SAMPLE` pointing to the chosen reference WAV/MP3 file.

## What's Left for the Builder
- Generate the complete, self-contained Hugging Face Space deployment repository (`hf_spaces/omnivoice/`).
- Update `apps/voice/gradio_tts.py` to target the named OmniVoice endpoint and reference voice file.
- Add configuration parameters to `config/config.yaml` and `.env`.
- Add test coverage in `tests/voice/test_gradio_tts.py` verifying API discovery, cloning fallback, and audio caching.
