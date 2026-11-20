# JARVIS current state snapshot

Date: 2026-11-11

## Runtime observed during audit

| Component | Observed state | Confidence |
|---|---|---|
| Core dashboard/API | Running locally on port 8000 | Runtime observed; pre-hardening process |
| Camera service | Separate local Picamera2 service reported IMX708 / Camera Module 3 | Runtime health response |
| Voice service | Separate user service present; preserve one microphone owner | Runtime process observation |
| AI runtime | Local Ollama service and local models present | Runtime observation |
| Apps Center | 20 manifest records, 3 Available, 17 Planned | Browser and source inspection |
| PCA9685 / ESP32 | Interfaces were previously detected but no actuation was authorized in this pass | Not hardware-verified |
| Environment sensors | No fresh physical reading accepted as verified | Unverified |

## Architecture as implemented

```text
Browser dashboard
  -> FastAPI routers
       -> Apps Center / identity / chat / voice / vision / robot APIs
       -> local services and tool registry
            -> optional camera service, voice daemon, sensors, robot controller
            -> local AI provider and optional explicitly authorized remote voice provider
```

Current cross-cutting boundaries:

- Camera and microphone must have a single process owner.
- Hardware starts disarmed; motion requires controller interlocks.
- Remote voice control is opt-in and per-request authorized in source. Remote
  cloning and cloud TTS are independently disabled until explicitly enabled.
- Privileged settings writes, backup export, and diagnostics require a fresh
  administrator PIN and explicit confirmation in source.
- Focused tests can build a narrow no-op-lifecycle FastAPI app; the production
  app intentionally retains its complete service lifecycle.
- Apps Center identity is server-resolved but still process-global until browser
  sessions are implemented.

## Known inconsistencies / limitations

- The currently running service is older than the source change set.
- Vision status has conflicting backend labels.
- Full per-request RBAC has not yet reached every chat, tool, and compound-task
  execution path.
- Several legacy tests still require migration away from full-app imports.
- Planned app cards are roadmap records, not functional applications.
