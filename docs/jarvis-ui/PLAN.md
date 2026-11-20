# JARVIS UI upgrade: PLAN
Branch: feature/jarvis-ui | Baseline commit: 3522f43c2f11a1fac50b686f1466f8d3ac929d65 | Started: 2026-11-20
Status values: pending, in-progress, awaiting-approval, blocked, verified.

## Status
| # | Phase | Status | Commit | Evidence |
|---|-------|--------|--------|----------|
| 0 | Audit (read-only) | awaiting-approval | | docs/jarvis-ui/evidence/phase-0/ |
| 1 | Regression harness and safe delivery path | pending | | |
| 2 | Design system and shell | pending | | |
| 3 | Data layer and dashboard | pending | | |
| 4 | Conversation panel | pending | | |
| 5 | Avatar | pending | | |
| 6 | Voice | pending | | |
| 7 | Agents and Developer Hub | pending | | |
| 8 | Tasks, memory, calendar, integrations | pending | | |
| 9 | Devices and robot | pending | | |
| 10 | Responsive, accessibility, performance | pending | | |
| 11 | Full verification and delivery | pending | | |

## Phases

### Phase 0: Audit (read-only)
May install dependencies and run existing builds and tests. Changes no tracked source file. Writes only under docs/jarvis-ui/.
Deliverables: AUDIT.md and FEATURES.md.
AUDIT.md contains: (1) stack, versions, and the commands to install, run, build and test, each actually executed with its result; (2) architecture map: frontend, backend, routes, API endpoints, WebSocket/SSE channels, entry points; (3) voice: STT and TTS engines, how audio is captured and played (browser, server or OS), and whether the frontend can get viseme/phoneme timing or the raw audio; (4) AI providers and agent orchestration: adapters present, how tasks are dispatched, existing isolation or worktree mechanisms; (5) storage: databases, memory and knowledge stores, the settings system; (6) robot backend, simulation support, safety limits; (7) existing tests with baseline counts and failures; (8) integration capability matrix for Codex, Antigravity, Gemini, Copilot, OpenRouter, Cline and local models. For each: installed, version, authenticated (use status commands only; never print tokens), and a class: A = API/SDK a backend can call, B = headless CLI a backend can call, C = IDE-only with no programmatic access, D = absent; (9) risks; (10) confirmation or revision of the avatar plan in section 5 of the launch pack, with the facts behind it; (11) proposed amendments to this plan.
FEATURES.md: a checklist of every existing user-visible feature and how to verify it.
Gate: every claim in AUDIT.md cites a file path or command output; no tracked source file modified. Set status to awaiting-approval and STOP for user approval.

### Phase 1: Regression harness and safe delivery path
Deliverables: baseline test run recorded; Playwright smoke tests (or the existing e2e framework) covering every automatable FEATURES.md item, run against the unchanged app; baseline screenshots; a feature flag or parallel route so the new UI is opt-in and the old UI stays reachable.
Gate: smoke suite green on the unchanged app; with the flag off, behavior is identical to baseline.

### Phase 2: Design system and shell
Deliverables: design tokens (SPEC section 2); core components (panel, card, button, toggle, skeleton, status chip, toast); responsive shell; sidebar with all 18 destinations (collapse, active state, keyboard navigation, mobile bottom nav); top bar; dark default plus light theme; reduced-motion support. Every destination has a route; pages not built yet show an honest 'Not implemented yet' state.
Gate: typecheck, lint and build pass; axe reports no critical violations on the shell; keyboard-only navigation test passes; screenshots at four breakpoints.

### Phase 3: Data layer and dashboard
Deliverables: typed API client; states for loading, empty, error, offline and reconnect; WebSocket/SSE/polling hooks; read-only telemetry endpoints limited to an allowlist of metrics (CPU, RAM, disk, GPU, temperature, battery, network, backend health, model status, agent processes); dashboard cards. Anything unreadable shows 'Unavailable'.
Gate: displayed values match independent system tools, with the comparison saved as evidence; stopping the backend shows offline and recovers on restart; a grep check proves no mock data in the production bundle.

### Phase 4: Conversation panel
Deliverables: streaming messages, markdown, highlighted code, copy, regenerate, stop, search, history, export, tool-call details, error recovery; attachments only where the backend supports them (otherwise 'Not available'); provider/model label taken from backend response metadata. Fully usable without the avatar.
Gate: E2E for send, stream, stop, regenerate and export; the provider label matches the backend log; related FEATURES.md items still pass.

### Phase 5: Avatar
Deliverables: AvatarController state machine (idle, listening, thinking, speaking, happy, concerned, error, offline, muted) driving an AvatarRenderer interface with two implementations (Vrm3D and Sprite2D) and a LipSyncDriver interface; boy/girl selection persisted through the existing settings system; lazy-loaded assets from a configured path; holographic styling; fallback selection logic; docs/jarvis-ui/ASSETS.md recording every asset's source and license. Design details are in section 5 of the launch pack.
Gate: all nine states render for both avatars; blinking and head motion are present; frame rate measured and recorded, including under CPU throttling; each fallback trigger tested. If real VRM files are absent this is a Stop Condition, and a placeholder avatar cannot make this phase verified.

