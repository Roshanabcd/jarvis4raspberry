# JARVIS OS — Phase 3H & 3I: 12-State Wake Word Engine & Silence-Driven Automatic Submission

## Executive Summary
Phase 3H and 3I implements a dedicated background voice assistant daemon on Raspberry Pi 5. It replaces rigid fixed-duration audio capture with a formal **12-State Explicit State Machine**, acoustic keyword detection for *"Wake up JARVIS"* / *"JARVIS"*, real-time Voice Activity Detection (VAD), 3.0-second continuous silence automatic submission, and a 15-second follow-up conversational window.

---

## The 12-State Voice Engine State Machine

```text
       ┌──────────┐
       │ DISABLED │
       └────┬─────┘
            │ start()
            ▼
┌───────────────────────┐  Keyword Matched   ┌─────────────────┐
│   STANDBY_LISTENING   │ ──────────────────► │  WAKE_DETECTED  │
└───────────────────────┘                     └────────┬────────┘
            ▲                                          │ Speak "Yes?"
            │ Timeout (15s)                            ▼
┌───────────┴───────────┐                     ┌─────────────────┐
│   FOLLOW_UP_STANDBY   │                     │ LISTENING_SPEECH│ ◄───────┐
└───────────▲───────────┘                     └────────┬────────┘         │
            │                                          │ Speech Heard     │
            │ Playback Ends                            ▼                  │
┌───────────┴───────────┐                     ┌─────────────────┐         │
│   SPEAKING_RESPONSE   │                     │    STREAMING_   │         │
└───────────▲───────────┘                     │  TRANSCRIPTION  │         │
            │                                 └────────┬────────┘         │
            │ Result Ready                             │ Silence Detected │
┌───────────┴───────────┐                              ▼                  │
│   PROCESSING_AGENT    │                     ┌─────────────────┐         │
└───────────▲───────────┘                     │     SILENCE_    │         │
            │                                 │    COUNTDOWN    │ ────────┘
            │ Finalized                       └────────┬────────┘  (User spoke again)
┌───────────┴───────────┐                              │ Silence >= 3.0s
│   COMMAND_SUBMITTED   │ ◄────────────────────────────┘
└───────────────────────┘
```

### Complete State Directory
1. `DISABLED`: Background listener daemon stopped.
2. `STANDBY_LISTENING`: Continuously sampling rolling 1.5s audio buffers from ReSpeaker Lite USB, scanning for wake phrases.
3. `WAKE_DETECTED`: Wake phrase matched; interrupts playing audio (barge-in) and delivers audible chime / acknowledgment ("Yes?").
4. `LISTENING_SPEECH`: Capturing active user command utterance.
5. `STREAMING_TRANSCRIPTION`: Audio frames being continuously decoded by STT.
6. `SILENCE_COUNTDOWN`: VAD silence detected; 3.0-second timer decrementing.
7. `COMMAND_SUBMITTED`: 3.0s continuous silence elapsed; command automatically sealed and dispatched.
8. `PROCESSING_AGENT`: JARVIS Brain and tool orchestrator executing actions.
9. `SPEAKING_RESPONSE`: Speech synthesis actively streaming out of the ReSpeaker physical speaker.
10. `FOLLOW_UP_STANDBY`: 15-second active conversational window. If user speaks within this period, JARVIS processes the command directly without requiring the wake word again.
11. `MUTED`: Audio ingestion paused by user.
12. `ERROR`: Hardware or network failure state with automatic recovery to standby.

---

## Wake Phrases Detected
- `"Wake up JARVIS"`
- `"Wake up, JARVIS"`
- `"Hey JARVIS"`
- `"OK JARVIS"`
- `"Hello JARVIS"`
- `"JARVIS"` (with phonetic variations `jarves`, `javis`)

---

## Silence-Driven Automatic Submission (VAD)
- **Problem:** Rigid 5-second timers either cut off the user mid-sentence or force an awkward wait when the user has finished speaking.
- **Solution:** `WakeWordEngine` measures continuous audio Root Mean Square (RMS) energy:
  - Energy $> 500$ indicates active speech; resets silence timer.
  - Energy $< 500$ decrements continuous silence countdown.
  - When continuous silence reaches **3.0 seconds**, JARVIS automatically submits the command to the brain for immediate execution.

---

## 15-Second Follow-Up Conversation Window
- After completing a task and speaking the response, JARVIS enters `FOLLOW_UP_STANDBY` for 15.0 seconds.
- If the user speaks during this window (e.g., *"Play the second result instead"*, *"Set volume to 50%"*, *"Go back"*), JARVIS transitions directly to `LISTENING_SPEECH` and executes the command immediately without requiring *"Wake up JARVIS"* again.
- If no speech occurs within 15.0s, JARVIS returns gracefully to `STANDBY_LISTENING`.
