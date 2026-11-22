# PLAN.md — JARVIS OS Long-Term Master Build and Agent Continuation Plan

> **Source-of-truth enhancement backlog** · Version `1.0.0` · Created `2026-11-22` · **1,420 uniquely numbered feature actions** · **71 capability domains**
>
> **Repository:** `https://github.com/Roshanabcd/jarvis4raspberry` · **Primary deployment:** Raspberry Pi 5, 8 GB RAM, Linux ARM64 · **Primary interface:** voice and text chat
>
> **Status of new roadmap:** All checkboxes below intentionally start *unchecked / requires verification*. Existing source and reports demonstrate some capabilities already exist; an unchecked item means **not yet accepted under this plan**, **not** necessarily unimplemented. Do not claim 1,420 features are missing, implemented, or working without individual verification.

## Why this file exists

This file is a durable, cross-agent implementation contract for Antigravity, Codex, Claude, Copilot, and future coding agents. Every feature below is intended to be invocable via **“Jarvis, ...” spoken command and/or equivalent chat text**. Users should not need to manually open a terminal for ordinary supported tasks. **Approvals, login, privileged work, payment, and physical motion still require meaningful human authorization.**

If an agent's context window, tool allowance, model quota, or session ends, **a future agent or a human must reopen the repository** and resume using this file. This file itself does **not** automatically start another AI model, grant it credentials, or keep work running without an active execution environment.

### Existing plans and engineering rules — MUST NOT OVERWRITE

1. Read `AGENTS.md` **before** all edits. Its preservation, safety, Git, approval, and evidence rules override convenience instructions here.
2. Read `docs/jarvis-ui/PLAN.md` and `docs/jarvis-ui/SPEC.md`; **that is the authoritative UI-phase plan** on `feature/jarvis-ui`. This new root file is an *umbrella capability roadmap*, not a replacement for that file. Respect its active gate and outstanding blocks.
3. Also inspect `docs/JARVIS_AUDIT_MASTER_REPORT.md`, `docs/JARVIS_BUGS_AND_IMPROVEMENTS.json`, `docs/AI_BUILD_ROADMAP.md`, `IMPLEMENTATION_PROGRESS.md`, `JARVIS_SELF_BUILD_SPEC.md`, and the newer milestone notes relevant to the selected feature.
4. The repository's existing browser, desktop, voice, AI, camera, and hardware code must be reused. Do not replace implementations without an approved, tested migration.
5. `main`, `feature/jarvis-ui`, the live Pi checkout, and any other worktree may diverge. Identify the correct checkout and service owner before development or deployment.
6. Never force-push, reset, clean, rebase, discard user changes, or push/deploy without the required approval.

## Plan size and priority policy

- **Total feature checkboxes:** **1,420** (one distinct action per ID).
- **P0 critical foundation:** 380 items; stable voice/chat execution, browser/desktop control, permissions, system administration.
- **P1 important:** 580 items; reliability, memory, performance, voice, tasks, engineering and recovery.
- **P2 advanced:** 360 items; documents, education, robotics, phone, media and integration enhancements.
- **P3 optional/future:** 100 items; personal laptop controls, smart home, extensions and consent-dependent features.

Prioritize **P0 → P1 → P2 → P3**, but satisfy a targeted feature's *minimum necessary prerequisite capability* first. Do not block all of one domain until all of its 20 actions are done. Also respect outstanding mandatory UI phase gates and the real deployment's needs.

### Milestones (E0–E8, separate from existing `docs/jarvis-ui/PLAN.md` phases)

| Milestone | Outcome | Exit gate |
|---|---|---|
| E0 — Truth and safe foundation | Git/runtime audit, ownership, identity, permissions, health | Evidence-backed inventory; unauthorized actions denied |
| E1 — Real conversations and tools | Voice/chat intent → real tool → verified result; memory and providers | A multi-turn task succeeds; no fake results or duplicate side effects |
| E2 — Browser and account control | Real visible Chrome, tabs, forms, persistent profiles and authorized YouTube accounts | Account switch verified in actual authenticated session; human handles 2FA/CAPTCHA |
| E3 — Native desktop and files | Keyboard, mouse, windows, app management, bounded files | Observed screen and file state match command, with cancellation |
| E4 — Linux admin with approvals | Logs, safe terminal, services, approved package actions | Exact privileged operation approved, audited, verified and rollback-ready |
| E5 — Natural voice interaction | Wake → STT → plan → action → TTS, follow-up and interruption | Real microphone/speaker test, one capture owner, genuine audio evidence |
| E6 — Hardware readiness | Camera, GPIO, sensors, ESP32 and robot controls | Simulation passes; live motor motion only after physical authorization and hardware checks |
| E7 — Useful daily work | Tasks, coding, documents, media, integrations, multitasking | Workflow-specific E2E and dependency/resource-lock checks |
| E8 — Release and continuity | Backup/recovery, performance, multi-agent handoff and production gates | Auditable final acceptance matrix, no open critical failures |

## Feature lifecycle, completion markers and how to skip completed work

- `- [ ]` **unverified / open** (may already be coded). **Do not assume source lacks it.**
- `- [ ]` plus `status: implemented_pending_verification` — code exists but acceptance gate is not met; next agent should test, not rebuild.
- `- [ ]` plus `status: blocked` — dependency, permission or hardware missing; document blocker and choose another eligible item.
- `- [ ]` plus `status: in_progress` — one designated worker owns it; do not edit same files in a competing worktree.
- `- [x]` plus `status: verified_offline` — permitted **only** for a purely offline feature whose accepted contract is entirely offline (e.g. a parser). Do not use it for a claimed live physical/browser/voice action.
- `- [x]` plus `status: verified_live` — the actual target action was observed on the correct Pi/session, with trace, revision, actual test output, and approval if required.
- `status: deprecated` or `superseded_by: JRV-...` — requires a clear explanation, migration and approval; preserve old IDs, never silently delete them.

**Completion rule:** a checkbox becomes checked **only after its acceptance evidence meets the feature's actual claim**. A repository containing functions, passing mocked tests, HTTP 200, or an attractive UI is NOT sufficient to mark a live-action item done. If feature evidence is uncertain, leave it unchecked. Mark complete items immutable except when regression evidence requires reopening them.

**Format for each completion:** append on the same checkbox line:

`<!-- status: verified_live; verified: YYYY-MM-DD; revision: <SHA>; evidence: docs/jarvis-execution/evidence/JRV-0001/; owner: <agent> -->`

For incomplete work use the same comment format with `status: in_progress | blocked | implemented_pending_verification`, `blocker: ...`, and `next: ...`. A full detail record goes into `docs/jarvis-execution/FEATURE_STATUS.md` (create when first used). Do not invent SHA or paths. When tests are not repeatable, document why and keep unchecked.

## Cross-model operating protocol — read on EVERY resumed session

1. **Read in order:** `AGENTS.md` → root `PLAN.md` → `docs/jarvis-ui/PLAN.md` → last verified checkpoint and relevant source/test files.
2. **Determine reality:** inspect actual repo, branch, clean/dirty state, services, Python environment, connected Pi vs development host, active browser session, installed tools, and any previous worker claims. Never overwrite existing changes.
3. **Reconcile status:** for a checkbox with existing implementation, perform its required tests first; if proven, mark it done with evidence without rewriting the feature. Unverified checkboxes remain open.
4. **Select next:** choose the *first highest-priority eligible unchecked feature* (or smallest vertical task that enables it) whose required authorization, dependency, device and service owner exist. Respect active UI phase gates. If blocked, record blocker and move to an independent eligible feature; do not bypass gates.
5. **Claim one scope:** record `feature_id`, branch/worktree, agent, affected files, start time and baseline revision in `docs/jarvis-execution/ACTIVE_TASK.md`; enforce one writer per shared file and one owner per physical device. Multiple agents may work on independent worktrees only.
6. **Plan before editing:** find existing implementations, related tests, callers, service owners, expected behavior, risk/permissions, and minimal patch path. Prefer a working vertical path from spoken/chat request through observable result.
7. **Implement safely:** small changes, no unnecessary new dependencies, no mock-success in production, no secret access, no unrestricted privileged shell, no unchecked physical motion. User approval is required at repository-defined stop conditions.
8. **Test precisely:** focused unit/integration tests, targeted UI/browser fixture first, real Pi acceptance when applicable. Record commanded action, actual state, service revision, screenshots/logs (redacted), duration, and failure modes. Do not repeatedly rerun irrelevant full suites.
9. **Mark status:** update only the applicable IDs, record evidence and remaining limitations; update related milestone docs and `docs/jarvis-execution/FEATURE_STATUS.md`. A completed feature is skipped by later agents unless there is a proven regression.
10. **Checkpoint:** save an actionable handoff in `docs/jarvis-execution/HANDOFF.md` containing completed IDs, in-progress ID, file paths, tests, evidence, exact commands, unresolved blockers and next eligible ID. Commit per the current branch's engineering rules; never push without required approval.
11. **On low context/quota/time:** finish or safely suspend the current atomic step, release locks where possible, update status and handoff, print the next command and **`Resume: continue per PLAN.md.`** Do not promise autonomous continuation after the session closes.
12. **On resume with a different model:** independently verify Git state and last checkpoint; do not trust uncommitted claims without source/evidence. Continue the first eligible unfinished ID. Do **not** restart Phase 0 or repeat full audits without a reason.
13. **When all features are verified:** close the release acceptance checklist, produce a final coverage report, then maintain a continuously numbered backlog for bugs, support, efficiency, security hardening, and new user-approved tasks. Append new IDs; never renumber existing IDs.

## Required acceptance for EACH feature (unless a stronger local gate is specified)

Every JRV checkbox must satisfy all of the following applicable conditions:

- **Voice and chat:** one natural language command reaches the same authorized backend tool or workflow from both interfaces; test both when the hardware supports it. If mic is unavailable, label chat verification and leave real-voice acceptance open.
- **Actual capability:** required adapter and target device/service are present. If absent, return `Unavailable: <reason>`; do not silently switch to simulated success.
- **Permission boundary:** guest/operator/administrator roles, confirmation, secrets, and untrusted webpage/tool input are enforced *before* action execution.
- **Observed outcome:** response must be grounded in a device state, file content, browser DOM, audio output observation, exit status, or supported external service result.
- **Failure path:** timeout, unavailable dependency, wrong account, ambiguous target and cancellation must be handled clearly without duplicating effects.
- **Auditability:** record revision, source paths, test command/results, mock/offline/live classification and redacted evidence for the feature.
- **Regressions:** relevant existing behavior remains intact; never weaken/delete tests to make them pass.
- **Risk tier:** read-only info may auto-run; workspace edits and UI actions follow scoped operator policy; privileged/destructive/external/purchase/financial/physical actions require explicit, action-specific authorization and suitable safeguards.

**Safety boundary:** This is the user's own Pi, but giving a model unchecked root, cookie theft access, account-login bypass, unattended payments, hidden surveillance, arbitrary remote laptop file access, or uncontrolled robot motion is NOT required to make JARVIS highly capable. Build task-specific authorization instead.

## Architecture anchors already present — verify before editing

- AI and task routing: `ai/brain.py`, `ai/local_engine.py`, `ai/tools/executor.py`, `tools/registry.py`.
- Browser: `tools/browser/browser_agent.py`, `tools/browser/youtube_controller.py`, `tools/desktop/browser_backend.py`, `tools/desktop/browser_controller.py`.
- Desktop: `tools/desktop/native_backend.py`, `tools/desktop/computer_action_engine.py`, `tools/desktop/unified_computer_service.py`.
- Safe terminal: `tools/shell/command_runner.py`, `security/permissions/`, `config/permissions.yaml`.
- Voice: `apps/voice/`, existing mic daemon ownership and speech services.
- Physical devices: `hardware/`, `tools/robotics/`, camera service owner and ESP32-S3 drivers.
- Frontend: `apps/dashboard/static/`, `apps/dashboard/futuristic/`; FastAPI entry `apps.core.main:app`.
- Existing UI-phase milestones: `docs/jarvis-ui/PLAN.md`; do not overwrite or mark blocked avatar/voice/deployment gates verified without evidence.

### Specific known risks requiring inspection

- Persistent Chrome browser profile and Google/YouTube **website account** are distinct. Implement two separate account-switching paths. Do not extract cookies or passwords; observe active account label after switching.
- Existing Playwright backend historically started a separate headless context; never claim it is the signed-in visible desktop session without validation. Review `--no-sandbox` and existing X11/Wayland limitations.
- Existing native desktop backend historically disabled PyAutoGUI FAILSAFE; preserve a functioning emergency stop and restore meaningful interrupt behavior before expanding automation.
- Existing terminal runner is intentionally allowlisted; do not solve privileged commands by running the entire assistant as root. Use a narrow privileged-action broker with exact argument and action approval.
- Existing acceptance reports claim partial live milestones; verify current deployed behavior and revision, not only report prose.
- The Ubuntu laptop contains valuable private data; remote laptop functionality is opt-in, independently paired, least-privilege, and initially read-only.

## 1,420 Voice/Chat Feature Checklist

All commands below are **desired action contracts**, not statements that the implementation already works. Each line is individually actionable and individually verifiable; features may share implementations but **may not share unearned completion evidence**. The checkbox is the authoritative resumable state marker.

### 01. Conversation and Chat — `P0` · `E1` · 20 features
**Prerequisite capability:** `Foundation`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0001** `P0` `E1` — “**Jarvis, start a new conversation.**”
- [ ] **JRV-0002** `P0` `E1` — “**Jarvis, rename the current conversation.**”
- [ ] **JRV-0003** `P0` `E1` — “**Jarvis, show my recent conversations.**”
- [ ] **JRV-0004** `P0` `E1` — “**Jarvis, resume the last conversation.**”
- [ ] **JRV-0005** `P0` `E1` — “**Jarvis, search conversations by keyword.**”
- [ ] **JRV-0006** `P0` `E1` — “**Jarvis, pin a conversation.**”
- [ ] **JRV-0007** `P0` `E1` — “**Jarvis, archive a conversation.**”
- [ ] **JRV-0008** `P0` `E1` — “**Jarvis, restore an archived conversation.**”
- [ ] **JRV-0009** `P0` `E1` — “**Jarvis, delete a conversation after confirmation.**”
- [ ] **JRV-0010** `P0` `E1` — “**Jarvis, export a conversation as Markdown.**”
- [ ] **JRV-0011** `P0` `E1` — “**Jarvis, copy the last answer.**”
- [ ] **JRV-0012** `P0` `E1` — “**Jarvis, regenerate the last answer.**”
- [ ] **JRV-0013** `P0` `E1` — “**Jarvis, stop generating the current answer.**”
- [ ] **JRV-0014** `P0` `E1` — “**Jarvis, show the model used for this answer.**”
- [ ] **JRV-0015** `P0` `E1` — “**Jarvis, attach an approved file to chat.**”
- [ ] **JRV-0016** `P0` `E1` — “**Jarvis, summarize this conversation.**”
- [ ] **JRV-0017** `P0` `E1` — “**Jarvis, display tool steps for this response.**”
- [ ] **JRV-0018** `P0` `E1` — “**Jarvis, switch between text and voice mode.**”
- [ ] **JRV-0019** `P0` `E1` — “**Jarvis, show chat connectivity status.**”
- [ ] **JRV-0020** `P0` `E1` — “**Jarvis, recover an interrupted conversation.**”

### 02. Intent Understanding — `P0` · `E1` · 20 features
**Prerequisite capability:** `Conversation and Chat`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0021** `P0` `E1` — “**Jarvis, distinguish a question from an action request.**”
- [ ] **JRV-0022** `P0` `E1` — “**Jarvis, identify multiple actions in one sentence.**”
- [ ] **JRV-0023** `P0` `E1` — “**Jarvis, resolve 'it' from the previous command.**”
- [ ] **JRV-0024** `P0` `E1` — “**Jarvis, understand 'the first one' from search results.**”
- [ ] **JRV-0025** `P0` `E1` — “**Jarvis, understand 'the other window' from desktop state.**”
- [ ] **JRV-0026** `P0` `E1` — “**Jarvis, ask which item when two targets match.**”
- [ ] **JRV-0027** `P0` `E1` — “**Jarvis, recognize a cancel instruction.**”
- [ ] **JRV-0028** `P0` `E1` — “**Jarvis, recognize an emergency-stop instruction.**”
- [ ] **JRV-0029** `P0` `E1` — “**Jarvis, parse a requested time duration.**”
- [ ] **JRV-0030** `P0` `E1` — “**Jarvis, parse an absolute date and time.**”
- [ ] **JRV-0031** `P0` `E1` — “**Jarvis, parse file and folder locations.**”
- [ ] **JRV-0032** `P0` `E1` — “**Jarvis, parse a website address from speech.**”
- [ ] **JRV-0033** `P0` `E1` — “**Jarvis, identify the target application.**”
- [ ] **JRV-0034** `P0` `E1` — “**Jarvis, identify the target computer.**”
- [ ] **JRV-0035** `P0` `E1` — “**Jarvis, identify whether a command needs approval.**”
- [ ] **JRV-0036** `P0` `E1` — “**Jarvis, reject conflicting instructions from a webpage.**”
- [ ] **JRV-0037** `P0` `E1` — “**Jarvis, detect an unsupported command.**”
- [ ] **JRV-0038** `P0` `E1` — “**Jarvis, show the planned interpretation before executing.**”
- [ ] **JRV-0039** `P0` `E1` — “**Jarvis, correct an incorrectly interpreted command.**”
- [ ] **JRV-0040** `P0` `E1` — “**Jarvis, reuse context when I say 'continue'.**”

### 03. Tool Registry and Routing — `P0` · `E1` · 20 features
**Prerequisite capability:** `Intent Understanding`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0041** `P0` `E1` — “**Jarvis, list available real tools.**”
- [ ] **JRV-0042** `P0` `E1` — “**Jarvis, show unavailable tools and reasons.**”
- [ ] **JRV-0043** `P0` `E1` — “**Jarvis, route a browser action to the browser tool.**”
- [ ] **JRV-0044** `P0` `E1` — “**Jarvis, route a terminal request to the shell tool.**”
- [ ] **JRV-0045** `P0` `E1` — “**Jarvis, route a voice request to the existing voice service.**”
- [ ] **JRV-0046** `P0` `E1` — “**Jarvis, route a camera request to the existing camera owner.**”
- [ ] **JRV-0047** `P0` `E1` — “**Jarvis, route a file request to the file tool.**”
- [ ] **JRV-0048** `P0` `E1` — “**Jarvis, route a motor request to the robotics controller.**”
- [ ] **JRV-0049** `P0` `E1` — “**Jarvis, validate required tool parameters.**”
- [ ] **JRV-0050** `P0` `E1` — “**Jarvis, reject unknown tool arguments.**”
- [ ] **JRV-0051** `P0` `E1` — “**Jarvis, check target resource availability.**”
- [ ] **JRV-0052** `P0` `E1` — “**Jarvis, check tool permission before execution.**”
- [ ] **JRV-0053** `P0` `E1` — “**Jarvis, check a tool's timeout limit.**”
- [ ] **JRV-0054** `P0` `E1` — “**Jarvis, log the chosen tool without secrets.**”
- [ ] **JRV-0055** `P0` `E1` — “**Jarvis, return structured tool errors.**”
- [ ] **JRV-0056** `P0` `E1` — “**Jarvis, retry a transient read-only tool error.**”
- [ ] **JRV-0057** `P0` `E1` — “**Jarvis, prevent duplicate side-effectful invocations.**”
- [ ] **JRV-0058** `P0` `E1` — “**Jarvis, show the exact tool result.**”
- [ ] **JRV-0059** `P0` `E1` — “**Jarvis, disable a failing optional tool gracefully.**”
- [ ] **JRV-0060** `P0` `E1` — “**Jarvis, restore a tool when its dependency returns.**”

### 04. Task Planning and Verification — `P0` · `E1` · 20 features
**Prerequisite capability:** `Tool Registry and Routing`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0061** `P0` `E1` — “**Jarvis, break a complex request into ordered steps.**”
- [ ] **JRV-0062** `P0` `E1` — “**Jarvis, show the task plan on request.**”
- [ ] **JRV-0063** `P0` `E1` — “**Jarvis, run a read-only preflight for a task.**”
- [ ] **JRV-0064** `P0` `E1` — “**Jarvis, pause a task awaiting approval.**”
- [ ] **JRV-0065** `P0` `E1` — “**Jarvis, resume a paused task.**”
- [ ] **JRV-0066** `P0` `E1` — “**Jarvis, verify each completed step.**”
- [ ] **JRV-0067** `P0` `E1` — “**Jarvis, capture evidence for a completed step.**”
- [ ] **JRV-0068** `P0` `E1` — “**Jarvis, avoid repeating an already committed action.**”
- [ ] **JRV-0069** `P0` `E1` — “**Jarvis, replan after an unexpected window appears.**”
- [ ] **JRV-0070** `P0` `E1` — “**Jarvis, replan after a page element changes.**”
- [ ] **JRV-0071** `P0` `E1` — “**Jarvis, skip an optional step and explain why.**”
- [ ] **JRV-0072** `P0` `E1` — “**Jarvis, stop a task after a hard failure.**”
- [ ] **JRV-0073** `P0` `E1` — “**Jarvis, undo a supported reversible action.**”
- [ ] **JRV-0074** `P0` `E1` — “**Jarvis, preview changes before applying them.**”
- [ ] **JRV-0075** `P0` `E1` — “**Jarvis, enforce a task execution deadline.**”
- [ ] **JRV-0076** `P0` `E1` — “**Jarvis, report partial completion accurately.**”
- [ ] **JRV-0077** `P0` `E1` — “**Jarvis, identify prerequisite tasks.**”
- [ ] **JRV-0078** `P0` `E1` — “**Jarvis, route ambiguous instructions back for clarification.**”
- [ ] **JRV-0079** `P0` `E1` — “**Jarvis, return a final step-by-step summary.**”
- [ ] **JRV-0080** `P0` `E1` — “**Jarvis, resume an interrupted task from its checkpoint.**”

