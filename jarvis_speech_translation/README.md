# JARVIS OS — Real-Time Speech Translation

Continuous bilingual speech recognition, multi-tier translation, custom terminology glossaries, and translated voice playback for **Raspberry Pi 5 (8GB)**.

## Features
- **Continuous Mic & Voice Playback UI (`static/index.html`)**: Uses browser `SpeechRecognition` for live microphone capture, streams utterances over WebSocket, and speaks translations via `speechSynthesis` with BCP-47 locale tags (`en-US`, `ne-NP`, `hi-IN`, `es-ES`, `fr-FR`, `de-DE`, `ja-JP`).
- **Multi-Tier Translator (`translator.py`)**: Supports OpenRouter LLM (`use_llm=true`), self-hosted LibreTranslate (`JARVIS_TRANSLATE_LIBRE_URL`), and a deterministic offline bilingual phrasebook + script-aware auto-detector.
- **SQLite WAL Sessions & Custom Glossaries (`storage.py`)**: Persists bilingual conversation transcripts and domain-specific terminology overrides.

## Quick Start (Standalone)
```bash
pip install -r requirements.txt
python3 -m jarvis_speech_translation.app
# Open http://localhost:8024/speech-translation
```

## Run Tests
```bash
python3 -m unittest discover -s jarvis_speech_translation/tests -v
```
