# JARVIS OS — Phase 3J & 3K: Speech Recognition & Universal Voice Output

## Overview
Phase 3J and 3K establishes the speech pipeline connecting physical hardware audio input (Seeed ReSpeaker Lite USB) to the neural intelligence core, ensuring that **every final JARVIS response appears as text in the chat and is spoken through the physical speaker**.

---

## 1. Real Speech Recognition (Phase 3J)
- **Hardware Capture:** Seeed ReSpeaker Lite USB (`plughw:2,0` or PipeWire default source) captured via `pw-record` (`16000 Hz, 1 channel, 16-bit PCM`).
- **Zero Mock Data:** Elimination of `transcribe_simulated()` and hardcoded placeholder text. All transcriptions are derived directly from physical microphone audio frames.
- **Engines:**
  - Fast Google Web Speech API via `SpeechRecognition` library (< 500ms latency).
  - Offline local OpenAI Whisper (`tiny` model) fallback when offline.

---

## 2. Text-First Decoupled Voice Output (Phase 3K)
- **Principle:** The UI and terminal must never freeze waiting for neural speech synthesis or audio playback.
- **Execution Flow:**
  1. The AI Brain or tool engine executes the command and yields the text response.
  2. The text response is rendered immediately in the chat interface / terminal output.
  3. An asynchronous worker thread passes the text to `SpeechOutputManager.synthesize_and_stage()`.
  4. Audio is synthesized using the primary voice engine (OmniVoice / Gradio client or Neural Fallback `en-GB-RyanNeural`).
  5. Audio is output through the physical speaker via `pw-play` while simultaneously ducking active background music.
  6. The frontend receives the audio asset descriptor (`audio_url`, `is_cloned`, `provider_label`).

---

## 3. Cloned Voice Integration (OmniVoice & Google Colab)
- **Primary Provider:** OmniVoice voice cloner with user reference sample (`data/voice_samples/myvoice_ref_clean.wav`).
- **Colab AutoRunner (`apps/voice/colab_runner.py`):** Automatically boots and verifies the remote Colab OmniVoice instance for the notebook `Super_Eleven_Lab_Lite_2_1.ipynb`.
- **Honest Provider Labeling:**
  - If OmniVoice is online: labeled `OmniVoice (Personal Cloned Voice)`.
  - If OmniVoice is offline: uses Microsoft Azure Neural `en-GB-RyanNeural` and explicitly labels `Neural Fallback (Edge-TTS Ryan)` (never misleads the user).