### 05. Job Queue and Concurrency — `P0` · `E7` · 20 features
**Prerequisite capability:** `Task Planning and Verification`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0081** `P0` `E7` — “**Jarvis, add a long-running job to the queue.**”
- [ ] **JRV-0082** `P0` `E7` — “**Jarvis, show currently queued jobs.**”
- [ ] **JRV-0083** `P0` `E7` — “**Jarvis, show running jobs.**”
- [ ] **JRV-0084** `P0` `E7` — “**Jarvis, pause a queued job.**”
- [ ] **JRV-0085** `P0` `E7` — “**Jarvis, resume a paused queued job.**”
- [ ] **JRV-0086** `P0` `E7` — “**Jarvis, cancel a queued job.**”
- [ ] **JRV-0087** `P0` `E7` — “**Jarvis, prioritize an urgent safe job.**”
- [ ] **JRV-0088** `P0` `E7` — “**Jarvis, set a maximum number of concurrent jobs.**”
- [ ] **JRV-0089** `P0` `E7` — “**Jarvis, serialize jobs that share the mouse.**”
- [ ] **JRV-0090** `P0` `E7` — “**Jarvis, serialize jobs that share a browser profile.**”
- [ ] **JRV-0091** `P0` `E7` — “**Jarvis, reserve a microphone capture lease.**”
- [ ] **JRV-0092** `P0` `E7` — “**Jarvis, reserve a camera capture lease.**”
- [ ] **JRV-0093** `P0` `E7` — “**Jarvis, reserve a motor-control lease.**”
- [ ] **JRV-0094** `P0` `E7` — “**Jarvis, run CPU monitoring while music plays.**”
- [ ] **JRV-0095** `P0` `E7` — “**Jarvis, run two independent read-only jobs concurrently.**”
- [ ] **JRV-0096** `P0` `E7` — “**Jarvis, detect and resolve a task dependency deadlock.**”
- [ ] **JRV-0097** `P0` `E7` — “**Jarvis, recover unfinished jobs after restart.**”
- [ ] **JRV-0098** `P0` `E7` — “**Jarvis, avoid re-running an already completed purchase or send.**”
- [ ] **JRV-0099** `P0` `E7` — “**Jarvis, display job progress percentages only when measurable.**”
- [ ] **JRV-0100** `P0` `E7` — “**Jarvis, export the job history.**”

### 06. Service Health and Observability — `P0` · `E0` · 20 features
**Prerequisite capability:** `Foundation`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0101** `P0` `E0` — “**Jarvis, show whether JARVIS core is running.**”
- [ ] **JRV-0102** `P0` `E0` — “**Jarvis, show whether voice capture is actually active.**”
- [ ] **JRV-0103** `P0` `E0` — “**Jarvis, show whether the camera owner is active.**”
- [ ] **JRV-0104** `P0` `E0` — “**Jarvis, show installed AI providers and actual health.**”
- [ ] **JRV-0105** `P0` `E0` — “**Jarvis, show currently connected device capabilities.**”
- [ ] **JRV-0106** `P0` `E0` — “**Jarvis, show the most recent command result.**”
- [ ] **JRV-0107** `P0` `E0` — “**Jarvis, show why the last command failed.**”
- [ ] **JRV-0108** `P0` `E0` — “**Jarvis, show frontend-to-backend connectivity.**”
- [ ] **JRV-0109** `P0` `E0` — “**Jarvis, show task queue health.**”
- [ ] **JRV-0110** `P0` `E0` — “**Jarvis, show the active display server.**”
- [ ] **JRV-0111** `P0` `E0` — “**Jarvis, show the current authenticated operator role.**”
- [ ] **JRV-0112** `P0` `E0` — “**Jarvis, show the timestamp of the last live sensor reading.**”
- [ ] **JRV-0113** `P0` `E0` — “**Jarvis, show CPU and memory used by each JARVIS service.**”
- [ ] **JRV-0114** `P0` `E0` — “**Jarvis, show the last five verified operations.**”
- [ ] **JRV-0115** `P0` `E0` — “**Jarvis, show the last five blocked operations.**”
- [ ] **JRV-0116** `P0` `E0` — “**Jarvis, distinguish simulated from physical measurements.**”
- [ ] **JRV-0117** `P0` `E0` — “**Jarvis, show the service restart count.**”
- [ ] **JRV-0118** `P0` `E0` — “**Jarvis, show a concise dependency health report.**”
- [ ] **JRV-0119** `P0` `E0` — “**Jarvis, export a redacted diagnostic report.**”
- [ ] **JRV-0120** `P0` `E0` — “**Jarvis, show what JARVIS cannot do yet.**”

### 07. Identity and Authentication — `P0` · `E0` · 20 features
**Prerequisite capability:** `Foundation`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0121** `P0` `E0` — “**Jarvis, identify the current voice-session role.**”
- [ ] **JRV-0122** `P0` `E0` — “**Jarvis, identify the current web-session role.**”
- [ ] **JRV-0123** `P0` `E0` — “**Jarvis, start a local operator session.**”
- [ ] **JRV-0124** `P0` `E0` — “**Jarvis, end the current operator session.**”
- [ ] **JRV-0125** `P0` `E0` — “**Jarvis, lock sensitive actions when idle.**”
- [ ] **JRV-0126** `P0` `E0` — “**Jarvis, unlock an operator session with approved authentication.**”
- [ ] **JRV-0127** `P0` `E0` — “**Jarvis, require a PIN for administrative elevation.**”
- [ ] **JRV-0128** `P0` `E0` — “**Jarvis, expire an administrative session after inactivity.**”
- [ ] **JRV-0129** `P0` `E0` — “**Jarvis, show which identity owns the current task.**”
- [ ] **JRV-0130** `P0` `E0` — “**Jarvis, prevent a chat message from impersonating an administrator.**”
- [ ] **JRV-0131** `P0` `E0` — “**Jarvis, reject client-supplied role escalation.**”
- [ ] **JRV-0132** `P0` `E0` — “**Jarvis, require reauthentication for high-risk operations.**”
- [ ] **JRV-0133** `P0` `E0` — “**Jarvis, separate guest and operator capabilities.**”
- [ ] **JRV-0134** `P0` `E0` — “**Jarvis, revoke another stale session after approval.**”
- [ ] **JRV-0135** `P0` `E0` — “**Jarvis, show active sessions without exposing secrets.**”
- [ ] **JRV-0136** `P0` `E0` — “**Jarvis, limit repeated failed authentication attempts.**”
- [ ] **JRV-0137** `P0` `E0` — “**Jarvis, invalidate a session on logout.**”
- [ ] **JRV-0138** `P0` `E0` — “**Jarvis, prevent replay of an old approval.**”
- [ ] **JRV-0139** `P0` `E0` — “**Jarvis, associate an action with its originating session.**”
- [ ] **JRV-0140** `P0` `E0` — “**Jarvis, check identity before a remote command.**”

### 08. Permissions and Approval Workflow — `P0` · `E0` · 20 features
**Prerequisite capability:** `Identity and Authentication`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0141** `P0` `E0` — “**Jarvis, explain why an action was denied.**”
- [ ] **JRV-0142** `P0` `E0` — “**Jarvis, show the risk level of a proposed action.**”
- [ ] **JRV-0143** `P0` `E0` — “**Jarvis, request approval for a protected file edit.**”
- [ ] **JRV-0144** `P0` `E0` — “**Jarvis, request approval for a service restart.**”
- [ ] **JRV-0145** `P0` `E0` — “**Jarvis, request approval for package installation.**”
- [ ] **JRV-0146** `P0` `E0` — “**Jarvis, request approval before deleting a file.**”
- [ ] **JRV-0147** `P0` `E0` — “**Jarvis, request approval before sending an email.**”
- [ ] **JRV-0148** `P0` `E0` — “**Jarvis, request approval before a paid action.**”
- [ ] **JRV-0149** `P0` `E0` — “**Jarvis, request approval before pushing code.**”
- [ ] **JRV-0150** `P0` `E0` — “**Jarvis, request approval before physical motor movement.**”
- [ ] **JRV-0151** `P0` `E0` — “**Jarvis, approve one exact action.**”
- [ ] **JRV-0152** `P0` `E0` — “**Jarvis, deny one exact action.**”
- [ ] **JRV-0153** `P0` `E0` — “**Jarvis, expire an unused approval token.**”
- [ ] **JRV-0154** `P0` `E0` — “**Jarvis, revoke an active approval.**”
- [ ] **JRV-0155** `P0` `E0` — “**Jarvis, show pending approval requests.**”
- [ ] **JRV-0156** `P0` `E0` — “**Jarvis, prevent a webpage from granting tool permission.**”
- [ ] **JRV-0157** `P0` `E0` — “**Jarvis, block privileged operations in guest mode.**”
- [ ] **JRV-0158** `P0` `E0` — “**Jarvis, record an approval decision in the audit log.**”
- [ ] **JRV-0159** `P0` `E0` — “**Jarvis, show a human-readable preview of dangerous arguments.**”
- [ ] **JRV-0160** `P0` `E0` — “**Jarvis, require separate approval when a task's scope expands.**”

### 09. Security and Emergency Controls — `P0` · `E0` · 20 features
**Prerequisite capability:** `Permissions and Approval Workflow`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0161** `P0` `E0` — “**Jarvis, activate an immediate desktop automation stop.**”
- [ ] **JRV-0162** `P0` `E0` — “**Jarvis, release all held keyboard keys.**”
- [ ] **JRV-0163** `P0` `E0` — “**Jarvis, release all held mouse buttons.**”
- [ ] **JRV-0164** `P0` `E0` — “**Jarvis, halt a queued automation workflow.**”
- [ ] **JRV-0165** `P0` `E0` — “**Jarvis, latch a robot emergency stop.**”
- [ ] **JRV-0166** `P0` `E0` — “**Jarvis, keep motors disarmed on startup.**”
- [ ] **JRV-0167** `P0` `E0` — “**Jarvis, confirm the emergency stop is still active.**”
- [ ] **JRV-0168** `P0` `E0` — “**Jarvis, require authentication to rearm after emergency stop.**”
- [ ] **JRV-0169** `P0` `E0` — “**Jarvis, detect command-injection syntax in untrusted content.**”
- [ ] **JRV-0170** `P0` `E0` — “**Jarvis, refuse an arbitrary root shell request.**”
- [ ] **JRV-0171** `P0` `E0` — “**Jarvis, refuse access to private keys by default.**”
- [ ] **JRV-0172** `P0` `E0` — “**Jarvis, redact credentials from tool output.**”
- [ ] **JRV-0173** `P0` `E0` — “**Jarvis, prevent secrets from reaching the dashboard.**”
- [ ] **JRV-0174** `P0` `E0` — “**Jarvis, check that localhost services are not publicly exposed.**”
- [ ] **JRV-0175** `P0` `E0` — “**Jarvis, rotate audit logs safely.**”
- [ ] **JRV-0176** `P0` `E0` — “**Jarvis, verify an audit log has not been altered.**”
- [ ] **JRV-0177** `P0` `E0` — “**Jarvis, rate-limit remote control requests.**”
- [ ] **JRV-0178** `P0` `E0` — “**Jarvis, cancel tasks when the operator logs out.**”
- [ ] **JRV-0179** `P0` `E0` — “**Jarvis, protect camera and microphone privacy indicators.**”
- [ ] **JRV-0180** `P0` `E0` — “**Jarvis, run a security self-check without modifying the system.**”

### 10. Wake Word and Microphone — `P1` · `E5` · 20 features
**Prerequisite capability:** `Security and Emergency Controls`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0181** `P1` `E5` — “**Jarvis, show available microphones.**”
- [ ] **JRV-0182** `P1` `E5` — “**Jarvis, select the approved microphone.**”
- [ ] **JRV-0183** `P1` `E5` — “**Jarvis, verify microphone capture permission.**”
- [ ] **JRV-0184** `P1` `E5` — “**Jarvis, start listening after the wake phrase.**”
- [ ] **JRV-0185** `P1` `E5` — “**Jarvis, stop listening after a mute command.**”
- [ ] **JRV-0186** `P1` `E5` — “**Jarvis, show the real microphone capture owner.**”
- [ ] **JRV-0187** `P1` `E5` — “**Jarvis, prevent two processes from capturing the same microphone.**”
- [ ] **JRV-0188** `P1` `E5` — “**Jarvis, show microphone signal level.**”
- [ ] **JRV-0189** `P1` `E5` — “**Jarvis, calibrate ambient-noise thresholds.**”
- [ ] **JRV-0190** `P1` `E5` — “**Jarvis, tune wake-word sensitivity.**”
- [ ] **JRV-0191** `P1` `E5` — “**Jarvis, test wake-word false positives.**”
- [ ] **JRV-0192** `P1` `E5` — “**Jarvis, test missed wake-word detection.**”
- [ ] **JRV-0193** `P1` `E5` — “**Jarvis, enable push-to-talk.**”
- [ ] **JRV-0194** `P1` `E5` — “**Jarvis, disable push-to-talk.**”
- [ ] **JRV-0195** `P1` `E5` — “**Jarvis, cancel listening after prolonged silence.**”
- [ ] **JRV-0196** `P1` `E5` — “**Jarvis, confirm listening with a short sound.**”
- [ ] **JRV-0197** `P1` `E5` — “**Jarvis, temporarily suspend wake detection during calls.**”
- [ ] **JRV-0198** `P1` `E5` — “**Jarvis, restore listening after a service reconnect.**”
- [ ] **JRV-0199** `P1` `E5` — “**Jarvis, diagnose an unavailable microphone.**”
- [ ] **JRV-0200** `P1` `E5` — “**Jarvis, report wake-word engine latency.**”

### 11. Speech Recognition — `P1` · `E5` · 20 features
**Prerequisite capability:** `Wake Word and Microphone`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0201** `P1` `E5` — “**Jarvis, transcribe a short English command.**”
- [ ] **JRV-0202** `P1` `E5` — “**Jarvis, transcribe a short Hindi command.**”
- [ ] **JRV-0203** `P1` `E5` — “**Jarvis, transcribe a short Nepali command when supported.**”
- [ ] **JRV-0204** `P1` `E5` — “**Jarvis, switch recognition language on request.**”
- [ ] **JRV-0205** `P1` `E5` — “**Jarvis, automatically detect a supported spoken language.**”
- [ ] **JRV-0206** `P1` `E5` — “**Jarvis, show recognized text before a risky action.**”
- [ ] **JRV-0207** `P1` `E5` — “**Jarvis, ask me to repeat unclear speech.**”
- [ ] **JRV-0208** `P1` `E5` — “**Jarvis, ignore speech below a confidence threshold.**”
- [ ] **JRV-0209** `P1` `E5` — “**Jarvis, handle speech in a noisy room.**”
- [ ] **JRV-0210** `P1` `E5` — “**Jarvis, handle a long dictated paragraph.**”
- [ ] **JRV-0211** `P1` `E5` — “**Jarvis, recognize punctuation in dictation.**”
- [ ] **JRV-0212** `P1` `E5` — “**Jarvis, recognize spoken file extensions.**”
- [ ] **JRV-0213** `P1` `E5` — “**Jarvis, recognize spoken website addresses.**”
- [ ] **JRV-0214** `P1` `E5` — “**Jarvis, recognize numbers and units accurately.**”
- [ ] **JRV-0215** `P1` `E5` — “**Jarvis, recognize a spoken time and date.**”
- [ ] **JRV-0216** `P1` `E5` — “**Jarvis, separate speech from background music.**”
- [ ] **JRV-0217** `P1` `E5` — “**Jarvis, stop transcription when I say cancel.**”
- [ ] **JRV-0218** `P1` `E5` — “**Jarvis, stream partial transcriptions without executing them.**”
- [ ] **JRV-0219** `P1` `E5` — “**Jarvis, recover after STT provider failure.**”
- [ ] **JRV-0220** `P1` `E5` — “**Jarvis, store transcripts only with approved retention settings.**”

### 12. Speech Synthesis and Playback — `P1` · `E5` · 20 features
**Prerequisite capability:** `Speech Recognition`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0221** `P1` `E5` — “**Jarvis, read the answer aloud.**”
- [ ] **JRV-0222** `P1` `E5` — “**Jarvis, stop speaking immediately.**”
- [ ] **JRV-0223** `P1` `E5` — “**Jarvis, pause the current spoken answer.**”
- [ ] **JRV-0224** `P1` `E5` — “**Jarvis, resume the spoken answer.**”
- [ ] **JRV-0225** `P1` `E5` — “**Jarvis, change the speech volume.**”
- [ ] **JRV-0226** `P1` `E5` — “**Jarvis, change the speech speed.**”
- [ ] **JRV-0227** `P1` `E5` — “**Jarvis, select an installed local voice.**”
- [ ] **JRV-0228** `P1` `E5` — “**Jarvis, choose an available neural voice.**”
- [ ] **JRV-0229** `P1` `E5` — “**Jarvis, switch spoken output language.**”
- [ ] **JRV-0230** `P1` `E5` — “**Jarvis, speak in English.**”
- [ ] **JRV-0231** `P1` `E5` — “**Jarvis, speak in Hindi.**”
- [ ] **JRV-0232** `P1` `E5` — “**Jarvis, speak in Nepali when supported.**”
- [ ] **JRV-0233** `P1` `E5` — “**Jarvis, announce an error in a short sentence.**”
- [ ] **JRV-0234** `P1` `E5` — “**Jarvis, announce task completion.**”
- [ ] **JRV-0235** `P1` `E5` — “**Jarvis, play speech through the selected speaker.**”
- [ ] **JRV-0236** `P1` `E5` — “**Jarvis, show the current audio output device.**”
- [ ] **JRV-0237** `P1` `E5` — “**Jarvis, reduce music volume while speaking.**”
- [ ] **JRV-0238** `P1` `E5` — “**Jarvis, restore music volume afterward.**”
- [ ] **JRV-0239** `P1` `E5` — “**Jarvis, cache approved synthesized phrases.**”
- [ ] **JRV-0240** `P1` `E5` — “**Jarvis, fall back to a local voice when cloud TTS fails.**”

### 13. Conversational Voice Experience — `P1` · `E5` · 20 features
**Prerequisite capability:** `Speech Synthesis and Playback`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0241** `P1` `E5` — “**Jarvis, answer 'Hey Jarvis' with a short acknowledgement.**”
- [ ] **JRV-0242** `P1` `E5` — “**Jarvis, remember the last spoken task.**”
- [ ] **JRV-0243** `P1` `E5` — “**Jarvis, accept a follow-up without repeating the wake word.**”
- [ ] **JRV-0244** `P1` `E5` — “**Jarvis, answer a factual question while a task is running.**”
- [ ] **JRV-0245** `P1` `E5` — “**Jarvis, interrupt a long spoken explanation.**”
- [ ] **JRV-0246** `P1` `E5` — “**Jarvis, resume an explanation from where it stopped.**”
- [ ] **JRV-0247** `P1` `E5` — “**Jarvis, ask a spoken clarification for two matching accounts.**”
- [ ] **JRV-0248** `P1` `E5` — “**Jarvis, announce when authentication needs manual input.**”
- [ ] **JRV-0249** `P1` `E5` — “**Jarvis, confirm an approved privileged action before executing it.**”
- [ ] **JRV-0250** `P1` `E5` — “**Jarvis, speak a concise failure explanation.**”
- [ ] **JRV-0251** `P1` `E5` — “**Jarvis, tell me the status of a queued job.**”
- [ ] **JRV-0252** `P1` `E5` — “**Jarvis, continue a previous voice conversation after a short pause.**”
- [ ] **JRV-0253** `P1` `E5` — “**Jarvis, end the conversation on request.**”
- [ ] **JRV-0254** `P1` `E5` — “**Jarvis, mute and unmute the assistant.**”
- [ ] **JRV-0255** `P1` `E5` — “**Jarvis, switch between concise and detailed replies.**”
- [ ] **JRV-0256** `P1` `E5` — “**Jarvis, avoid repeating a spoken response after timeout.**”
- [ ] **JRV-0257** `P1` `E5` — “**Jarvis, synchronize captions with spoken output.**”
- [ ] **JRV-0258** `P1` `E5` — “**Jarvis, avoid speaking over active call audio.**”
- [ ] **JRV-0259** `P1` `E5` — “**Jarvis, react to an explicit 'be quiet' instruction.**”
- [ ] **JRV-0260** `P1` `E5` — “**Jarvis, handle a long natural multi-turn exchange.**”

### 14. Conversation Memory — `P1` · `E1` · 20 features
**Prerequisite capability:** `Identity and Authentication`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0261** `P1` `E1` — “**Jarvis, remember a preference after permission.**”
- [ ] **JRV-0262** `P1` `E1` — “**Jarvis, recall an explicitly saved preference.**”
- [ ] **JRV-0263** `P1` `E1` — “**Jarvis, forget a selected memory entry.**”
- [ ] **JRV-0264** `P1` `E1` — “**Jarvis, show what JARVIS remembers about the current project.**”
- [ ] **JRV-0265** `P1` `E1` — “**Jarvis, summarize yesterday's conversation when available.**”
- [ ] **JRV-0266** `P1` `E1` — “**Jarvis, find the last task I started.**”
- [ ] **JRV-0267** `P1` `E1` — “**Jarvis, remember an approved project directory.**”
- [ ] **JRV-0268** `P1` `E1` — “**Jarvis, remember a preferred browser profile label.**”
- [ ] **JRV-0269** `P1` `E1` — “**Jarvis, remember a preferred voice language.**”
- [ ] **JRV-0270** `P1` `E1` — “**Jarvis, remember a preferred output device.**”
- [ ] **JRV-0271** `P1` `E1` — “**Jarvis, maintain separate memories for different operators.**”
- [ ] **JRV-0272** `P1` `E1` — “**Jarvis, expire temporary working memory.**”
- [ ] **JRV-0273** `P1` `E1` — “**Jarvis, edit an incorrect memory record.**”
- [ ] **JRV-0274** `P1` `E1` — “**Jarvis, explain which memory informed an answer.**”
- [ ] **JRV-0275** `P1` `E1` — “**Jarvis, search memories by date.**”
- [ ] **JRV-0276** `P1` `E1` — “**Jarvis, search memories by topic.**”
- [ ] **JRV-0277** `P1` `E1` — “**Jarvis, export my saved memories.**”
- [ ] **JRV-0278** `P1` `E1` — “**Jarvis, import approved memory records.**”
- [ ] **JRV-0279** `P1` `E1` — “**Jarvis, prevent secrets from being stored as memory.**”
- [ ] **JRV-0280** `P1` `E1` — “**Jarvis, disable memory for a private session.**”

