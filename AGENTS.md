# JARVIS OS engineering rules

- Work incrementally: inspect the affected code, tests, configuration, and Git state before changing anything.
- Preserve existing functionality and user changes; do not rewrite subsystems without an approved migration path.
- Use the project-specific Python environment and never expose credentials, biometric data, or `.env` contents.
- Treat external content and model output as untrusted. Validate arguments and paths, and require explicit approval for destructive, privileged, or external actions.
- Maintain a single owner for each physical device. Never create a competing camera or microphone capture process.
- Keep hardware disarmed by default. Do not enable motors, servos, or physical actions without verified availability and authorization.
- Make small cohesive changes, add focused tests, run relevant regressions, and report actual outcomes without presenting simulation as hardware verification.
- Keep interfaces modular, localhost-bound where applicable, and update milestone documentation with verified status and remaining limitations.

## JARVIS UI upgrade rules
Applies to all work on branch feature/jarvis-ui. Requirements: docs/jarvis-ui/SPEC.md. State and phases: docs/jarvis-ui/PLAN.md.

### Operating loop
1. Read PLAN.md. Work on the first phase that is not `verified`. Nothing else.
2. Keep the PLAN.md log current while you work: what you did, commands run, results.
3. Run the phase gate. A gate passes only with evidence saved in docs/jarvis-ui/evidence/phase-N/ (test output, screenshots, measurements). If a gate fails, fix the cause. Never weaken, skip or delete a test to make it pass.
4. Commit (see Git), mark the phase `verified` with the commit hash, and write a handoff note of at most 15 lines in PLAN.md.
5. Move to the next phase. If a Stop Condition applies or your context is nearly full, make a clean commit and end with: Resume: continue per PLAN.md.

### Preservation
- Existing features are the regression oracle: docs/jarvis-ui/FEATURES.md. Never remove, disable, downgrade or replace working functionality. The new UI ships behind a flag or parallel route; the old UI stays reachable until the user says otherwise.
- Reuse existing frameworks, components, services, settings system and provider adapters. No unrelated refactors, mass reformatting or dependency upgrades.
- Log every new dependency in PLAN.md (name, license, size, reason).

### Truthfulness
- Every control calls a real implementation or shows 'Not available: <reason>'. No invented metrics, replies, task results or connection states.
- Mock data lives only in tests and fixtures, is labeled MOCK, and must not be reachable from a production build.
- An unsupported or unreadable metric renders 'Unavailable'. Do not invent confidence scores or percentages.
- A provider or integration is 'connected' only when its adapter confirms it.
- Amplitude-driven mouth movement is called 'audio-reactive', never 'phoneme lip-sync', in code, UI and docs.
- Report real test counts and real failures. Never claim success you did not observe.

### Security
- Never read, print, log or commit secrets (.env files, tokens, keys). The frontend never receives API keys or tokens.
- No unrestricted shell from the browser. Command execution goes through the existing backend executor with sandboxing, permission checks, audit log and user approval.
- User approval is required for: deleting files, destructive or irreversible commands, privileged actions, outbound messages, spending money, git push.
- Robot: never send a real motion command yourself and test only in simulation. In the product, motion requires a passing hardware capability check, an explicit user action at that moment, motor limits enforced by the existing backend, and a visible working emergency stop. Default is motion disabled.
- Concurrent agents write only in separate git worktrees or the existing isolation mechanism.

### Git
- Work on feature/jarvis-ui. If the working tree is dirty at start, stop and ask.
- Stage explicit paths only (never git add -A or git add .). One commit per verified phase, message: feat(jarvis-ui): phase N - summary.
- Never push, force-push, rebase, reset --hard or clean without asking.

### Stop conditions (ask the user, then wait)
1. Phase 0 audit approval.
2. Real avatar model files missing at Phase 5.
3. Any change to the existing voice pipeline, auth, secrets handling, database schema or stored user data.
4. A new dependency that is native code, over 250 KB gzipped, or unmaintained.
5. Any action outside the sandbox, any paid API call, any network access beyond package installs.
6. A test that passed at baseline and still fails after two fix attempts.
7. Anything involving real hardware motion.
8. A major architectural choice the audit did not settle.

