# OmniVoice Permanent Voice Cloning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate the user's "Super Eleven Lab Lite 2.1" OmniVoice cloning engine into JARVIS OS via a permanent Hugging Face Space package and reference voice sample (`myvoice.mpeg`), with automated fallback, caching, and startup auto-connection.

**Architecture:** A standalone Hugging Face Space repository (`hf_spaces/omnivoice/`) encapsulates the OmniVoice Gradio server with ZeroGPU support (`@spaces.GPU`) and a dedicated `/clone_voice` endpoint. The reference voice sample (`myvoice.mpeg`) is standardized in `data/voice_samples/`. In JARVIS OS, `GradioVoiceCloner` connects to the permanent Space, passes the reference sample, caches synthesized phrases under `~/.cache/jarvis_voice_cache/`, and falls back to local TTS if offline.

**Tech Stack:** Python 3.14 / Python 3.11, Gradio 5.x, PyTorch, OmniVoice, gradio_client, Pytest, FFmpeg / Wave.

**Spec:** [`docs/superpowers/specs/2026-11-07-omnivoice-voice-cloning-design.md`](file:///home/roshan/.gemini/antigravity/scratch/jarvis-os/docs/superpowers/specs/2026-11-07-omnivoice-voice-cloning-design.md)

## Global Constraints

- Never hardcode ephemeral `.gradio.live` links; use configurable `GRADIO_VOICE_URL` or HF Space identifier.
- Preserve 100% test pass rate across existing 143 test cases in `tests/`.
- Offline resilience: If network is unavailable or cloud Space is sleeping, JARVIS must never crash or block speech; it must gracefully fall back to local TTS.
- Audio header validation: Audio outputs must be verified before caching or playing (WAV RIFF, MP3 ID3/MPEG frame).

## Review Focus

1. **Unreachable / Sleeping Cloud Space:** Must trigger offline fallback within probe timeout without hanging user interaction.
2. **Missing Reference Voice File:** When `GRADIO_VOICE_SAMPLE` points to a non-existent path, must log a clear warning and fall back to local TTS.
3. **MPEG/MP3 vs WAV Header Validation:** `_validate_audio_file` must accept both WAV RIFF headers and MPEG/MP3 audio frames.
4. **Cache Key Determinism:** Identical text must hit disk cache without re-querying the cloud endpoint.
5. **Special Characters / Tag Stripping:** Text containing non-verbal tags (e.g. `[laughter]`) or markdown should be sanitized before synthesis.

---

### Task 1: Reference Voice Standardization & Header Validation

**Files:**
- Create: `data/voice_samples/myvoice.wav`
- Modify: `apps/voice/gradio_tts.py:145-165`
- Test: `tests/voice/test_gradio_tts.py`

**Interfaces:**
- Consumes: `/home/roshan/Downloads/myvoice.mpeg`
- Produces: `data/voice_samples/myvoice.wav`, updated `GradioVoiceCloner._validate_audio_file(file_path: str) -> bool` supporting MPEG/MP3 and WAV.

- [ ] **Step 1: Write the failing test for MP3/MPEG header validation and reference sample detection**

```python
def test_validate_mp3_and_reference_audio(tmp_path):
    from apps.voice.gradio_tts import GradioVoiceCloner
    cloner = GradioVoiceCloner(gradio_url="http://disabled", cache_dir=str(tmp_path))
    # Test valid MP3 header
    mp3_file = tmp_path / "sample.mp3"
    mp3_file.write_bytes(b"\xff\xfb\x90\x44" + b"\x00" * 200)
    assert cloner._validate_audio_file(str(mp3_file)) is True
```

- [ ] **Step 2: Run test to verify it fails or needs implementation**

Run: `python3 -m pytest tests/voice/test_gradio_tts.py -k test_validate_mp3_and_reference_audio -v`
Expected: FAIL or missing verification

- [ ] **Step 3: Convert `myvoice.mpeg` to `data/voice_samples/myvoice.wav` and update `_validate_audio_file`**

Standardize `myvoice.mpeg` into `data/voice_samples/myvoice.wav` (24kHz mono 16-bit PCM for optimal OmniVoice cloning) using `ffmpeg -y -i /home/roshan/Downloads/myvoice.mpeg -ar 24000 -ac 1 data/voice_samples/myvoice.wav`.
Update `_validate_audio_file` in `apps/voice/gradio_tts.py` to check for MP3 frame sync (`0xFF 0xFB/0xF3/0xF2` or `ID3`) and WAV (`RIFF....WAVE`).

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/voice/test_gradio_tts.py -k test_validate_mp3_and_reference_audio -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add data/voice_samples/ apps/voice/gradio_tts.py tests/voice/test_gradio_tts.py
git commit -m "feat(voice): standardize reference voice sample and add robust audio header validation"
```

---

### Task 2: OmniVoice Hugging Face Space Package & ZeroGPU Engine

**Files:**
- Create: `hf_spaces/omnivoice/app.py`
- Create: `hf_spaces/omnivoice/requirements.txt`
- Create: `hf_spaces/omnivoice/README.md`
- Create: `hf_spaces/omnivoice/deploy.sh`

**Interfaces:**
- Consumes: Code extracted from `/home/roshan/Downloads/Copy of Super Eleven Lab Lite 2.1`
- Produces: Complete, deployable Hugging Face Space repository with `/clone_voice` endpoint and ZeroGPU `@spaces.GPU` decorator.

- [ ] **Step 1: Write integration test verifying Space package structure and syntax**

```python
def test_hf_space_package_structure():
    import os
    base = "hf_spaces/omnivoice"
    assert os.path.exists(f"{base}/app.py")
    assert os.path.exists(f"{base}/requirements.txt")
    assert os.path.exists(f"{base}/README.md")
    assert os.path.exists(f"{base}/deploy.sh")
    with open(f"{base}/README.md") as f:
        content = f.read()
    assert "sdk: gradio" in content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/voice/test_gradio_tts.py -k test_hf_space_package_structure -v`
Expected: FAIL (files do not exist yet)

- [ ] **Step 3: Create Hugging Face Space package files**

Generate `hf_spaces/omnivoice/app.py` with:
- OmniVoice model loading with ZeroGPU decorator (`import spaces` fallback).
- Gradio web UI from the user's project.
- Dedicated named API endpoint:
  ```python
  @spaces.GPU
  def clone_voice_api(text: str, ref_audio, num_steps: int = 32, speed: float = 1.0):
      ...
  ```
Generate `hf_spaces/omnivoice/requirements.txt`, `hf_spaces/omnivoice/README.md`, and `hf_spaces/omnivoice/deploy.sh`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/voice/test_gradio_tts.py -k test_hf_space_package_structure -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add hf_spaces/omnivoice/ tests/voice/test_gradio_tts.py
git commit -m "feat(voice): create deployable OmniVoice Hugging Face Space package with ZeroGPU"
```

---

### Task 3: GradioVoiceCloner Space URL & Reference Sample Parameter Binding

**Files:**
- Modify: `apps/voice/gradio_tts.py:43-145,195-245`
- Test: `tests/voice/test_gradio_tts.py`

**Interfaces:**
- Consumes: `config.voice.gradio_url`, `config.voice.reference_audio_path`
- Produces: `GradioVoiceCloner.synthesize()` with automatic reference audio transmission, fallback, and caching.

- [ ] **Step 1: Write test for Space URL resolution and parameter binding**

```python
def test_cloner_reference_voice_configuration(tmp_path):
    from apps.voice.gradio_tts import GradioVoiceCloner
    sample = tmp_path / "ref.wav"
    sample.write_bytes(b"RIFF$   WAVEfmt " + b"\x00" * 30)
    cloner = GradioVoiceCloner(
        gradio_url="https://test-user-space.hf.space",
        reference_voice_path=str(sample),
        cache_dir=str(tmp_path / "cache")
    )
    status = cloner.get_provider_status()
    assert status["has_reference_audio"] is True
    assert status["url"] == "https://test-user-space.hf.space"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/voice/test_gradio_tts.py -k test_cloner_reference_voice_configuration -v`
Expected: FAIL or partial mismatch

- [ ] **Step 3: Update `apps/voice/gradio_tts.py`**

- Allow HF Space IDs (`username/space_name`) and full URLs (`https://*.hf.space`).
- In `synthesize()`, prioritize `/clone_voice` endpoint with `handle_file(self.reference_voice_path)`.
- Fall back gracefully to local TTS if remote call fails.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/voice/test_gradio_tts.py -k test_cloner_reference_voice_configuration -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/voice/gradio_tts.py tests/voice/test_gradio_tts.py
git commit -m "feat(voice): enhance GradioVoiceCloner with HF Space integration and reference audio binding"
```

---

### Task 4: Configuration Update, System Integration & Full Test Suite

**Files:**
- Modify: `config/config.yaml:5-10`
- Modify: `.env:21-27`
- Modify: `.env.example:21-27`
- Test: All suites in `tests/`

**Interfaces:**
- Consumes: Standardized voice sample at `data/voice_samples/myvoice.wav`
- Produces: Updated runtime configuration, passing test suite.

- [ ] **Step 1: Update configuration files**

Set `reference_audio_path: data/voice_samples/myvoice.wav` in `config/config.yaml`.
Add `GRADIO_VOICE_SAMPLE=/home/roshan/.gemini/antigravity/scratch/jarvis-os/data/voice_samples/myvoice.wav` to `.env` and `.env.example`.

- [ ] **Step 2: Run full automated test suite**

Run: `python3 -m pytest tests/ -v`
Expected: 143+ tests PASS (100% PASS)

- [ ] **Step 3: Commit and verify git status**

```bash
git add config/config.yaml .env.example
git commit -m "chore(config): configure reference voice audio and HF space voice cloning settings"
```