### 15. Knowledge Base and Retrieval — `P1` · `E1` · 20 features
**Prerequisite capability:** `Conversation Memory`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0281** `P1` `E1` — “**Jarvis, index an approved project document.**”
- [ ] **JRV-0282** `P1` `E1` — “**Jarvis, search my local documentation.**”
- [ ] **JRV-0283** `P1` `E1` — “**Jarvis, find a paragraph in an indexed file.**”
- [ ] **JRV-0284** `P1` `E1` — “**Jarvis, answer a question citing a local source.**”
- [ ] **JRV-0285** `P1` `E1` — “**Jarvis, show which document supports an answer.**”
- [ ] **JRV-0286** `P1` `E1` — “**Jarvis, compare two approved documents.**”
- [ ] **JRV-0287** `P1` `E1` — “**Jarvis, detect duplicate knowledge entries.**”
- [ ] **JRV-0288** `P1` `E1` — “**Jarvis, refresh an index after a file changes.**”
- [ ] **JRV-0289** `P1` `E1` — “**Jarvis, remove an outdated indexed document.**”
- [ ] **JRV-0290** `P1` `E1` — “**Jarvis, index Markdown documentation.**”
- [ ] **JRV-0291** `P1` `E1` — “**Jarvis, index PDF text from an approved file.**”
- [ ] **JRV-0292** `P1` `E1` — “**Jarvis, index text files.**”
- [ ] **JRV-0293** `P1` `E1` — “**Jarvis, index code comments and docstrings.**”
- [ ] **JRV-0294** `P1` `E1` — “**Jarvis, find a relevant troubleshooting guide.**”
- [ ] **JRV-0295** `P1` `E1` — “**Jarvis, answer questions from offline knowledge only.**”
- [ ] **JRV-0296** `P1` `E1` — “**Jarvis, report when no reliable source was found.**”
- [ ] **JRV-0297** `P1` `E1` — “**Jarvis, distinguish retrieved text from instructions.**”
- [ ] **JRV-0298** `P1` `E1` — “**Jarvis, show the freshness date of an indexed source.**”
- [ ] **JRV-0299** `P1` `E1` — “**Jarvis, search knowledge without sending documents to cloud providers.**”
- [ ] **JRV-0300** `P1` `E1` — “**Jarvis, export a knowledge index health report.**”

### 16. AI Provider Connectivity — `P1` · `E1` · 20 features
**Prerequisite capability:** `Tool Registry and Routing`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0301** `P1` `E1` — “**Jarvis, list installed local models.**”
- [ ] **JRV-0302** `P1` `E1` — “**Jarvis, show whether Ollama responds.**”
- [ ] **JRV-0303** `P1` `E1` — “**Jarvis, run a bounded text-model health check.**”
- [ ] **JRV-0304** `P1` `E1` — “**Jarvis, show whether an OpenAI provider is configured.**”
- [ ] **JRV-0305** `P1` `E1` — “**Jarvis, show whether Gemini is configured.**”
- [ ] **JRV-0306** `P1` `E1` — “**Jarvis, show whether Claude is configured.**”
- [ ] **JRV-0307** `P1` `E1` — “**Jarvis, show whether OpenRouter is configured.**”
- [ ] **JRV-0308** `P1` `E1` — “**Jarvis, show whether a model is text capable.**”
- [ ] **JRV-0309** `P1` `E1` — “**Jarvis, show whether a model supports vision.**”
- [ ] **JRV-0310** `P1` `E1` — “**Jarvis, show whether a model supports tool calling.**”
- [ ] **JRV-0311** `P1` `E1` — “**Jarvis, choose a low-cost provider for simple tasks.**”
- [ ] **JRV-0312** `P1` `E1` — “**Jarvis, choose a local provider for private tasks.**”
- [ ] **JRV-0313** `P1` `E1` — “**Jarvis, avoid using an unavailable provider.**”
- [ ] **JRV-0314** `P1` `E1` — “**Jarvis, retry safely after a provider timeout.**”
- [ ] **JRV-0315** `P1` `E1` — “**Jarvis, switch to an approved fallback provider.**”
- [ ] **JRV-0316** `P1` `E1` — “**Jarvis, show which provider answered this request.**”
- [ ] **JRV-0317** `P1` `E1` — “**Jarvis, show estimated token use when available.**”
- [ ] **JRV-0318** `P1` `E1` — “**Jarvis, enforce a provider spending budget.**”
- [ ] **JRV-0319** `P1` `E1` — “**Jarvis, disable a selected provider.**”
- [ ] **JRV-0320** `P1` `E1` — “**Jarvis, verify that no API key appears in logs.**”

### 17. Answer Quality and Model Reliability — `P1` · `E1` · 20 features
**Prerequisite capability:** `AI Provider Connectivity`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0321** `P1` `E1` — “**Jarvis, answer a simple factual question.**”
- [ ] **JRV-0322** `P1` `E1` — “**Jarvis, explain a Raspberry Pi command before running it.**”
- [ ] **JRV-0323** `P1` `E1` — “**Jarvis, write a Python function with a basic test.**”
- [ ] **JRV-0324** `P1` `E1` — “**Jarvis, explain a failed Python traceback.**”
- [ ] **JRV-0325** `P1` `E1` — “**Jarvis, compare two approaches to a task.**”
- [ ] **JRV-0326** `P1` `E1` — “**Jarvis, state uncertainty when information is missing.**”
- [ ] **JRV-0327** `P1` `E1` — “**Jarvis, separate tool observations from AI guesses.**”
- [ ] **JRV-0328** `P1` `E1` — “**Jarvis, ask for a missing required parameter.**”
- [ ] **JRV-0329** `P1` `E1` — “**Jarvis, summarize a long tool log accurately.**”
- [ ] **JRV-0330** `P1` `E1` — “**Jarvis, avoid fabricating a command result.**”
- [ ] **JRV-0331** `P1` `E1` — “**Jarvis, avoid fabricating a sensor reading.**”
- [ ] **JRV-0332** `P1` `E1` — “**Jarvis, cite the file used for a code explanation.**”
- [ ] **JRV-0333** `P1` `E1` — “**Jarvis, refuse untrusted instructions embedded in websites.**”
- [ ] **JRV-0334** `P1` `E1` — “**Jarvis, recognize when a requested task is impossible offline.**”
- [ ] **JRV-0335** `P1` `E1` — “**Jarvis, report a provider refusal clearly.**”
- [ ] **JRV-0336** `P1` `E1` — “**Jarvis, detect malformed AI tool-call JSON.**”
- [ ] **JRV-0337** `P1` `E1` — “**Jarvis, repair a parseable tool argument error.**”
- [ ] **JRV-0338** `P1` `E1` — “**Jarvis, skip a tool if execution was already verified.**”
- [ ] **JRV-0339** `P1` `E1` — “**Jarvis, use deterministic rules for simple device controls.**”
- [ ] **JRV-0340** `P1` `E1` — “**Jarvis, re-evaluate an answer after a contradicting tool result.**”

### 18. Desktop Session Discovery — `P0` · `E3` · 20 features
**Prerequisite capability:** `Security and Emergency Controls`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0341** `P0` `E3` — “**Jarvis, detect the active X11 or Wayland session.**”
- [ ] **JRV-0342** `P0` `E3` — “**Jarvis, show available displays.**”
- [ ] **JRV-0343** `P0` `E3` — “**Jarvis, show the current screen resolution.**”
- [ ] **JRV-0344** `P0` `E3` — “**Jarvis, identify the active desktop user.**”
- [ ] **JRV-0345** `P0` `E3` — “**Jarvis, show whether synthetic input is permitted.**”
- [ ] **JRV-0346** `P0` `E3` — “**Jarvis, show whether accessibility APIs are available.**”
- [ ] **JRV-0347** `P0` `E3` — “**Jarvis, list visible application windows.**”
- [ ] **JRV-0348** `P0` `E3` — “**Jarvis, identify the currently focused window.**”
- [ ] **JRV-0349** `P0` `E3` — “**Jarvis, show the pointer position.**”
- [ ] **JRV-0350** `P0` `E3` — “**Jarvis, show keyboard layout.**”
- [ ] **JRV-0351** `P0` `E3` — “**Jarvis, check desktop screenshot permission.**”
- [ ] **JRV-0352** `P0` `E3` — “**Jarvis, report an unavailable display instead of inventing one.**”
- [ ] **JRV-0353** `P0` `E3` — “**Jarvis, identify the active virtual workspace.**”
- [ ] **JRV-0354** `P0` `E3` — “**Jarvis, show the running window manager.**”
- [ ] **JRV-0355** `P0` `E3` — “**Jarvis, detect whether a VNC session differs from the local desktop.**”
- [ ] **JRV-0356** `P0` `E3` — “**Jarvis, choose the authorized display session.**”
- [ ] **JRV-0357** `P0` `E3` — “**Jarvis, verify the desktop session is unlocked.**”
- [ ] **JRV-0358** `P0` `E3` — “**Jarvis, avoid GUI actions while the session is locked.**”
- [ ] **JRV-0359** `P0` `E3` — “**Jarvis, reconnect after a display-session restart.**”
- [ ] **JRV-0360** `P0` `E3` — “**Jarvis, show desktop automation backend health.**”

### 19. Mouse and Pointer Control — `P0` · `E3` · 20 features
**Prerequisite capability:** `Desktop Session Discovery`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0361** `P0` `E3` — “**Jarvis, move the pointer to a named button.**”
- [ ] **JRV-0362** `P0` `E3` — “**Jarvis, move the pointer to specified screen coordinates.**”
- [ ] **JRV-0363** `P0` `E3` — “**Jarvis, single-click a visible button.**”
- [ ] **JRV-0364** `P0` `E3` — “**Jarvis, double-click a selected file.**”
- [ ] **JRV-0365** `P0` `E3` — “**Jarvis, right-click a visible item.**”
- [ ] **JRV-0366** `P0` `E3` — “**Jarvis, scroll down one page.**”
- [ ] **JRV-0367** `P0` `E3` — “**Jarvis, scroll up one page.**”
- [ ] **JRV-0368** `P0` `E3` — “**Jarvis, scroll a specified number of steps.**”
- [ ] **JRV-0369** `P0` `E3` — “**Jarvis, drag a file into an approved folder.**”
- [ ] **JRV-0370** `P0` `E3` — “**Jarvis, drag a window by its title bar.**”
- [ ] **JRV-0371** `P0` `E3` — “**Jarvis, hover over a menu option.**”
- [ ] **JRV-0372** `P0` `E3` — “**Jarvis, select a visible checkbox.**”
- [ ] **JRV-0373** `P0` `E3` — “**Jarvis, select a visible radio option.**”
- [ ] **JRV-0374** `P0` `E3` — “**Jarvis, move the pointer into a search field.**”
- [ ] **JRV-0375** `P0` `E3` — “**Jarvis, click a target found by accessibility label.**”
- [ ] **JRV-0376** `P0` `E3` — “**Jarvis, click a target found by OCR only with verified coordinates.**”
- [ ] **JRV-0377** `P0` `E3` — “**Jarvis, avoid clicking two ambiguous matches.**”
- [ ] **JRV-0378** `P0` `E3` — “**Jarvis, release the mouse after cancellation.**”
- [ ] **JRV-0379** `P0` `E3` — “**Jarvis, verify pointer location after movement.**”
- [ ] **JRV-0380** `P0` `E3` — “**Jarvis, recover gracefully from a missing pointer backend.**”

### 20. Keyboard and Clipboard Control — `P0` · `E3` · 20 features
**Prerequisite capability:** `Desktop Session Discovery`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0381** `P0` `E3` — “**Jarvis, type a provided sentence into the focused field.**”
- [ ] **JRV-0382** `P0` `E3` — “**Jarvis, press Enter in the active app.**”
- [ ] **JRV-0383** `P0` `E3` — “**Jarvis, press Escape to close a dialog.**”
- [ ] **JRV-0384** `P0` `E3` — “**Jarvis, select all text in an editable field.**”
- [ ] **JRV-0385** `P0` `E3` — “**Jarvis, copy selected text.**”
- [ ] **JRV-0386** `P0` `E3` — “**Jarvis, paste approved clipboard content.**”
- [ ] **JRV-0387** `P0` `E3` — “**Jarvis, cut selected text.**”
- [ ] **JRV-0388** `P0` `E3` — “**Jarvis, undo an editable action.**”
- [ ] **JRV-0389** `P0` `E3` — “**Jarvis, redo an editable action.**”
- [ ] **JRV-0390** `P0` `E3` — “**Jarvis, press a specified safe keyboard shortcut.**”
- [ ] **JRV-0391** `P0` `E3` — “**Jarvis, hold and release a modifier key correctly.**”
- [ ] **JRV-0392** `P0` `E3` — “**Jarvis, clear a text field without deleting the file.**”
- [ ] **JRV-0393** `P0` `E3` — “**Jarvis, type Unicode text in a supported editor.**”
- [ ] **JRV-0394** `P0` `E3` — “**Jarvis, type Hindi text in a supported input method.**”
- [ ] **JRV-0395** `P0` `E3` — “**Jarvis, type Nepali text in a supported input method.**”
- [ ] **JRV-0396** `P0` `E3` — “**Jarvis, read the current clipboard only after permission.**”
- [ ] **JRV-0397** `P0` `E3` — “**Jarvis, clear sensitive clipboard content.**”
- [ ] **JRV-0398** `P0` `E3` — “**Jarvis, avoid typing into a password field without approval.**”
- [ ] **JRV-0399** `P0` `E3` — “**Jarvis, stop a typing sequence on emergency stop.**”
- [ ] **JRV-0400** `P0` `E3` — “**Jarvis, verify entered text in an approved test field.**”

### 21. Window and Workspace Management — `P1` · `E3` · 20 features
**Prerequisite capability:** `Desktop Session Discovery`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0401** `P1` `E3` — “**Jarvis, list all open windows.**”
- [ ] **JRV-0402** `P1` `E3` — “**Jarvis, focus Chrome.**”
- [ ] **JRV-0403** `P1` `E3` — “**Jarvis, focus the terminal.**”
- [ ] **JRV-0404** `P1` `E3` — “**Jarvis, switch to the previous application.**”
- [ ] **JRV-0405** `P1` `E3` — “**Jarvis, minimize an approved window.**”
- [ ] **JRV-0406** `P1` `E3` — “**Jarvis, maximize an approved window.**”
- [ ] **JRV-0407** `P1` `E3` — “**Jarvis, restore a minimized window.**”
- [ ] **JRV-0408** `P1` `E3` — “**Jarvis, move a window to another workspace.**”
- [ ] **JRV-0409** `P1` `E3` — “**Jarvis, switch to workspace two.**”
- [ ] **JRV-0410** `P1` `E3` — “**Jarvis, close a selected unsaved window only after confirmation.**”
- [ ] **JRV-0411** `P1` `E3` — “**Jarvis, show the title of the focused window.**”
- [ ] **JRV-0412** `P1` `E3` — “**Jarvis, move a window without leaving the visible screen.**”
- [ ] **JRV-0413** `P1` `E3` — “**Jarvis, resize an approved application window.**”
- [ ] **JRV-0414** `P1` `E3` — “**Jarvis, tile two windows side by side.**”
- [ ] **JRV-0415** `P1` `E3` — “**Jarvis, switch between two Chrome windows.**”
- [ ] **JRV-0416** `P1` `E3` — “**Jarvis, open a new desktop workspace.**”
- [ ] **JRV-0417** `P1` `E3` — “**Jarvis, close an empty workspace.**”
- [ ] **JRV-0418** `P1` `E3` — “**Jarvis, show windows belonging to an application.**”
- [ ] **JRV-0419** `P1` `E3` — “**Jarvis, detect an unexpected dialog blocking a task.**”
- [ ] **JRV-0420** `P1` `E3` — “**Jarvis, restore focus to the original app after a task.**”

### 22. Desktop Application Control — `P1` · `E3` · 20 features
**Prerequisite capability:** `Window and Workspace Management`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0421** `P1` `E3` — “**Jarvis, open the calculator application.**”
- [ ] **JRV-0422** `P1` `E3` — “**Jarvis, open the file manager.**”
- [ ] **JRV-0423** `P1` `E3` — “**Jarvis, open the terminal.**”
- [ ] **JRV-0424** `P1` `E3` — “**Jarvis, open VS Code.**”
- [ ] **JRV-0425** `P1` `E3` — “**Jarvis, open Chrome.**”
- [ ] **JRV-0426** `P1` `E3` — “**Jarvis, open Firefox if installed.**”
- [ ] **JRV-0427** `P1` `E3` — “**Jarvis, open an approved text editor.**”
- [ ] **JRV-0428** `P1` `E3` — “**Jarvis, open a PDF viewer.**”
- [ ] **JRV-0429** `P1` `E3` — “**Jarvis, open image viewer.**”
- [ ] **JRV-0430** `P1` `E3` — “**Jarvis, open system settings.**”
- [ ] **JRV-0431** `P1` `E3` — “**Jarvis, close an application politely.**”
- [ ] **JRV-0432** `P1` `E3` — “**Jarvis, check whether an application is installed.**”
- [ ] **JRV-0433** `P1` `E3` — “**Jarvis, search for installed applications.**”
- [ ] **JRV-0434** `P1` `E3` — “**Jarvis, open a file in its default app.**”
- [ ] **JRV-0435** `P1` `E3` — “**Jarvis, open a project in the configured IDE.**”
- [ ] **JRV-0436** `P1` `E3` — “**Jarvis, bring an existing app instance to the front.**”
- [ ] **JRV-0437** `P1` `E3` — “**Jarvis, detect a crashed desktop application.**”
- [ ] **JRV-0438** `P1` `E3` — “**Jarvis, restart a crashed noncritical app after approval.**”
- [ ] **JRV-0439** `P1` `E3` — “**Jarvis, show the executable used to open an app.**”
- [ ] **JRV-0440** `P1` `E3` — “**Jarvis, explain why an application cannot start.**”

### 23. Screenshot and Screen Understanding — `P1` · `E3` · 20 features
**Prerequisite capability:** `Desktop Session Discovery`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0441** `P1` `E3` — “**Jarvis, capture the current authorized screen.**”
- [ ] **JRV-0442** `P1` `E3` — “**Jarvis, capture one selected window.**”
- [ ] **JRV-0443** `P1` `E3` — “**Jarvis, read visible text from a screenshot.**”
- [ ] **JRV-0444** `P1` `E3` — “**Jarvis, locate a button by its accessible name.**”
- [ ] **JRV-0445** `P1` `E3` — “**Jarvis, locate a menu using OCR.**”
- [ ] **JRV-0446** `P1` `E3` — “**Jarvis, describe a screenshot with an available vision model.**”
- [ ] **JRV-0447** `P1` `E3` — “**Jarvis, identify an on-screen error message.**”
- [ ] **JRV-0448** `P1` `E3` — “**Jarvis, explain a visible traceback.**”
- [ ] **JRV-0449** `P1` `E3` — “**Jarvis, read the title of a dialog.**”
- [ ] **JRV-0450** `P1` `E3` — “**Jarvis, compare two screenshots to detect a change.**”
- [ ] **JRV-0451** `P1` `E3` — “**Jarvis, mask password fields before storing screenshots.**”
- [ ] **JRV-0452** `P1` `E3` — “**Jarvis, avoid capturing unauthorized windows.**”
- [ ] **JRV-0453** `P1` `E3` — “**Jarvis, show screenshot timestamp and active display.**”
- [ ] **JRV-0454** `P1` `E3` — “**Jarvis, report low-confidence OCR text as uncertain.**”
- [ ] **JRV-0455** `P1` `E3` — “**Jarvis, detect an offscreen target.**”
- [ ] **JRV-0456** `P1` `E3` — “**Jarvis, scroll until an element becomes visible.**”
- [ ] **JRV-0457** `P1` `E3` — “**Jarvis, verify that a confirmation banner appeared.**”
- [ ] **JRV-0458** `P1` `E3` — “**Jarvis, identify a loading indicator.**”
- [ ] **JRV-0459** `P1` `E3` — “**Jarvis, wait for a page to finish rendering.**”
- [ ] **JRV-0460** `P1` `E3` — “**Jarvis, discard sensitive screen images after task completion.**”

### 24. Chrome and Browser Lifecycle — `P0` · `E2` · 20 features
**Prerequisite capability:** `Desktop Application Control`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0461** `P0` `E2` — “**Jarvis, open Chrome in the real desktop session.**”
- [ ] **JRV-0462** `P0` `E2` — “**Jarvis, open a requested URL in Chrome.**”
- [ ] **JRV-0463** `P0` `E2` — “**Jarvis, reuse the currently running Chrome window.**”
- [ ] **JRV-0464** `P0` `E2` — “**Jarvis, open a new Chrome tab.**”
- [ ] **JRV-0465** `P0` `E2` — “**Jarvis, open a new Chrome window.**”
- [ ] **JRV-0466** `P0` `E2` — “**Jarvis, close a selected Chrome tab.**”
- [ ] **JRV-0467** `P0` `E2` — “**Jarvis, close a selected Chrome window with confirmation.**”
- [ ] **JRV-0468** `P0` `E2` — “**Jarvis, focus an existing Chrome tab.**”
- [ ] **JRV-0469** `P0` `E2` — “**Jarvis, list currently open browser windows.**”
- [ ] **JRV-0470** `P0` `E2` — “**Jarvis, show the active page URL.**”
- [ ] **JRV-0471** `P0` `E2` — “**Jarvis, show the active tab title.**”
- [ ] **JRV-0472** `P0` `E2` — “**Jarvis, detect whether Chrome is installed.**”
- [ ] **JRV-0473** `P0` `E2` — “**Jarvis, detect whether Chrome is running.**”
- [ ] **JRV-0474** `P0` `E2` — “**Jarvis, recover from a failed browser launch.**”
- [ ] **JRV-0475** `P0` `E2` — “**Jarvis, reconnect to an authorized browser session.**”
- [ ] **JRV-0476** `P0` `E2` — “**Jarvis, distinguish headless browser from visible user Chrome.**”
- [ ] **JRV-0477** `P0` `E2` — “**Jarvis, choose Chrome or Firefox on request.**”
- [ ] **JRV-0478** `P0` `E2` — “**Jarvis, avoid starting duplicate browser sessions.**”
- [ ] **JRV-0479** `P0` `E2` — “**Jarvis, close the automation-owned browser without closing personal tabs.**”
- [ ] **JRV-0480** `P0` `E2` — “**Jarvis, show the active browser backend.**”

