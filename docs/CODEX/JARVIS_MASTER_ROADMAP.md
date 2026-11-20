# JARVIS master roadmap

Date: 2026-11-11

The goal is a dependable local robotics assistant, not a dashboard that merely
claims broad capabilities. Milestones below are ordered by safety and evidence.

## P0 — deployable safety foundation

1. Build a test-safe FastAPI app factory.
   - Test mode must not initialize camera, microphone, I2C, GPIO, PCA9685, or
     ESP32 devices.
   - Ordinary `pytest` must not send serial/PWM stop frames.
   - Hardware tests remain explicit and supervised.
2. Deploy the current source hardening during a stationary maintenance window.
   - Confirm the core service is bound only to loopback.
   - Confirm remote voice monitor/runner are off after restart.
   - Confirm dashboard reports the correct listener and identity state.
3. Add an immutable authorization context for every action request.
   - Enforce it in Brain, LocalEngine, ToolExecutor, ToolRegistry, direct
     Tools API, and CompoundTaskOrchestrator.
   - A face-recognized administrator stays USER-authorized until PIN elevation.
   - High-risk actions still require explicit confirmation after authorization.

## P1 — trustworthy local application platform

1. Replace process-global identity with localhost browser sessions.
2. Bind chat history, app settings, favorites, recent apps, and task records to
   the authenticated session owner.
3. Add rate limits, audit events, session expiration, logout, and CSRF-aware
   same-origin protections.
4. Repair dashboard state labels and create browser regression tests that run
   against the test-safe app factory.
5. Make each of the three Available applications independently testable;
   retain Planned status for every unfinished app.

## P2 — software-first robot capabilities

1. Sensor abstraction: real/simulated state, calibration, health, and no fake
   sensor claims.
2. Perception: camera-service adapter, object detection, scene description,
   privacy controls, and accurate backend reporting.
3. Voice: single microphone ownership, local STT/TTS fallback, explicit remote
   provider consent, and safe voice identity flow.
4. Task engine: cancellable tasks, bounded retries, audit trail, and recovery
   without direct side-effect bypasses.
5. Document QA/RAG only after a privacy design, local ingestion path, access
   controls, citations, storage policy, and tests are implemented.

## P3 — supervised hardware integration

1. Validate power distribution, grounding, fuse/current limits, motor driver
   wiring, and physical e-stop before software actuation tests.
2. Validate PCA9685/servo channels with no mechanical load first.
3. Validate ESP32 protocol, encoder feedback, and motor direction at low speed
   on a stand or raised chassis.
4. Add environment sensors one by one with address detection and calibration.
5. Add camera and ReSpeaker integration only through their single owners.

## P4 — humanoid platform expansion

Likely later procurement decisions should follow mechanical and power design,
not precede it: chassis/actuator selection, protected battery/BMS and fuse
system, regulated power rails, encoders/IMU, safe docking/charging, wiring
harnesses, and physical emergency-stop hardware. No purchase recommendation is
made until payload, degrees of freedom, run time, and budget are defined.

## Definition of done for a feature

A feature is marked Available only when it has a real implementation, isolated
tests, an end-to-end test against a safe runtime, failure behavior, and truthful
dashboard status. A simulation is labelled simulation; it is never presented as
hardware verification.
