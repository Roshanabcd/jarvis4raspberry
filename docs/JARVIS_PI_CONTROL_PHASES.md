# Raspberry Pi JARVIS: control gap analysis and implementation prompts

Review date: 22 November 2026. Local source checkpoint: ccba75f, feature/jarvis-ui, with existing operator changes. Public repository reviewed: https://github.com/Roshanabcd/jarvis4raspberry/ (repository overview; no claim that remote main matches this checkout).

## Scope and evidence

This is a proposed implementation workstream, not a replacement for AGENTS.md, SPEC.md or PLAN.md. Read those files first. PLAN.md retains blocked avatar and final-delivery gates, alongside later master-phase handoffs. Reconcile these tracks before starting another phase; do not interpret a handoff's "next" line as approval to bypass a stop condition. The documented 2D/voice exception does not complete the real-avatar gate.

Read CLAUDE.md, CLAUDE2.md, AGENTS.md and AGENTS2.md. The paired files were identical at review. Preserve the current uncommitted changes in AI, voice, desktop, permissions and dashboard code. Do not silently commit another contributor's work. Historical reports are evidence from their stated revision, not fresh verification of this dirty checkout.

Current review inspected source and documentation only. It did not run privileged commands, switch a real account, move the mouse, capture a microphone, call a paid provider, deploy code or operate hardware. Later master-phase voice handoffs report successful checks; those have not been independently repeated here. The project is an assistant running on Linux, not a replacement kernel or a guarantee that any requested task can be completed.

## Prioritized gaps

| Priority | Finding and source | Required result | Status in this review |
|---|---|---|---|
| P0 | tools/desktop/unified_computer_service.py account branch guesses two coordinates, ignores click results and returns verified=True. Its broad account match does not establish a target account. | Explicit target and observed page identity; verify each transition; never claim an account changed merely because a menu was opened. | Confirmed source defect; not repaired here. |
| P0 | tools/terminal/terminal_manager.py uses regex classification before bash -c. confirm=True bypasses its confirmation branch; stored tokens include a time but this branch does not enforce expiry or bind a user/session/cwd. | Trace every caller and existing policy first. Enforce server-owned, scoped approval at the execution boundary and test bypass/replay paths. | Confirmed engine behavior; external exploitability is unverified because endpoint guards must also be traced. |
| P1 | tools/desktop/browser_backend.py starts a fresh browser/new_context, not a named persistent operator profile. It also passes --no-sandbox. | Separate named browser profiles from website account selection; retain isolation, review sandbox support, never attach to private profiles implicitly. | Current launch path inspected; other adapters may exist. |
| P1 | Desktop account workflow assumes DISPLAY=:0 and fixed layout; terminal defaults DISPLAY when absent. | Discover the actual desktop/session and supported input method; fail clearly when unavailable. | Source assumptions confirmed; Pi/session availability unverified. |
| P1 | Chat quality and provider latency cannot be established from a provider name, health response or module card. | Real first-token/completion measurements, bounded fallback, cancellation and honest failures. | Live inference not measured in this review. |
| P1 | Voice has recent ownership/preemption repairs and recorded master-phase evidence, while the original phase-6 acceptance remains open. | Reconcile evidence at the deployed revision; one capture owner, one output owner, interruption and mute acceptance. | Implementation/historical evidence present; no new physical verification. |
| P1 | Multiple task and automatic repair capabilities need end-to-end resource and approval tests. | Independent tasks progress concurrently; shared desktop/mic operations serialize; failed commands cannot trigger unapproved execution. | Integration acceptance gap; do not assume orchestration is absent. |
| P2 | Module visibility/reachability and hardware panels are not operational acceptance. | Representative real tasks per module; read-only hardware discovery; simulated motion acceptance. | UI availability has historical evidence; individual functions and Pi devices need scoped acceptance. |

## Architecture to build on, subject to existing approval gates

Keep apps.core.main:app and apps/core/app_factory.py, the existing permission manager, capability dispatcher/router, tool executor, browser service, task manager and apps/voice owners. Preserve both classic and futuristic UIs. Avoid a second service, second executor or another microphone process.

Use the existing task identifier across chat, planner, policy decision, tool execution, progress and final result. A proposed structured action records capability, validated arguments, target device/profile, expected effect and risk. Policy checks precede execution; verification follows execution. Tool output and web pages are untrusted evidence, never instructions to grant privileges. Acknowledgment means accepted/queued, not successful. Completion requires an observed result; partial, cancelled, denied and unavailable are distinct outcomes.

For privileged work, keep JARVIS unprivileged. Propose a small OS-mediated helper for specific operations (for example restarting an explicitly allowlisted JARVIS unit), using fixed executable/argument schemas and narrow authorization. Do not grant unrestricted passwordless sudo, run the application as root, pipe model text to a privileged shell, collect passwords or let a browser set an approval boolean. A grant should bind authenticated actor, exact normalized action/arguments, device, working directory where applicable, expiry and single-use nonce. Re-check authorization immediately before execution and record a redacted audit event. Installation/polkit/sudoers changes require explicit approval after a concrete reviewed proposal.