### 25. Browser Page Navigation — `P0` · `E2` · 20 features
**Prerequisite capability:** `Chrome and Browser Lifecycle`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0481** `P0` `E2` — “**Jarvis, go back one page.**”
- [ ] **JRV-0482** `P0` `E2` — “**Jarvis, go forward one page.**”
- [ ] **JRV-0483** `P0` `E2` — “**Jarvis, reload the current page.**”
- [ ] **JRV-0484** `P0` `E2` — “**Jarvis, navigate to a specific URL.**”
- [ ] **JRV-0485** `P0` `E2` — “**Jarvis, open a link in a new tab.**”
- [ ] **JRV-0486** `P0` `E2` — “**Jarvis, switch to tab one.**”
- [ ] **JRV-0487** `P0` `E2` — “**Jarvis, switch to the next tab.**”
- [ ] **JRV-0488** `P0` `E2` — “**Jarvis, switch to the previous tab.**”
- [ ] **JRV-0489** `P0` `E2` — “**Jarvis, scroll a webpage down.**”
- [ ] **JRV-0490** `P0` `E2` — “**Jarvis, scroll a webpage up.**”
- [ ] **JRV-0491** `P0` `E2` — “**Jarvis, jump to the top of a page.**”
- [ ] **JRV-0492** `P0` `E2` — “**Jarvis, jump to the bottom of a page.**”
- [ ] **JRV-0493** `P0` `E2` — “**Jarvis, find text within a webpage.**”
- [ ] **JRV-0494** `P0` `E2` — “**Jarvis, copy the active page URL.**”
- [ ] **JRV-0495** `P0` `E2` — “**Jarvis, copy the active page title.**”
- [ ] **JRV-0496** `P0` `E2` — “**Jarvis, wait for page navigation to complete.**”
- [ ] **JRV-0497** `P0` `E2` — “**Jarvis, detect a navigation timeout.**”
- [ ] **JRV-0498** `P0` `E2` — “**Jarvis, return to a previous verified page.**”
- [ ] **JRV-0499** `P0` `E2` — “**Jarvis, recognize a login-required page.**”
- [ ] **JRV-0500** `P0` `E2` — “**Jarvis, summarize the visible webpage.**”

### 26. Browser Forms and DOM Interaction — `P0` · `E2` · 20 features
**Prerequisite capability:** `Browser Page Navigation`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0501** `P0` `E2` — “**Jarvis, click a button by its accessible label.**”
- [ ] **JRV-0502** `P0` `E2` — “**Jarvis, fill a search box.**”
- [ ] **JRV-0503** `P0` `E2` — “**Jarvis, submit a simple search form.**”
- [ ] **JRV-0504** `P0` `E2` — “**Jarvis, select a dropdown option.**”
- [ ] **JRV-0505** `P0` `E2` — “**Jarvis, check a named checkbox.**”
- [ ] **JRV-0506** `P0` `E2` — “**Jarvis, uncheck a named checkbox.**”
- [ ] **JRV-0507** `P0` `E2` — “**Jarvis, choose a radio button.**”
- [ ] **JRV-0508** `P0` `E2` — “**Jarvis, type into a text area.**”
- [ ] **JRV-0509** `P0` `E2` — “**Jarvis, clear a form field.**”
- [ ] **JRV-0510** `P0` `E2` — “**Jarvis, upload an approved local file to a form.**”
- [ ] **JRV-0511** `P0` `E2` — “**Jarvis, click a pagination link.**”
- [ ] **JRV-0512** `P0` `E2` — “**Jarvis, open an accessible menu.**”
- [ ] **JRV-0513** `P0` `E2` — “**Jarvis, select a menu entry.**”
- [ ] **JRV-0514** `P0` `E2` — “**Jarvis, read a result table.**”
- [ ] **JRV-0515** `P0` `E2` — “**Jarvis, extract a visible result title.**”
- [ ] **JRV-0516** `P0` `E2` — “**Jarvis, handle an autocomplete suggestion.**”
- [ ] **JRV-0517** `P0` `E2` — “**Jarvis, detect multiple matching Submit buttons.**”
- [ ] **JRV-0518** `P0` `E2` — “**Jarvis, pause before posting a form with external effects.**”
- [ ] **JRV-0519** `P0` `E2` — “**Jarvis, verify a form submission confirmation.**”
- [ ] **JRV-0520** `P0` `E2` — “**Jarvis, stop when the page demands CAPTCHA completion.**”

### 27. Browser Profiles and Accounts — `P0` · `E2` · 20 features
**Prerequisite capability:** `Browser Forms and DOM Interaction`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0521** `P0` `E2` — “**Jarvis, list locally registered Chrome profile labels.**”
- [ ] **JRV-0522** `P0` `E2` — “**Jarvis, identify the current Chrome profile.**”
- [ ] **JRV-0523** `P0` `E2` — “**Jarvis, open Chrome with a selected registered profile.**”
- [ ] **JRV-0524** `P0` `E2` — “**Jarvis, switch to a different approved Chrome profile.**”
- [ ] **JRV-0525** `P0` `E2` — “**Jarvis, return to the previous Chrome profile.**”
- [ ] **JRV-0526** `P0` `E2` — “**Jarvis, show whether a profile has an active YouTube session.**”
- [ ] **JRV-0527** `P0` `E2` — “**Jarvis, open the YouTube account menu.**”
- [ ] **JRV-0528** `P0` `E2` — “**Jarvis, list account labels shown in the YouTube switcher.**”
- [ ] **JRV-0529** `P0` `E2` — “**Jarvis, select an already signed-in YouTube account.**”
- [ ] **JRV-0530** `P0` `E2` — “**Jarvis, verify the active YouTube account label.**”
- [ ] **JRV-0531** `P0` `E2` — “**Jarvis, switch to another signed-in Google account.**”
- [ ] **JRV-0532** `P0` `E2` — “**Jarvis, verify the active Google account after switching.**”
- [ ] **JRV-0533** `P0` `E2` — “**Jarvis, request a human login when a session expired.**”
- [ ] **JRV-0534** `P0` `E2` — “**Jarvis, wait for completion of two-factor authentication.**”
- [ ] **JRV-0535** `P0` `E2` — “**Jarvis, avoid storing browser passwords in JARVIS memory.**”
- [ ] **JRV-0536** `P0` `E2` — “**Jarvis, avoid exporting Chrome cookies or session tokens.**”
- [ ] **JRV-0537** `P0` `E2` — “**Jarvis, keep a task inside its chosen browser profile.**”
- [ ] **JRV-0538** `P0` `E2` — “**Jarvis, detect a conflicting profile lock.**”
- [ ] **JRV-0539** `P0` `E2` — “**Jarvis, ask which account when labels are ambiguous.**”
- [ ] **JRV-0540** `P0` `E2` — “**Jarvis, abort account switching when identity cannot be verified.**”

### 28. YouTube and Streaming Media — `P1` · `E2` · 20 features
**Prerequisite capability:** `Browser Profiles and Accounts`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0541** `P1` `E2` — “**Jarvis, open the YouTube home page.**”
- [ ] **JRV-0542** `P1` `E2` — “**Jarvis, search YouTube for a topic.**”
- [ ] **JRV-0543** `P1` `E2` — “**Jarvis, read the top video result titles.**”
- [ ] **JRV-0544** `P1` `E2` — “**Jarvis, open the first requested search result.**”
- [ ] **JRV-0545** `P1` `E2` — “**Jarvis, open a specified numbered search result.**”
- [ ] **JRV-0546** `P1` `E2` — “**Jarvis, play the opened YouTube video.**”
- [ ] **JRV-0547** `P1` `E2` — “**Jarvis, pause the active video.**”
- [ ] **JRV-0548** `P1` `E2` — “**Jarvis, resume the paused video.**”
- [ ] **JRV-0549** `P1` `E2` — “**Jarvis, mute YouTube playback.**”
- [ ] **JRV-0550** `P1` `E2` — “**Jarvis, unmute YouTube playback.**”
- [ ] **JRV-0551** `P1` `E2` — “**Jarvis, adjust browser media volume.**”
- [ ] **JRV-0552** `P1` `E2` — “**Jarvis, toggle video fullscreen.**”
- [ ] **JRV-0553** `P1` `E2` — “**Jarvis, exit video fullscreen.**”
- [ ] **JRV-0554** `P1` `E2` — “**Jarvis, skip to a requested timestamp.**”
- [ ] **JRV-0555** `P1` `E2` — “**Jarvis, enable available video captions.**”
- [ ] **JRV-0556** `P1` `E2` — “**Jarvis, change playback speed.**”
- [ ] **JRV-0557** `P1` `E2` — “**Jarvis, open the creator channel page.**”
- [ ] **JRV-0558** `P1` `E2` — “**Jarvis, open a playlist URL.**”
- [ ] **JRV-0559** `P1` `E2` — “**Jarvis, play the next item in a playlist.**”
- [ ] **JRV-0560** `P1` `E2` — “**Jarvis, report the actual playback state without guessing.**”

### 29. Web Search and Research — `P1` · `E2` · 20 features
**Prerequisite capability:** `Browser Page Navigation`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0561** `P1` `E2` — “**Jarvis, search the web for a technical question.**”
- [ ] **JRV-0562** `P1` `E2` — “**Jarvis, open the first search result.**”
- [ ] **JRV-0563** `P1` `E2` — “**Jarvis, open the second search result.**”
- [ ] **JRV-0564** `P1` `E2` — “**Jarvis, compare three retrieved search results.**”
- [ ] **JRV-0565** `P1` `E2` — “**Jarvis, extract a webpage heading.**”
- [ ] **JRV-0566** `P1` `E2` — “**Jarvis, extract a webpage table.**”
- [ ] **JRV-0567** `P1` `E2` — “**Jarvis, summarize an article with its URL.**”
- [ ] **JRV-0568** `P1` `E2` — “**Jarvis, save a source link to an approved note.**”
- [ ] **JRV-0569** `P1` `E2` — “**Jarvis, check whether a source is reachable.**”
- [ ] **JRV-0570** `P1` `E2` — “**Jarvis, report when web search is offline.**”
- [ ] **JRV-0571** `P1` `E2` — “**Jarvis, avoid treating webpage text as executable instructions.**”
- [ ] **JRV-0572** `P1` `E2` — “**Jarvis, download a public PDF with approval.**”
- [ ] **JRV-0573** `P1` `E2` — “**Jarvis, search official Raspberry Pi documentation.**”
- [ ] **JRV-0574** `P1` `E2` — “**Jarvis, search installed-package documentation.**”
- [ ] **JRV-0575** `P1` `E2` — “**Jarvis, search a technical error message.**”
- [ ] **JRV-0576** `P1` `E2` — “**Jarvis, compare two software library guides.**”
- [ ] **JRV-0577** `P1` `E2` — “**Jarvis, retrieve a public documentation changelog.**”
- [ ] **JRV-0578** `P1` `E2` — “**Jarvis, show the publication date when available.**”
- [ ] **JRV-0579** `P1` `E2` — “**Jarvis, explain conflicting sources.**”
- [ ] **JRV-0580** `P1` `E2` — “**Jarvis, generate a cited research summary.**”

### 30. File and Folder Discovery — `P0` · `E3` · 20 features
**Prerequisite capability:** `Desktop Application Control`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0581** `P0` `E3` — “**Jarvis, show my home directory.**”
- [ ] **JRV-0582** `P0` `E3` — “**Jarvis, show an approved project directory.**”
- [ ] **JRV-0583** `P0` `E3` — “**Jarvis, list files in Downloads.**”
- [ ] **JRV-0584** `P0` `E3` — “**Jarvis, list folders in Documents.**”
- [ ] **JRV-0585** `P0` `E3` — “**Jarvis, find files by filename.**”
- [ ] **JRV-0586** `P0` `E3` — “**Jarvis, find files by extension.**”
- [ ] **JRV-0587** `P0` `E3` — “**Jarvis, find files modified today.**”
- [ ] **JRV-0588** `P0` `E3` — “**Jarvis, find files larger than a given size.**”
- [ ] **JRV-0589** `P0` `E3` — “**Jarvis, find duplicate filenames in a directory.**”
- [ ] **JRV-0590** `P0` `E3` — “**Jarvis, show file ownership.**”
- [ ] **JRV-0591** `P0` `E3` — “**Jarvis, show file permissions.**”
- [ ] **JRV-0592** `P0` `E3` — “**Jarvis, show a directory tree.**”
- [ ] **JRV-0593** `P0` `E3` — “**Jarvis, show hidden files after approval.**”
- [ ] **JRV-0594** `P0` `E3` — “**Jarvis, resolve a symbolic link safely.**”
- [ ] **JRV-0595** `P0` `E3` — “**Jarvis, check whether a file exists.**”
- [ ] **JRV-0596** `P0` `E3` — “**Jarvis, identify a file's MIME type.**”
- [ ] **JRV-0597** `P0` `E3` — “**Jarvis, show disk usage for a directory.**”
- [ ] **JRV-0598** `P0` `E3` — “**Jarvis, show recent files in the project.**”
- [ ] **JRV-0599** `P0` `E3` — “**Jarvis, bookmark an approved folder.**”
- [ ] **JRV-0600** `P0` `E3` — “**Jarvis, report inaccessible directories without escalation.**”

### 31. File Management and Organization — `P1` · `E3` · 20 features
**Prerequisite capability:** `File and Folder Discovery`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0601** `P1` `E3` — “**Jarvis, create a named folder in my workspace.**”
- [ ] **JRV-0602** `P1` `E3` — “**Jarvis, create a blank text file.**”
- [ ] **JRV-0603** `P1` `E3` — “**Jarvis, rename an approved file.**”
- [ ] **JRV-0604** `P1` `E3` — “**Jarvis, copy a file into an approved folder.**”
- [ ] **JRV-0605** `P1` `E3` — “**Jarvis, move a file into an approved folder.**”
- [ ] **JRV-0606** `P1` `E3` — “**Jarvis, preview files that would be moved.**”
- [ ] **JRV-0607** `P1` `E3` — “**Jarvis, archive a selected folder as ZIP.**”
- [ ] **JRV-0608** `P1` `E3` — “**Jarvis, extract an approved ZIP archive safely.**”
- [ ] **JRV-0609** `P1` `E3` — “**Jarvis, create a dated backup copy of a file.**”
- [ ] **JRV-0610** `P1` `E3` — “**Jarvis, compare two filenames and sizes.**”
- [ ] **JRV-0611** `P1` `E3` — “**Jarvis, show checksums for two files.**”
- [ ] **JRV-0612** `P1` `E3` — “**Jarvis, remove a duplicate only after approval.**”
- [ ] **JRV-0613** `P1` `E3` — “**Jarvis, move an unwanted file to Trash after approval.**”
- [ ] **JRV-0614** `P1` `E3` — “**Jarvis, restore a file from Trash.**”
- [ ] **JRV-0615** `P1` `E3` — “**Jarvis, empty Trash only after explicit approval.**”
- [ ] **JRV-0616** `P1` `E3` — “**Jarvis, protect files outside the active workspace.**”
- [ ] **JRV-0617** `P1` `E3` — “**Jarvis, resolve filename conflicts before copying.**”
- [ ] **JRV-0618** `P1` `E3` — “**Jarvis, show which files changed during a task.**”
- [ ] **JRV-0619** `P1` `E3` — “**Jarvis, undo a supported move operation.**”
- [ ] **JRV-0620** `P1` `E3` — “**Jarvis, produce a manifest of an approved directory.**”

### 32. Text and Content Editing — `P1` · `E3` · 20 features
**Prerequisite capability:** `File Management and Organization`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0621** `P1` `E3` — “**Jarvis, read an approved text file aloud.**”
- [ ] **JRV-0622** `P1` `E3` — “**Jarvis, display the first lines of a file.**”
- [ ] **JRV-0623** `P1` `E3` — “**Jarvis, display the last lines of a file.**”
- [ ] **JRV-0624** `P1` `E3` — “**Jarvis, search text inside an approved file.**”
- [ ] **JRV-0625** `P1` `E3` — “**Jarvis, append a note to an approved Markdown file.**”
- [ ] **JRV-0626** `P1` `E3` — “**Jarvis, replace an exact text string after preview.**”
- [ ] **JRV-0627** `P1` `E3` — “**Jarvis, create a Markdown checklist.**”
- [ ] **JRV-0628** `P1` `E3` — “**Jarvis, format an approved JSON file.**”
- [ ] **JRV-0629** `P1` `E3` — “**Jarvis, validate JSON syntax.**”
- [ ] **JRV-0630** `P1` `E3` — “**Jarvis, validate a YAML configuration.**”
- [ ] **JRV-0631** `P1` `E3` — “**Jarvis, compare two file contents.**”
- [ ] **JRV-0632** `P1` `E3` — “**Jarvis, show a unified diff before editing.**”
- [ ] **JRV-0633** `P1` `E3` — “**Jarvis, revert an edit from a backup.**”
- [ ] **JRV-0634** `P1` `E3` — “**Jarvis, extract URLs from a text file.**”
- [ ] **JRV-0635** `P1` `E3` — “**Jarvis, count words in a document.**”
- [ ] **JRV-0636** `P1` `E3` — “**Jarvis, count lines in a source file.**”
- [ ] **JRV-0637** `P1` `E3` — “**Jarvis, convert plaintext to Markdown.**”
- [ ] **JRV-0638** `P1` `E3` — “**Jarvis, convert an approved text file to CSV.**”
- [ ] **JRV-0639** `P1` `E3` — “**Jarvis, redact email addresses from an approved export.**”
- [ ] **JRV-0640** `P1` `E3` — “**Jarvis, verify that an edited file still parses.**”

### 33. Terminal and Command Execution — `P0` · `E4` · 20 features
**Prerequisite capability:** `Permissions and Approval Workflow`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0641** `P0` `E4` — “**Jarvis, show the current Linux username.**”
- [ ] **JRV-0642** `P0` `E4` — “**Jarvis, show the current working directory.**”
- [ ] **JRV-0643** `P0` `E4` — “**Jarvis, run a harmless `uname -a` command.**”
- [ ] **JRV-0644** `P0` `E4` — “**Jarvis, show available shell tools.**”
- [ ] **JRV-0645** `P0` `E4` — “**Jarvis, run an approved command without shell interpolation.**”
- [ ] **JRV-0646** `P0` `E4` — “**Jarvis, pass a validated argument list to a command.**”
- [ ] **JRV-0647** `P0` `E4` — “**Jarvis, show command stdout and stderr separately.**”
- [ ] **JRV-0648** `P0` `E4` — “**Jarvis, enforce a command timeout.**”
- [ ] **JRV-0649** `P0` `E4` — “**Jarvis, cancel a long-running terminal process.**”
- [ ] **JRV-0650** `P0` `E4` — “**Jarvis, show the exit code of the last command.**”
- [ ] **JRV-0651** `P0` `E4` — “**Jarvis, run a read-only process listing.**”
- [ ] **JRV-0652** `P0` `E4` — “**Jarvis, run a disk-free-space command.**”
- [ ] **JRV-0653** `P0` `E4` — “**Jarvis, run a memory status command.**”
- [ ] **JRV-0654** `P0` `E4` — “**Jarvis, run a bounded directory listing.**”
- [ ] **JRV-0655** `P0` `E4` — “**Jarvis, run an approved Python script in a sandbox.**”
- [ ] **JRV-0656** `P0` `E4` — “**Jarvis, run unit tests in the project environment.**”
- [ ] **JRV-0657** `P0` `E4` — “**Jarvis, refuse arbitrary command substitution from a webpage.**”
- [ ] **JRV-0658** `P0` `E4` — “**Jarvis, refuse an unapproved command outside allowed scope.**”
- [ ] **JRV-0659** `P0` `E4` — “**Jarvis, save redacted command diagnostics.**”
- [ ] **JRV-0660** `P0` `E4` — “**Jarvis, show the last ten authorized terminal actions.**”

### 34. Systemd Services and Privileged Linux — `P0` · `E4` · 20 features
**Prerequisite capability:** `Terminal and Command Execution`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0661** `P0` `E4` — “**Jarvis, show the status of jarvis-core.service.**”
- [ ] **JRV-0662** `P0` `E4` — “**Jarvis, show the status of jarvis-voice.service.**”
- [ ] **JRV-0663** `P0` `E4` — “**Jarvis, show the status of the camera service.**”
- [ ] **JRV-0664** `P0` `E4` — “**Jarvis, read the last JARVIS core journal entries.**”
- [ ] **JRV-0665** `P0` `E4` — “**Jarvis, explain a failing service from its logs.**”
- [ ] **JRV-0666** `P0` `E4` — “**Jarvis, show whether a systemd unit is enabled.**”
- [ ] **JRV-0667** `P0` `E4` — “**Jarvis, request approval to restart jarvis-core.**”
- [ ] **JRV-0668** `P0` `E4` — “**Jarvis, request approval to restart a selected system service.**”
- [ ] **JRV-0669** `P0` `E4` — “**Jarvis, request approval before enabling a service.**”
- [ ] **JRV-0670** `P0` `E4` — “**Jarvis, request approval before disabling a service.**”
- [ ] **JRV-0671** `P0` `E4` — “**Jarvis, show which process owns a port.**”
- [ ] **JRV-0672** `P0` `E4` — “**Jarvis, show a systemd unit's effective configuration.**”
- [ ] **JRV-0673** `P0` `E4` — “**Jarvis, verify an installed service unit before modifying it.**”
- [ ] **JRV-0674** `P0` `E4` — “**Jarvis, create a rollback snapshot of an approved service config.**”
- [ ] **JRV-0675** `P0` `E4` — “**Jarvis, run a narrowly scoped privileged action through an approved broker.**”
- [ ] **JRV-0676** `P0` `E4` — “**Jarvis, deny an arbitrary `sudo su` or root shell.**”
- [ ] **JRV-0677** `P0` `E4` — “**Jarvis, require authentication for a new privileged operation.**”
- [ ] **JRV-0678** `P0` `E4` — “**Jarvis, verify the service state after an approved restart.**”
- [ ] **JRV-0679** `P0` `E4` — “**Jarvis, roll back a failing service change when safe.**”
- [ ] **JRV-0680** `P0` `E4` — “**Jarvis, export a redacted service-health report.**”

