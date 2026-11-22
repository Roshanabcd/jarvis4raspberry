# Security & Safety Model — JARVIS Module 31 (JARVIS Robot Brain)

1. **Fail-Safe E-STOP Interlock**: Engaging E-STOP halts velocities immediately and rejects all subsequent motion/mission calls with `409 ESTOP_ENGAGED` until cleared with explicit `confirm_reset: true`.
2. **Physical Safety Envelopes**: Velocity commands are clamped to `JARVIS_M31_MAX_LINEAR_MPS` and `JARVIS_M31_MAX_ANGULAR_RPS`; forward motion is blocked below `JARVIS_M31_MIN_OBSTACLE_M`; autonomous missions are blocked below `JARVIS_M31_MIN_BATTERY_PCT`.
3. **Simulation Transparency**: Every `/health` and `/status` response reports `simulated: true` when using `SimulatedRobotHardwareAdapter`.
4. **Hardware Reminder**: Software E-STOP is a control-plane interlock and must always be paired with a physical cut-off switch on real robotic actuators.
