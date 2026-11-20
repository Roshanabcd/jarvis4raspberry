# Phase 9 — trusted voice session and startup hardening

## Objective

Complete the first bounded Phase 9 increment: bind voice commands to a server-owned identity session, prevent conversational/JSON role spoofing, require a PIN before an identified administrator receives administrative tool authority, and prevent Whisper initialization from blocking API import.

## Implementation

- Added `AGENTS.md` with permanent preservation, safety, hardware-owner, testing, and secrecy rules.
- Added `apps/voice/session_manager.py` integration fixes:
  - Uses `CameraManager.capture_photo()` and the returned `image_path`.
  - Keeps the existing camera-service proxy as the sole physical camera owner.
  - Converts missing/failed recognition to safe GUEST state.
  - Separates displayed identity role from `authorization_role()`: a face-recognized ADMIN has USER authority until a successful PIN verification elevates that exact session.
- Added server-owned session endpoints under `/api/voice/session`:
  - `GET /session`
  - `POST /session/identify`
  - `POST /session/verify-pin`
  - `POST /session/invalidate`
- Made `/api/voice/command` accept only a bounded transcript. Extra fields such as `role: ADMIN` are rejected. `VoiceService` independently reads its local authoritative session and ignores caller identity arguments.
- Updated the wake-word daemon to refresh identity through the local backend and send only the transcript; it no longer forwards a process-local identity claim to the API.
- Made Whisper model initialization lazy. The API can now import without immediately loading/downloading a speech model; Whisper initializes only after lightweight STT cannot produce a transcription.
- Declared the existing OpenCV dependency in `pyproject.toml` and installed `opencv-python-headless` into the project environment.

## Automated tests

`tests/unit/test_phase9_voice_session_security.py` verifies:

1. Admin face recognition does not itself authorize admin tools.
2. PIN verification elevates only the active session.
3. Recognition uses the camera manager's service-backed capture result and `image_path`.
4. Camera failure retains GUEST authority.
5. Caller-supplied identity fields fail validation.
6. Command routing uses the server-owned voice service session.
7. Whisper initialization is deferred.

Result: 7 Phase 9 tests passed. The Phase 3 simulated STT regression also passed in the same run (8 total).

## Hardware and security status

- **Implemented and unit tested:** role-spoofing rejection, session reset, PIN-gated admin authority, camera-capture error fallback, lazy Whisper startup.
- **Simulated only:** the Phase 3 STT regression test.
- **Not hardware-verified:** ReSpeaker capture, speaker output, wake-word detection, live face recognition, physical camera snapshot, motors, servos, and sensors.
- **Security finding fixed:** a separate wake-word process could previously submit `user_id`, `session_id`, and `role` fields that the API did not authenticate. The API now rejects such fields and derives identity locally.

## Remaining blocker / next milestone

FastAPI lifespan integration needs a dedicated reliability pass. A bounded `TestClient` request did not return within 25 seconds, so this milestone does not claim end-to-end HTTP verification. The next change should make optional background services (particularly auto-started remote Colab execution) explicitly configured and startup-bounded, then add a health-route integration test.

At handoff, user-systemd inspection was unavailable in this execution context and both expected loopback service ports (`8000`, `8082`) refused connections. No physical service or hardware claim is made.