### 35. Raspberry Pi Hardware and Performance — `P1` · `E4` · 20 features
**Prerequisite capability:** `Service Health and Observability`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0681** `P1` `E4` — “**Jarvis, show Raspberry Pi model information.**”
- [ ] **JRV-0682** `P1` `E4` — “**Jarvis, show kernel and OS version.**”
- [ ] **JRV-0683** `P1` `E4` — “**Jarvis, show CPU utilization.**”
- [ ] **JRV-0684** `P1` `E4` — “**Jarvis, show memory utilization.**”
- [ ] **JRV-0685** `P1` `E4` — “**Jarvis, show CPU temperature.**”
- [ ] **JRV-0686** `P1` `E4` — “**Jarvis, show system uptime.**”
- [ ] **JRV-0687** `P1` `E4` — “**Jarvis, show available swap.**”
- [ ] **JRV-0688** `P1` `E4` — “**Jarvis, show filesystem usage.**”
- [ ] **JRV-0689** `P1` `E4` — “**Jarvis, show CPU frequency when available.**”
- [ ] **JRV-0690** `P1` `E4` — “**Jarvis, show thermal throttling flags.**”
- [ ] **JRV-0691** `P1` `E4` — “**Jarvis, show voltage or undervoltage warnings when available.**”
- [ ] **JRV-0692** `P1` `E4` — “**Jarvis, show running high-CPU processes.**”
- [ ] **JRV-0693** `P1` `E4` — “**Jarvis, show JARVIS process memory consumption.**”
- [ ] **JRV-0694** `P1` `E4` — “**Jarvis, show I/O pressure metrics when available.**”
- [ ] **JRV-0695** `P1` `E4` — “**Jarvis, show USB devices.**”
- [ ] **JRV-0696** `P1` `E4` — “**Jarvis, show attached storage devices.**”
- [ ] **JRV-0697** `P1` `E4` — “**Jarvis, show available I2C buses.**”
- [ ] **JRV-0698** `P1` `E4` — “**Jarvis, show enabled SPI interfaces.**”
- [ ] **JRV-0699** `P1` `E4` — “**Jarvis, show enabled UART interfaces.**”
- [ ] **JRV-0700** `P1` `E4` — “**Jarvis, warn when temperature crosses my approved threshold.**”

### 36. Network and Connectivity — `P1` · `E4` · 20 features
**Prerequisite capability:** `Systemd Services and Privileged Linux`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0701** `P1` `E4` — “**Jarvis, show active network interfaces.**”
- [ ] **JRV-0702** `P1` `E4` — “**Jarvis, show the current IP address.**”
- [ ] **JRV-0703** `P1` `E4` — “**Jarvis, show the current Wi-Fi SSID when permitted.**”
- [ ] **JRV-0704** `P1` `E4` — “**Jarvis, show signal strength.**”
- [ ] **JRV-0705** `P1` `E4` — “**Jarvis, show the default route.**”
- [ ] **JRV-0706** `P1` `E4` — “**Jarvis, resolve a domain name.**”
- [ ] **JRV-0707** `P1` `E4` — “**Jarvis, ping the local gateway.**”
- [ ] **JRV-0708** `P1` `E4` — “**Jarvis, ping a public endpoint on request.**”
- [ ] **JRV-0709** `P1` `E4` — “**Jarvis, show whether DNS resolution works.**”
- [ ] **JRV-0710** `P1` `E4` — “**Jarvis, show network latency to an approved target.**”
- [ ] **JRV-0711** `P1` `E4` — “**Jarvis, show whether Tailscale is connected.**”
- [ ] **JRV-0712** `P1` `E4` — “**Jarvis, show trusted Tailscale peers.**”
- [ ] **JRV-0713** `P1` `E4` — “**Jarvis, show whether SSH is listening.**”
- [ ] **JRV-0714** `P1` `E4` — “**Jarvis, show whether VNC is active.**”
- [ ] **JRV-0715** `P1` `E4` — “**Jarvis, show local ports used by JARVIS.**”
- [ ] **JRV-0716** `P1` `E4` — “**Jarvis, diagnose a disconnected network interface.**”
- [ ] **JRV-0717** `P1` `E4` — “**Jarvis, test access to the configured AI endpoint.**”
- [ ] **JRV-0718** `P1` `E4` — “**Jarvis, show active Wi-Fi and Ethernet status.**”
- [ ] **JRV-0719** `P1` `E4` — “**Jarvis, request approval before changing network settings.**”
- [ ] **JRV-0720** `P1` `E4` — “**Jarvis, recover the application after a temporary network outage.**”

### 37. Package and Software Management — `P1` · `E4` · 20 features
**Prerequisite capability:** `Systemd Services and Privileged Linux`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0721** `P1` `E4` — “**Jarvis, check whether a package is installed.**”
- [ ] **JRV-0722** `P1` `E4` — “**Jarvis, show a package version.**”
- [ ] **JRV-0723** `P1` `E4` — “**Jarvis, list outstanding package updates without applying them.**”
- [ ] **JRV-0724** `P1` `E4` — “**Jarvis, show a package's installation source.**”
- [ ] **JRV-0725** `P1` `E4` — “**Jarvis, check available disk space before installing.**”
- [ ] **JRV-0726** `P1` `E4` — “**Jarvis, show a package installation preview.**”
- [ ] **JRV-0727** `P1` `E4` — “**Jarvis, request approval to install a system package.**”
- [ ] **JRV-0728** `P1` `E4` — “**Jarvis, request approval to uninstall a package.**”
- [ ] **JRV-0729** `P1` `E4` — “**Jarvis, request approval to upgrade a package.**”
- [ ] **JRV-0730** `P1` `E4` — “**Jarvis, install a Python dependency in the approved venv after approval.**”
- [ ] **JRV-0731** `P1` `E4` — “**Jarvis, show the active Python virtual environment.**”
- [ ] **JRV-0732** `P1` `E4` — “**Jarvis, show a pip package's version.**”
- [ ] **JRV-0733** `P1` `E4` — “**Jarvis, check compatibility with ARM64.**”
- [ ] **JRV-0734** `P1` `E4` — “**Jarvis, verify a package checksum when supplied.**”
- [ ] **JRV-0735** `P1` `E4` — “**Jarvis, show whether a dependency requires a reboot.**”
- [ ] **JRV-0736** `P1` `E4` — “**Jarvis, report a package install failure.**”
- [ ] **JRV-0737** `P1` `E4` — “**Jarvis, roll back a supported dependency change.**”
- [ ] **JRV-0738** `P1` `E4` — “**Jarvis, show stale dependencies in the project.**”
- [ ] **JRV-0739** `P1` `E4` — “**Jarvis, audit declared versus imported dependencies.**”
- [ ] **JRV-0740** `P1` `E4` — “**Jarvis, generate a dependency-change report.**”

### 38. Coding and IDE Assistance — `P1` · `E7` · 20 features
**Prerequisite capability:** `Task Planning and Verification`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0741** `P1` `E7` — “**Jarvis, open my current project in VS Code.**”
- [ ] **JRV-0742** `P1` `E7` — “**Jarvis, create a Python module in the approved workspace.**”
- [ ] **JRV-0743** `P1` `E7` — “**Jarvis, write a simple tested function.**”
- [ ] **JRV-0744** `P1` `E7` — “**Jarvis, add docstrings to a selected function.**”
- [ ] **JRV-0745** `P1` `E7` — “**Jarvis, explain a selected source file.**”
- [ ] **JRV-0746** `P1` `E7` — “**Jarvis, find the definition of a function.**”
- [ ] **JRV-0747** `P1` `E7` — “**Jarvis, find references to a function.**”
- [ ] **JRV-0748** `P1` `E7` — “**Jarvis, create a small unit test.**”
- [ ] **JRV-0749** `P1` `E7` — “**Jarvis, run a focused unit test.**”
- [ ] **JRV-0750** `P1` `E7` — “**Jarvis, interpret a test failure.**”
- [ ] **JRV-0751** `P1` `E7` — “**Jarvis, suggest a minimal code patch.**”
- [ ] **JRV-0752** `P1` `E7` — “**Jarvis, preview a code patch as a diff.**”
- [ ] **JRV-0753** `P1` `E7` — “**Jarvis, apply an approved patch to a tracked file.**”
- [ ] **JRV-0754** `P1` `E7` — “**Jarvis, run a formatter on selected files.**”
- [ ] **JRV-0755** `P1` `E7` — “**Jarvis, run a linter on selected files.**”
- [ ] **JRV-0756** `P1` `E7` — “**Jarvis, run static type checks when configured.**”
- [ ] **JRV-0757** `P1` `E7` — “**Jarvis, explain an import error.**”
- [ ] **JRV-0758** `P1` `E7` — “**Jarvis, repair a known configuration error after approval.**”
- [ ] **JRV-0759** `P1` `E7` — “**Jarvis, summarize code changes in the workspace.**”
- [ ] **JRV-0760** `P1` `E7` — “**Jarvis, revert a failed change safely from a checkpoint.**”

### 39. Git and GitHub Operations — `P1` · `E7` · 20 features
**Prerequisite capability:** `Coding and IDE Assistance`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0761** `P1` `E7` — “**Jarvis, show the current Git repository.**”
- [ ] **JRV-0762** `P1` `E7` — “**Jarvis, show the current branch.**”
- [ ] **JRV-0763** `P1` `E7` — “**Jarvis, show uncommitted changes.**”
- [ ] **JRV-0764** `P1` `E7` — “**Jarvis, show the last five commits.**”
- [ ] **JRV-0765** `P1` `E7` — “**Jarvis, show the diff of a selected file.**”
- [ ] **JRV-0766** `P1` `E7` — “**Jarvis, list local branches.**”
- [ ] **JRV-0767** `P1` `E7` — “**Jarvis, create a named feature branch.**”
- [ ] **JRV-0768** `P1` `E7` — “**Jarvis, switch branches only when safe.**”
- [ ] **JRV-0769** `P1` `E7` — “**Jarvis, show a commit's changed files.**”
- [ ] **JRV-0770** `P1` `E7` — “**Jarvis, stage one explicitly named file.**”
- [ ] **JRV-0771** `P1` `E7` — “**Jarvis, unstage an explicitly named file.**”
- [ ] **JRV-0772** `P1` `E7` — “**Jarvis, create a descriptive local commit after approval.**”
- [ ] **JRV-0773** `P1` `E7` — “**Jarvis, show the configured remote URL.**”
- [ ] **JRV-0774** `P1` `E7` — “**Jarvis, fetch remote metadata without overwriting local work.**”
- [ ] **JRV-0775** `P1` `E7` — “**Jarvis, compare local and remote branches.**”
- [ ] **JRV-0776** `P1` `E7` — “**Jarvis, show open pull requests when authenticated.**”
- [ ] **JRV-0777** `P1` `E7` — “**Jarvis, inspect a pull request diff.**”
- [ ] **JRV-0778** `P1` `E7` — “**Jarvis, prepare a pull request description.**”
- [ ] **JRV-0779** `P1` `E7` — “**Jarvis, ask before pushing any commits.**”
- [ ] **JRV-0780** `P1` `E7` — “**Jarvis, refuse destructive Git cleanup without explicit approval.**”

### 40. Testing Debugging and Validation — `P1` · `E8` · 20 features
**Prerequisite capability:** `Coding and IDE Assistance`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0781** `P1` `E8` — “**Jarvis, run a focused Python test module.**”
- [ ] **JRV-0782** `P1` `E8` — “**Jarvis, run a selected frontend test.**”
- [ ] **JRV-0783** `P1` `E8` — “**Jarvis, run a reviewed Playwright test.**”
- [ ] **JRV-0784** `P1` `E8` — “**Jarvis, show failing tests only.**”
- [ ] **JRV-0785** `P1` `E8` — “**Jarvis, summarize a traceback.**”
- [ ] **JRV-0786** `P1` `E8` — “**Jarvis, save test stdout to a report.**”
- [ ] **JRV-0787** `P1` `E8` — “**Jarvis, compare two test runs.**”
- [ ] **JRV-0788** `P1` `E8` — “**Jarvis, check whether an API endpoint responds.**”
- [ ] **JRV-0789** `P1` `E8` — “**Jarvis, validate a JSON API response.**”
- [ ] **JRV-0790** `P1` `E8` — “**Jarvis, test a timeout recovery case.**”
- [ ] **JRV-0791** `P1` `E8` — “**Jarvis, test a duplicate-command prevention case.**”
- [ ] **JRV-0792** `P1` `E8` — “**Jarvis, test approval denials.**”
- [ ] **JRV-0793** `P1` `E8` — “**Jarvis, test guest authorization restrictions.**”
- [ ] **JRV-0794** `P1` `E8` — “**Jarvis, test keyboard cancellation.**”
- [ ] **JRV-0795** `P1` `E8` — “**Jarvis, test browser profile selection with test accounts.**”
- [ ] **JRV-0796** `P1` `E8` — “**Jarvis, test voice recognition using approved audio samples.**”
- [ ] **JRV-0797** `P1` `E8` — “**Jarvis, measure first-response latency.**”
- [ ] **JRV-0798** `P1` `E8` — “**Jarvis, measure task completion time.**”
- [ ] **JRV-0799** `P1` `E8` — “**Jarvis, record a live-versus-mock classification.**”
- [ ] **JRV-0800** `P1` `E8` — “**Jarvis, generate a verification report with evidence paths.**”

### 41. PDF and Document Work — `P2` · `E7` · 20 features
**Prerequisite capability:** `File and Folder Discovery`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0801** `P2` `E7` — “**Jarvis, open an approved PDF.**”
- [ ] **JRV-0802** `P2` `E7` — “**Jarvis, read a PDF page aloud.**”
- [ ] **JRV-0803** `P2` `E7` — “**Jarvis, search text inside a PDF.**”
- [ ] **JRV-0804** `P2` `E7` — “**Jarvis, summarize an approved PDF.**”
- [ ] **JRV-0805** `P2` `E7` — “**Jarvis, extract headings from a PDF.**”
- [ ] **JRV-0806** `P2` `E7` — “**Jarvis, extract tables from a PDF.**”
- [ ] **JRV-0807** `P2` `E7` — “**Jarvis, compare two PDF text versions.**”
- [ ] **JRV-0808** `P2` `E7` — “**Jarvis, rotate a PDF page in a generated copy.**”
- [ ] **JRV-0809** `P2` `E7` — “**Jarvis, merge approved PDF files.**”
- [ ] **JRV-0810** `P2` `E7` — “**Jarvis, split a PDF into page ranges.**”
- [ ] **JRV-0811** `P2` `E7` — “**Jarvis, extract images from an approved PDF.**”
- [ ] **JRV-0812** `P2` `E7` — “**Jarvis, convert a text document to PDF.**”
- [ ] **JRV-0813** `P2` `E7` — “**Jarvis, create a formatted letter as PDF.**”
- [ ] **JRV-0814** `P2` `E7` — “**Jarvis, create a study handout as PDF.**”
- [ ] **JRV-0815** `P2` `E7` — “**Jarvis, identify scanned versus text-based PDF.**”
- [ ] **JRV-0816** `P2` `E7` — “**Jarvis, run OCR on a scanned PDF with permission.**”
- [ ] **JRV-0817** `P2` `E7` — “**Jarvis, redact specified text in a new PDF with verification.**”
- [ ] **JRV-0818** `P2` `E7` — “**Jarvis, add page numbers to a generated PDF.**”
- [ ] **JRV-0819** `P2` `E7` — “**Jarvis, export a PDF summary as Markdown.**”
- [ ] **JRV-0820** `P2` `E7` — “**Jarvis, verify that the output PDF opens and renders.**”

### 42. Spreadsheet and Data Work — `P2` · `E7` · 20 features
**Prerequisite capability:** `File and Folder Discovery`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0821** `P2` `E7` — “**Jarvis, open an approved Excel workbook.**”
- [ ] **JRV-0822** `P2` `E7` — “**Jarvis, list workbook sheets.**”
- [ ] **JRV-0823** `P2` `E7` — “**Jarvis, read an approved cell range.**”
- [ ] **JRV-0824** `P2` `E7` — “**Jarvis, find a value in a sheet.**”
- [ ] **JRV-0825** `P2` `E7` — “**Jarvis, sort rows by a specified column.**”
- [ ] **JRV-0826** `P2` `E7` — “**Jarvis, filter rows by a condition.**”
- [ ] **JRV-0827** `P2` `E7` — “**Jarvis, create a formatted data table.**”
- [ ] **JRV-0828** `P2` `E7` — “**Jarvis, add a formula to a specified cell.**”
- [ ] **JRV-0829** `P2` `E7` — “**Jarvis, explain a spreadsheet formula.**”
- [ ] **JRV-0830** `P2` `E7` — “**Jarvis, calculate a column sum.**”
- [ ] **JRV-0831** `P2` `E7` — “**Jarvis, calculate a column average.**”
- [ ] **JRV-0832** `P2` `E7` — “**Jarvis, detect duplicate rows.**”
- [ ] **JRV-0833** `P2` `E7` — “**Jarvis, highlight missing values.**”
- [ ] **JRV-0834** `P2` `E7` — “**Jarvis, create a pivot-style summary.**”
- [ ] **JRV-0835** `P2` `E7` — “**Jarvis, generate a bar chart.**”
- [ ] **JRV-0836** `P2` `E7` — “**Jarvis, generate a line chart.**”
- [ ] **JRV-0837** `P2` `E7` — “**Jarvis, import a CSV file.**”
- [ ] **JRV-0838** `P2` `E7` — “**Jarvis, export a worksheet to CSV.**”
- [ ] **JRV-0839** `P2` `E7` — “**Jarvis, compare two spreadsheets for changes.**”
- [ ] **JRV-0840** `P2` `E7` — “**Jarvis, save a validated workbook copy.**”

### 43. Presentation and Slide Work — `P2` · `E7` · 20 features
**Prerequisite capability:** `File and Folder Discovery`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0841** `P2` `E7` — “**Jarvis, create a simple presentation outline.**”
- [ ] **JRV-0842** `P2` `E7` — “**Jarvis, create a title slide.**”
- [ ] **JRV-0843** `P2` `E7` — “**Jarvis, create an agenda slide.**”
- [ ] **JRV-0844** `P2` `E7` — “**Jarvis, add a bullet-list slide.**”
- [ ] **JRV-0845** `P2` `E7` — “**Jarvis, add a table slide.**”
- [ ] **JRV-0846** `P2` `E7` — “**Jarvis, add a chart slide.**”
- [ ] **JRV-0847** `P2` `E7` — “**Jarvis, add speaker notes.**”
- [ ] **JRV-0848** `P2` `E7` — “**Jarvis, apply a consistent theme.**”
- [ ] **JRV-0849** `P2` `E7` — “**Jarvis, insert an approved local image.**”
- [ ] **JRV-0850** `P2` `E7` — “**Jarvis, reorder presentation slides.**”
- [ ] **JRV-0851** `P2` `E7` — “**Jarvis, duplicate a selected slide.**”
- [ ] **JRV-0852** `P2` `E7` — “**Jarvis, delete a slide after approval.**”
- [ ] **JRV-0853** `P2` `E7` — “**Jarvis, summarize a presentation.**”
- [ ] **JRV-0854** `P2` `E7` — “**Jarvis, extract slide notes.**”
- [ ] **JRV-0855** `P2` `E7` — “**Jarvis, translate approved slide text.**”
- [ ] **JRV-0856** `P2` `E7` — “**Jarvis, generate an executive summary slide.**”
- [ ] **JRV-0857** `P2` `E7` — “**Jarvis, create a quiz slide.**”
- [ ] **JRV-0858** `P2` `E7` — “**Jarvis, export a presentation to PDF.**”
- [ ] **JRV-0859** `P2` `E7` — “**Jarvis, check for missing fonts or assets.**”
- [ ] **JRV-0860** `P2` `E7` — “**Jarvis, render and verify slide previews.**”

### 44. Email and Communication — `P2` · `E7` · 20 features
**Prerequisite capability:** `Identity and Authentication`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0861** `P2` `E7` — “**Jarvis, show the number of unread emails when connected.**”
- [ ] **JRV-0862** `P2` `E7` — “**Jarvis, search my inbox for a subject.**”
- [ ] **JRV-0863** `P2` `E7` — “**Jarvis, find an email from an approved sender.**”
- [ ] **JRV-0864** `P2` `E7` — “**Jarvis, summarize a selected email.**”
- [ ] **JRV-0865** `P2` `E7` — “**Jarvis, read a selected email aloud.**”
- [ ] **JRV-0866** `P2` `E7` — “**Jarvis, list attachments of an email.**”
- [ ] **JRV-0867** `P2` `E7` — “**Jarvis, save an approved attachment.**”
- [ ] **JRV-0868** `P2` `E7` — “**Jarvis, draft a reply without sending.**”
- [ ] **JRV-0869** `P2` `E7` — “**Jarvis, rewrite a draft more politely.**”
- [ ] **JRV-0870** `P2` `E7` — “**Jarvis, translate a draft.**”
- [ ] **JRV-0871** `P2` `E7` — “**Jarvis, find an email thread by date.**”
- [ ] **JRV-0872** `P2` `E7` — “**Jarvis, show draft messages.**”
- [ ] **JRV-0873** `P2` `E7` — “**Jarvis, add a label to a selected email after approval.**”
- [ ] **JRV-0874** `P2` `E7` — “**Jarvis, archive a selected email after approval.**”
- [ ] **JRV-0875** `P2` `E7` — “**Jarvis, mark a selected message as read.**”
- [ ] **JRV-0876** `P2` `E7` — “**Jarvis, request confirmation before sending an email.**”
- [ ] **JRV-0877** `P2` `E7` — “**Jarvis, send the exact approved draft.**”
- [ ] **JRV-0878** `P2` `E7` — “**Jarvis, check whether the send completed.**”
- [ ] **JRV-0879** `P2` `E7` — “**Jarvis, report an email connection failure.**”
- [ ] **JRV-0880** `P2` `E7` — “**Jarvis, avoid exposing email contents to an unapproved AI provider.**”

