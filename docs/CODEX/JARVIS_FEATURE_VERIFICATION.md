# JARVIS feature verification matrix

Date: 2026-11-11

This is an evidence record, not a claim that every advertised feature is complete.
"Verified" means the listed evidence was observed. "Source hardened" means a
change was tested in isolation but has not been applied to the running service.

| Area | Status | Evidence / limitation |
|---|---|---|
| Static dashboard shell | Verified | Local dashboard rendered at `127.0.0.1:8000`; browser console was empty during the tested flow. |
| Chat arithmetic | Verified | Browser request `What is 2 + 2?` returned `Calculation: 2 + 2 = 4` through the local fast path. |
| Apps Center catalog | Verified | Browser showed exactly 20 cards: 3 Available and 17 Planned. Router regression tests prove server-owned app ownership and guest denial. |
| Available-app launch | Partially verified | The old running service correctly denied the guest browser role. Source now resolves identity server-side; a verified local USER identity is required before a USER app can launch. This source change is not deployed yet. |
| Planned apps | Verified as blocked | Planned cards show roadmap information and are not represented as implemented. Document QA/RAG remains planned only. |
| Camera service | Runtime observed | The independent camera service reported a Raspberry Pi Camera Module 3 / IMX708 using Picamera2. No new camera capture or biometric operation was performed in this pass. |
| Vision status wording | Defect recorded | Dashboard camera status reported an `rpicam-still` backend while the dedicated service reported Picamera2. Treat the status wording as inaccurate until repaired. |
| Voice daemon / microphone | Runtime observed | A single systemd voice daemon and the ReSpeaker route were observed. No new microphone capture was initiated, preserving the single-owner rule. |
| Speaker | Previously verified, not repeated | Earlier diagnostic playback was observed; this pass did not play sound. Do not treat this as a new physical verification. |
| Remote OmniVoice / Colab | Source hardened | Startup, monitoring, manual control, and runner launch are disabled by default and require explicit configuration, a fresh admin PIN, and confirmation. A configured URL cannot cause a status-page probe; remote cloning and cloud TTS each require their own opt-in. No external request was made by these tests. |
| Settings writes / backup | Source hardened | Configuration writes, `.env` updates, diagnostics, and full backup export now require a fresh administrator PIN and explicit acknowledgement. Bare-router tests prove denial occurs before persistence or diagnostic dispatch. |
| Test app factory | Verified | A no-op FastAPI lifecycle and selected safe router were constructed and exercised in `tests/unit/test_app_factory.py` without importing the production app. Legacy full-app tests still require migration. |
| Robot motor / servo motion | Not physically verified | No arm, movement, servo, e-stop-clear, or GPIO/I2C/serial hardware test was authorized. Controller and HTTP gates were tested only with fakes. |
| Sensor boards | Not physically verified | Existing BME280/BH1750/ToF/PIR/ultrasonic runtime status was not treated as confirmation. Hardware tests are opt-in. |
| ESP32 / PCA9685 | Detected previously, not verified for actuation | No movement or PWM command was sent in this pass. |
| AI provider stack | Partially verified | Local Ollama models were observed; the browser arithmetic response proves the deterministic fast path, not a full model/tool-call matrix. |
| Tool execution authorization | In progress | Arguments and confirmations now forward correctly through `/api/tools/execute`; full per-request identity propagation through Brain, LocalEngine, ToolExecutor, and compound tasks is still required. |

## Safe regression evidence

The following tests were run without booting `apps.core.main`, opening a camera
or microphone owner, or calling attached actuator hardware:

```text
venv/bin/python -m pytest \
  tests/unit/test_app_factory.py \
  tests/unit/test_security_hardening_milestone.py \
  tests/voice/test_gradio_tts.py \
  tests/voice/test_speech_manager.py \
  tests/voice/test_colab_registration.py \
  tests/unit/test_phase9_voice_session_security.py \
  tests/voice/test_colab_runner.py -k 'not api' -q

53 passed, 1 deselected
```

Additional checks passed:

- Python compilation for every changed Python module.
- Dashboard inline JavaScript parsed successfully with Node.
- `git diff --check` reported no whitespace errors.
- `pytest tests/hardware -q` skipped 28 hardware tests (0.31s) because
  `JARVIS_RUN_HARDWARE_TESTS=1` was not deliberately set. Collection did not
  initialize an app lifespan, camera/microphone owner, or physical actuator.

## Explicit exclusions

The full test suite was not run. Several legacy tests import the full FastAPI
app at module import time; that app can initialize sensors, serial/I2C
controllers, audio services, and a shutdown safety path. Those tests must be
migrated to a test-safe app factory before an ordinary full-suite run is
credible. Hardware verification also requires an operator-supervised area,
confirmed wiring, and explicit authorization.