### Phase 6: Voice
Deliverables: existing STT and TTS services wired in, not replaced; mic button, push-to-talk, wake word only if existing infrastructure supports it; waveforms from real audio; subtitles; volume, mute, voice, speed and output device where supported; barge-in; microphone privacy indicator; lip-sync tier chosen from the Phase 0 audit; graceful failure paths.
Gate: automated tests for permission denied, STT unavailable, TTS failure, offline, and interruption mid-speech (animation cancel time measured and recorded); mute indicator verified. A real-microphone and real-speaker check is a user-run checklist in evidence/phase-6/MANUAL.md.

### Phase 7: Agents and Developer Hub
Deliverables: agent cards from the real orchestrator (status, task, provider, progress, logs; tokens and cost only if reported); pause, resume and cancel mapped to real orchestrator calls, otherwise disabled with a reason; task graph or timeline; adapters for class A and B tools only, while class C tools appear as 'IDE-only: not controllable from JARVIS'; one git worktree per concurrent agent; developer workspace (file tree, viewer/editor reusing the existing editor integration, git status and branch, build and test results, logs, diagnostics); terminal through the existing secure executor with approvals and audit log.
Gate: run a real multi-step instruction (inspect project, find frontend issues, assign agents, run tests, report) on a throwaway copy of the repo; no concurrent write conflicts; an approval prompt appears for a destructive command and a denial is honored; audit log entries exist.

### Phase 8: Tasks, memory, calendar, integrations
Deliverables: tasks with the SPEC section 9 statuses, scheduling with explicit time zones and confirmed schedule results, approval stages, retry, pause and resume; memory UI over existing storage that separates active context, persistent memory, project knowledge and retrieved documents; calendar and notifications over existing services; integrations grid whose status comes only from adapter responses.
Gate: a task runs the create, schedule, run, fail, retry cycle for real; a scheduled item fires at the correct time under two different TZ settings; memory edit and delete work only where the backend supports them; review confirms no invented percentages or scores.

### Phase 9: Devices and robot
Deliverables: simulation mode first; capability checks; status panels for Pi, ESP32-S3, camera, microphone/speaker, motors, sensors and power where the backend exposes them; emergency stop; activity log. Motion disabled by default, enabled only by explicit user action, with every command validated by the existing backend limits.
Gate: all tests run in simulation; emergency stop tested in simulation; disconnected, unsupported and simulation states are visibly distinct. Real-hardware verification is a user-run checklist in evidence/phase-9/HARDWARE_CHECKLIST.md. The agent never moves real hardware.

### Phase 10: Responsive, accessibility, performance
Deliverables: four layouts from SPEC section 16 (mobile is voice-first with bottom navigation, not a scaled desktop); low-power mode; reduced-motion; visible focus; screen-reader labels; touch targets sized for touch; lazy-loaded avatar assets; bundle analysis.
Gate: Playwright at four viewports; axe reports no critical or serious violations; Lighthouse accessibility and performance numbers recorded, with accessibility at 90 or above as the target.

### Phase 11: Full verification and delivery
Deliverables: full unit, integration and Playwright E2E run; console-error sweep; offline and reconnect checks; FEATURES.md re-verified in full; secret scan of the bundle; dependency license list; install, run and operate docs; screenshots; final report covering the 12 items in SPEC section 21.
Gate: FEATURES.md fully verified or each exception documented with a reason; final report states real counts; user review.

## Dependencies
| Name | License | Size | Reason | Phase |
|------|---------|------|--------|-------|

## Decisions
(none yet)

## Open questions
- Awaiting user input: original master prompt text to populate `docs/jarvis-ui/SPEC.md`.

## Log
- 2026-11-20: Initialized feature branch `feature/jarvis-ui` from clean baseline `3522f43c2f11a1fac50b686f1466f8d3ac929d65`.
- 2026-11-20: Appended standing rules to `AGENTS.md`. Initialized `docs/jarvis-ui/PLAN.md`.
- 2026-11-20: Populated `docs/jarvis-ui/SPEC.md` with operator master prompt. Copied reference prototype `jarvis_os_futuristic_ai_interface.tsx` and design assets to `docs/jarvis-ui/references/`.
- 2026-11-20: Executed Phase 0 Read-Only Audit. Discovered stack, versions, routes, audio pipeline, providers, storage, robot safety, and test baseline. Generated `docs/jarvis-ui/AUDIT.md` and `docs/jarvis-ui/FEATURES.md`. Set status to `awaiting-approval`. STOPPING for user approval per Stop Condition 1.
