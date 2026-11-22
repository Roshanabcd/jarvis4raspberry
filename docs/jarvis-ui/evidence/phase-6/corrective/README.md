Current checkpoint (21 November 2026): source integrated into feature/jarvis-ui.
Core reload still pending operator action. Physical microphone/speaker acceptance
and offline wake detection remain unverified. Current evidence: merged-python.txt
(78 passed), merged-frontend.txt (84 passed), browser-capture-privacy.txt (9 focused,
included in the frontend total), browser-playback.txt (1 Chromium synthetic muted
audio test), browser-extensions.txt (2 Chromium route/escaping tests). The browser
checks use intercepted fixtures, not physical audio or provider calls. Inline
JavaScript syntax for the complete merged root dashboard also passed.

Earlier checkpoint details below are historical; integration and browser permission
statements in that record are superseded above.

# Phase 6 corrective evidence — integrated source, live acceptance pending

All checks here are offline, use synthetic audio/mocked inference and perform no
physical microphone, speaker, camera or robot operation. No network socket was
opened by the API guard test; FastAPI TestClient calls the ASGI application in-process.

## Recorded commands and results

- `node --test tests/frontend/futuristic-voice-ownership.test.cjs`: 7 passed.
- `PYTHONPATH="$PWD" /home/roshan/.gemini/antigravity/scratch/jarvis-os/venv/bin/python -m pytest tests/unit/test_voice_capture_reliability.py tests/unit/test_voice_daemon_delivery.py tests/unit/test_voice_job_delivery.py -q`: 74 passed.
- `node --test tests/frontend/*.test.cjs`: 72 passed, including the final mute fix.
- `node --check apps/dashboard/futuristic/voice.js` and `api.js`: passed.
- `git diff --check`: passed.

The preserved STT fast-mode and wake-sensitivity edits came from the user's
working checkout. Repairs add existing-owner push-to-talk, monitor server-owned
speech jobs without a second synthesis/player, reject unknown outcomes without
replaying a task, cancel late jobs after interruption, and keep mute authoritative.
Accumulated audio is bounded and uses private per-turn temporary files. A previous
recording can no longer replace a current one-word command. Raw transcripts are
not logged in the repaired wake paths. Existing recordings were not deleted.

The old browser Phase 6 gate has not been rerun or weakened. Localhost browser
network permission is pending. Full voice/hardware acceptance is not claimed.
The main checkout is receiving concurrent changes; this checkpoint is isolated
in `jarvis-os-phase05-b`, detached from `feature/jarvis-ui` at `5a65caa`.
Integration requires a conflict-aware comparison with the latest main branch.
