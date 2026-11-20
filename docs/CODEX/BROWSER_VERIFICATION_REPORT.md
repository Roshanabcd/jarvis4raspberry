# Browser verification report

Date tested: 2026-11-10

Target: local JARVIS dashboard at `http://127.0.0.1:8000/`.

## Observed workflows

| Workflow | Result |
|---|---|
| Dashboard loading | Passed. The local dashboard rendered with live system information. |
| Apps Center | Passed for catalog rendering: 20 cards, 3 Available and 17 Planned. |
| Available app as guest | Correctly denied by the then-running backend: `Access requires USER role. Current role is GUEST.` This exposed the hard-coded guest identity defect later repaired in source. |
| Planned app behavior | Cards show roadmap actions rather than pretending to launch an implementation. |
| Text chat | Passed. Auto-speak was turned off first; a safe arithmetic prompt returned the correct result. |
| Browser console | No console warnings or errors were reported during the tested local flow. |
| Vision tab | Rendered and showed IMX708 availability. Camera Status returned a backend label inconsistent with the dedicated Picamera2 service; no capture or face-identification action was performed. |

## Safety constraints used

- No motor, servo, arm, clear-e-stop, or other physical action was clicked.
- No microphone capture was started.
- No biometric image or face enrollment was performed.
- No remote web service or Google login was used.
- Auto-speech was disabled before chat testing to avoid unsolicited playback.

## Screenshot evidence

A local browser screenshot was observed during the chat workflow, including the
successful arithmetic result. It was not saved as a repository artifact, so
this report intentionally does not invent a local screenshot path.

## Deployment note

This browser pass predates the source hardening in this change set. The active
systemd service was intentionally not restarted because the legacy lifecycle
can touch hardware during shutdown. A fresh browser pass is required after a
test-safe deployment maintenance window.
