# JARVIS OS validation report — 2026-11-10

## Verified working

| Area | Verification | Result |
|---|---|---|
| Camera Module 3 | Physical camera-service health and JPEG capture through the Sony IMX708 service | Passed |
| Vision API and object detection | `tests/vision/test_vision.py` and camera integration tests | Passed |
| Local scene description | Moondream through local Ollama, no cloud service | Passed in 50.52 s |
| ReSpeaker Lite routing | PipeWire selected it as both default source and sink | Detected |
| Speaker transport | A physical PipeWire test tone was decoded, streamed, and completed | Passed; human audibility still needs confirmation |
| Voice software | Full `tests/voice` suite | 52 passed |
| Agent tools, Phase 3, Phase 7 identity, and voice-session security | Focused regression suite | 43 passed |
| ESP32 protocol and sensor simulations | Safe protocol/simulation suite | 17 passed, 3 API tests excluded |

The full suite currently collects 381 tests without import errors.

## Hardware status and constraints

No motor, servo, relay, or other physical actuation was commanded during this validation. The configuration is in hardware mode, and unverified wiring, motor power, mechanical clearances, and an emergency-stop path make arming unsafe.

- The ESP32 serial controller can connect on `/dev/ttyAMA0`, but motor movement and encoder feedback have **not** been verified.
- The PCA9685 address `0x40` was detected, but register operations returned I2C remote-I/O errors. Treat the servo HAT as not working until wiring, power, pull-ups, and the I2C bus are checked.
- BME280 and BH1750 did not respond on the configured bus. VL53L0X, PIR, and HC-SR04 remain simulation-only because their physical interfaces/libraries are not available.
- A running JARVIS wake-word process already owns the ReSpeaker microphone (`pw-record`). A second capture was deliberately not started, preserving the single microphone-owner rule.

## External-service limitations

- DuckDuckGo returned an HTTP 202 anti-bot challenge, so live web-search results were not verified. The test now validates JARVIS's search-session contract with a controlled provider response rather than treating an external anti-bot response as a software regression.
- Chrome automation was denied by the desktop browser security policy. No browser restriction was bypassed.

## Remaining physical acceptance tests

Before actuator testing, verify an emergency-stop, common ground, motor and servo power supplies, all driver wiring, a clear test area, and a safe lift/stand. Then test one unpowered/output channel at a time before connecting motors or servos.