### 45. Calendar and Time Management — `P2` · `E7` · 20 features
**Prerequisite capability:** `Identity and Authentication`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0881** `P2` `E7` — “**Jarvis, show today's calendar events.**”
- [ ] **JRV-0882** `P2` `E7` — “**Jarvis, show tomorrow's calendar events.**”
- [ ] **JRV-0883** `P2` `E7` — “**Jarvis, find a meeting by title.**”
- [ ] **JRV-0884** `P2` `E7` — “**Jarvis, check free time on a given day.**”
- [ ] **JRV-0885** `P2` `E7` — “**Jarvis, create a draft event.**”
- [ ] **JRV-0886** `P2` `E7` — “**Jarvis, schedule an approved event.**”
- [ ] **JRV-0887** `P2` `E7` — “**Jarvis, set a reminder before an event.**”
- [ ] **JRV-0888** `P2` `E7` — “**Jarvis, reschedule an event after confirmation.**”
- [ ] **JRV-0889** `P2` `E7` — “**Jarvis, cancel an event after confirmation.**”
- [ ] **JRV-0890** `P2` `E7` — “**Jarvis, show recurring events.**”
- [ ] **JRV-0891** `P2` `E7` — “**Jarvis, create a recurring calendar event.**”
- [ ] **JRV-0892** `P2` `E7` — “**Jarvis, read meeting location information.**”
- [ ] **JRV-0893** `P2` `E7` — “**Jarvis, detect overlapping appointments.**”
- [ ] **JRV-0894** `P2` `E7` — “**Jarvis, prepare a daily agenda.**”
- [ ] **JRV-0895** `P2` `E7` — “**Jarvis, prepare a weekly agenda.**”
- [ ] **JRV-0896** `P2` `E7` — “**Jarvis, report an event's timezone.**”
- [ ] **JRV-0897** `P2` `E7` — “**Jarvis, convert a meeting to local time.**”
- [ ] **JRV-0898** `P2` `E7` — “**Jarvis, summarize an upcoming event.**”
- [ ] **JRV-0899** `P2` `E7` — “**Jarvis, check the event was saved.**”
- [ ] **JRV-0900** `P2` `E7` — “**Jarvis, show calendar connection status.**”

### 46. Tasks Reminders and Notes — `P1` · `E7` · 20 features
**Prerequisite capability:** `Conversation Memory`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0901** `P1` `E7` — “**Jarvis, create a to-do item.**”
- [ ] **JRV-0902** `P1` `E7` — “**Jarvis, show today's unfinished tasks.**”
- [ ] **JRV-0903** `P1` `E7` — “**Jarvis, complete a selected to-do.**”
- [ ] **JRV-0904** `P1` `E7` — “**Jarvis, reopen a completed to-do.**”
- [ ] **JRV-0905** `P1` `E7` — “**Jarvis, set a task due date.**”
- [ ] **JRV-0906** `P1` `E7` — “**Jarvis, prioritize a selected task.**”
- [ ] **JRV-0907** `P1` `E7` — “**Jarvis, add a checklist to a task.**”
- [ ] **JRV-0908** `P1` `E7` — “**Jarvis, assign a task to an approved project.**”
- [ ] **JRV-0909** `P1` `E7` — “**Jarvis, create a repeating reminder.**”
- [ ] **JRV-0910** `P1` `E7` — “**Jarvis, pause a repeating reminder.**”
- [ ] **JRV-0911** `P1` `E7` — “**Jarvis, resume a repeating reminder.**”
- [ ] **JRV-0912** `P1` `E7` — “**Jarvis, cancel a reminder.**”
- [ ] **JRV-0913** `P1` `E7` — “**Jarvis, read out my pending reminders.**”
- [ ] **JRV-0914** `P1` `E7` — “**Jarvis, create a quick note.**”
- [ ] **JRV-0915** `P1` `E7` — “**Jarvis, search saved notes.**”
- [ ] **JRV-0916** `P1` `E7` — “**Jarvis, edit a selected note.**”
- [ ] **JRV-0917** `P1` `E7` — “**Jarvis, archive an old note.**”
- [ ] **JRV-0918** `P1` `E7` — “**Jarvis, summarize a meeting note.**”
- [ ] **JRV-0919** `P1` `E7` — “**Jarvis, export tasks to Markdown.**”
- [ ] **JRV-0920** `P1` `E7` — “**Jarvis, show overdue tasks.**”

### 47. Music and System Audio — `P2` · `E7` · 20 features
**Prerequisite capability:** `Speech Synthesis and Playback`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0921** `P2` `E7` — “**Jarvis, show active audio sinks.**”
- [ ] **JRV-0922** `P2` `E7` — “**Jarvis, select the active speaker.**”
- [ ] **JRV-0923** `P2` `E7` — “**Jarvis, set system volume to a requested percentage.**”
- [ ] **JRV-0924** `P2` `E7` — “**Jarvis, mute the system speaker.**”
- [ ] **JRV-0925** `P2` `E7` — “**Jarvis, unmute the system speaker.**”
- [ ] **JRV-0926** `P2` `E7` — “**Jarvis, show the active audio source.**”
- [ ] **JRV-0927** `P2` `E7` — “**Jarvis, play an approved local audio file.**”
- [ ] **JRV-0928** `P2` `E7` — “**Jarvis, pause local audio playback.**”
- [ ] **JRV-0929** `P2` `E7` — “**Jarvis, resume local audio playback.**”
- [ ] **JRV-0930** `P2` `E7` — “**Jarvis, skip to the next local track.**”
- [ ] **JRV-0931** `P2` `E7` — “**Jarvis, restart the current local track.**”
- [ ] **JRV-0932** `P2` `E7` — “**Jarvis, show the current track title.**”
- [ ] **JRV-0933** `P2` `E7` — “**Jarvis, create a playlist from approved files.**”
- [ ] **JRV-0934** `P2` `E7` — “**Jarvis, shuffle a local playlist.**”
- [ ] **JRV-0935** `P2` `E7` — “**Jarvis, repeat a local playlist.**”
- [ ] **JRV-0936** `P2` `E7` — “**Jarvis, stop the current music player.**”
- [ ] **JRV-0937** `P2` `E7` — “**Jarvis, duck music when JARVIS speaks.**”
- [ ] **JRV-0938** `P2` `E7` — “**Jarvis, restore the previous volume after speech.**”
- [ ] **JRV-0939** `P2` `E7` — “**Jarvis, prevent audio from routing to a disconnected device.**”
- [ ] **JRV-0940** `P2` `E7` — “**Jarvis, report a media playback failure.**”

### 48. Photos Images and Videos — `P2` · `E7` · 20 features
**Prerequisite capability:** `File and Folder Discovery`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0941** `P2` `E7` — “**Jarvis, open an approved image.**”
- [ ] **JRV-0942** `P2` `E7` — “**Jarvis, show image dimensions.**”
- [ ] **JRV-0943** `P2` `E7` — “**Jarvis, rotate an image copy.**”
- [ ] **JRV-0944** `P2` `E7` — “**Jarvis, resize an image copy.**”
- [ ] **JRV-0945** `P2` `E7` — “**Jarvis, crop an image copy.**”
- [ ] **JRV-0946** `P2` `E7` — “**Jarvis, convert PNG to JPEG.**”
- [ ] **JRV-0947** `P2` `E7` — “**Jarvis, convert JPEG to PNG.**”
- [ ] **JRV-0948** `P2` `E7` — “**Jarvis, extract image metadata without location fields.**”
- [ ] **JRV-0949** `P2` `E7` — “**Jarvis, remove location metadata from a copy.**”
- [ ] **JRV-0950** `P2` `E7` — “**Jarvis, compress a large image.**”
- [ ] **JRV-0951** `P2` `E7` — “**Jarvis, make a thumbnail image.**”
- [ ] **JRV-0952** `P2` `E7` — “**Jarvis, create an image contact sheet.**”
- [ ] **JRV-0953** `P2` `E7` — “**Jarvis, open an approved MP4 file.**”
- [ ] **JRV-0954** `P2` `E7` — “**Jarvis, show video duration.**”
- [ ] **JRV-0955** `P2` `E7` — “**Jarvis, extract a video thumbnail.**”
- [ ] **JRV-0956** `P2` `E7` — “**Jarvis, trim an approved video to a time range.**”
- [ ] **JRV-0957** `P2` `E7` — “**Jarvis, combine two approved videos.**”
- [ ] **JRV-0958** `P2` `E7` — “**Jarvis, extract audio from an approved video.**”
- [ ] **JRV-0959** `P2` `E7` — “**Jarvis, add an approved subtitle file.**”
- [ ] **JRV-0960** `P2` `E7` — “**Jarvis, verify a generated media file plays.**”

### 49. Raspberry Pi Camera and Vision — `P1` · `E6` · 20 features
**Prerequisite capability:** `Security and Emergency Controls`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0961** `P1` `E6` — “**Jarvis, show whether Camera Module 3 is detected.**”
- [ ] **JRV-0962** `P1` `E6` — “**Jarvis, show the active camera capture owner.**”
- [ ] **JRV-0963** `P1` `E6` — “**Jarvis, request an authorized still photo.**”
- [ ] **JRV-0964** `P1` `E6` — “**Jarvis, show a recent authorized snapshot.**”
- [ ] **JRV-0965** `P1` `E6` — “**Jarvis, describe a photo with an available vision model.**”
- [ ] **JRV-0966** `P1` `E6` — “**Jarvis, read visible text from a camera image.**”
- [ ] **JRV-0967** `P1` `E6` — “**Jarvis, find objects in a camera frame when model available.**”
- [ ] **JRV-0968** `P1` `E6` — “**Jarvis, report low-confidence object recognition.**”
- [ ] **JRV-0969** `P1` `E6` — “**Jarvis, stop a camera preview.**”
- [ ] **JRV-0970** `P1` `E6` — “**Jarvis, start an authorized camera preview.**”
- [ ] **JRV-0971** `P1` `E6` — “**Jarvis, show available camera resolutions.**”
- [ ] **JRV-0972** `P1` `E6` — “**Jarvis, show camera frame rate.**”
- [ ] **JRV-0973** `P1` `E6` — “**Jarvis, show camera service CPU load.**”
- [ ] **JRV-0974** `P1` `E6` — “**Jarvis, use idle throttling when nobody is viewing.**”
- [ ] **JRV-0975** `P1` `E6` — “**Jarvis, restore preview performance on demand.**”
- [ ] **JRV-0976** `P1` `E6` — “**Jarvis, report a camera permission error.**”
- [ ] **JRV-0977** `P1` `E6` — “**Jarvis, check whether another process owns the camera.**”
- [ ] **JRV-0978** `P1` `E6` — “**Jarvis, avoid saving private frames unless approved.**”
- [ ] **JRV-0979** `P1` `E6` — “**Jarvis, delete temporary camera frames after use.**”
- [ ] **JRV-0980** `P1` `E6` — “**Jarvis, record a camera validation result without claiming unsupported hardware.**”

### 50. Environmental Sensors — `P2` · `E6` · 20 features
**Prerequisite capability:** `Raspberry Pi Hardware and Performance`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-0981** `P2` `E6` — “**Jarvis, list detected sensors.**”
- [ ] **JRV-0982** `P2` `E6` — “**Jarvis, show the temperature sensor reading.**”
- [ ] **JRV-0983** `P2` `E6` — “**Jarvis, show humidity when BME280 is connected.**”
- [ ] **JRV-0984** `P2` `E6` — “**Jarvis, show pressure when BME280 is connected.**”
- [ ] **JRV-0985** `P2` `E6` — “**Jarvis, show ambient light when BH1750 is connected.**”
- [ ] **JRV-0986** `P2` `E6` — “**Jarvis, show distance when VL53L0X is connected.**”
- [ ] **JRV-0987** `P2` `E6` — “**Jarvis, show ultrasonic distance when wired safely.**”
- [ ] **JRV-0988** `P2` `E6` — “**Jarvis, show PIR motion state when connected.**”
- [ ] **JRV-0989** `P2` `E6` — “**Jarvis, read an I2C bus inventory.**”
- [ ] **JRV-0990** `P2` `E6` — “**Jarvis, distinguish simulated from physical sensor data.**”
- [ ] **JRV-0991** `P2` `E6` — “**Jarvis, show when a sensor last responded.**”
- [ ] **JRV-0992** `P2` `E6` — “**Jarvis, warn when a sensor disconnects.**”
- [ ] **JRV-0993** `P2` `E6` — “**Jarvis, set a temperature alert threshold.**”
- [ ] **JRV-0994** `P2` `E6` — “**Jarvis, set a humidity alert threshold.**”
- [ ] **JRV-0995** `P2` `E6` — “**Jarvis, record a sensor reading with timestamp.**”
- [ ] **JRV-0996** `P2` `E6` — “**Jarvis, chart hourly sensor readings.**”
- [ ] **JRV-0997** `P2` `E6` — “**Jarvis, compare current and previous readings.**”
- [ ] **JRV-0998** `P2` `E6` — “**Jarvis, check an I2C address conflict.**”
- [ ] **JRV-0999** `P2` `E6` — “**Jarvis, report missing sensor wiring without inventing data.**”
- [ ] **JRV-1000** `P2` `E6` — “**Jarvis, export a redacted sensor diagnostic report.**”

### 51. Two-Wheel Robot and Motors — `P2` · `E6` · 20 features
**Prerequisite capability:** `Security and Emergency Controls`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-1001** `P2` `E6` — “**Jarvis, show whether motor drivers are connected.**”
- [ ] **JRV-1002** `P2` `E6` — “**Jarvis, show whether the robot is armed.**”
- [ ] **JRV-1003** `P2` `E6` — “**Jarvis, keep motor outputs disabled at boot.**”
- [ ] **JRV-1004** `P2` `E6` — “**Jarvis, show the configured motor speed limit.**”
- [ ] **JRV-1005** `P2` `E6` — “**Jarvis, show the physical emergency-stop state.**”
- [ ] **JRV-1006** `P2` `E6` — “**Jarvis, request explicit arming authorization.**”
- [ ] **JRV-1007** `P2` `E6` — “**Jarvis, disarm the robot.**”
- [ ] **JRV-1008** `P2` `E6` — “**Jarvis, issue an authorized low-speed forward command.**”
- [ ] **JRV-1009** `P2` `E6` — “**Jarvis, issue an authorized low-speed reverse command.**”
- [ ] **JRV-1010** `P2` `E6` — “**Jarvis, issue an authorized low-speed left turn.**”
- [ ] **JRV-1011** `P2` `E6` — “**Jarvis, issue an authorized low-speed right turn.**”
- [ ] **JRV-1012** `P2` `E6` — “**Jarvis, stop the robot immediately.**”
- [ ] **JRV-1013** `P2` `E6` — “**Jarvis, halt motion after communications timeout.**”
- [ ] **JRV-1014** `P2` `E6` — “**Jarvis, halt motion on watchdog expiry.**”
- [ ] **JRV-1015** `P2` `E6` — “**Jarvis, prevent movement when battery voltage is unsafe.**”
- [ ] **JRV-1016** `P2` `E6` — “**Jarvis, prevent movement when obstacle data is unavailable for autonomous mode.**”
- [ ] **JRV-1017** `P2` `E6` — “**Jarvis, show motor encoder readings when installed.**”
- [ ] **JRV-1018** `P2` `E6` — “**Jarvis, show measured wheel-speed estimates when available.**”
- [ ] **JRV-1019** `P2` `E6` — “**Jarvis, run a simulation-only drive sequence.**”
- [ ] **JRV-1020** `P2` `E6` — “**Jarvis, record real-motion tests only after physical inspection and approval.**”

### 52. ESP32-S3 and Serial Hardware — `P2` · `E6` · 20 features
**Prerequisite capability:** `Raspberry Pi Hardware and Performance`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-1021** `P2` `E6` — “**Jarvis, detect a connected ESP32-S3 serial device.**”
- [ ] **JRV-1022** `P2` `E6` — “**Jarvis, show the current serial port.**”
- [ ] **JRV-1023** `P2` `E6` — “**Jarvis, show the configured baud rate.**”
- [ ] **JRV-1024** `P2` `E6` — “**Jarvis, test serial handshake without motion.**”
- [ ] **JRV-1025** `P2` `E6` — “**Jarvis, show the ESP32 firmware version if reported.**”
- [ ] **JRV-1026** `P2` `E6` — “**Jarvis, validate command packet framing.**”
- [ ] **JRV-1027** `P2` `E6` — “**Jarvis, validate serial checksums.**”
- [ ] **JRV-1028** `P2` `E6` — “**Jarvis, verify acknowledgment sequence numbers.**”
- [ ] **JRV-1029** `P2` `E6` — “**Jarvis, detect an ESP32 disconnect.**”
- [ ] **JRV-1030** `P2` `E6` — “**Jarvis, reconnect serial communication safely.**”
- [ ] **JRV-1031** `P2` `E6` — “**Jarvis, stop motor outputs when serial communications fail.**”
- [ ] **JRV-1032** `P2` `E6` — “**Jarvis, show ESP32 telemetry timestamps.**”
- [ ] **JRV-1033** `P2` `E6` — “**Jarvis, show battery voltage reported by ESP32.**”
- [ ] **JRV-1034** `P2` `E6` — “**Jarvis, show encoder counts reported by ESP32.**”
- [ ] **JRV-1035** `P2` `E6` — “**Jarvis, show device heartbeat age.**”
- [ ] **JRV-1036** `P2` `E6` — “**Jarvis, enter firmware update mode only after authorization.**”
- [ ] **JRV-1037** `P2` `E6` — “**Jarvis, back up firmware configuration.**”
- [ ] **JRV-1038** `P2` `E6` — “**Jarvis, verify a firmware image checksum before update.**”
- [ ] **JRV-1039** `P2` `E6` — “**Jarvis, report an unsuccessful firmware upload.**”
- [ ] **JRV-1040** `P2` `E6` — “**Jarvis, restore safe device state after serial errors.**”

### 53. Servos and Robotic Manipulators — `P2` · `E6` · 20 features
**Prerequisite capability:** `Two-Wheel Robot and Motors`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-1041** `P2` `E6` — “**Jarvis, show connected servo-controller availability.**”
- [ ] **JRV-1042** `P2` `E6` — “**Jarvis, list configured servo channels.**”
- [ ] **JRV-1043** `P2` `E6` — “**Jarvis, show a servo's safe angle range.**”
- [ ] **JRV-1044** `P2` `E6` — “**Jarvis, show the servo home position.**”
- [ ] **JRV-1045** `P2` `E6` — “**Jarvis, request authorization before physical movement.**”
- [ ] **JRV-1046** `P2` `E6` — “**Jarvis, move a servo to a bounded angle after approval.**”
- [ ] **JRV-1047** `P2` `E6` — “**Jarvis, return a servo to its calibrated home angle.**”
- [ ] **JRV-1048** `P2` `E6` — “**Jarvis, limit servo motion speed.**”
- [ ] **JRV-1049** `P2` `E6` — “**Jarvis, prevent movement beyond calibration bounds.**”
- [ ] **JRV-1050** `P2` `E6` — “**Jarvis, show a PCA9685 I2C address.**”
- [ ] **JRV-1051** `P2` `E6` — “**Jarvis, detect an unavailable PCA9685 board.**”
- [ ] **JRV-1052** `P2` `E6` — “**Jarvis, run servo angle tests in simulation.**”
- [ ] **JRV-1053** `P2` `E6` — “**Jarvis, store an approved servo calibration.**”
- [ ] **JRV-1054** `P2` `E6` — “**Jarvis, restore a previous servo calibration.**”
- [ ] **JRV-1055** `P2` `E6` — “**Jarvis, report excess motion current if sensor installed.**”
- [ ] **JRV-1056** `P2` `E6` — “**Jarvis, stop all servo commands on emergency stop.**”
- [ ] **JRV-1057** `P2` `E6` — “**Jarvis, avoid moving servos during boot.**”
- [ ] **JRV-1058** `P2` `E6` — “**Jarvis, describe the robot arm's current known state.**”
- [ ] **JRV-1059** `P2` `E6` — “**Jarvis, identify unreachable target coordinates.**”
- [ ] **JRV-1060** `P2` `E6` — “**Jarvis, record hardware-tested servo accuracy.**”