A Chrome profile is a browser data directory; a YouTube account/channel is website state inside that profile. Ask for the intended target when ambiguous. Prefer observed DOM controls where supported. Use fresh observed screen targets only as a bounded fallback, with verified window focus and coordinate transforms. Stop for user login/MFA or ambiguous identities; do not extract cookies or bypass account checks. Keep debugging endpoints localhost-only and do not expose an unrestricted browser-control port.

On Pi, measure CPU/RAM/temperature and end-to-end latency before choosing concurrency limits. Do not assume a particular RAM size, OS architecture, X11/Wayland session, model speed or attached peripherals. Prefer bounded heavy inference concurrency, bounded queues and timeouts. Laptop access is separately scoped to approved folders and actions; Pi authorization does not grant access to personal laptop data.

## Reusable Antigravity master prompt

> Continue this existing repository as the implementation lead. First read AGENTS.md, AGENTS2.md, CLAUDE.md, CLAUDE2.md, docs/jarvis-ui/PLAN.md, SPEC.md, FEATURES.md, the audit report, issue JSON, roadmap, and this document. Inspect branch, dirty files, current service owner and relevant code/tests without reading secrets. Preserve all existing features and operator changes. Reconcile the UI phase gate with later master-phase handoffs; select only an eligible phase. These proposed control phases do not authorize bypassing stop conditions. Work incrementally: inspect, implement a cohesive change, run its focused checks, save evidence, update status, checkpoint only your explicit paths, then advance when permitted. Do not spend a whole session rerunning unchanged suites. Do not replace subsystems or add dependencies without the required review. Every UI control must invoke the real backend or explain its unavailable state. Never claim complete from HTTP 200, mocked tests or process exit alone. Stop only at a real approval boundary or missing prerequisite, with the exact decision and prepared proposal. End with changed files, checks/results, remaining limitations and the next executable step.

Use the following phase prompt only after reconciling it with PLAN.md. The C-prefix distinguishes this proposed control workstream from existing UI phases.

### C0 — Reconcile and measure (first action)

> Map the existing routes and capability-to-executor chain for chat, terminal, browser, native input, task jobs and voice. Record which implementations are active, which are legacy, and which safeguards actually surround each caller. Inspect the current diff without reverting it. Resolve the discrepancy between blocked original UI phases and later master-phase progress in a proposed PLAN amendment; do not mark gates passed. Inventory Pi deployment facts using approved read-only checks: OS/architecture, Python, desktop session, service owner, devices and provider status without keys. Produce an implementation ownership map and a small acceptance matrix. Run only relevant existing offline tests as baseline. No device capture, real account actions, provider spending or privileged configuration. Request approval for any unresolved architecture or phase amendment before implementation.

Gate: named active call paths, source revision, dirty-file ownership, baseline results and approved next phase. Report missing evidence rather than inventing a hardware inventory.

### C1 — Truthful browser and desktop results

> Repair the verified=True account workflow in the existing desktop service after C0 approval. Use the target account/profile explicitly; remove guessed-coordinate success claims. Reuse the existing observation and input adapters. Check focus and action results; verify the requested account label after selection. If only a menu opened, report that intermediate result. If there is no reliable target, return needs_input or unavailable through the existing result schema. Avoid changing auth, saved profiles or voice in this phase. Preserve supported media/navigation behavior and add bounded cancellation between steps.

Gate: mocked backend tests for focus failure, click failure, missing/ambiguous target, menu-only state, actual verified selection and cancellation. No real account interaction in automated tests. Verify the frontend shows partial/failed state without a success announcement. Capture fixture evidence at 1440×900 and 1280×720 if UI changes.

### C2 — Scoped terminal approval (separate security approval)

> Trace terminal API, dispatcher, tools and engine, including direct callers, before changing approval behavior. Prepare an exact compatibility plan for removing any client-controlled confirm bypass. Integrate with the existing authenticated policy/audit mechanism; do not create a second identity store. Bind approvals to actor, action, parameters, session/device, cwd and short expiry; consume once at the execution boundary. Keep ordinary permitted commands working. Use structured executable arguments for privileged capabilities. Treat compound shell text as a separately restricted capability, not something regexes can make safe. Keep output bounded and redact secret-bearing content. Present the minimal OS-helper configuration for review; do not install it yourself.

Gate: unit/integration tests with fake executor for denial, guest calls, expired/mismatched/replayed grants, cwd changes, shell metacharacters, direct-engine calls, cancellation, bounded output and audit records. Assert zero subprocess execution for rejected requests. No real sudo or destructive test. User approval is required for auth changes and deployment.

### C3 — Browser profiles and reliable desktop automation

