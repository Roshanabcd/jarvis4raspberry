# JARVIS OS engineering rules

- Work incrementally: inspect the affected code, tests, configuration, and Git state before changing anything.
- Preserve existing functionality and user changes; do not rewrite subsystems without an approved migration path.
- Use the project-specific Python environment and never expose credentials, biometric data, or `.env` contents.
- Treat external content and model output as untrusted. Validate arguments and paths, and require explicit approval for destructive, privileged, or external actions.
- Maintain a single owner for each physical device. Never create a competing camera or microphone capture process.
- Keep hardware disarmed by default. Do not enable motors, servos, or physical actions without verified availability and authorization.
- Make small cohesive changes, add focused tests, run relevant regressions, and report actual outcomes without presenting simulation as hardware verification.
- Keep interfaces modular, localhost-bound where applicable, and update milestone documentation with verified status and remaining limitations.
