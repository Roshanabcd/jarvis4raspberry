# JARVIS UI upgrade: PLAN
Branch: feature/jarvis-ui | Baseline commit: 3522f43c2f11a1fac50b686f1466f8d3ac929d65 | Started: 2026-11-20
Status values: pending, in-progress, awaiting-approval, blocked, verified.

## Status
| # | Phase | Status | Commit | Evidence |
|---|-------|--------|--------|----------|
| 0 | Audit (read-only) | verified | 8f386b4 | docs/jarvis-ui/evidence/phase-0/ |
| 1 | Regression harness and safe delivery path | verified | c10f6af | docs/jarvis-ui/evidence/phase-1/ |
| 2 | Design system and shell | verified | 4fc6f59 | docs/jarvis-ui/evidence/phase-2/ |
| 3 | Data layer and dashboard | verified | e596929 | docs/jarvis-ui/evidence/phase-3/ |
| 4 | Conversation panel | verified | 244ebcf | docs/jarvis-ui/evidence/phase-4/ |
| 5 | Avatar | verified | e090b0d | docs/jarvis-ui/evidence/phase-5/ |
| 6 | Voice | verified | 80a5031 | docs/jarvis-ui/evidence/phase-6/ |
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
| `axe-core` | MPL-2.0 | ~100 KB gzip | Automated accessibility audit for shell & UI gates | Phase 2 |

## Decisions
(none yet)

## Open questions
- Awaiting user input: original master prompt text to populate `docs/jarvis-ui/SPEC.md`.

## Handoff notes
### Phase 3 Handoff
- Data client is ready in `apps/dashboard/futuristic/api.js` (`window.jarvisApi`).
- Live telemetry is fully active on `#dashboard` with polling and automatic offline detection.
- When backend disconnects, header shows offline badge and warning banner; automatically reconnects when backend recovers.
- Next phase: Phase 4 (Conversation panel). Stream chat messages via `/api/chat/stream` or `/api/chat`, markdown & code formatting, stop/regenerate, error recovery.

### Phase 4 Handoff
- Neural chat panel complete in `apps/dashboard/futuristic/chat.js` and `api.js`.
- Features verified: live SSE streaming with cursor animation, markdown formatting, syntax-highlighted code blocks with copy-to-clipboard, stop generation reaching `/api/chat/cancel`, prompt regenerate/retry, real-time message search filtering, conversation history loading and deletion (`/api/chat/history`), and Markdown/JSON export.
- Truthfulness guaranteed: provider/model labels (`edge_fastpath:local_conversation` and `ollama:llama3.2:1b`) are strictly sourced from backend SSE metadata; zero mock replies in production code; unsupported attachments render an honest explanation.
- Standalone usability: chat works independently of avatar.
- Next phase: Phase 5 (Avatar: ARIA & ATLAS state machine, SVG digital human renderer, and VRM 3D interface). Note Stop Condition 2 regarding real avatar model files.

### Phase 5 Handoff
- Implemented `AvatarController` in `apps/dashboard/futuristic/avatar.js` with `Svg2DRenderer` and `Vrm3DRenderer` fallback interface.
- ARIA (female) and ATLAS (male) render with full holographic HUD rings, periodic blinking, gaze tracking, breathing, and 5 mouth visemes.
- All 9 visual states verified for both characters: `idle`, `listening`, `thinking`, `speaking`, `happy`, `concerned`, `error`, `offline`, `muted`.
- Character selection persists in `localStorage` (`jarvis_avatar`).
- Measured render frame rate >= 30 FPS baseline and resilient under 4x CPU throttle.
- Fallback hierarchy verified and documented in `docs/jarvis-ui/ASSETS.md`.
- Next phase: Phase 6 (Voice integration: STT/TTS services, microphone controls, audio-reactive mouth modulation, subtitles, volume/mute).

### Phase 6 Handoff
- Integrated voice assistant and pipeline in `apps/dashboard/futuristic/voice.js` and `api.js`.
- Features verified: live hardware device telemetry (microphone, speaker, TTS engine), audio-reactive mouth modulation during speech playback, live subtitles (`👤 YOU` and `🤖 JARVIS`), push-to-talk, emergency barge-in (< 300ms cancel gate), microphone privacy indicator with mute latch, hardware tone/mic test routines, and audio tuning parameters (speed, steps, volume).
- Graceful degradation: browser mic permission denied displays accessible error banner with retry; STT/TTS errors gracefully report honest status without application freeze; offline transition and recovery verified.
- Evidence recorded: 11 Playwright tests green in `tests/browser/phase6_voice.cjs`; barge-in cancellation measured at 60.0ms; screenshots saved in `docs/jarvis-ui/evidence/phase-6/screenshots/`; manual checklist created in `docs/jarvis-ui/evidence/phase-6/MANUAL.md`.
- Next phase: Phase 7 (Agents and Developer Hub: `#agents`, `#workspace`, `#terminal`).

