# Security and safety repair report

Date: 2026-11-11

## Completed source repairs

### Remote voice and Colab controls

- Removed the reusable registration secret from source and dashboard JavaScript.
- Disabled Colab auto-run and remote health monitoring by default.
- Removed the fallback public endpoint used during import/startup.
- Stopped failed session creation from being treated as success.
- Made manual external voice actions opt-in through configuration and require a
  fresh administrator PIN plus explicit acknowledgement per request.
- Kept remote monitoring off unless separately enabled by the operator.
- Added separate `remote_voice_enabled` and `cloud_tts_enabled` switches,
  both off by default.  A configured or environment URL is no longer enough to
  make the module-global cloner probe a remote host.
- Remote cloning now accepts only a registered, currently verified endpoint;
  provider status checks remain local while remote voice is disabled.
- Kept the local TTS fallback available while preventing implicit Edge/cloud
  fallback, which would otherwise transmit the requested speech text.
- Corrected the voice API, health response, and dashboard labels so they no
  longer claim Edge/cloud fallback is active when local fallback is in use.

### Apps Center identity boundary

- The first-run state is now GUEST with `is_setup=true`; it is no longer an
  implicit ADMIN identity.
- Apps Center resolves the active identity only on the server.
- Client `user_id` and PIN fields were removed from Apps Center launch and
  settings bodies; extra identity fields are rejected.
- Favorites, recents, settings, task ownership, and app launches use the
  server-resolved identity rather than query/body input.
- App status changes require both a server-resolved ADMIN role and PIN
  verification.

This is an interim single-local-operator boundary. It is not a replacement for
per-browser authenticated sessions; that work remains on the roadmap.

### Actuator safety

- Servo commands now obey disarmed and emergency-stop interlocks in
  `RobotController`, not only in the HTTP layer.
- Robot controller construction is lazy; importing a router no longer opens
  I2C or serial hardware.
- HTTP arm, clear-e-stop, movement, and servo endpoints are disabled by
  default. When explicitly enabled later, each request must include a fresh
  admin PIN and `physical-motion` confirmation.
- Stop, e-stop, and disarm remain available as safety actions.
- Registry robot arm/move/servo tools now require high-risk confirmation and
  report safety interlock rejection instead of false success.
- Shutdown no longer creates a new servo controller solely to issue stop
  frames; it only disarms a controller already owned by the process.

### Local network posture

- The source systemd unit now binds Uvicorn to `127.0.0.1`.
- Credentialed CORS no longer includes `*`.
- Health reporting now distinguishes a configured loopback host from a
  wildcard listener it can actually observe.

### Privileged settings and diagnostics

- Settings writes, configuration backup export, and diagnostics now require a
  fresh administrator PIN plus an explicit per-request acknowledgement.
- The dashboard asks for that acknowledgement and PIN before sending one of
  those privileged requests; it reports a server denial rather than a false
  success.
- Rendering the settings page no longer dereferences the lazy robot proxy.  It
  reports an uninitialized controller as disarmed instead of opening I2C or
  serial interfaces just to display a status card.

### Test-safe application construction

- Added a separate FastAPI factory.  Production retains the full router list
  and lifecycle; focused tests can select routers and use a no-op lifecycle.
- This permits new narrow ASGI tests without importing the production app or
  starting its sensor, microphone, scheduler, or robot lifecycle.

### Test hygiene

- Hardware tests require `JARVIS_RUN_HARDWARE_TESTS=1`.
- Hardware-test imports that previously booted the full app during collection
  are delayed until an explicitly opted-in test executes.
- Added focused fake-controller/fake-database regression coverage.

## Important deployment status

These are source changes. The currently running core service was not restarted
in this work because its legacy lifecycle has hardware side effects. Therefore
the running process may still have the old network bind, identity behavior, and
remote monitor behavior until a controlled maintenance deployment occurs.

## Remaining high-priority repairs

1. Migrate legacy tests away from `from apps.core.main import app` and
   eliminate the remaining import-time hardware construction.
2. Pass immutable authorization context from chat/voice through Brain,
   LocalEngine, ToolExecutor, ToolRegistry, and compound tasks.
3. Add real browser/session authentication and bind chat history to it.
4. Repair Vision Status so it reports the actual camera-service backend.
5. Validate a stationary, supervised hardware deployment only after the
   software safety gates are deployed and confirmed.