> Extend existing browser adapters with an explicit profile/session selector after approval for stored-session handling. Reuse existing settings, avoid a schema migration unless separately approved, and validate profile paths/ownership. Distinguish app-owned automation sessions from the operator's personal browser. Never copy cookies or passwords. Support opening a chosen profile and website account switching as separate actions. Verify window, origin, account target and result. Detect actual X11/Wayland capabilities and explain unsupported capture/input instead of forcing DISPLAY=:0. Keep one desktop action owner, bounded steps, cancellation and key/button release in finally blocks. Review Chromium sandbox compatibility; never silently downgrade isolation.

Gate: isolated fixture sites and temporary profiles only; profile lock contention, account ambiguity, login/MFA handoff, navigation failure, scaled viewport, stale screenshot and cancellation tests. Actual personal login/account changes require the operator. No unrestricted remote debugging listener.

### C4 — Responsive chat and concurrent jobs

> Extend existing chat streaming and task management rather than introducing duplicate schedulers. Return a real job ID and immediate accepted/queued acknowledgment, stream progress, then announce completion only from the final verified result. Preserve conversation context and drafts on failure. Discover available models through adapters, avoid vision-only models for general chat, impose bounded provider deadlines/fallback attempts, and expose actual provider/model metadata. No automatic paid fallback. Serialize desktop, microphone and hardware resources while allowing independent safe jobs to progress. Enforce bounded queue size, cancellation, idempotency and recovery rules; never replay a privileged task automatically after a restart. Turn terminal errors into a suggested diagnosis and reviewable repair, not unconditional self-execution.

Gate: provider-independent tests for delayed/error streams, two concurrent tasks, contention, duplicate requests, cancellation, disconnect/reconnect and restart. Approved live benchmark reports median and p95 first-token/completion times with sample count/model/device; set a measured target rather than promise instant inference.

### C5 — Finish voice acceptance without replacing the pipeline

> Read docs/CODEX_VOICE_CONTINUATION.md and current phase-6 evidence. Reconcile recent master-phase changes before modifying anything. Obtain the required approval for a concrete voice-pipeline change. Preserve the existing capture/output owners, IPC and job delivery. Ensure one spoken response, early acknowledgment for long jobs, final completion once, reliable mute and barge-in, no late speech from cancelled jobs and no browser/server double playback. Use actual speech stage events and audio-reactive animation. Offline wake must use a verified compatible/licensed local detector; cloud transcription standby is not offline wake. Do not install native runtimes or download models without the required approval.

Gate: focused fake-media tests plus a separate operator checklist for actual microphone, speaker, interruption, mute, wake, unplug/reconnect and a long task. Record installed runtime/model/version and license. Report limitations when offline STT/wake is absent. Do not mark physical acceptance from fake media.

### C6 — Hardware, deployment and final acceptance

> Inventory Pi 5, ESP32-S3, IMX708, ReSpeaker Lite and other peripherals as detected, absent or unknown. Use the existing owner per device. Add read-only capability/health visibility first. Keep motion disabled by default; implement and test permissions, limits, disconnect behavior, watchdog and latched E-STOP in simulation only. Never move real hardware or click the live E-STOP. Prepare a reviewed deployment/rollback procedure with one service owner, localhost binding and resource limits. Preserve both UIs and existing settings. Run broader regressions once at the integration milestone, then execute an acceptance matrix across representative modules instead of equating catalog visibility with completion.

Gate: saved simulation results, deployment revision, operator-run physical checklist, chat and task acceptance, no unsupported connected claims, and explicit remaining gaps. User approves privileged deployment and any real hardware operation separately. Full project completion requires every agreed acceptance item, not completion of this document.

## Claude/Codex fallback prompt and handoff

> Continue the same phase selected in docs/jarvis-ui/PLAN.md using docs/JARVIS_PI_CONTROL_PHASES.md. Read CLAUDE.md and its synchronized CLAUDE2.md, but treat generic orchestration commands as examples, not startup instructions. Inspect the latest diff and evidence; do not redo completed work or overwrite another AI's edits. Own one cohesive task and one isolated worktree if working concurrently. Do not assume Antigravity, Claude or Codex can be remotely controlled merely because their CLI is installed. Use an available authenticated integration only within the authorized scope; otherwise leave a concrete handoff. Preserve the original phase gates, safety approvals and device ownership. Report implemented, verified_offline, verified_live and unresolved separately. Save the next action and exact blocker before context ends.

Suggested ownership when parallel work is explicitly authorized: lead owns PLAN/integration; one worker owns browser fixture tests and account verification; one owns terminal policy proposal/tests; one owns chat/task tests. Voice and physical devices remain with their existing owners. No two workers write the same checkout or restart shared services. Merge only reviewed scoped commits after targeted integration checks.

Handoff record per checkpoint: revision and dirty-file ownership; selected phase and authorization; changes; commands and actual results; fixture/live classification; evidence paths; remaining failure; next action. Never include keys, raw transcripts, cookies, private screen captures or biometric data.