## Log
- 2026-11-20: Initialized feature branch `feature/jarvis-ui` from clean baseline `3522f43c2f11a1fac50b686f1466f8d3ac929d65`.
- 2026-11-20: Appended standing rules to `AGENTS.md`. Initialized `docs/jarvis-ui/PLAN.md`.
- 2026-11-20: Populated `docs/jarvis-ui/SPEC.md` with operator master prompt. Copied reference prototype `jarvis_os_futuristic_ai_interface.tsx` and design assets to `docs/jarvis-ui/references/`.
- 2026-11-20: Executed Phase 0 Read-Only Audit. Discovered stack, versions, routes, audio pipeline, providers, storage, robot safety, and test baseline. Generated `docs/jarvis-ui/AUDIT.md` and `docs/jarvis-ui/FEATURES.md`. Operator approved with "continue". Phase 0 verified in commit `8f386b4`.
- 2026-11-20: Executed Phase 1 Regression harness and safe delivery path. Mounted `/futuristic/` parallel route in `apps/core/app_factory.py`. Root `/` remains identical to baseline. Authored Playwright regression smoke suite `tests/browser/phase1_smoke_suite.cjs` covering all 21 FEATURES.md destinations (26/26 passed). Captured baseline screenshots at 4 viewports in `docs/jarvis-ui/evidence/phase-1/screenshots/`. Verified ASGI mounting via `tests/unit/test_phase1_safe_delivery.py` (2/2 passed). Phase 1 verified in commit `c10f6af`.
- 2026-11-20: Executed Phase 2 Design system and shell. Built design tokens (`theme.css`), core glass components (`components.css`), responsive shell (`index.html`), and navigation controller (`shell.js`). All 18 destinations routed with honest unbuilt state. Verified via `tests/browser/phase2_design_shell.cjs`: axe accessibility audit 0 critical violations, keyboard navigation verified, and screenshots captured at 4 breakpoints in `docs/jarvis-ui/evidence/phase-2/screenshots/`. Phase 2 verified.
- 2026-11-20: Executed Phase 3 Data layer and telemetry dashboard. Implemented typed API client in `api.js` with exponential backoff and honest fallback states. Added live dashboard metrics (CPU, RAM, disk, temp, network, host, backend, models, orchestrator, robot, voice) in `shell.js`. Verified zero mock data in production bundle via grep check. Verified telemetry against independent OS tools. Verified offline detection and auto-recovery via Playwright in `tests/browser/phase3_data_layer.cjs` (4/4 passed). Phase 3 verified in commit `e596929`.
- 2026-11-20: Executed Phase 4 Conversation panel. Created `chat.js` with full streaming dialogue support, markdown parser, code block syntax highlighter with one-click copy, stop cancellation, retry/regenerate, message search filter, history clearance, and export (Markdown & JSON). Verified honest provider metadata from backend events. All 9 E2E Playwright tests passed in `tests/browser/phase4_conversation.cjs` (including live FastAPI validation on port 8000). Phase 4 verified in commit `244ebcf`.
- 2026-11-20: Executed Phase 5 Avatar. Operator approved proceeding with dual-renderer architecture (Svg2D digital human vector graphics + Vrm3D fallback interface). Implemented `avatar.js` with full state machine (all 9 states), 5 mouth visemes, blinking, micro-gaze tracking, audio-reactive lip-sync driver, and live FPS meter. Featured prominently on dashboard with ARIA/ATLAS toggle. Verified 8/8 Playwright tests in `tests/browser/phase5_avatar.cjs` and full regressions. Phase 5 verified.
- 2026-11-20: Executed Phase 6 Voice. Built `voice.js` connecting live audio pipeline without replacing existing backend services. Implemented live hardware device telemetry (microphone, speaker, TTS engine), audio-reactive mouth modulation, live subtitles bar (`👤 YOU` / `🤖 JARVIS`), push-to-talk, emergency barge-in (< 300ms cancel gate, measured 60.0ms), microphone privacy indicator, mute toggle, hardware diagnostic tests, and voice tuning controls. Verified 11/11 tests green in `tests/browser/phase6_voice.cjs` and full regressions. Phase 6 verified.