### 54. Remote Raspberry Pi Access — `P1` · `E7` · 20 features
**Prerequisite capability:** `Network and Connectivity`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-1061** `P1` `E7` — “**Jarvis, show whether Tailscale is running.**”
- [ ] **JRV-1062** `P1` `E7` — “**Jarvis, show the Raspberry Pi's Tailscale address.**”
- [ ] **JRV-1063** `P1` `E7` — “**Jarvis, show authorized remote clients.**”
- [ ] **JRV-1064** `P1` `E7` — “**Jarvis, show whether SSH remote access is active.**”
- [ ] **JRV-1065** `P1` `E7` — “**Jarvis, show whether VNC is bound to the intended desktop session.**”
- [ ] **JRV-1066** `P1` `E7` — “**Jarvis, show whether remote dashboard access is configured.**”
- [ ] **JRV-1067** `P1` `E7` — “**Jarvis, test remote connectivity without exposing private credentials.**”
- [ ] **JRV-1068** `P1` `E7` — “**Jarvis, list recent authorized remote connections.**”
- [ ] **JRV-1069** `P1` `E7` — “**Jarvis, disconnect an unrecognized remote session after approval.**”
- [ ] **JRV-1070** `P1` `E7` — “**Jarvis, revoke a remote token after approval.**”
- [ ] **JRV-1071** `P1` `E7` — “**Jarvis, require authentication for remote commands.**”
- [ ] **JRV-1072** `P1` `E7` — “**Jarvis, prevent public exposure of the control API.**”
- [ ] **JRV-1073** `P1` `E7` — “**Jarvis, check whether a remote session is idle.**”
- [ ] **JRV-1074** `P1` `E7` — “**Jarvis, disable remote desktop access after approval.**”
- [ ] **JRV-1075** `P1` `E7` — “**Jarvis, re-enable remote desktop access after approval.**”
- [ ] **JRV-1076** `P1` `E7` — “**Jarvis, report a failed remote login without guessing credentials.**”
- [ ] **JRV-1077** `P1` `E7` — “**Jarvis, choose read-only remote monitoring mode.**”
- [ ] **JRV-1078** `P1` `E7` — “**Jarvis, stream redacted system status to an approved client.**”
- [ ] **JRV-1079** `P1` `E7` — “**Jarvis, show remote bandwidth use when available.**”
- [ ] **JRV-1080** `P1` `E7` — “**Jarvis, lock remote actions if the primary operator disconnects.**”

### 55. Ubuntu Laptop Restricted Bridge — `P3` · `E7` · 20 features
**Prerequisite capability:** `Remote Raspberry Pi Access`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-1081** `P3` `E7` — “**Jarvis, discover an explicitly paired Ubuntu laptop.**”
- [ ] **JRV-1082** `P3` `E7` — “**Jarvis, show the paired laptop connection state.**”
- [ ] **JRV-1083** `P3` `E7` — “**Jarvis, request laptop-side approval before any command.**”
- [ ] **JRV-1084** `P3` `E7` — “**Jarvis, read laptop CPU and RAM through a read-only agent.**”
- [ ] **JRV-1085** `P3` `E7` — “**Jarvis, read laptop battery percentage if available.**”
- [ ] **JRV-1086** `P3` `E7` — “**Jarvis, read laptop free disk space.**”
- [ ] **JRV-1087** `P3` `E7` — “**Jarvis, show laptop OS version.**”
- [ ] **JRV-1088** `P3` `E7` — “**Jarvis, show laptop network reachability.**”
- [ ] **JRV-1089** `P3` `E7` — “**Jarvis, open an approved application only after laptop confirmation.**”
- [ ] **JRV-1090** `P3` `E7` — “**Jarvis, send a one-time notification to the laptop.**”
- [ ] **JRV-1091** `P3` `E7` — “**Jarvis, copy a user-selected file from Pi to laptop after approval.**”
- [ ] **JRV-1092** `P3` `E7` — “**Jarvis, copy a user-selected file from laptop to Pi after approval.**”
- [ ] **JRV-1093** `P3` `E7` — “**Jarvis, prevent default browsing of laptop personal folders.**”
- [ ] **JRV-1094** `P3` `E7` — “**Jarvis, deny reading laptop credentials.**”
- [ ] **JRV-1095** `P3` `E7` — “**Jarvis, deny clipboard access without laptop approval.**”
- [ ] **JRV-1096** `P3` `E7` — “**Jarvis, revoke a laptop pairing.**”
- [ ] **JRV-1097** `P3` `E7` — “**Jarvis, enforce per-task laptop permission scopes.**”
- [ ] **JRV-1098** `P3` `E7` — “**Jarvis, show an audit trail of laptop actions.**”
- [ ] **JRV-1099** `P3` `E7` — “**Jarvis, disconnect the laptop agent immediately.**”
- [ ] **JRV-1100** `P3` `E7` — “**Jarvis, verify that laptop-side denial blocks remote execution.**”

### 56. Mobile JARVIS Client — `P2` · `E7` · 20 features
**Prerequisite capability:** `Remote Raspberry Pi Access`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-1101** `P2` `E7` — “**Jarvis, open the JARVIS mobile dashboard.**”
- [ ] **JRV-1102** `P2` `E7` — “**Jarvis, show current JARVIS status on the phone.**”
- [ ] **JRV-1103** `P2` `E7` — “**Jarvis, send a text command from the phone.**”
- [ ] **JRV-1104** `P2` `E7` — “**Jarvis, read the latest task result on the phone.**”
- [ ] **JRV-1105** `P2` `E7` — “**Jarvis, start an approved voice command from the phone.**”
- [ ] **JRV-1106** `P2` `E7` — “**Jarvis, stop a running task from the phone.**”
- [ ] **JRV-1107** `P2` `E7` — “**Jarvis, view pending approval requests on the phone.**”
- [ ] **JRV-1108** `P2` `E7` — “**Jarvis, approve one exact task from an authenticated phone session.**”
- [ ] **JRV-1109** `P2` `E7` — “**Jarvis, deny a pending task on the phone.**”
- [ ] **JRV-1110** `P2` `E7` — “**Jarvis, show real Raspberry Pi CPU temperature on the phone.**”
- [ ] **JRV-1111** `P2` `E7` — “**Jarvis, show a camera preview only with permission.**”
- [ ] **JRV-1112** `P2` `E7` — “**Jarvis, view recent notifications.**”
- [ ] **JRV-1113** `P2` `E7` — “**Jarvis, configure phone push notifications when supported.**”
- [ ] **JRV-1114** `P2` `E7` — “**Jarvis, disable phone notifications.**”
- [ ] **JRV-1115** `P2` `E7` — “**Jarvis, show scheduled tasks.**”
- [ ] **JRV-1116** `P2` `E7` — “**Jarvis, switch between phone text and voice input.**”
- [ ] **JRV-1117** `P2` `E7` — “**Jarvis, sign out a lost phone remotely.**”
- [ ] **JRV-1118** `P2` `E7` — “**Jarvis, expire an inactive mobile session.**”
- [ ] **JRV-1119** `P2` `E7` — “**Jarvis, show a helpful offline status when the Pi cannot be reached.**”
- [ ] **JRV-1120** `P2` `E7` — “**Jarvis, reconnect automatically after network restoration without repeating effects.**”

### 57. Smart Home and IoT Integrations — `P3` · `E7` · 20 features
**Prerequisite capability:** `Permissions and Approval Workflow`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-1121** `P3` `E7` — “**Jarvis, discover compatible approved smart devices.**”
- [ ] **JRV-1122** `P3` `E7` — “**Jarvis, list connected smart lights.**”
- [ ] **JRV-1123** `P3` `E7` — “**Jarvis, turn on an authorized smart light.**”
- [ ] **JRV-1124** `P3` `E7` — “**Jarvis, turn off an authorized smart light.**”
- [ ] **JRV-1125** `P3` `E7` — “**Jarvis, set an authorized light brightness level.**”
- [ ] **JRV-1126** `P3` `E7` — “**Jarvis, set an authorized light color.**”
- [ ] **JRV-1127** `P3` `E7` — “**Jarvis, show an authorized smart plug state.**”
- [ ] **JRV-1128** `P3` `E7` — “**Jarvis, turn off a low-risk approved smart plug.**”
- [ ] **JRV-1129** `P3` `E7` — “**Jarvis, request confirmation before turning on a high-power plug.**”
- [ ] **JRV-1130** `P3` `E7` — “**Jarvis, read a compatible home temperature sensor.**”
- [ ] **JRV-1131** `P3` `E7` — “**Jarvis, show a compatible smart thermostat state.**”
- [ ] **JRV-1132** `P3` `E7` — “**Jarvis, request confirmation before changing thermostat setpoint.**”
- [ ] **JRV-1133** `P3` `E7` — “**Jarvis, show whether a Home Assistant integration is connected.**”
- [ ] **JRV-1134** `P3` `E7` — “**Jarvis, run an approved named Home Assistant scene.**”
- [ ] **JRV-1135** `P3` `E7` — “**Jarvis, schedule a smart light to turn off.**”
- [ ] **JRV-1136** `P3` `E7` — “**Jarvis, report a disconnected smart home device.**”
- [ ] **JRV-1137** `P3` `E7` — “**Jarvis, avoid sending commands to unidentified devices.**”
- [ ] **JRV-1138** `P3` `E7` — “**Jarvis, block unsafe heating and appliance automation.**”
- [ ] **JRV-1139** `P3` `E7` — “**Jarvis, show a smart-home activity log.**”
- [ ] **JRV-1140** `P3` `E7` — “**Jarvis, revoke a smart-home device integration.**”

### 58. Accessibility and Assistive Control — `P2` · `E7` · 20 features
**Prerequisite capability:** `Speech Synthesis and Playback`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-1141** `P2` `E7` — “**Jarvis, increase dashboard text size.**”
- [ ] **JRV-1142** `P2` `E7` — “**Jarvis, decrease dashboard text size.**”
- [ ] **JRV-1143** `P2` `E7` — “**Jarvis, enable high-contrast theme.**”
- [ ] **JRV-1144** `P2` `E7` — “**Jarvis, enable reduced-motion mode.**”
- [ ] **JRV-1145** `P2` `E7` — “**Jarvis, turn on screen-reader-friendly labels.**”
- [ ] **JRV-1146** `P2` `E7` — “**Jarvis, navigate the dashboard using keyboard only.**”
- [ ] **JRV-1147** `P2` `E7` — “**Jarvis, read focused button labels aloud.**”
- [ ] **JRV-1148** `P2` `E7` — “**Jarvis, describe the visible screen in simple words.**”
- [ ] **JRV-1149** `P2` `E7` — “**Jarvis, repeat the last instruction slowly.**”
- [ ] **JRV-1150** `P2` `E7` — “**Jarvis, shorten spoken answers.**”
- [ ] **JRV-1151** `P2` `E7` — “**Jarvis, provide large accessible action targets.**”
- [ ] **JRV-1152** `P2` `E7` — “**Jarvis, show captions for spoken instructions.**”
- [ ] **JRV-1153** `P2` `E7` — “**Jarvis, enable a simplified control dashboard.**”
- [ ] **JRV-1154** `P2` `E7` — “**Jarvis, announce blocking error dialogs.**”
- [ ] **JRV-1155** `P2` `E7` — “**Jarvis, support focus indicators on all controls.**”
- [ ] **JRV-1156** `P2` `E7` — “**Jarvis, avoid color-only status meaning.**”
- [ ] **JRV-1157** `P2` `E7` — “**Jarvis, provide explicit labels for unavailable controls.**”
- [ ] **JRV-1158** `P2` `E7` — “**Jarvis, verify keyboard tab order.**”
- [ ] **JRV-1159** `P2` `E7` — “**Jarvis, export an accessibility diagnostic report.**”
- [ ] **JRV-1160** `P2` `E7` — “**Jarvis, reset accessibility preferences.**”

### 59. Multilingual Translation and Study — `P2` · `E7` · 20 features
**Prerequisite capability:** `Conversational Voice Experience`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-1161** `P2` `E7` — “**Jarvis, translate a sentence from English to Hindi.**”
- [ ] **JRV-1162** `P2` `E7` — “**Jarvis, translate a sentence from Hindi to English.**”
- [ ] **JRV-1163** `P2` `E7` — “**Jarvis, translate a sentence from English to Nepali.**”
- [ ] **JRV-1164** `P2` `E7` — “**Jarvis, translate a sentence from Nepali to English.**”
- [ ] **JRV-1165** `P2` `E7` — “**Jarvis, explain a technical term in simple English.**”
- [ ] **JRV-1166** `P2` `E7` — “**Jarvis, define an unfamiliar English word.**”
- [ ] **JRV-1167** `P2` `E7` — “**Jarvis, correct a short spoken English sentence.**”
- [ ] **JRV-1168** `P2` `E7` — “**Jarvis, practice an IELTS speaking question.**”
- [ ] **JRV-1169** `P2` `E7` — “**Jarvis, give feedback on a written IELTS answer.**”
- [ ] **JRV-1170** `P2` `E7` — “**Jarvis, read a paragraph slowly.**”
- [ ] **JRV-1171** `P2` `E7` — “**Jarvis, quiz me on ten saved vocabulary words.**”
- [ ] **JRV-1172** `P2` `E7` — “**Jarvis, generate flashcards from approved study notes.**”
- [ ] **JRV-1173** `P2` `E7` — “**Jarvis, create a short Python quiz.**”
- [ ] **JRV-1174** `P2` `E7` — “**Jarvis, explain an algorithm step by step.**”
- [ ] **JRV-1175** `P2` `E7` — “**Jarvis, summarize a textbook chapter from approved files.**”
- [ ] **JRV-1176** `P2` `E7` — “**Jarvis, translate a short technical document.**”
- [ ] **JRV-1177** `P2` `E7` — “**Jarvis, compare two translations and explain differences.**”
- [ ] **JRV-1178** `P2` `E7` — “**Jarvis, switch the assistant's response language.**”
- [ ] **JRV-1179** `P2` `E7` — “**Jarvis, detect when translation confidence is low.**”
- [ ] **JRV-1180** `P2` `E7` — “**Jarvis, save approved vocabulary practice progress.**”

### 60. Notifications and Monitoring Rules — `P2` · `E7` · 20 features
**Prerequisite capability:** `Tasks Reminders and Notes`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-1181** `P2` `E7` — “**Jarvis, show unread JARVIS notifications.**”
- [ ] **JRV-1182** `P2` `E7` — “**Jarvis, dismiss a selected notification.**”
- [ ] **JRV-1183** `P2` `E7` — “**Jarvis, configure a CPU temperature alert.**”
- [ ] **JRV-1184** `P2` `E7` — “**Jarvis, configure a disk-space warning.**”
- [ ] **JRV-1185** `P2` `E7` — “**Jarvis, configure a failed-service warning.**”
- [ ] **JRV-1186** `P2` `E7` — “**Jarvis, configure an internet-down alert.**”
- [ ] **JRV-1187** `P2` `E7` — “**Jarvis, configure an AI-provider-outage alert.**”
- [ ] **JRV-1188** `P2` `E7` — “**Jarvis, configure a failed-task alert.**”
- [ ] **JRV-1189** `P2` `E7` — “**Jarvis, configure a battery or UPS alert when available.**”
- [ ] **JRV-1190** `P2` `E7` — “**Jarvis, configure a sensor-disconnect alert.**”
- [ ] **JRV-1191** `P2` `E7` — “**Jarvis, set quiet hours for noncritical alerts.**”
- [ ] **JRV-1192** `P2` `E7` — “**Jarvis, send an approved desktop notification.**”
- [ ] **JRV-1193** `P2` `E7` — “**Jarvis, send an approved phone push notification.**”
- [ ] **JRV-1194** `P2` `E7` — “**Jarvis, speak a critical safety warning.**”
- [ ] **JRV-1195** `P2` `E7` — “**Jarvis, suppress repetitive duplicate alerts.**”
- [ ] **JRV-1196** `P2` `E7` — “**Jarvis, show alert history.**”
- [ ] **JRV-1197** `P2` `E7` — “**Jarvis, acknowledge an alert.**”
- [ ] **JRV-1198** `P2` `E7` — “**Jarvis, pause a noncritical monitoring rule.**”
- [ ] **JRV-1199** `P2` `E7` — “**Jarvis, resume a monitoring rule.**”
- [ ] **JRV-1200** `P2` `E7` — “**Jarvis, test a notification delivery path safely.**”

### 61. Backup and Data Recovery — `P1` · `E8` · 20 features
**Prerequisite capability:** `File Management and Organization`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-1201** `P1` `E8` — “**Jarvis, show which JARVIS directories are backed up.**”
- [ ] **JRV-1202** `P1` `E8` — “**Jarvis, create an approved configuration backup.**”
- [ ] **JRV-1203** `P1` `E8` — “**Jarvis, create a versioned database backup.**”
- [ ] **JRV-1204** `P1` `E8` — “**Jarvis, create a project source checkpoint.**”
- [ ] **JRV-1205** `P1` `E8` — “**Jarvis, verify a backup checksum.**”
- [ ] **JRV-1206** `P1` `E8` — “**Jarvis, list available backup restore points.**”
- [ ] **JRV-1207** `P1` `E8` — “**Jarvis, preview a restore operation.**”
- [ ] **JRV-1208** `P1` `E8` — “**Jarvis, restore a specific configuration backup after approval.**”
- [ ] **JRV-1209** `P1` `E8` — “**Jarvis, restore an approved memory database snapshot.**”
- [ ] **JRV-1210** `P1` `E8` — “**Jarvis, export a portable JARVIS settings bundle.**”
- [ ] **JRV-1211** `P1` `E8` — “**Jarvis, exclude secrets from public backups.**”
- [ ] **JRV-1212** `P1` `E8` — “**Jarvis, encrypt a sensitive backup with operator-managed keys.**”
- [ ] **JRV-1213** `P1` `E8` — “**Jarvis, verify a backup can be read.**”
- [ ] **JRV-1214** `P1` `E8` — “**Jarvis, schedule approved regular backups.**”
- [ ] **JRV-1215** `P1` `E8` — “**Jarvis, prune old backups only after explicit approval.**”
- [ ] **JRV-1216** `P1` `E8` — “**Jarvis, show backup storage usage.**”
- [ ] **JRV-1217** `P1` `E8` — “**Jarvis, warn when no recent backup exists.**”
- [ ] **JRV-1218** `P1` `E8` — “**Jarvis, simulate a restore without overwriting production files.**”
- [ ] **JRV-1219** `P1` `E8` — “**Jarvis, document a disaster-recovery procedure.**”
- [ ] **JRV-1220** `P1` `E8` — “**Jarvis, report the last successful backup timestamp.**”

### 62. Power Cooling and UPS — `P2` · `E6` · 20 features
**Prerequisite capability:** `Raspberry Pi Hardware and Performance`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-1221** `P2` `E6` — “**Jarvis, show current Pi thermal state.**”
- [ ] **JRV-1222** `P2` `E6` — “**Jarvis, show reported undervoltage events.**”
- [ ] **JRV-1223** `P2` `E6` — “**Jarvis, show available UPS telemetry if connected.**”
- [ ] **JRV-1224** `P2` `E6` — “**Jarvis, show battery percentage from a compatible UPS.**”
- [ ] **JRV-1225** `P2` `E6` — “**Jarvis, warn of low UPS battery.**”
- [ ] **JRV-1226** `P2` `E6` — “**Jarvis, reduce background AI workload when overheated.**”
- [ ] **JRV-1227** `P2` `E6` — “**Jarvis, pause noncritical jobs when thermal throttling occurs.**”
- [ ] **JRV-1228** `P2` `E6` — “**Jarvis, show a power-mode profile.**”
- [ ] **JRV-1229** `P2` `E6` — “**Jarvis, switch to an approved low-power mode.**”
- [ ] **JRV-1230** `P2` `E6` — “**Jarvis, restore a normal performance profile.**”
- [ ] **JRV-1231** `P2` `E6` — “**Jarvis, show the current cooling fan state when detectable.**”
- [ ] **JRV-1232** `P2` `E6` — “**Jarvis, show fan speed if supported.**”
- [ ] **JRV-1233** `P2` `E6` — “**Jarvis, test a cooling fan with authorized hardware interface.**”
- [ ] **JRV-1234** `P2` `E6` — “**Jarvis, measure idle CPU utilization.**”
- [ ] **JRV-1235** `P2` `E6` — “**Jarvis, measure idle memory utilization.**”
- [ ] **JRV-1236** `P2` `E6` — “**Jarvis, estimate remaining runtime only from real UPS telemetry.**”
- [ ] **JRV-1237** `P2` `E6` — “**Jarvis, prepare a safe shutdown on critical UPS event.**”
- [ ] **JRV-1238** `P2` `E6` — “**Jarvis, request confirmation before ordinary poweroff.**”
- [ ] **JRV-1239** `P2` `E6` — “**Jarvis, request confirmation before reboot.**”
- [ ] **JRV-1240** `P2` `E6` — “**Jarvis, verify that unsaved tasks are checkpointed before shutdown.**”

### 63. Reusable Workflow Recipes — `P2` · `E7` · 20 features
**Prerequisite capability:** `Task Planning and Verification`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-1241** `P2` `E7` — “**Jarvis, list approved workflow recipes.**”
- [ ] **JRV-1242** `P2` `E7` — “**Jarvis, create a workflow from my spoken steps.**”
- [ ] **JRV-1243** `P2` `E7` — “**Jarvis, save a named workflow template.**”
- [ ] **JRV-1244** `P2` `E7` — “**Jarvis, show the steps of a saved workflow.**”
- [ ] **JRV-1245** `P2` `E7` — “**Jarvis, run a safe saved workflow.**”
- [ ] **JRV-1246** `P2` `E7` — “**Jarvis, pause a running workflow.**”
- [ ] **JRV-1247** `P2` `E7` — “**Jarvis, resume a paused workflow.**”
- [ ] **JRV-1248** `P2` `E7` — “**Jarvis, cancel a running workflow.**”
- [ ] **JRV-1249** `P2` `E7` — “**Jarvis, edit one step in a workflow.**”
- [ ] **JRV-1250** `P2` `E7` — “**Jarvis, reorder workflow steps.**”
- [ ] **JRV-1251** `P2` `E7` — “**Jarvis, add a conditional branch to a workflow.**”
- [ ] **JRV-1252** `P2` `E7` — “**Jarvis, add an error-handling branch.**”
- [ ] **JRV-1253** `P2` `E7` — “**Jarvis, set a workflow timeout.**”
- [ ] **JRV-1254** `P2` `E7` — “**Jarvis, add an approval step before external actions.**”
- [ ] **JRV-1255** `P2` `E7` — “**Jarvis, schedule an approved workflow.**”
- [ ] **JRV-1256** `P2` `E7` — “**Jarvis, clone an existing workflow.**”
- [ ] **JRV-1257** `P2` `E7` — “**Jarvis, export a workflow as a JSON specification.**”
- [ ] **JRV-1258** `P2` `E7` — “**Jarvis, import a validated workflow specification.**”
- [ ] **JRV-1259** `P2` `E7` — “**Jarvis, show a workflow's previous runs.**”
- [ ] **JRV-1260** `P2` `E7` — “**Jarvis, disable an outdated workflow.**”

