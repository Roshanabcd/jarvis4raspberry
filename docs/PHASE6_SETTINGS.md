# JARVIS OS — Phase 6 Settings Architecture & Configuration Center

**Comprehensive System Configuration & Persistence Strategy**

---

## 1. Categories Implemented & Persisted

All settings connect to `/home/roshan/.gemini/antigravity/scratch/jarvis-os/config/config.yaml` and runtime state:

### 1. General Settings
- Application startup and desktop auto-login.
- Standalone launcher behavior.
- UI Theme (Dark Navy / Cyan Arc-Reactor palette).
- Window geometry preference (Default: 1360×768).

### 2. AI Engine Settings
- Active provider selection (`ollama`, `gemini`, `openai`, `anthropic`).
- Local Ollama models (`llama3.2:1b`, `qwen3.5:4b`).
- Cold-start timeouts and CPU inference tuning.
- System prompt rules and tool calling gates.

### 3. Microphone & Speech-to-Text Settings
- Default capture device (`Seeed ReSpeaker Lite USB`).
- Capture backend (`pw-record` on PipeWire).
- Sample rate: 16000 Hz, Channels: 1.
- Wake phrase patterns: `Wake up JARVIS`, `JARVIS`.
- Speech recognition engine: Google Web Speech API with Whisper local fallback.
- Voice Activity Detection energy threshold: `120.0` RMS.
- Silence timeout threshold: `3.0` seconds.

### 4. Physical Speaker Settings
- Default output sink: `ReSpeaker Lite Analog Stereo` (PipeWire Node 54).
- Safe volume default: `0.65` (65%).
- Auto-speak toggle (asynchronously synthesize all final AI responses).
- Media ducking toggle: ducks background players to 20% during speech, restores automatically.

### 5. Personal Voice Cloning Settings
- Reference prompt audio: `/home/roshan/Downloads/myvoice_clean.wav`.
- Phonetic alignment guide text: `Good morning everyone, my name is Roshan Sharma.`.
- Diffusion steps: `32` steps.
- Speaking pace: `0.85x`.
- Google Colab Gradio registration endpoint: `/api/voice/register_colab`.
- Neural fallback provider: `Edge-TTS Ryan` (`en-GB-RyanNeural`).

### 6. Privacy & Security Settings
- Strict prohibition against uploading continuous ambient microphone audio to cloud servers.
- Automatic disk cache cleanup for staged voice phrases.
- Prohibited file access filters (`.env`, `id_rsa`, `.pem`).
