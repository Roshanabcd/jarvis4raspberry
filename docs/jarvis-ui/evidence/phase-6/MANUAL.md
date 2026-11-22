# JARVIS OS Phase 6: Voice Pipeline Manual Verification Checklist

**Branch:** `feature/jarvis-ui`  
**Phase:** 6 — Voice Pipeline, Waveforms & Audio-Reactive Lip-Sync  
**Verified Target:** `http://127.0.0.1:8000/futuristic/#voice`  
**Date:** 20 November 2026  

This checklist is for the human operator to verify real physical hardware audio input (microphone), speech-to-text (STT), physical speaker output aloud, and audio-reactive digital human mouth movement.

---

## 1. Physical Microphone & Push-to-Talk Verification

- [ ] **Hardware Detection**:
  - Open `http://127.0.0.1:8000/futuristic/#voice`.
  - Confirm the **Microphone** hardware label displays your detected physical audio device (e.g. `Lite [ReSpeaker Lite] - USB Audio` or system default).
- [ ] **3-Second Diagnostic Mic Recording**:
  - Click **🎙️ Test Mic (3s)** in the Hardware & Audio Pipeline card.
  - Speak aloud: *"Testing JARVIS microphone hardware."*
  - Confirm the subtitles display the recorded audio signal and RMS level, indicating unclipped audio capture.
- [ ] **Push-to-Talk Interaction**:
  - Click the large central glowing microphone button (or hold it).
  - Verify the microphone button turns pulsating red with *"Listening... Speak now"*.
  - Speak a command: *"What is the system status?"*
  - Verify your speech transcript appears in the **Subtitles** box with the `👤 YOU` speaker badge.

---

## 2. Real-Time Audio Waveform Verification

- [ ] **Resting Baseline**:
  - When idle, observe the waveform canvas.
  - Confirm the ambient cyan and holographic purple sine waves are smoothly oscillating at the resting baseline.
- [ ] **Active Sound Spectrum**:
  - While speaking or while JARVIS responds, confirm the waveform canvas transitions to real frequency spectrum bars matching the audio amplitude and cadence.

---

## 3. Physical Speaker Output & Audio-Reactive Lip-Sync Verification

- [ ] **Speaker Diagnostic Tone**:
  - Click **🔊 Test Speaker Tone**.
  - Listen for the 1-second 440Hz sine wave tone played aloud through the physical speaker.
  - Confirm the sound is audible, clear, and unmuted.
- [ ] **Spoken AI Response**:
  - Click **🗣️ Test Voice** or issue a voice query.
  - Confirm JARVIS's voice response plays aloud through the speaker.
  - Confirm the subtitles box displays the `🤖 JARVIS` speaker badge and response text.
- [ ] **Audio-Reactive Mouth Movement**:
  - Observe the digital human avatar (ARIA / ATLAS).
  - Confirm the avatar transitions to the **Speaking** state with blue holographic scanline glow.
  - Confirm the avatar's mouth visemes modulate (`small`, `mid`, `wide`) in sync with the spoken audio amplitude.
  - Confirm the mouth returns to `closed` when speech ends.

---

## 4. Barge-In / Speech Interruption Verification

- [ ] **Emergency Barge-In**:
  - While JARVIS is speaking aloud, click **🛑 Interrupt (Barge-In)**.
  - Confirm audio playback stops instantly.
  - Confirm the avatar's state resets to `idle` in under 300ms.
  - Confirm the subtitles box shows `[Interrupted]`.

---

## 5. Microphone Privacy & Mute Control

- [ ] **Mute Privacy Latch**:
  - Click **🔇 Mute Mic**.
  - Confirm the top right privacy indicator turns amber with **"Microphone Muted"**.
  - Confirm the central mic button enters muted state and prevents recording.
  - Click **🔊 Unmute Mic** and confirm the privacy indicator returns to cyan **"Standby (Wake Word: 'jarvis')"**.

---

## Sign-Off

| Item | Verified (Y/N) | Notes / Observations |
|---|---|---|
| Physical Microphone | | |
| Real Waveform Spectrum | | |
| Physical Speaker Audio | | |
| Audio-Reactive Mouth | | |
| Barge-In (<300ms) | | |
| Mute Privacy | | |