### 64. Dashboard and Avatar Interaction — `P2` · `E8` · 20 features
**Prerequisite capability:** `Conversation and Chat`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-1261** `P2` `E8` — “**Jarvis, show the main JARVIS dashboard.**”
- [ ] **JRV-1262** `P2` `E8` — “**Jarvis, switch to the chat panel.**”
- [ ] **JRV-1263** `P2` `E8` — “**Jarvis, switch to the Computer Use panel.**”
- [ ] **JRV-1264** `P2` `E8` — “**Jarvis, switch to the voice diagnostics panel.**”
- [ ] **JRV-1265** `P2` `E8` — “**Jarvis, switch to the task queue panel.**”
- [ ] **JRV-1266** `P2` `E8` — “**Jarvis, switch to the robotics panel.**”
- [ ] **JRV-1267** `P2` `E8` — “**Jarvis, show the provider-health panel.**”
- [ ] **JRV-1268** `P2` `E8` — “**Jarvis, show the app catalog.**”
- [ ] **JRV-1269** `P2` `E8` — “**Jarvis, show current authenticated identity.**”
- [ ] **JRV-1270** `P2` `E8` — “**Jarvis, toggle dark and light themes.**”
- [ ] **JRV-1271** `P2` `E8` — “**Jarvis, show a compact status overview.**”
- [ ] **JRV-1272** `P2` `E8` — “**Jarvis, display an honest unavailable-state label.**”
- [ ] **JRV-1273** `P2` `E8` — “**Jarvis, show a pending approval modal.**”
- [ ] **JRV-1274** `P2` `E8` — “**Jarvis, show an emergency-stop control.**”
- [ ] **JRV-1275** `P2` `E8` — “**Jarvis, display live task progress.**”
- [ ] **JRV-1276** `P2` `E8` — “**Jarvis, show chat message streaming.**”
- [ ] **JRV-1277** `P2` `E8` — “**Jarvis, select a supported avatar style.**”
- [ ] **JRV-1278** `P2` `E8` — “**Jarvis, show an audio-reactive speaking animation.**”
- [ ] **JRV-1279** `P2` `E8` — “**Jarvis, disable avatar animation to save CPU.**”
- [ ] **JRV-1280** `P2` `E8` — “**Jarvis, export a dashboard usability test report.**”

### 65. External Plugins and Connected Services — `P3` · `E7` · 20 features
**Prerequisite capability:** `Identity and Authentication`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-1281** `P3` `E7` — “**Jarvis, list configured connector integrations.**”
- [ ] **JRV-1282** `P3` `E7` — “**Jarvis, show connector authentication status.**”
- [ ] **JRV-1283** `P3` `E7` — “**Jarvis, connect an approved Gmail account using supported authentication.**”
- [ ] **JRV-1284** `P3` `E7` — “**Jarvis, connect an approved calendar account.**”
- [ ] **JRV-1285** `P3` `E7` — “**Jarvis, connect an approved cloud drive account.**”
- [ ] **JRV-1286** `P3` `E7` — “**Jarvis, disconnect an external service.**”
- [ ] **JRV-1287** `P3` `E7` — “**Jarvis, list capabilities of a connected service.**”
- [ ] **JRV-1288** `P3` `E7` — “**Jarvis, show the scope of a service authorization.**”
- [ ] **JRV-1289** `P3` `E7` — “**Jarvis, revoke a connector token via its supported method.**”
- [ ] **JRV-1290** `P3` `E7` — “**Jarvis, restrict a connector to read-only mode if supported.**”
- [ ] **JRV-1291** `P3` `E7` — “**Jarvis, route a calendar query to a calendar connector.**”
- [ ] **JRV-1292** `P3` `E7` — “**Jarvis, route an email search to an email connector.**”
- [ ] **JRV-1293** `P3` `E7` — “**Jarvis, route a document search to a drive connector.**”
- [ ] **JRV-1294** `P3` `E7` — “**Jarvis, block a tool when its connector is disconnected.**”
- [ ] **JRV-1295** `P3` `E7` — “**Jarvis, ask approval before modifying external records.**”
- [ ] **JRV-1296** `P3` `E7` — “**Jarvis, show an external service rate-limit error.**”
- [ ] **JRV-1297** `P3` `E7` — “**Jarvis, avoid copying secret tokens into model prompts.**”
- [ ] **JRV-1298** `P3` `E7` — “**Jarvis, renew authorization through official sign-in.**”
- [ ] **JRV-1299** `P3` `E7` — “**Jarvis, log a redacted connector action summary.**”
- [ ] **JRV-1300** `P3` `E7` — “**Jarvis, export a connector capability matrix.**”

### 66. Autonomous Development and Cross-Agent Handoff — `P1` · `E8` · 20 features
**Prerequisite capability:** `Testing Debugging and Validation`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-1301** `P1` `E8` — “**Jarvis, read the root PLAN.md before starting work.**”
- [ ] **JRV-1302** `P1` `E8` — “**Jarvis, read AGENTS.md and existing UI phase gates.**”
- [ ] **JRV-1303** `P1` `E8` — “**Jarvis, inspect Git status before modifying files.**”
- [ ] **JRV-1304** `P1` `E8` — “**Jarvis, find the first eligible unfinished feature.**”
- [ ] **JRV-1305** `P1` `E8` — “**Jarvis, skip features marked verified with evidence.**”
- [ ] **JRV-1306** `P1` `E8` — “**Jarvis, check dependencies before selecting a task.**”
- [ ] **JRV-1307** `P1` `E8` — “**Jarvis, acquire an exclusive task claim for one coding agent.**”
- [ ] **JRV-1308** `P1` `E8` — “**Jarvis, create a dedicated branch or worktree when authorized.**”
- [ ] **JRV-1309** `P1` `E8` — “**Jarvis, record baseline test results.**”
- [ ] **JRV-1310** `P1` `E8` — “**Jarvis, implement the smallest coherent change.**”
- [ ] **JRV-1311** `P1` `E8` — “**Jarvis, run focused tests for the change.**”
- [ ] **JRV-1312** `P1` `E8` — “**Jarvis, record real-versus-mock test evidence.**”
- [ ] **JRV-1313** `P1` `E8` — “**Jarvis, update the plan item status and evidence path.**”
- [ ] **JRV-1314** `P1` `E8` — “**Jarvis, write a handoff record before context exhaustion.**”
- [ ] **JRV-1315** `P1` `E8` — “**Jarvis, resume from the recorded handoff after model switch.**”
- [ ] **JRV-1316** `P1` `E8` — “**Jarvis, avoid replaying already committed external actions.**”
- [ ] **JRV-1317** `P1` `E8` — “**Jarvis, document an explicit blocker rather than pretending progress.**”
- [ ] **JRV-1318** `P1` `E8` — “**Jarvis, request approval before pushing or deployment.**”
- [ ] **JRV-1319** `P1` `E8` — “**Jarvis, reconcile conflicting edits across coding agents.**”
- [ ] **JRV-1320** `P1` `E8` — “**Jarvis, end a checkpoint with 'Resume: continue per PLAN.md.'.**”

### 67. System Privacy and Data Governance — `P1` · `E0` · 20 features
**Prerequisite capability:** `Security and Emergency Controls`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-1321** `P1` `E0` — “**Jarvis, show which directories the assistant can read.**”
- [ ] **JRV-1322** `P1` `E0` — “**Jarvis, show which directories the assistant can write.**”
- [ ] **JRV-1323** `P1` `E0` — “**Jarvis, revoke access to a selected workspace.**”
- [ ] **JRV-1324** `P1` `E0` — “**Jarvis, enable a private conversation mode.**”
- [ ] **JRV-1325** `P1` `E0` — “**Jarvis, show data-retention settings.**”
- [ ] **JRV-1326** `P1` `E0` — “**Jarvis, set an approved transcript retention limit.**”
- [ ] **JRV-1327** `P1` `E0` — “**Jarvis, delete one approved stored transcript.**”
- [ ] **JRV-1328** `P1` `E0` — “**Jarvis, purge temporary screenshots after a task.**”
- [ ] **JRV-1329** `P1` `E0` — “**Jarvis, redact access tokens from diagnostics.**”
- [ ] **JRV-1330** `P1` `E0` — “**Jarvis, prevent logging of password inputs.**”
- [ ] **JRV-1331** `P1` `E0` — “**Jarvis, prevent cloud transmission of protected files by default.**”
- [ ] **JRV-1332** `P1` `E0` — “**Jarvis, show outbound requests by integration.**”
- [ ] **JRV-1333** `P1` `E0` — “**Jarvis, disable one cloud AI provider for private tasks.**”
- [ ] **JRV-1334** `P1` `E0` — “**Jarvis, require explicit screen-sharing consent.**”
- [ ] **JRV-1335** `P1` `E0` — “**Jarvis, stop screen sharing.**”
- [ ] **JRV-1336** `P1` `E0` — “**Jarvis, show current camera access status.**”
- [ ] **JRV-1337** `P1` `E0` — “**Jarvis, show current microphone access status.**”
- [ ] **JRV-1338** `P1` `E0` — “**Jarvis, revoke a device session.**”
- [ ] **JRV-1339** `P1` `E0` — “**Jarvis, export an audit trail without secrets.**”
- [ ] **JRV-1340** `P1` `E0` — “**Jarvis, verify a privacy rule with an automated denial test.**”

### 68. Disaster Recovery and Safe Mode — `P1` · `E8` · 20 features
**Prerequisite capability:** `Backup and Data Recovery`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-1341** `P1` `E8` — “**Jarvis, start JARVIS in diagnostics-only mode.**”
- [ ] **JRV-1342** `P1` `E8` — “**Jarvis, start JARVIS without robotics hardware.**”
- [ ] **JRV-1343** `P1` `E8` — “**Jarvis, start JARVIS without external AI services.**”
- [ ] **JRV-1344** `P1` `E8` — “**Jarvis, show a minimal offline health page.**”
- [ ] **JRV-1345** `P1` `E8` — “**Jarvis, detect a failed startup dependency.**”
- [ ] **JRV-1346** `P1` `E8` — “**Jarvis, show the last known-good software revision.**”
- [ ] **JRV-1347** `P1` `E8` — “**Jarvis, roll back a failed local change after approval.**”
- [ ] **JRV-1348** `P1` `E8` — “**Jarvis, restore the previous JARVIS service unit after deployment failure.**”
- [ ] **JRV-1349** `P1` `E8` — “**Jarvis, disable a crashing optional integration.**”
- [ ] **JRV-1350** `P1` `E8` — “**Jarvis, keep the command API unavailable until authentication is ready.**”
- [ ] **JRV-1351** `P1` `E8` — “**Jarvis, prevent runaway restart loops.**”
- [ ] **JRV-1352** `P1` `E8` — “**Jarvis, verify a failed model does not block basic controls.**”
- [ ] **JRV-1353** `P1` `E8` — “**Jarvis, stop queued actions during a service crash.**”
- [ ] **JRV-1354** `P1` `E8` — “**Jarvis, resume only idempotent jobs after restart.**”
- [ ] **JRV-1355** `P1` `E8` — “**Jarvis, require fresh confirmation for interrupted external actions.**”
- [ ] **JRV-1356** `P1` `E8` — “**Jarvis, repair a corrupted generated cache after validation.**”
- [ ] **JRV-1357** `P1` `E8` — “**Jarvis, recover from an unavailable browser profile.**”
- [ ] **JRV-1358** `P1` `E8` — “**Jarvis, recover after audio device reconnect.**”
- [ ] **JRV-1359** `P1` `E8` — “**Jarvis, generate an incident timeline from local logs.**”
- [ ] **JRV-1360** `P1` `E8` — “**Jarvis, export a safe recovery checklist.**”

### 69. Developer API and Custom Skill Extensions — `P3` · `E7` · 20 features
**Prerequisite capability:** `Tool Registry and Routing`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-1361** `P3` `E7` — “**Jarvis, list documented local API endpoints.**”
- [ ] **JRV-1362** `P3` `E7` — “**Jarvis, request the API schema.**”
- [ ] **JRV-1363** `P3` `E7` — “**Jarvis, call a read-only local API endpoint.**”
- [ ] **JRV-1364** `P3` `E7` — “**Jarvis, validate incoming tool JSON against a schema.**”
- [ ] **JRV-1365** `P3` `E7` — “**Jarvis, reject unknown API parameters.**”
- [ ] **JRV-1366** `P3` `E7` — “**Jarvis, register a trusted local skill manifest.**”
- [ ] **JRV-1367** `P3` `E7` — “**Jarvis, show the permissions required by a custom skill.**”
- [ ] **JRV-1368** `P3` `E7` — “**Jarvis, disable a custom skill.**”
- [ ] **JRV-1369** `P3` `E7` — “**Jarvis, enable an approved custom skill.**”
- [ ] **JRV-1370** `P3` `E7` — “**Jarvis, run a skill in a constrained environment.**”
- [ ] **JRV-1371** `P3` `E7` — “**Jarvis, set a time limit on a custom skill.**”
- [ ] **JRV-1372** `P3` `E7` — “**Jarvis, set an output size limit on a skill.**”
- [ ] **JRV-1373** `P3` `E7` — “**Jarvis, validate a custom skill signature or trusted origin.**”
- [ ] **JRV-1374** `P3` `E7` — “**Jarvis, reject untrusted executable plugin archives.**”
- [ ] **JRV-1375** `P3` `E7` — “**Jarvis, test a new skill against fixture inputs.**”
- [ ] **JRV-1376** `P3` `E7` — “**Jarvis, generate a typed API client from the schema.**”
- [ ] **JRV-1377** `P3` `E7` — “**Jarvis, show per-tool usage statistics.**”
- [ ] **JRV-1378** `P3` `E7` — “**Jarvis, version a custom skill manifest.**”
- [ ] **JRV-1379** `P3` `E7` — “**Jarvis, deprecate a skill without breaking existing calls.**”
- [ ] **JRV-1380** `P3` `E7` — “**Jarvis, export an extension compatibility report.**”

### 70. Personal Finance and Record Assistance — `P3` · `E7` · 20 features
**Prerequisite capability:** `System Privacy and Data Governance`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-1381** `P3` `E7` — “**Jarvis, calculate a budget from numbers I provide.**”
- [ ] **JRV-1382** `P3` `E7` — “**Jarvis, summarize an approved expense CSV.**”
- [ ] **JRV-1383** `P3` `E7` — “**Jarvis, categorize expenses into editable groups.**”
- [ ] **JRV-1384** `P3` `E7` — “**Jarvis, show monthly expense totals.**”
- [ ] **JRV-1385** `P3` `E7` — “**Jarvis, show yearly expense totals.**”
- [ ] **JRV-1386** `P3` `E7` — “**Jarvis, identify duplicate expenses.**”
- [ ] **JRV-1387** `P3` `E7` — “**Jarvis, calculate a savings target.**”
- [ ] **JRV-1388** `P3` `E7` — “**Jarvis, calculate a simple-interest amount.**”
- [ ] **JRV-1389** `P3` `E7` — “**Jarvis, calculate a compound-interest amount.**”
- [ ] **JRV-1390** `P3` `E7` — “**Jarvis, convert an amount using a supplied exchange rate.**”
- [ ] **JRV-1391** `P3` `E7` — “**Jarvis, estimate an invoice total with specified taxes.**”
- [ ] **JRV-1392** `P3` `E7` — “**Jarvis, create a simple invoice draft.**”
- [ ] **JRV-1393** `P3` `E7` — “**Jarvis, search approved receipts by date.**”
- [ ] **JRV-1394** `P3` `E7` — “**Jarvis, extract totals from a receipt image after permission.**”
- [ ] **JRV-1395** `P3` `E7` — “**Jarvis, build a household expense chart.**”
- [ ] **JRV-1396** `P3` `E7` — “**Jarvis, export an expense report as CSV.**”
- [ ] **JRV-1397** `P3` `E7` — “**Jarvis, flag missing transaction descriptions.**”
- [ ] **JRV-1398** `P3` `E7` — “**Jarvis, compare two budget scenarios.**”
- [ ] **JRV-1399** `P3` `E7` — “**Jarvis, request explicit approval before any payment or transfer.**”
- [ ] **JRV-1400** `P3` `E7` — “**Jarvis, never initiate investment trades without separately authorized controls.**”

### 71. Completion and Release Management — `P1` · `E8` · 20 features
**Prerequisite capability:** `Autonomous Development and Cross-Agent Handoff`. **Domain gate:** prove the exact requested observable action; use a live service/device and genuine session where relevant, test denials and failures, keep evidence per ID.
- [ ] **JRV-1401** `P1` `E8` — “**Jarvis, show count of unchecked feature IDs.**”
- [ ] **JRV-1402** `P1` `E8` — “**Jarvis, show count of verified feature IDs.**”
- [ ] **JRV-1403** `P1` `E8` — “**Jarvis, show count of blocked feature IDs.**”
- [ ] **JRV-1404** `P1` `E8` — “**Jarvis, show the next eligible high-priority feature.**”
- [ ] **JRV-1405** `P1` `E8` — “**Jarvis, show which dependencies block a feature.**”
- [ ] **JRV-1406** `P1` `E8` — “**Jarvis, show all features lacking live validation.**”
- [ ] **JRV-1407** `P1` `E8` — “**Jarvis, show feature evidence paths.**”
- [ ] **JRV-1408** `P1` `E8` — “**Jarvis, show the current Git commit and branch.**”
- [ ] **JRV-1409** `P1` `E8` — “**Jarvis, run a release-gate checklist.**”
- [ ] **JRV-1410** `P1` `E8` — “**Jarvis, verify dashboard actions against the backend.**”
- [ ] **JRV-1411** `P1` `E8` — “**Jarvis, verify browser account switching end to end.**”
- [ ] **JRV-1412** `P1` `E8` — “**Jarvis, verify administrative approval enforcement.**”
- [ ] **JRV-1413** `P1` `E8` — “**Jarvis, verify cancellation releases input devices.**”
- [ ] **JRV-1414** `P1` `E8` — “**Jarvis, verify services recover after restart.**”
- [ ] **JRV-1415** `P1` `E8` — “**Jarvis, verify the Pi does not overheat under workload.**”
- [ ] **JRV-1416** `P1` `E8` — “**Jarvis, verify private data is not logged.**”
- [ ] **JRV-1417** `P1` `E8` — “**Jarvis, generate a feature acceptance matrix.**”
- [ ] **JRV-1418** `P1` `E8` — “**Jarvis, publish release notes only after approval.**”
- [ ] **JRV-1419** `P1` `E8` — “**Jarvis, maintain a post-release bug backlog.**”
- [ ] **JRV-1420** `P1` `E8` — “**Jarvis, start a new approved improvement cycle without altering verified history.**”

## Execution and verification ledger (start here when modifying source)

| Date UTC | Agent | Feature ID(s) | Baseline → revision | Real test and result | Status | Evidence path | Next / blocker |
|---|---|---|---|---|---|---|---|
| 2026-11-22 | Plan author | JRV-0001–JRV-1420 | Initial feature proposal only | No live Pi tests were executed to certify these new items | unverified | None | Audit first eligible P0 feature and existing feature coverage |

**Required update order for each completed item:** (1) create an evidence record, (2) mark checkbox and append verification comment, (3) update this ledger or linked feature status, (4) update handoff, (5) commit per repository rules and only push with authorization. Do not mark `verified` before proof.

### Feature execution evidence template

```yaml
feature_id: JRV-0001
status: implemented_pending_verification  # unverified|in_progress|blocked|implemented_pending_verification|verified_offline|verified_live
owner: <coding-agent>
source_revision: <git-sha>
worktree_branch: <branch>
paths_changed: []
interface: voice_and_chat
manual_or_hardware_approval: not_required
mock_or_live: offline  # mocked|offline|live_raspberry_pi
intent: "Jarvis, ..."
actual_result: "<real observed result; no fabricated success>"
commands_run: []
results: []
evidence_paths: []
remaining_blockers: []
next_feature: JRV-0002
```

### Recommended minimal vertical acceptance workflows

1. **Visible Chrome:** “Jarvis, open YouTube in Chrome.” → actual Chrome window and YouTube page exist on the authorized desktop.
2. **Account switching:** “Jarvis, switch to my second signed-in YouTube account.” → selects only authorized existing session, handles ambiguity/2FA, verifies account label.
3. **Desktop control:** “Jarvis, open a text editor, type Hello, save it in my project test folder.” → actual file and editor state verified; mouse/keyboard release works.
4. **Privilege broker:** “Jarvis, diagnose Bluetooth and propose a restart.” → real service status, exact-action approval, approved action, verified post-state; no root shell.
5. **Natural spoken follow-up:** “Hey Jarvis ... open Chrome ... now search Raspberry Pi tutorial ... play the first result.” → real acoustic capture and real browser action, narrated output.
6. **Parallel tasks:** “Jarvis, monitor CPU while music plays and a safe code test runs.” → independent resources parallel; shared resources serialized.
7. **Hardware safety:** “Jarvis, show robot status.” → live status or explicit not-connected/simulated; never moves motors without authorization.
8. **Cross-agent resume:** one agent marks JRV-XXXX with real evidence, exits at a checkpoint; another agent reads plan, skips verified item and resumes the next unblocked ID without overwriting user changes.

## Final release criteria and new backlog rule

The checkbox inventory is **a roadmap**, not a promise of universal action support. “Final” requires an evidence-backed count of accepted features, clear listing of intentionally unavailable/unsupported integrations, safe authorization and hardware gates, production regressions, and operator-approved deployment. A task may be blocked because its physical component or cloud account is not present; do not assert 100% live hardware coverage while it is absent.

After all feasible approved features meet acceptance, continue normal operation: support user voice/chat requests, fix defects, improve efficiency, refresh compatibility, and append newly requested features as `JRV-1421` onward. Never renumber or erase the historical record.

**Canonical handoff phrase:** `Resume: continue per PLAN.md.`
