# Changelog — Module 20: Real-Time Conversational AI

## [1.0.0] - 2026-11-20
### Added
- Configurable AI provider adapters (`SimulatedLocalProvider`, `OpenAICompatibleProvider`) with automatic error recovery fallback.
- Streaming WebSocket (`/api/v1/conversational-ai/ws/chat`) with live token delivery and mid-stream barge-in interruption.
- Animated holographic SVG avatars for **ARIA** (female) and **ATLAS** (male) with natural blinking, facial states, approximate syllable/viseme lip-sync, browser STT/TTS, voice selection, and live subtitles.
- SQLite WAL session and rolling context-window management.
