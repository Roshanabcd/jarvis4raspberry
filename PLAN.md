# JARVIS canonical execution plan — reconciled 22 November 2026

## Authority, order and current resume point

Root `PLAN.md` is the single editable capability ledger. `JARVIS_PLAN_FEATURES.json` is its machine-readable index; `NEXT_AGENT_PROMPT.md` is the resume prompt. The three `2` files are synchronized handoff copies, not separate instruction sets. Update canonical files first, then sync the copies. AGENTS.md and the existing UI phase gates remain authoritative; this merge does not authorize new security, voice, database, privileged, paid or hardware actions.

Read in order: AGENTS.md → this section → docs/jarvis-ui/PLAN.md → docs/jarvis-execution/HANDOFF.md → applicable feature and code/tests. Preserve the current dirty working tree. Read the audit/roadmap before choosing scope. Do not restart completed audits.

**Current continuation:** finish the scoped browser/account reliability work. Read-only JRV-0528/0539 managed-session observation now has offline evidence. Next is JRV-0527 (session-bound menu observation/opening), then JRV-0529/0530 selection and active-identity verification; keep JRV-0539 open until its live ambiguity contract is met. JRV-1313–JRV-1315 are continuity prerequisites; the plan checker is coding-agent tooling, not yet a voice-callable JARVIS capability. Never auto-select the numerically first item if a checkpoint already owns a dependency slice. After this slice, select P0 → P1 → P2 → P3 by verified prerequisites and applicable approvals. Blocked UI gates stay blocked; recorded scoped exceptions do not complete them.

**Preserved progress:** legacy J001–J003 have offline account-path evidence (37 focused checks at the latest checkpoint); J007 has partial cancellation coverage; J171 is the completed offline roadmap creation item. These do NOT complete the broader JRV/JF capabilities. See the immutable prior ledger at `docs/jarvis-execution/imports/2026-11-22/legacy-PLAN.md` and current `docs/jarvis-execution/FEATURE_STATUS.md`. Never rebuild those fixes without inspecting current code/evidence.

**Namespaces:** 1,420 JRV action contracts are the primary backlog. 1,020 JF entries from the Documents copy are supplemental acceptance contracts below, not 1,020 proven distinct new capabilities. The 180 legacy J IDs and statuses remain in the archived ledger and JSON `legacy_items`. IDs are never renumbered or automatically equated. Overlapping contracts share implementation but need their own scoped evidence before completion. Total row counts are not implementation counts.

**Source reconciliation:** uploaded PLAN2/JSON2/PROMPT2 are preserved under `docs/jarvis-execution/imports/2026-11-22/`. The Documents plan describes a different historical main-branch revision; those deployment claims are not adopted as facts about this dirty feature/jarvis-ui checkout. The declared Pi 5/8 GB configuration is a target to verify, not a fresh hardware observation. The Documents source remains unchanged; the canonical merged plan is here.

**Status updates:** record evidence first; update the checkbox and metadata; run `venv/bin/python scripts/plan_tracker.py --sync`; run `--validate`; update HANDOFF and related UI/issue scope. Checkboxes only pass for their full acceptance contract. An unchecked verified_offline annotation may record partial fixture evidence without declaring a live feature complete. Run `--summary` or `--next 10` for navigation only: suggestions never grant approval or prove dependency readiness. Preserve source revision and evidence, and never overwrite historical captures.

# PLAN.md — JARVIS OS Long-Term Master Build and Agent Continuation Plan

> **Source-of-truth enhancement backlog** · Version `1.0.0` · Created `2026-11-22` · **1,420 uniquely numbered feature actions** · **71 capability domains**
>
> **Repository:** `https://github.com/Roshanabcd/jarvis4raspberry` · **Target deployment (verify on device):** Raspberry Pi 5, 8 GB RAM, Linux ARM64 · **Primary interface:** voice and text chat
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
- Existing terminal paths require caller-by-caller review; the inspected engine includes regex-gated bash execution, which is not a sufficient allowlist; do not solve privileged commands by running the entire assistant as root. Use a narrow privileged-action broker with exact argument and action approval.
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
- [ ] **JRV-0528** `P0` `E2` — “**Jarvis, list account labels shown in the YouTube switcher.**” <!-- status: implemented_pending_verification; evidence: docs/jarvis-execution/evidence/2026-11-22-account-observation/verification.json; next: live authorized managed-session acceptance; blocker: current site markup unverified -->
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
- [ ] **JRV-0539** `P0` `E2` — “**Jarvis, ask which account when labels are ambiguous.**” <!-- status: in_progress; evidence: docs/jarvis-execution/evidence/2026-11-22-account-observation/verification.json; next: session-bound menu and candidate selection; blocker: managed observation only, no native identity verification -->
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
- [ ] **JRV-1313** `P1` `E8` — “**Jarvis, update the plan item status and evidence path.**” <!-- status: implemented_pending_verification; evidence: docs/jarvis-execution/evidence/2026-11-22-plan-merge/verification.json; next: approved JARVIS capability integration; blocker: CLI tracker is not voice integration -->
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


# Supplemental JF acceptance contracts

Source: Documents plan snapshot. These share implementations with primary items; do not double-count work. The authority/resume section at the top overrides historical source ordering.

## Capability dependency registry

- **CAP-CHAT** — Conversation and context: Read the active conversation session; never present an unverified memory as fact.
- **CAP-VOICE** — Voice input and speech output: Use the existing single microphone owner and backend STT/TTS; respect mute and privacy state.
- **CAP-WAKE** — Wake word and listening modes: Listening is visibly indicated, opt-in, locally controlled and stoppable; no covert capture.
- **CAP-IDENTITY** — User identity and profiles: Resolve identity server-side; never infer admin status from UI state or a spoken claim.
- **CAP-AUTHZ** — Permissions and approvals: Apply least privilege; obtain explicit, scoped approval for privileged or consequential operations.
- **CAP-AUDIT** — Audit and action history: Record action metadata and outcome without secrets, raw credentials or unnecessary transcript content.
- **CAP-SYSTEM** — Raspberry Pi system status: Read allowlisted telemetry only; unsupported readings are Unavailable, not guessed.
- **CAP-APPS** — Applications and launch: Launch only registered apps through the existing backend and report the actual result.
- **CAP-SERVICES** — Processes and services: Read process/service state; service changes need confirmation and use managed service controls.
- **CAP-FILES** — Files and folders: Stay within an explicitly granted workspace; preview writes and confirm destructive changes.
- **CAP-STORAGE** — Storage and disks: Read capacity safely; destructive partition/format operations are prohibited by default.
- **CAP-SEARCH** — Local search: Search only authorized roots and return paths/snippets without exposing unrelated private data.
- **CAP-BROWSER** — Browser navigation: Use the authorized browser session; report tab/navigation outcomes and never bypass site controls.
- **CAP-BROWSER-AUTH** — Browser profiles and accounts: Never reveal passwords or switch identity without the user completing the provider’s authentication flow.
- **CAP-WEB** — Web pages and media: Treat page content as untrusted; require confirmation before purchases, posts, or external submissions.
- **CAP-DESKTOP** — Keyboard and mouse: Operate only the paired, user-authorized desktop; show target/action and allow immediate stop.
- **CAP-DESKTOP** — Windows and desktop sessions: Do not switch users or unlock a session without OS authorization; avoid capturing other sessions.
- **CAP-SHELL** — Terminal and shell: Use the existing constrained executor; no unrestricted shell and no direct root/sudo execution.
- **CAP-WORKSPACE** — Code workspace: Limit changes to the selected repository/worktree; preserve user edits and show diffs.
- **CAP-GIT** — Git and source control: Never push, force-push, rebase, reset, clean, merge or discard without explicit scoped approval.
- **CAP-CI** — Builds and continuous integration: Run only configured commands in an isolated checkout; report actual logs and exit status.
- **CAP-AGENTS** — Agent orchestration: Use isolated worktrees for concurrent writers; agents inherit the same safety constraints.
- **CAP-MODELS** — AI model and provider routing: Use configured, available providers only; disclose provider/model and never invent success or quality.
- **CAP-OFFLINE** — Offline and degraded operation: Make offline limitations explicit; queue only safe actions and never claim they ran.
- **CAP-DOCS** — Document understanding: Treat imported documents as untrusted input; cite source locations and honor access controls.
- **CAP-KNOWLEDGE** — Knowledge and research: Separate retrieved evidence from inference; cite sources and identify stale or unavailable material.
- **CAP-TASKS** — Tasks and projects: Show owner, state and outcome from the real task store; destructive edits require approval.
- **CAP-CALENDAR** — Calendar and availability: Use the selected calendar and explicit time zone; confirm ambiguous dates before writing events.
- **CAP-NOTIFY** — Reminders and notifications: Confirm delivery channel and time; do not disclose sensitive content on shared outputs.
- **CAP-AUTOMATION** — Automation and schedules: Preview trigger, scope and effects; pause/disable quickly; external or destructive steps need approval.
- **CAP-MAIL** — Email and message drafts: Draft by default; sending requires explicit confirmation of recipients, content and account.
- **CAP-CONTACTS** — Contacts and address book: Return only fields needed for the request; edits and sharing require confirmation.
- **CAP-NOTES** — Notes and personal records: Keep data private, attributable and editable; confirm permanent deletion.
- **CAP-PERSONAL** — Personal routines and planning: Use only user-provided or authorized data; distinguish suggestions from actions taken.
- **CAP-HOME** — Smart home controls: Check device identity and current state; safety-critical or access-control changes require confirmation.
- **CAP-SENSORS** — Sensors and environment: Use the existing hardware owner; label simulated, stale, disconnected and measured readings distinctly.
- **CAP-ROBOT-SIM** — Robot simulation and safety: Plan and test in simulation only; never dispatch real motion from this roadmap execution.
- **CAP-CAMERA** — Camera and visual input: Use the established camera owner and explicit capture indicator; do not retain images without authorization.
- **CAP-AUDIO** — Audio devices and media: Use the selected output/input device and a single owner; do not record or play sensitive media unexpectedly.
- **CAP-DEVICES** — Cross-device notifications: Pair devices explicitly, authenticate each target and disclose which device receives information.
- **CAP-PRIVACY** — Privacy and data controls: Apply data minimization, retention choices and visible capture indicators; never export secrets.
- **CAP-BACKUP** — Backup and recovery: Verify destination, scope and restore point; never overwrite the only copy without approval.
- **CAP-NETWORK** — Network and connectivity: Read network state safely; do not expose services or change firewall/router settings without approval.
- **CAP-PERIPHERALS** — Printers and peripherals: Verify target device and job content; confirm before printing or sharing sensitive documents.
- **CAP-PACKAGES** — Software inventory and installation: Inventory is read-only; installation/removal and privileged package actions require scoped approval.
- **CAP-UPDATES** — Updates and rollback: Check signatures, compatibility and backups; stage changes and require confirmation before applying.
- **CAP-DIAGNOSTICS** — Logs and diagnostics: Redact secrets and personal content; diagnostics never silently change system configuration.
- **CAP-HEALTH** — Health and performance: Measure with named sources and timestamps; do not claim health from HTTP reachability alone.
- **CAP-POWER** — Power and energy: Report observed values; power-off, reboot and actuator changes require explicit confirmation.
- **CAP-SYNC** — Portability and synchronization: Keep the Pi and personal laptop trust zones separate; synchronize only selected paths and fields.
- **CAP-POLICY** — Policy and administrator controls: Enforce backend policy and role checks; voice/chat cannot grant itself privileges or bypass denial.

## Shared acceptance gates

- **G-INTENT:** Test the quoted intent through both typed chat and the configured voice path where available. Assert parsed entities, ambiguity handling, correct capability route and a useful clarification when required.
- **G-REALITY:** Exercise the real backend adapter or clearly labeled fixture. Compare result against its authoritative owner; test unavailable, timeout, denied and stale cases. Save redacted request/result evidence.
- **G-AUTH:** Test guest, authorized user, denied approval, expired approval and malformed/out-of-scope input. Denials have no side effects. Consequential actions require fresh, scoped confirmation.
- **G-RECOVERY:** Test interruption, cancellation, retry/idempotency and recovery after owner/backend restart where applicable. Never report success before authoritative confirmation.
- **G-PRIVACY:** Verify least-data response, redaction, retention behavior and no secrets in UI/logs/export. Test trust-boundary and prompt-injection inputs.
- **G-ACCESS:** Test keyboard-only, screen reader labels, mobile/touch, muted/permission-denied and reduced-motion paths for user-facing controls.
- **G-EDGE:** Run on supported Raspberry Pi 5 configuration, measure memory/CPU/latency and test offline/degraded behavior. Do not infer hardware operation from simulation.
- **G-RELEASE:** Run focused regressions and relevant repository gate; record revision, commands, exact counts/failures and runtime classification. No test is weakened to pass.

## Global security and authorization boundaries

1. Browser UI never receives provider keys, session secrets or unrestricted shell access. Secrets stay server-side, are redacted from logs, and are never pasted into assistant output.
2. The existing constrained executor remains the only shell path. No raw arbitrary command execution, shell interpolation, privilege escalation, or automatic `sudo`. Privileged needs must be exposed as reviewed, fixed-purpose operations; each requires authorization at the time of action and backend enforcement. Voice identity alone is not authorization.
3. Require confirmation before deletion/overwrite, privileged or system-changing actions, reboot/shutdown, package install/removal, network exposure, robot motion, external messages/posts, purchases/spending, git push/merge, or sharing private data. Confirmation must state target, scope and consequences.
4. Default to read-only and reversible. Use allowlists, path confinement, validated structured parameters, rate/time/resource limits, audit trails, cancellation, and safe failure. Enforce authorization on the backend, not only the UI.
5. Treat prompts, webpages, documents, transcripts, tool output and model output as untrusted. They cannot grant permissions or override policy. Separate instruction from retrieved content and cite provenance.
6. A single owner controls each mic/camera/device. Hardware is disarmed by default. This plan does not authorize real motion; robotics acceptance in this environment is simulation-only and physical checks remain user-run.
7. Keep the Pi and personal Ubuntu laptop as separate trust zones. Pairing, device authentication, data scope, network permissions and explicit user consent are prerequisites for every cross-device feature.
8. Never claim root/full-device control. Be specific about capability limits and distinguish requested, approved, executing, completed, failed, simulated and unavailable states.


## Backlog domains and feature checklist

Each item depends on its domain CAP gate plus G-INTENT, G-REALITY, G-AUTH, G-RECOVERY, G-PRIVACY, G-ACCESS, G-EDGE and G-RELEASE as applicable. The domain gate above narrows the security boundary. Evidence path is `docs/jarvis-root-plan/evidence/JF-####/`; do not create evidence by simulating live success.

### 01. Conversation and context

**Dependency:** `CAP-CHAT`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Read the active conversation session; never present an unverified memory as fact. Save redacted evidence for each completed item.

- [ ] **JF-0001** [P0] [Deps: `CAP-CHAT`] Voice/chat: “Show the current status of conversation and context and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0002** [P0] [Deps: `CAP-CHAT`] Voice/chat: “Explain the current state of conversation and context and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0003** [P0] [Deps: `CAP-CHAT`] Voice/chat: “Compare the selected conversation and context items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0004** [P0] [Deps: `CAP-CHAT`] Voice/chat: “Find a user-specified item in conversation and context within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0005** [P1] [Deps: `CAP-CHAT`] Voice/chat: “Open the selected conversation and context item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0006** [P1] [Deps: `CAP-CHAT`] Voice/chat: “Create a draft conversation and context item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0007** [P1] [Deps: `CAP-CHAT`] Voice/chat: “Preview the requested conversation and context change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0008** [P1] [Deps: `CAP-CHAT`] Voice/chat: “Validate the requested conversation and context action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0009** [P1] [Deps: `CAP-CHAT`] Voice/chat: “Update the selected conversation and context item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0010** [P1] [Deps: `CAP-CHAT`] Voice/chat: “Undo the last reversible conversation and context change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0011** [P1] [Deps: `CAP-CHAT`] Voice/chat: “Schedule the requested conversation and context action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0012** [P1] [Deps: `CAP-CHAT`] Voice/chat: “Pause the selected running conversation and context workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0013** [P2] [Deps: `CAP-CHAT`] Voice/chat: “Resume the selected paused conversation and context workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0014** [P2] [Deps: `CAP-CHAT`] Voice/chat: “Cancel the selected conversation and context operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0015** [P2] [Deps: `CAP-CHAT`] Voice/chat: “Summarize recent conversation and context activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0016** [P2] [Deps: `CAP-CHAT`] Voice/chat: “Export selected conversation and context data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0017** [P2] [Deps: `CAP-CHAT`] Voice/chat: “Diagnose an conversation and context failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0018** [P2] [Deps: `CAP-CHAT`] Voice/chat: “Notify the user about a confirmed conversation and context event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0019** [P3] [Deps: `CAP-CHAT`] Voice/chat: “Configure a reversible conversation and context preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0020** [P3] [Deps: `CAP-CHAT`] Voice/chat: “Plan a multi-step conversation and context request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 02. Voice input and speech output

**Dependency:** `CAP-VOICE`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Use the existing single microphone owner and backend STT/TTS; respect mute and privacy state. Save redacted evidence for each completed item.

- [ ] **JF-0021** [P0] [Deps: `CAP-VOICE`] Voice/chat: “Show the current status of voice input and speech output and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0022** [P0] [Deps: `CAP-VOICE`] Voice/chat: “Explain the current state of voice input and speech output and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0023** [P0] [Deps: `CAP-VOICE`] Voice/chat: “Compare the selected voice input and speech output items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0024** [P0] [Deps: `CAP-VOICE`] Voice/chat: “Find a user-specified item in voice input and speech output within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0025** [P1] [Deps: `CAP-VOICE`] Voice/chat: “Open the selected voice input and speech output item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0026** [P1] [Deps: `CAP-VOICE`] Voice/chat: “Create a draft voice input and speech output item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0027** [P1] [Deps: `CAP-VOICE`] Voice/chat: “Preview the requested voice input and speech output change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0028** [P1] [Deps: `CAP-VOICE`] Voice/chat: “Validate the requested voice input and speech output action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0029** [P1] [Deps: `CAP-VOICE`] Voice/chat: “Update the selected voice input and speech output item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0030** [P1] [Deps: `CAP-VOICE`] Voice/chat: “Undo the last reversible voice input and speech output change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0031** [P1] [Deps: `CAP-VOICE`] Voice/chat: “Schedule the requested voice input and speech output action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0032** [P1] [Deps: `CAP-VOICE`] Voice/chat: “Pause the selected running voice input and speech output workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0033** [P2] [Deps: `CAP-VOICE`] Voice/chat: “Resume the selected paused voice input and speech output workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0034** [P2] [Deps: `CAP-VOICE`] Voice/chat: “Cancel the selected voice input and speech output operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0035** [P2] [Deps: `CAP-VOICE`] Voice/chat: “Summarize recent voice input and speech output activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0036** [P2] [Deps: `CAP-VOICE`] Voice/chat: “Export selected voice input and speech output data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0037** [P2] [Deps: `CAP-VOICE`] Voice/chat: “Diagnose an voice input and speech output failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0038** [P2] [Deps: `CAP-VOICE`] Voice/chat: “Notify the user about a confirmed voice input and speech output event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0039** [P3] [Deps: `CAP-VOICE`] Voice/chat: “Configure a reversible voice input and speech output preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0040** [P3] [Deps: `CAP-VOICE`] Voice/chat: “Plan a multi-step voice input and speech output request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 03. Wake word and listening modes

**Dependency:** `CAP-WAKE`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Listening is visibly indicated, opt-in, locally controlled and stoppable; no covert capture. Save redacted evidence for each completed item.

- [ ] **JF-0041** [P0] [Deps: `CAP-WAKE`] Voice/chat: “Show the current status of wake word and listening modes and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0042** [P0] [Deps: `CAP-WAKE`] Voice/chat: “Explain the current state of wake word and listening modes and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0043** [P0] [Deps: `CAP-WAKE`] Voice/chat: “Compare the selected wake word and listening modes items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0044** [P0] [Deps: `CAP-WAKE`] Voice/chat: “Find a user-specified item in wake word and listening modes within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0045** [P1] [Deps: `CAP-WAKE`] Voice/chat: “Open the selected wake word and listening modes item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0046** [P1] [Deps: `CAP-WAKE`] Voice/chat: “Create a draft wake word and listening modes item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0047** [P1] [Deps: `CAP-WAKE`] Voice/chat: “Preview the requested wake word and listening modes change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0048** [P1] [Deps: `CAP-WAKE`] Voice/chat: “Validate the requested wake word and listening modes action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0049** [P1] [Deps: `CAP-WAKE`] Voice/chat: “Update the selected wake word and listening modes item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0050** [P1] [Deps: `CAP-WAKE`] Voice/chat: “Undo the last reversible wake word and listening modes change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0051** [P1] [Deps: `CAP-WAKE`] Voice/chat: “Schedule the requested wake word and listening modes action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0052** [P1] [Deps: `CAP-WAKE`] Voice/chat: “Pause the selected running wake word and listening modes workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0053** [P2] [Deps: `CAP-WAKE`] Voice/chat: “Resume the selected paused wake word and listening modes workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0054** [P2] [Deps: `CAP-WAKE`] Voice/chat: “Cancel the selected wake word and listening modes operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0055** [P2] [Deps: `CAP-WAKE`] Voice/chat: “Summarize recent wake word and listening modes activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0056** [P2] [Deps: `CAP-WAKE`] Voice/chat: “Export selected wake word and listening modes data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0057** [P2] [Deps: `CAP-WAKE`] Voice/chat: “Diagnose an wake word and listening modes failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0058** [P2] [Deps: `CAP-WAKE`] Voice/chat: “Notify the user about a confirmed wake word and listening modes event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0059** [P3] [Deps: `CAP-WAKE`] Voice/chat: “Configure a reversible wake word and listening modes preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0060** [P3] [Deps: `CAP-WAKE`] Voice/chat: “Plan a multi-step wake word and listening modes request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 04. User identity and profiles

**Dependency:** `CAP-IDENTITY`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Resolve identity server-side; never infer admin status from UI state or a spoken claim. Save redacted evidence for each completed item.

- [ ] **JF-0061** [P0] [Deps: `CAP-IDENTITY`] Voice/chat: “Show the current status of user identity and profiles and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0062** [P0] [Deps: `CAP-IDENTITY`] Voice/chat: “Explain the current state of user identity and profiles and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0063** [P0] [Deps: `CAP-IDENTITY`] Voice/chat: “Compare the selected user identity and profiles items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0064** [P0] [Deps: `CAP-IDENTITY`] Voice/chat: “Find a user-specified item in user identity and profiles within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0065** [P1] [Deps: `CAP-IDENTITY`] Voice/chat: “Open the selected user identity and profiles item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0066** [P1] [Deps: `CAP-IDENTITY`] Voice/chat: “Create a draft user identity and profiles item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0067** [P1] [Deps: `CAP-IDENTITY`] Voice/chat: “Preview the requested user identity and profiles change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0068** [P1] [Deps: `CAP-IDENTITY`] Voice/chat: “Validate the requested user identity and profiles action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0069** [P1] [Deps: `CAP-IDENTITY`] Voice/chat: “Update the selected user identity and profiles item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0070** [P1] [Deps: `CAP-IDENTITY`] Voice/chat: “Undo the last reversible user identity and profiles change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0071** [P1] [Deps: `CAP-IDENTITY`] Voice/chat: “Schedule the requested user identity and profiles action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0072** [P1] [Deps: `CAP-IDENTITY`] Voice/chat: “Pause the selected running user identity and profiles workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0073** [P2] [Deps: `CAP-IDENTITY`] Voice/chat: “Resume the selected paused user identity and profiles workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0074** [P2] [Deps: `CAP-IDENTITY`] Voice/chat: “Cancel the selected user identity and profiles operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0075** [P2] [Deps: `CAP-IDENTITY`] Voice/chat: “Summarize recent user identity and profiles activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0076** [P2] [Deps: `CAP-IDENTITY`] Voice/chat: “Export selected user identity and profiles data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0077** [P2] [Deps: `CAP-IDENTITY`] Voice/chat: “Diagnose an user identity and profiles failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0078** [P2] [Deps: `CAP-IDENTITY`] Voice/chat: “Notify the user about a confirmed user identity and profiles event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0079** [P3] [Deps: `CAP-IDENTITY`] Voice/chat: “Configure a reversible user identity and profiles preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0080** [P3] [Deps: `CAP-IDENTITY`] Voice/chat: “Plan a multi-step user identity and profiles request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 05. Permissions and approvals

**Dependency:** `CAP-AUTHZ`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Apply least privilege; obtain explicit, scoped approval for privileged or consequential operations. Save redacted evidence for each completed item.

- [ ] **JF-0081** [P0] [Deps: `CAP-AUTHZ`] Voice/chat: “Show the current status of permissions and approvals and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0082** [P0] [Deps: `CAP-AUTHZ`] Voice/chat: “Explain the current state of permissions and approvals and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0083** [P0] [Deps: `CAP-AUTHZ`] Voice/chat: “Compare the selected permissions and approvals items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0084** [P0] [Deps: `CAP-AUTHZ`] Voice/chat: “Find a user-specified item in permissions and approvals within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0085** [P1] [Deps: `CAP-AUTHZ`] Voice/chat: “Open the selected permissions and approvals item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0086** [P1] [Deps: `CAP-AUTHZ`] Voice/chat: “Create a draft permissions and approvals item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0087** [P1] [Deps: `CAP-AUTHZ`] Voice/chat: “Preview the requested permissions and approvals change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0088** [P1] [Deps: `CAP-AUTHZ`] Voice/chat: “Validate the requested permissions and approvals action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0089** [P1] [Deps: `CAP-AUTHZ`] Voice/chat: “Update the selected permissions and approvals item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0090** [P1] [Deps: `CAP-AUTHZ`] Voice/chat: “Undo the last reversible permissions and approvals change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0091** [P1] [Deps: `CAP-AUTHZ`] Voice/chat: “Schedule the requested permissions and approvals action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0092** [P1] [Deps: `CAP-AUTHZ`] Voice/chat: “Pause the selected running permissions and approvals workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0093** [P2] [Deps: `CAP-AUTHZ`] Voice/chat: “Resume the selected paused permissions and approvals workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0094** [P2] [Deps: `CAP-AUTHZ`] Voice/chat: “Cancel the selected permissions and approvals operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0095** [P2] [Deps: `CAP-AUTHZ`] Voice/chat: “Summarize recent permissions and approvals activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0096** [P2] [Deps: `CAP-AUTHZ`] Voice/chat: “Export selected permissions and approvals data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0097** [P2] [Deps: `CAP-AUTHZ`] Voice/chat: “Diagnose an permissions and approvals failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0098** [P2] [Deps: `CAP-AUTHZ`] Voice/chat: “Notify the user about a confirmed permissions and approvals event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0099** [P3] [Deps: `CAP-AUTHZ`] Voice/chat: “Configure a reversible permissions and approvals preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0100** [P3] [Deps: `CAP-AUTHZ`] Voice/chat: “Plan a multi-step permissions and approvals request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 06. Audit and action history

**Dependency:** `CAP-AUDIT`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Record action metadata and outcome without secrets, raw credentials or unnecessary transcript content. Save redacted evidence for each completed item.

- [ ] **JF-0101** [P0] [Deps: `CAP-AUDIT`] Voice/chat: “Show the current status of audit and action history and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0102** [P0] [Deps: `CAP-AUDIT`] Voice/chat: “Explain the current state of audit and action history and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0103** [P0] [Deps: `CAP-AUDIT`] Voice/chat: “Compare the selected audit and action history items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0104** [P0] [Deps: `CAP-AUDIT`] Voice/chat: “Find a user-specified item in audit and action history within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0105** [P1] [Deps: `CAP-AUDIT`] Voice/chat: “Open the selected audit and action history item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0106** [P1] [Deps: `CAP-AUDIT`] Voice/chat: “Create a draft audit and action history item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0107** [P1] [Deps: `CAP-AUDIT`] Voice/chat: “Preview the requested audit and action history change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0108** [P1] [Deps: `CAP-AUDIT`] Voice/chat: “Validate the requested audit and action history action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0109** [P1] [Deps: `CAP-AUDIT`] Voice/chat: “Update the selected audit and action history item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0110** [P1] [Deps: `CAP-AUDIT`] Voice/chat: “Undo the last reversible audit and action history change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0111** [P1] [Deps: `CAP-AUDIT`] Voice/chat: “Schedule the requested audit and action history action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0112** [P1] [Deps: `CAP-AUDIT`] Voice/chat: “Pause the selected running audit and action history workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0113** [P2] [Deps: `CAP-AUDIT`] Voice/chat: “Resume the selected paused audit and action history workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0114** [P2] [Deps: `CAP-AUDIT`] Voice/chat: “Cancel the selected audit and action history operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0115** [P2] [Deps: `CAP-AUDIT`] Voice/chat: “Summarize recent audit and action history activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0116** [P2] [Deps: `CAP-AUDIT`] Voice/chat: “Export selected audit and action history data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0117** [P2] [Deps: `CAP-AUDIT`] Voice/chat: “Diagnose an audit and action history failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0118** [P2] [Deps: `CAP-AUDIT`] Voice/chat: “Notify the user about a confirmed audit and action history event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0119** [P3] [Deps: `CAP-AUDIT`] Voice/chat: “Configure a reversible audit and action history preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0120** [P3] [Deps: `CAP-AUDIT`] Voice/chat: “Plan a multi-step audit and action history request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 07. Raspberry Pi system status

**Dependency:** `CAP-SYSTEM`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Read allowlisted telemetry only; unsupported readings are Unavailable, not guessed. Save redacted evidence for each completed item.

- [ ] **JF-0121** [P0] [Deps: `CAP-SYSTEM`] Voice/chat: “Show the current status of raspberry pi system status and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0122** [P0] [Deps: `CAP-SYSTEM`] Voice/chat: “Explain the current state of raspberry pi system status and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0123** [P0] [Deps: `CAP-SYSTEM`] Voice/chat: “Compare the selected raspberry pi system status items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0124** [P0] [Deps: `CAP-SYSTEM`] Voice/chat: “Find a user-specified item in raspberry pi system status within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0125** [P1] [Deps: `CAP-SYSTEM`] Voice/chat: “Open the selected raspberry pi system status item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0126** [P1] [Deps: `CAP-SYSTEM`] Voice/chat: “Create a draft raspberry pi system status item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0127** [P1] [Deps: `CAP-SYSTEM`] Voice/chat: “Preview the requested raspberry pi system status change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0128** [P1] [Deps: `CAP-SYSTEM`] Voice/chat: “Validate the requested raspberry pi system status action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0129** [P1] [Deps: `CAP-SYSTEM`] Voice/chat: “Update the selected raspberry pi system status item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0130** [P1] [Deps: `CAP-SYSTEM`] Voice/chat: “Undo the last reversible raspberry pi system status change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0131** [P1] [Deps: `CAP-SYSTEM`] Voice/chat: “Schedule the requested raspberry pi system status action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0132** [P1] [Deps: `CAP-SYSTEM`] Voice/chat: “Pause the selected running raspberry pi system status workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0133** [P2] [Deps: `CAP-SYSTEM`] Voice/chat: “Resume the selected paused raspberry pi system status workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0134** [P2] [Deps: `CAP-SYSTEM`] Voice/chat: “Cancel the selected raspberry pi system status operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0135** [P2] [Deps: `CAP-SYSTEM`] Voice/chat: “Summarize recent raspberry pi system status activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0136** [P2] [Deps: `CAP-SYSTEM`] Voice/chat: “Export selected raspberry pi system status data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0137** [P2] [Deps: `CAP-SYSTEM`] Voice/chat: “Diagnose an raspberry pi system status failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0138** [P2] [Deps: `CAP-SYSTEM`] Voice/chat: “Notify the user about a confirmed raspberry pi system status event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0139** [P3] [Deps: `CAP-SYSTEM`] Voice/chat: “Configure a reversible raspberry pi system status preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0140** [P3] [Deps: `CAP-SYSTEM`] Voice/chat: “Plan a multi-step raspberry pi system status request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 08. Applications and launch

**Dependency:** `CAP-APPS`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Launch only registered apps through the existing backend and report the actual result. Save redacted evidence for each completed item.

- [ ] **JF-0141** [P0] [Deps: `CAP-APPS`] Voice/chat: “Show the current status of applications and launch and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0142** [P0] [Deps: `CAP-APPS`] Voice/chat: “Explain the current state of applications and launch and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0143** [P0] [Deps: `CAP-APPS`] Voice/chat: “Compare the selected applications and launch items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0144** [P0] [Deps: `CAP-APPS`] Voice/chat: “Find a user-specified item in applications and launch within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0145** [P1] [Deps: `CAP-APPS`] Voice/chat: “Open the selected applications and launch item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0146** [P1] [Deps: `CAP-APPS`] Voice/chat: “Create a draft applications and launch item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0147** [P1] [Deps: `CAP-APPS`] Voice/chat: “Preview the requested applications and launch change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0148** [P1] [Deps: `CAP-APPS`] Voice/chat: “Validate the requested applications and launch action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0149** [P1] [Deps: `CAP-APPS`] Voice/chat: “Update the selected applications and launch item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0150** [P1] [Deps: `CAP-APPS`] Voice/chat: “Undo the last reversible applications and launch change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0151** [P1] [Deps: `CAP-APPS`] Voice/chat: “Schedule the requested applications and launch action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0152** [P1] [Deps: `CAP-APPS`] Voice/chat: “Pause the selected running applications and launch workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0153** [P2] [Deps: `CAP-APPS`] Voice/chat: “Resume the selected paused applications and launch workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0154** [P2] [Deps: `CAP-APPS`] Voice/chat: “Cancel the selected applications and launch operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0155** [P2] [Deps: `CAP-APPS`] Voice/chat: “Summarize recent applications and launch activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0156** [P2] [Deps: `CAP-APPS`] Voice/chat: “Export selected applications and launch data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0157** [P2] [Deps: `CAP-APPS`] Voice/chat: “Diagnose an applications and launch failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0158** [P2] [Deps: `CAP-APPS`] Voice/chat: “Notify the user about a confirmed applications and launch event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0159** [P3] [Deps: `CAP-APPS`] Voice/chat: “Configure a reversible applications and launch preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0160** [P3] [Deps: `CAP-APPS`] Voice/chat: “Plan a multi-step applications and launch request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 09. Processes and services

**Dependency:** `CAP-SERVICES`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Read process/service state; service changes need confirmation and use managed service controls. Save redacted evidence for each completed item.

- [ ] **JF-0161** [P0] [Deps: `CAP-SERVICES`] Voice/chat: “Show the current status of processes and services and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0162** [P0] [Deps: `CAP-SERVICES`] Voice/chat: “Explain the current state of processes and services and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0163** [P0] [Deps: `CAP-SERVICES`] Voice/chat: “Compare the selected processes and services items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0164** [P0] [Deps: `CAP-SERVICES`] Voice/chat: “Find a user-specified item in processes and services within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0165** [P1] [Deps: `CAP-SERVICES`] Voice/chat: “Open the selected processes and services item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0166** [P1] [Deps: `CAP-SERVICES`] Voice/chat: “Create a draft processes and services item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0167** [P1] [Deps: `CAP-SERVICES`] Voice/chat: “Preview the requested processes and services change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0168** [P1] [Deps: `CAP-SERVICES`] Voice/chat: “Validate the requested processes and services action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0169** [P1] [Deps: `CAP-SERVICES`] Voice/chat: “Update the selected processes and services item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0170** [P1] [Deps: `CAP-SERVICES`] Voice/chat: “Undo the last reversible processes and services change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0171** [P1] [Deps: `CAP-SERVICES`] Voice/chat: “Schedule the requested processes and services action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0172** [P1] [Deps: `CAP-SERVICES`] Voice/chat: “Pause the selected running processes and services workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0173** [P2] [Deps: `CAP-SERVICES`] Voice/chat: “Resume the selected paused processes and services workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0174** [P2] [Deps: `CAP-SERVICES`] Voice/chat: “Cancel the selected processes and services operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0175** [P2] [Deps: `CAP-SERVICES`] Voice/chat: “Summarize recent processes and services activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0176** [P2] [Deps: `CAP-SERVICES`] Voice/chat: “Export selected processes and services data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0177** [P2] [Deps: `CAP-SERVICES`] Voice/chat: “Diagnose an processes and services failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0178** [P2] [Deps: `CAP-SERVICES`] Voice/chat: “Notify the user about a confirmed processes and services event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0179** [P3] [Deps: `CAP-SERVICES`] Voice/chat: “Configure a reversible processes and services preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0180** [P3] [Deps: `CAP-SERVICES`] Voice/chat: “Plan a multi-step processes and services request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 10. Files and folders

**Dependency:** `CAP-FILES`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Stay within an explicitly granted workspace; preview writes and confirm destructive changes. Save redacted evidence for each completed item.

- [ ] **JF-0181** [P0] [Deps: `CAP-FILES`] Voice/chat: “Show the current status of files and folders and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0182** [P0] [Deps: `CAP-FILES`] Voice/chat: “Explain the current state of files and folders and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0183** [P0] [Deps: `CAP-FILES`] Voice/chat: “Compare the selected files and folders items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0184** [P0] [Deps: `CAP-FILES`] Voice/chat: “Find a user-specified item in files and folders within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0185** [P1] [Deps: `CAP-FILES`] Voice/chat: “Open the selected files and folders item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0186** [P1] [Deps: `CAP-FILES`] Voice/chat: “Create a draft files and folders item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0187** [P1] [Deps: `CAP-FILES`] Voice/chat: “Preview the requested files and folders change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0188** [P1] [Deps: `CAP-FILES`] Voice/chat: “Validate the requested files and folders action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0189** [P1] [Deps: `CAP-FILES`] Voice/chat: “Update the selected files and folders item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0190** [P1] [Deps: `CAP-FILES`] Voice/chat: “Undo the last reversible files and folders change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0191** [P1] [Deps: `CAP-FILES`] Voice/chat: “Schedule the requested files and folders action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0192** [P1] [Deps: `CAP-FILES`] Voice/chat: “Pause the selected running files and folders workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0193** [P2] [Deps: `CAP-FILES`] Voice/chat: “Resume the selected paused files and folders workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0194** [P2] [Deps: `CAP-FILES`] Voice/chat: “Cancel the selected files and folders operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0195** [P2] [Deps: `CAP-FILES`] Voice/chat: “Summarize recent files and folders activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0196** [P2] [Deps: `CAP-FILES`] Voice/chat: “Export selected files and folders data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0197** [P2] [Deps: `CAP-FILES`] Voice/chat: “Diagnose an files and folders failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0198** [P2] [Deps: `CAP-FILES`] Voice/chat: “Notify the user about a confirmed files and folders event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0199** [P3] [Deps: `CAP-FILES`] Voice/chat: “Configure a reversible files and folders preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0200** [P3] [Deps: `CAP-FILES`] Voice/chat: “Plan a multi-step files and folders request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 11. Storage and disks

**Dependency:** `CAP-STORAGE`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Read capacity safely; destructive partition/format operations are prohibited by default. Save redacted evidence for each completed item.

- [ ] **JF-0201** [P0] [Deps: `CAP-STORAGE`] Voice/chat: “Show the current status of storage and disks and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0202** [P0] [Deps: `CAP-STORAGE`] Voice/chat: “Explain the current state of storage and disks and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0203** [P0] [Deps: `CAP-STORAGE`] Voice/chat: “Compare the selected storage and disks items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0204** [P0] [Deps: `CAP-STORAGE`] Voice/chat: “Find a user-specified item in storage and disks within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0205** [P1] [Deps: `CAP-STORAGE`] Voice/chat: “Open the selected storage and disks item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0206** [P1] [Deps: `CAP-STORAGE`] Voice/chat: “Create a draft storage and disks item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0207** [P1] [Deps: `CAP-STORAGE`] Voice/chat: “Preview the requested storage and disks change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0208** [P1] [Deps: `CAP-STORAGE`] Voice/chat: “Validate the requested storage and disks action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0209** [P1] [Deps: `CAP-STORAGE`] Voice/chat: “Update the selected storage and disks item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0210** [P1] [Deps: `CAP-STORAGE`] Voice/chat: “Undo the last reversible storage and disks change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0211** [P1] [Deps: `CAP-STORAGE`] Voice/chat: “Schedule the requested storage and disks action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0212** [P1] [Deps: `CAP-STORAGE`] Voice/chat: “Pause the selected running storage and disks workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0213** [P2] [Deps: `CAP-STORAGE`] Voice/chat: “Resume the selected paused storage and disks workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0214** [P2] [Deps: `CAP-STORAGE`] Voice/chat: “Cancel the selected storage and disks operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0215** [P2] [Deps: `CAP-STORAGE`] Voice/chat: “Summarize recent storage and disks activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0216** [P2] [Deps: `CAP-STORAGE`] Voice/chat: “Export selected storage and disks data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0217** [P2] [Deps: `CAP-STORAGE`] Voice/chat: “Diagnose an storage and disks failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0218** [P2] [Deps: `CAP-STORAGE`] Voice/chat: “Notify the user about a confirmed storage and disks event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0219** [P3] [Deps: `CAP-STORAGE`] Voice/chat: “Configure a reversible storage and disks preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0220** [P3] [Deps: `CAP-STORAGE`] Voice/chat: “Plan a multi-step storage and disks request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 12. Local search

**Dependency:** `CAP-SEARCH`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Search only authorized roots and return paths/snippets without exposing unrelated private data. Save redacted evidence for each completed item.

- [ ] **JF-0221** [P0] [Deps: `CAP-SEARCH`] Voice/chat: “Show the current status of local search and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0222** [P0] [Deps: `CAP-SEARCH`] Voice/chat: “Explain the current state of local search and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0223** [P0] [Deps: `CAP-SEARCH`] Voice/chat: “Compare the selected local search items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0224** [P0] [Deps: `CAP-SEARCH`] Voice/chat: “Find a user-specified item in local search within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0225** [P1] [Deps: `CAP-SEARCH`] Voice/chat: “Open the selected local search item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0226** [P1] [Deps: `CAP-SEARCH`] Voice/chat: “Create a draft local search item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0227** [P1] [Deps: `CAP-SEARCH`] Voice/chat: “Preview the requested local search change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0228** [P1] [Deps: `CAP-SEARCH`] Voice/chat: “Validate the requested local search action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0229** [P1] [Deps: `CAP-SEARCH`] Voice/chat: “Update the selected local search item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0230** [P1] [Deps: `CAP-SEARCH`] Voice/chat: “Undo the last reversible local search change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0231** [P1] [Deps: `CAP-SEARCH`] Voice/chat: “Schedule the requested local search action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0232** [P1] [Deps: `CAP-SEARCH`] Voice/chat: “Pause the selected running local search workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0233** [P2] [Deps: `CAP-SEARCH`] Voice/chat: “Resume the selected paused local search workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0234** [P2] [Deps: `CAP-SEARCH`] Voice/chat: “Cancel the selected local search operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0235** [P2] [Deps: `CAP-SEARCH`] Voice/chat: “Summarize recent local search activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0236** [P2] [Deps: `CAP-SEARCH`] Voice/chat: “Export selected local search data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0237** [P2] [Deps: `CAP-SEARCH`] Voice/chat: “Diagnose an local search failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0238** [P2] [Deps: `CAP-SEARCH`] Voice/chat: “Notify the user about a confirmed local search event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0239** [P3] [Deps: `CAP-SEARCH`] Voice/chat: “Configure a reversible local search preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0240** [P3] [Deps: `CAP-SEARCH`] Voice/chat: “Plan a multi-step local search request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 13. Browser navigation

**Dependency:** `CAP-BROWSER`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Use the authorized browser session; report tab/navigation outcomes and never bypass site controls. Save redacted evidence for each completed item.

- [ ] **JF-0241** [P0] [Deps: `CAP-BROWSER`] Voice/chat: “Show the current status of browser navigation and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0242** [P0] [Deps: `CAP-BROWSER`] Voice/chat: “Explain the current state of browser navigation and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0243** [P0] [Deps: `CAP-BROWSER`] Voice/chat: “Compare the selected browser navigation items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0244** [P0] [Deps: `CAP-BROWSER`] Voice/chat: “Find a user-specified item in browser navigation within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0245** [P1] [Deps: `CAP-BROWSER`] Voice/chat: “Open the selected browser navigation item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0246** [P1] [Deps: `CAP-BROWSER`] Voice/chat: “Create a draft browser navigation item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0247** [P1] [Deps: `CAP-BROWSER`] Voice/chat: “Preview the requested browser navigation change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0248** [P1] [Deps: `CAP-BROWSER`] Voice/chat: “Validate the requested browser navigation action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0249** [P1] [Deps: `CAP-BROWSER`] Voice/chat: “Update the selected browser navigation item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0250** [P1] [Deps: `CAP-BROWSER`] Voice/chat: “Undo the last reversible browser navigation change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0251** [P1] [Deps: `CAP-BROWSER`] Voice/chat: “Schedule the requested browser navigation action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0252** [P1] [Deps: `CAP-BROWSER`] Voice/chat: “Pause the selected running browser navigation workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0253** [P2] [Deps: `CAP-BROWSER`] Voice/chat: “Resume the selected paused browser navigation workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0254** [P2] [Deps: `CAP-BROWSER`] Voice/chat: “Cancel the selected browser navigation operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0255** [P2] [Deps: `CAP-BROWSER`] Voice/chat: “Summarize recent browser navigation activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0256** [P2] [Deps: `CAP-BROWSER`] Voice/chat: “Export selected browser navigation data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0257** [P2] [Deps: `CAP-BROWSER`] Voice/chat: “Diagnose an browser navigation failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0258** [P2] [Deps: `CAP-BROWSER`] Voice/chat: “Notify the user about a confirmed browser navigation event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0259** [P3] [Deps: `CAP-BROWSER`] Voice/chat: “Configure a reversible browser navigation preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0260** [P3] [Deps: `CAP-BROWSER`] Voice/chat: “Plan a multi-step browser navigation request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 14. Browser profiles and accounts

**Dependency:** `CAP-BROWSER-AUTH`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Never reveal passwords or switch identity without the user completing the provider’s authentication flow. Save redacted evidence for each completed item.

- [ ] **JF-0261** [P0] [Deps: `CAP-BROWSER-AUTH`] Voice/chat: “Show the current status of browser profiles and accounts and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0262** [P0] [Deps: `CAP-BROWSER-AUTH`] Voice/chat: “Explain the current state of browser profiles and accounts and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0263** [P0] [Deps: `CAP-BROWSER-AUTH`] Voice/chat: “Compare the selected browser profiles and accounts items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0264** [P0] [Deps: `CAP-BROWSER-AUTH`] Voice/chat: “Find a user-specified item in browser profiles and accounts within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0265** [P1] [Deps: `CAP-BROWSER-AUTH`] Voice/chat: “Open the selected browser profiles and accounts item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0266** [P1] [Deps: `CAP-BROWSER-AUTH`] Voice/chat: “Create a draft browser profiles and accounts item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0267** [P1] [Deps: `CAP-BROWSER-AUTH`] Voice/chat: “Preview the requested browser profiles and accounts change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0268** [P1] [Deps: `CAP-BROWSER-AUTH`] Voice/chat: “Validate the requested browser profiles and accounts action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0269** [P1] [Deps: `CAP-BROWSER-AUTH`] Voice/chat: “Update the selected browser profiles and accounts item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0270** [P1] [Deps: `CAP-BROWSER-AUTH`] Voice/chat: “Undo the last reversible browser profiles and accounts change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0271** [P1] [Deps: `CAP-BROWSER-AUTH`] Voice/chat: “Schedule the requested browser profiles and accounts action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0272** [P1] [Deps: `CAP-BROWSER-AUTH`] Voice/chat: “Pause the selected running browser profiles and accounts workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0273** [P2] [Deps: `CAP-BROWSER-AUTH`] Voice/chat: “Resume the selected paused browser profiles and accounts workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0274** [P2] [Deps: `CAP-BROWSER-AUTH`] Voice/chat: “Cancel the selected browser profiles and accounts operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0275** [P2] [Deps: `CAP-BROWSER-AUTH`] Voice/chat: “Summarize recent browser profiles and accounts activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0276** [P2] [Deps: `CAP-BROWSER-AUTH`] Voice/chat: “Export selected browser profiles and accounts data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0277** [P2] [Deps: `CAP-BROWSER-AUTH`] Voice/chat: “Diagnose an browser profiles and accounts failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0278** [P2] [Deps: `CAP-BROWSER-AUTH`] Voice/chat: “Notify the user about a confirmed browser profiles and accounts event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0279** [P3] [Deps: `CAP-BROWSER-AUTH`] Voice/chat: “Configure a reversible browser profiles and accounts preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0280** [P3] [Deps: `CAP-BROWSER-AUTH`] Voice/chat: “Plan a multi-step browser profiles and accounts request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 15. Web pages and media

**Dependency:** `CAP-WEB`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Treat page content as untrusted; require confirmation before purchases, posts, or external submissions. Save redacted evidence for each completed item.

- [ ] **JF-0281** [P0] [Deps: `CAP-WEB`] Voice/chat: “Show the current status of web pages and media and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0282** [P0] [Deps: `CAP-WEB`] Voice/chat: “Explain the current state of web pages and media and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0283** [P0] [Deps: `CAP-WEB`] Voice/chat: “Compare the selected web pages and media items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0284** [P0] [Deps: `CAP-WEB`] Voice/chat: “Find a user-specified item in web pages and media within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0285** [P1] [Deps: `CAP-WEB`] Voice/chat: “Open the selected web pages and media item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0286** [P1] [Deps: `CAP-WEB`] Voice/chat: “Create a draft web pages and media item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0287** [P1] [Deps: `CAP-WEB`] Voice/chat: “Preview the requested web pages and media change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0288** [P1] [Deps: `CAP-WEB`] Voice/chat: “Validate the requested web pages and media action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0289** [P1] [Deps: `CAP-WEB`] Voice/chat: “Update the selected web pages and media item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0290** [P1] [Deps: `CAP-WEB`] Voice/chat: “Undo the last reversible web pages and media change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0291** [P1] [Deps: `CAP-WEB`] Voice/chat: “Schedule the requested web pages and media action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0292** [P1] [Deps: `CAP-WEB`] Voice/chat: “Pause the selected running web pages and media workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0293** [P2] [Deps: `CAP-WEB`] Voice/chat: “Resume the selected paused web pages and media workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0294** [P2] [Deps: `CAP-WEB`] Voice/chat: “Cancel the selected web pages and media operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0295** [P2] [Deps: `CAP-WEB`] Voice/chat: “Summarize recent web pages and media activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0296** [P2] [Deps: `CAP-WEB`] Voice/chat: “Export selected web pages and media data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0297** [P2] [Deps: `CAP-WEB`] Voice/chat: “Diagnose an web pages and media failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0298** [P2] [Deps: `CAP-WEB`] Voice/chat: “Notify the user about a confirmed web pages and media event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0299** [P3] [Deps: `CAP-WEB`] Voice/chat: “Configure a reversible web pages and media preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0300** [P3] [Deps: `CAP-WEB`] Voice/chat: “Plan a multi-step web pages and media request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 16. Keyboard and mouse

**Dependency:** `CAP-DESKTOP`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Operate only the paired, user-authorized desktop; show target/action and allow immediate stop. Save redacted evidence for each completed item.

- [ ] **JF-0301** [P0] [Deps: `CAP-DESKTOP`] Voice/chat: “Show the current status of keyboard and mouse and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0302** [P0] [Deps: `CAP-DESKTOP`] Voice/chat: “Explain the current state of keyboard and mouse and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0303** [P0] [Deps: `CAP-DESKTOP`] Voice/chat: “Compare the selected keyboard and mouse items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0304** [P0] [Deps: `CAP-DESKTOP`] Voice/chat: “Find a user-specified item in keyboard and mouse within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0305** [P1] [Deps: `CAP-DESKTOP`] Voice/chat: “Open the selected keyboard and mouse item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0306** [P1] [Deps: `CAP-DESKTOP`] Voice/chat: “Create a draft keyboard and mouse item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0307** [P1] [Deps: `CAP-DESKTOP`] Voice/chat: “Preview the requested keyboard and mouse change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0308** [P1] [Deps: `CAP-DESKTOP`] Voice/chat: “Validate the requested keyboard and mouse action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0309** [P1] [Deps: `CAP-DESKTOP`] Voice/chat: “Update the selected keyboard and mouse item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0310** [P1] [Deps: `CAP-DESKTOP`] Voice/chat: “Undo the last reversible keyboard and mouse change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0311** [P1] [Deps: `CAP-DESKTOP`] Voice/chat: “Schedule the requested keyboard and mouse action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0312** [P1] [Deps: `CAP-DESKTOP`] Voice/chat: “Pause the selected running keyboard and mouse workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0313** [P2] [Deps: `CAP-DESKTOP`] Voice/chat: “Resume the selected paused keyboard and mouse workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0314** [P2] [Deps: `CAP-DESKTOP`] Voice/chat: “Cancel the selected keyboard and mouse operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0315** [P2] [Deps: `CAP-DESKTOP`] Voice/chat: “Summarize recent keyboard and mouse activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0316** [P2] [Deps: `CAP-DESKTOP`] Voice/chat: “Export selected keyboard and mouse data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0317** [P2] [Deps: `CAP-DESKTOP`] Voice/chat: “Diagnose an keyboard and mouse failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0318** [P2] [Deps: `CAP-DESKTOP`] Voice/chat: “Notify the user about a confirmed keyboard and mouse event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0319** [P3] [Deps: `CAP-DESKTOP`] Voice/chat: “Configure a reversible keyboard and mouse preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0320** [P3] [Deps: `CAP-DESKTOP`] Voice/chat: “Plan a multi-step keyboard and mouse request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 17. Windows and desktop sessions

**Dependency:** `CAP-DESKTOP`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Do not switch users or unlock a session without OS authorization; avoid capturing other sessions. Save redacted evidence for each completed item.

- [ ] **JF-0321** [P0] [Deps: `CAP-DESKTOP`] Voice/chat: “Show the current status of windows and desktop sessions and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0322** [P0] [Deps: `CAP-DESKTOP`] Voice/chat: “Explain the current state of windows and desktop sessions and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0323** [P0] [Deps: `CAP-DESKTOP`] Voice/chat: “Compare the selected windows and desktop sessions items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0324** [P0] [Deps: `CAP-DESKTOP`] Voice/chat: “Find a user-specified item in windows and desktop sessions within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0325** [P1] [Deps: `CAP-DESKTOP`] Voice/chat: “Open the selected windows and desktop sessions item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0326** [P1] [Deps: `CAP-DESKTOP`] Voice/chat: “Create a draft windows and desktop sessions item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0327** [P1] [Deps: `CAP-DESKTOP`] Voice/chat: “Preview the requested windows and desktop sessions change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0328** [P1] [Deps: `CAP-DESKTOP`] Voice/chat: “Validate the requested windows and desktop sessions action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0329** [P1] [Deps: `CAP-DESKTOP`] Voice/chat: “Update the selected windows and desktop sessions item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0330** [P1] [Deps: `CAP-DESKTOP`] Voice/chat: “Undo the last reversible windows and desktop sessions change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0331** [P1] [Deps: `CAP-DESKTOP`] Voice/chat: “Schedule the requested windows and desktop sessions action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0332** [P1] [Deps: `CAP-DESKTOP`] Voice/chat: “Pause the selected running windows and desktop sessions workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0333** [P2] [Deps: `CAP-DESKTOP`] Voice/chat: “Resume the selected paused windows and desktop sessions workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0334** [P2] [Deps: `CAP-DESKTOP`] Voice/chat: “Cancel the selected windows and desktop sessions operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0335** [P2] [Deps: `CAP-DESKTOP`] Voice/chat: “Summarize recent windows and desktop sessions activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0336** [P2] [Deps: `CAP-DESKTOP`] Voice/chat: “Export selected windows and desktop sessions data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0337** [P2] [Deps: `CAP-DESKTOP`] Voice/chat: “Diagnose an windows and desktop sessions failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0338** [P2] [Deps: `CAP-DESKTOP`] Voice/chat: “Notify the user about a confirmed windows and desktop sessions event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0339** [P3] [Deps: `CAP-DESKTOP`] Voice/chat: “Configure a reversible windows and desktop sessions preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0340** [P3] [Deps: `CAP-DESKTOP`] Voice/chat: “Plan a multi-step windows and desktop sessions request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 18. Terminal and shell

**Dependency:** `CAP-SHELL`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Use the existing constrained executor; no unrestricted shell and no direct root/sudo execution. Save redacted evidence for each completed item.

- [ ] **JF-0341** [P0] [Deps: `CAP-SHELL`] Voice/chat: “Show the current status of terminal and shell and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0342** [P0] [Deps: `CAP-SHELL`] Voice/chat: “Explain the current state of terminal and shell and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0343** [P0] [Deps: `CAP-SHELL`] Voice/chat: “Compare the selected terminal and shell items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0344** [P0] [Deps: `CAP-SHELL`] Voice/chat: “Find a user-specified item in terminal and shell within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0345** [P1] [Deps: `CAP-SHELL`] Voice/chat: “Open the selected terminal and shell item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0346** [P1] [Deps: `CAP-SHELL`] Voice/chat: “Create a draft terminal and shell item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0347** [P1] [Deps: `CAP-SHELL`] Voice/chat: “Preview the requested terminal and shell change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0348** [P1] [Deps: `CAP-SHELL`] Voice/chat: “Validate the requested terminal and shell action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0349** [P1] [Deps: `CAP-SHELL`] Voice/chat: “Update the selected terminal and shell item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0350** [P1] [Deps: `CAP-SHELL`] Voice/chat: “Undo the last reversible terminal and shell change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0351** [P1] [Deps: `CAP-SHELL`] Voice/chat: “Schedule the requested terminal and shell action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0352** [P1] [Deps: `CAP-SHELL`] Voice/chat: “Pause the selected running terminal and shell workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0353** [P2] [Deps: `CAP-SHELL`] Voice/chat: “Resume the selected paused terminal and shell workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0354** [P2] [Deps: `CAP-SHELL`] Voice/chat: “Cancel the selected terminal and shell operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0355** [P2] [Deps: `CAP-SHELL`] Voice/chat: “Summarize recent terminal and shell activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0356** [P2] [Deps: `CAP-SHELL`] Voice/chat: “Export selected terminal and shell data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0357** [P2] [Deps: `CAP-SHELL`] Voice/chat: “Diagnose an terminal and shell failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0358** [P2] [Deps: `CAP-SHELL`] Voice/chat: “Notify the user about a confirmed terminal and shell event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0359** [P3] [Deps: `CAP-SHELL`] Voice/chat: “Configure a reversible terminal and shell preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0360** [P3] [Deps: `CAP-SHELL`] Voice/chat: “Plan a multi-step terminal and shell request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 19. Code workspace

**Dependency:** `CAP-WORKSPACE`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Limit changes to the selected repository/worktree; preserve user edits and show diffs. Save redacted evidence for each completed item.

- [ ] **JF-0361** [P0] [Deps: `CAP-WORKSPACE`] Voice/chat: “Show the current status of code workspace and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0362** [P0] [Deps: `CAP-WORKSPACE`] Voice/chat: “Explain the current state of code workspace and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0363** [P0] [Deps: `CAP-WORKSPACE`] Voice/chat: “Compare the selected code workspace items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0364** [P0] [Deps: `CAP-WORKSPACE`] Voice/chat: “Find a user-specified item in code workspace within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0365** [P1] [Deps: `CAP-WORKSPACE`] Voice/chat: “Open the selected code workspace item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0366** [P1] [Deps: `CAP-WORKSPACE`] Voice/chat: “Create a draft code workspace item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0367** [P1] [Deps: `CAP-WORKSPACE`] Voice/chat: “Preview the requested code workspace change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0368** [P1] [Deps: `CAP-WORKSPACE`] Voice/chat: “Validate the requested code workspace action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0369** [P1] [Deps: `CAP-WORKSPACE`] Voice/chat: “Update the selected code workspace item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0370** [P1] [Deps: `CAP-WORKSPACE`] Voice/chat: “Undo the last reversible code workspace change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0371** [P1] [Deps: `CAP-WORKSPACE`] Voice/chat: “Schedule the requested code workspace action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0372** [P1] [Deps: `CAP-WORKSPACE`] Voice/chat: “Pause the selected running code workspace workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0373** [P2] [Deps: `CAP-WORKSPACE`] Voice/chat: “Resume the selected paused code workspace workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0374** [P2] [Deps: `CAP-WORKSPACE`] Voice/chat: “Cancel the selected code workspace operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0375** [P2] [Deps: `CAP-WORKSPACE`] Voice/chat: “Summarize recent code workspace activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0376** [P2] [Deps: `CAP-WORKSPACE`] Voice/chat: “Export selected code workspace data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0377** [P2] [Deps: `CAP-WORKSPACE`] Voice/chat: “Diagnose an code workspace failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0378** [P2] [Deps: `CAP-WORKSPACE`] Voice/chat: “Notify the user about a confirmed code workspace event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0379** [P3] [Deps: `CAP-WORKSPACE`] Voice/chat: “Configure a reversible code workspace preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0380** [P3] [Deps: `CAP-WORKSPACE`] Voice/chat: “Plan a multi-step code workspace request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 20. Git and source control

**Dependency:** `CAP-GIT`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Never push, force-push, rebase, reset, clean, merge or discard without explicit scoped approval. Save redacted evidence for each completed item.

- [ ] **JF-0381** [P0] [Deps: `CAP-GIT`] Voice/chat: “Show the current status of git and source control and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0382** [P0] [Deps: `CAP-GIT`] Voice/chat: “Explain the current state of git and source control and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0383** [P0] [Deps: `CAP-GIT`] Voice/chat: “Compare the selected git and source control items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0384** [P0] [Deps: `CAP-GIT`] Voice/chat: “Find a user-specified item in git and source control within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0385** [P1] [Deps: `CAP-GIT`] Voice/chat: “Open the selected git and source control item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0386** [P1] [Deps: `CAP-GIT`] Voice/chat: “Create a draft git and source control item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0387** [P1] [Deps: `CAP-GIT`] Voice/chat: “Preview the requested git and source control change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0388** [P1] [Deps: `CAP-GIT`] Voice/chat: “Validate the requested git and source control action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0389** [P1] [Deps: `CAP-GIT`] Voice/chat: “Update the selected git and source control item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0390** [P1] [Deps: `CAP-GIT`] Voice/chat: “Undo the last reversible git and source control change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0391** [P1] [Deps: `CAP-GIT`] Voice/chat: “Schedule the requested git and source control action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0392** [P1] [Deps: `CAP-GIT`] Voice/chat: “Pause the selected running git and source control workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0393** [P2] [Deps: `CAP-GIT`] Voice/chat: “Resume the selected paused git and source control workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0394** [P2] [Deps: `CAP-GIT`] Voice/chat: “Cancel the selected git and source control operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0395** [P2] [Deps: `CAP-GIT`] Voice/chat: “Summarize recent git and source control activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0396** [P2] [Deps: `CAP-GIT`] Voice/chat: “Export selected git and source control data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0397** [P2] [Deps: `CAP-GIT`] Voice/chat: “Diagnose an git and source control failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0398** [P2] [Deps: `CAP-GIT`] Voice/chat: “Notify the user about a confirmed git and source control event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0399** [P3] [Deps: `CAP-GIT`] Voice/chat: “Configure a reversible git and source control preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0400** [P3] [Deps: `CAP-GIT`] Voice/chat: “Plan a multi-step git and source control request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 21. Builds and continuous integration

**Dependency:** `CAP-CI`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Run only configured commands in an isolated checkout; report actual logs and exit status. Save redacted evidence for each completed item.

- [ ] **JF-0401** [P1] [Deps: `CAP-CI`] Voice/chat: “Show the current status of builds and continuous integration and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0402** [P1] [Deps: `CAP-CI`] Voice/chat: “Explain the current state of builds and continuous integration and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0403** [P1] [Deps: `CAP-CI`] Voice/chat: “Compare the selected builds and continuous integration items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0404** [P1] [Deps: `CAP-CI`] Voice/chat: “Find a user-specified item in builds and continuous integration within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0405** [P1] [Deps: `CAP-CI`] Voice/chat: “Open the selected builds and continuous integration item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0406** [P1] [Deps: `CAP-CI`] Voice/chat: “Create a draft builds and continuous integration item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0407** [P1] [Deps: `CAP-CI`] Voice/chat: “Preview the requested builds and continuous integration change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0408** [P1] [Deps: `CAP-CI`] Voice/chat: “Validate the requested builds and continuous integration action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0409** [P1] [Deps: `CAP-CI`] Voice/chat: “Update the selected builds and continuous integration item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0410** [P1] [Deps: `CAP-CI`] Voice/chat: “Undo the last reversible builds and continuous integration change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0411** [P1] [Deps: `CAP-CI`] Voice/chat: “Schedule the requested builds and continuous integration action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0412** [P1] [Deps: `CAP-CI`] Voice/chat: “Pause the selected running builds and continuous integration workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0413** [P2] [Deps: `CAP-CI`] Voice/chat: “Resume the selected paused builds and continuous integration workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0414** [P2] [Deps: `CAP-CI`] Voice/chat: “Cancel the selected builds and continuous integration operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0415** [P2] [Deps: `CAP-CI`] Voice/chat: “Summarize recent builds and continuous integration activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0416** [P2] [Deps: `CAP-CI`] Voice/chat: “Export selected builds and continuous integration data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0417** [P2] [Deps: `CAP-CI`] Voice/chat: “Diagnose an builds and continuous integration failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0418** [P2] [Deps: `CAP-CI`] Voice/chat: “Notify the user about a confirmed builds and continuous integration event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0419** [P3] [Deps: `CAP-CI`] Voice/chat: “Configure a reversible builds and continuous integration preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0420** [P3] [Deps: `CAP-CI`] Voice/chat: “Plan a multi-step builds and continuous integration request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 22. Agent orchestration

**Dependency:** `CAP-AGENTS`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Use isolated worktrees for concurrent writers; agents inherit the same safety constraints. Save redacted evidence for each completed item.

- [ ] **JF-0421** [P1] [Deps: `CAP-AGENTS`] Voice/chat: “Show the current status of agent orchestration and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0422** [P1] [Deps: `CAP-AGENTS`] Voice/chat: “Explain the current state of agent orchestration and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0423** [P1] [Deps: `CAP-AGENTS`] Voice/chat: “Compare the selected agent orchestration items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0424** [P1] [Deps: `CAP-AGENTS`] Voice/chat: “Find a user-specified item in agent orchestration within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0425** [P1] [Deps: `CAP-AGENTS`] Voice/chat: “Open the selected agent orchestration item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0426** [P1] [Deps: `CAP-AGENTS`] Voice/chat: “Create a draft agent orchestration item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0427** [P1] [Deps: `CAP-AGENTS`] Voice/chat: “Preview the requested agent orchestration change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0428** [P1] [Deps: `CAP-AGENTS`] Voice/chat: “Validate the requested agent orchestration action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0429** [P1] [Deps: `CAP-AGENTS`] Voice/chat: “Update the selected agent orchestration item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0430** [P1] [Deps: `CAP-AGENTS`] Voice/chat: “Undo the last reversible agent orchestration change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0431** [P1] [Deps: `CAP-AGENTS`] Voice/chat: “Schedule the requested agent orchestration action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0432** [P1] [Deps: `CAP-AGENTS`] Voice/chat: “Pause the selected running agent orchestration workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0433** [P2] [Deps: `CAP-AGENTS`] Voice/chat: “Resume the selected paused agent orchestration workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0434** [P2] [Deps: `CAP-AGENTS`] Voice/chat: “Cancel the selected agent orchestration operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0435** [P2] [Deps: `CAP-AGENTS`] Voice/chat: “Summarize recent agent orchestration activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0436** [P2] [Deps: `CAP-AGENTS`] Voice/chat: “Export selected agent orchestration data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0437** [P2] [Deps: `CAP-AGENTS`] Voice/chat: “Diagnose an agent orchestration failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0438** [P2] [Deps: `CAP-AGENTS`] Voice/chat: “Notify the user about a confirmed agent orchestration event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0439** [P3] [Deps: `CAP-AGENTS`] Voice/chat: “Configure a reversible agent orchestration preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0440** [P3] [Deps: `CAP-AGENTS`] Voice/chat: “Plan a multi-step agent orchestration request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 23. AI model and provider routing

**Dependency:** `CAP-MODELS`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Use configured, available providers only; disclose provider/model and never invent success or quality. Save redacted evidence for each completed item.

- [ ] **JF-0441** [P1] [Deps: `CAP-MODELS`] Voice/chat: “Show the current status of ai model and provider routing and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0442** [P1] [Deps: `CAP-MODELS`] Voice/chat: “Explain the current state of ai model and provider routing and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0443** [P1] [Deps: `CAP-MODELS`] Voice/chat: “Compare the selected ai model and provider routing items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0444** [P1] [Deps: `CAP-MODELS`] Voice/chat: “Find a user-specified item in ai model and provider routing within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0445** [P1] [Deps: `CAP-MODELS`] Voice/chat: “Open the selected ai model and provider routing item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0446** [P1] [Deps: `CAP-MODELS`] Voice/chat: “Create a draft ai model and provider routing item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0447** [P1] [Deps: `CAP-MODELS`] Voice/chat: “Preview the requested ai model and provider routing change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0448** [P1] [Deps: `CAP-MODELS`] Voice/chat: “Validate the requested ai model and provider routing action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0449** [P1] [Deps: `CAP-MODELS`] Voice/chat: “Update the selected ai model and provider routing item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0450** [P1] [Deps: `CAP-MODELS`] Voice/chat: “Undo the last reversible ai model and provider routing change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0451** [P1] [Deps: `CAP-MODELS`] Voice/chat: “Schedule the requested ai model and provider routing action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0452** [P1] [Deps: `CAP-MODELS`] Voice/chat: “Pause the selected running ai model and provider routing workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0453** [P2] [Deps: `CAP-MODELS`] Voice/chat: “Resume the selected paused ai model and provider routing workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0454** [P2] [Deps: `CAP-MODELS`] Voice/chat: “Cancel the selected ai model and provider routing operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0455** [P2] [Deps: `CAP-MODELS`] Voice/chat: “Summarize recent ai model and provider routing activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0456** [P2] [Deps: `CAP-MODELS`] Voice/chat: “Export selected ai model and provider routing data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0457** [P2] [Deps: `CAP-MODELS`] Voice/chat: “Diagnose an ai model and provider routing failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0458** [P2] [Deps: `CAP-MODELS`] Voice/chat: “Notify the user about a confirmed ai model and provider routing event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0459** [P3] [Deps: `CAP-MODELS`] Voice/chat: “Configure a reversible ai model and provider routing preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0460** [P3] [Deps: `CAP-MODELS`] Voice/chat: “Plan a multi-step ai model and provider routing request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 24. Offline and degraded operation

**Dependency:** `CAP-OFFLINE`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Make offline limitations explicit; queue only safe actions and never claim they ran. Save redacted evidence for each completed item.

- [ ] **JF-0461** [P1] [Deps: `CAP-OFFLINE`] Voice/chat: “Show the current status of offline and degraded operation and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0462** [P1] [Deps: `CAP-OFFLINE`] Voice/chat: “Explain the current state of offline and degraded operation and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0463** [P1] [Deps: `CAP-OFFLINE`] Voice/chat: “Compare the selected offline and degraded operation items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0464** [P1] [Deps: `CAP-OFFLINE`] Voice/chat: “Find a user-specified item in offline and degraded operation within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0465** [P1] [Deps: `CAP-OFFLINE`] Voice/chat: “Open the selected offline and degraded operation item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0466** [P1] [Deps: `CAP-OFFLINE`] Voice/chat: “Create a draft offline and degraded operation item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0467** [P1] [Deps: `CAP-OFFLINE`] Voice/chat: “Preview the requested offline and degraded operation change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0468** [P1] [Deps: `CAP-OFFLINE`] Voice/chat: “Validate the requested offline and degraded operation action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0469** [P1] [Deps: `CAP-OFFLINE`] Voice/chat: “Update the selected offline and degraded operation item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0470** [P1] [Deps: `CAP-OFFLINE`] Voice/chat: “Undo the last reversible offline and degraded operation change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0471** [P1] [Deps: `CAP-OFFLINE`] Voice/chat: “Schedule the requested offline and degraded operation action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0472** [P1] [Deps: `CAP-OFFLINE`] Voice/chat: “Pause the selected running offline and degraded operation workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0473** [P2] [Deps: `CAP-OFFLINE`] Voice/chat: “Resume the selected paused offline and degraded operation workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0474** [P2] [Deps: `CAP-OFFLINE`] Voice/chat: “Cancel the selected offline and degraded operation operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0475** [P2] [Deps: `CAP-OFFLINE`] Voice/chat: “Summarize recent offline and degraded operation activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0476** [P2] [Deps: `CAP-OFFLINE`] Voice/chat: “Export selected offline and degraded operation data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0477** [P2] [Deps: `CAP-OFFLINE`] Voice/chat: “Diagnose an offline and degraded operation failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0478** [P2] [Deps: `CAP-OFFLINE`] Voice/chat: “Notify the user about a confirmed offline and degraded operation event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0479** [P3] [Deps: `CAP-OFFLINE`] Voice/chat: “Configure a reversible offline and degraded operation preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0480** [P3] [Deps: `CAP-OFFLINE`] Voice/chat: “Plan a multi-step offline and degraded operation request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 25. Document understanding

**Dependency:** `CAP-DOCS`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Treat imported documents as untrusted input; cite source locations and honor access controls. Save redacted evidence for each completed item.

- [ ] **JF-0481** [P1] [Deps: `CAP-DOCS`] Voice/chat: “Show the current status of document understanding and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0482** [P1] [Deps: `CAP-DOCS`] Voice/chat: “Explain the current state of document understanding and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0483** [P1] [Deps: `CAP-DOCS`] Voice/chat: “Compare the selected document understanding items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0484** [P1] [Deps: `CAP-DOCS`] Voice/chat: “Find a user-specified item in document understanding within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0485** [P1] [Deps: `CAP-DOCS`] Voice/chat: “Open the selected document understanding item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0486** [P1] [Deps: `CAP-DOCS`] Voice/chat: “Create a draft document understanding item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0487** [P1] [Deps: `CAP-DOCS`] Voice/chat: “Preview the requested document understanding change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0488** [P1] [Deps: `CAP-DOCS`] Voice/chat: “Validate the requested document understanding action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0489** [P1] [Deps: `CAP-DOCS`] Voice/chat: “Update the selected document understanding item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0490** [P1] [Deps: `CAP-DOCS`] Voice/chat: “Undo the last reversible document understanding change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0491** [P1] [Deps: `CAP-DOCS`] Voice/chat: “Schedule the requested document understanding action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0492** [P1] [Deps: `CAP-DOCS`] Voice/chat: “Pause the selected running document understanding workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0493** [P2] [Deps: `CAP-DOCS`] Voice/chat: “Resume the selected paused document understanding workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0494** [P2] [Deps: `CAP-DOCS`] Voice/chat: “Cancel the selected document understanding operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0495** [P2] [Deps: `CAP-DOCS`] Voice/chat: “Summarize recent document understanding activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0496** [P2] [Deps: `CAP-DOCS`] Voice/chat: “Export selected document understanding data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0497** [P2] [Deps: `CAP-DOCS`] Voice/chat: “Diagnose an document understanding failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0498** [P2] [Deps: `CAP-DOCS`] Voice/chat: “Notify the user about a confirmed document understanding event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0499** [P3] [Deps: `CAP-DOCS`] Voice/chat: “Configure a reversible document understanding preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0500** [P3] [Deps: `CAP-DOCS`] Voice/chat: “Plan a multi-step document understanding request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 26. Knowledge and research

**Dependency:** `CAP-KNOWLEDGE`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Separate retrieved evidence from inference; cite sources and identify stale or unavailable material. Save redacted evidence for each completed item.

- [ ] **JF-0501** [P1] [Deps: `CAP-KNOWLEDGE`] Voice/chat: “Show the current status of knowledge and research and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0502** [P1] [Deps: `CAP-KNOWLEDGE`] Voice/chat: “Explain the current state of knowledge and research and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0503** [P1] [Deps: `CAP-KNOWLEDGE`] Voice/chat: “Compare the selected knowledge and research items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0504** [P1] [Deps: `CAP-KNOWLEDGE`] Voice/chat: “Find a user-specified item in knowledge and research within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0505** [P1] [Deps: `CAP-KNOWLEDGE`] Voice/chat: “Open the selected knowledge and research item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0506** [P1] [Deps: `CAP-KNOWLEDGE`] Voice/chat: “Create a draft knowledge and research item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0507** [P1] [Deps: `CAP-KNOWLEDGE`] Voice/chat: “Preview the requested knowledge and research change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0508** [P1] [Deps: `CAP-KNOWLEDGE`] Voice/chat: “Validate the requested knowledge and research action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0509** [P1] [Deps: `CAP-KNOWLEDGE`] Voice/chat: “Update the selected knowledge and research item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0510** [P1] [Deps: `CAP-KNOWLEDGE`] Voice/chat: “Undo the last reversible knowledge and research change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0511** [P1] [Deps: `CAP-KNOWLEDGE`] Voice/chat: “Schedule the requested knowledge and research action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0512** [P1] [Deps: `CAP-KNOWLEDGE`] Voice/chat: “Pause the selected running knowledge and research workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0513** [P2] [Deps: `CAP-KNOWLEDGE`] Voice/chat: “Resume the selected paused knowledge and research workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0514** [P2] [Deps: `CAP-KNOWLEDGE`] Voice/chat: “Cancel the selected knowledge and research operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0515** [P2] [Deps: `CAP-KNOWLEDGE`] Voice/chat: “Summarize recent knowledge and research activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0516** [P2] [Deps: `CAP-KNOWLEDGE`] Voice/chat: “Export selected knowledge and research data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0517** [P2] [Deps: `CAP-KNOWLEDGE`] Voice/chat: “Diagnose an knowledge and research failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0518** [P2] [Deps: `CAP-KNOWLEDGE`] Voice/chat: “Notify the user about a confirmed knowledge and research event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0519** [P3] [Deps: `CAP-KNOWLEDGE`] Voice/chat: “Configure a reversible knowledge and research preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0520** [P3] [Deps: `CAP-KNOWLEDGE`] Voice/chat: “Plan a multi-step knowledge and research request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 27. Tasks and projects

**Dependency:** `CAP-TASKS`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Show owner, state and outcome from the real task store; destructive edits require approval. Save redacted evidence for each completed item.

- [ ] **JF-0521** [P1] [Deps: `CAP-TASKS`] Voice/chat: “Show the current status of tasks and projects and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0522** [P1] [Deps: `CAP-TASKS`] Voice/chat: “Explain the current state of tasks and projects and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0523** [P1] [Deps: `CAP-TASKS`] Voice/chat: “Compare the selected tasks and projects items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0524** [P1] [Deps: `CAP-TASKS`] Voice/chat: “Find a user-specified item in tasks and projects within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0525** [P1] [Deps: `CAP-TASKS`] Voice/chat: “Open the selected tasks and projects item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0526** [P1] [Deps: `CAP-TASKS`] Voice/chat: “Create a draft tasks and projects item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0527** [P1] [Deps: `CAP-TASKS`] Voice/chat: “Preview the requested tasks and projects change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0528** [P1] [Deps: `CAP-TASKS`] Voice/chat: “Validate the requested tasks and projects action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0529** [P1] [Deps: `CAP-TASKS`] Voice/chat: “Update the selected tasks and projects item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0530** [P1] [Deps: `CAP-TASKS`] Voice/chat: “Undo the last reversible tasks and projects change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0531** [P1] [Deps: `CAP-TASKS`] Voice/chat: “Schedule the requested tasks and projects action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0532** [P1] [Deps: `CAP-TASKS`] Voice/chat: “Pause the selected running tasks and projects workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0533** [P2] [Deps: `CAP-TASKS`] Voice/chat: “Resume the selected paused tasks and projects workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0534** [P2] [Deps: `CAP-TASKS`] Voice/chat: “Cancel the selected tasks and projects operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0535** [P2] [Deps: `CAP-TASKS`] Voice/chat: “Summarize recent tasks and projects activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0536** [P2] [Deps: `CAP-TASKS`] Voice/chat: “Export selected tasks and projects data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0537** [P2] [Deps: `CAP-TASKS`] Voice/chat: “Diagnose an tasks and projects failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0538** [P2] [Deps: `CAP-TASKS`] Voice/chat: “Notify the user about a confirmed tasks and projects event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0539** [P3] [Deps: `CAP-TASKS`] Voice/chat: “Configure a reversible tasks and projects preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0540** [P3] [Deps: `CAP-TASKS`] Voice/chat: “Plan a multi-step tasks and projects request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 28. Calendar and availability

**Dependency:** `CAP-CALENDAR`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Use the selected calendar and explicit time zone; confirm ambiguous dates before writing events. Save redacted evidence for each completed item.

- [ ] **JF-0541** [P1] [Deps: `CAP-CALENDAR`] Voice/chat: “Show the current status of calendar and availability and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0542** [P1] [Deps: `CAP-CALENDAR`] Voice/chat: “Explain the current state of calendar and availability and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0543** [P1] [Deps: `CAP-CALENDAR`] Voice/chat: “Compare the selected calendar and availability items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0544** [P1] [Deps: `CAP-CALENDAR`] Voice/chat: “Find a user-specified item in calendar and availability within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0545** [P1] [Deps: `CAP-CALENDAR`] Voice/chat: “Open the selected calendar and availability item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0546** [P1] [Deps: `CAP-CALENDAR`] Voice/chat: “Create a draft calendar and availability item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0547** [P1] [Deps: `CAP-CALENDAR`] Voice/chat: “Preview the requested calendar and availability change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0548** [P1] [Deps: `CAP-CALENDAR`] Voice/chat: “Validate the requested calendar and availability action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0549** [P1] [Deps: `CAP-CALENDAR`] Voice/chat: “Update the selected calendar and availability item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0550** [P1] [Deps: `CAP-CALENDAR`] Voice/chat: “Undo the last reversible calendar and availability change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0551** [P1] [Deps: `CAP-CALENDAR`] Voice/chat: “Schedule the requested calendar and availability action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0552** [P1] [Deps: `CAP-CALENDAR`] Voice/chat: “Pause the selected running calendar and availability workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0553** [P2] [Deps: `CAP-CALENDAR`] Voice/chat: “Resume the selected paused calendar and availability workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0554** [P2] [Deps: `CAP-CALENDAR`] Voice/chat: “Cancel the selected calendar and availability operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0555** [P2] [Deps: `CAP-CALENDAR`] Voice/chat: “Summarize recent calendar and availability activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0556** [P2] [Deps: `CAP-CALENDAR`] Voice/chat: “Export selected calendar and availability data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0557** [P2] [Deps: `CAP-CALENDAR`] Voice/chat: “Diagnose an calendar and availability failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0558** [P2] [Deps: `CAP-CALENDAR`] Voice/chat: “Notify the user about a confirmed calendar and availability event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0559** [P3] [Deps: `CAP-CALENDAR`] Voice/chat: “Configure a reversible calendar and availability preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0560** [P3] [Deps: `CAP-CALENDAR`] Voice/chat: “Plan a multi-step calendar and availability request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 29. Reminders and notifications

**Dependency:** `CAP-NOTIFY`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Confirm delivery channel and time; do not disclose sensitive content on shared outputs. Save redacted evidence for each completed item.

- [ ] **JF-0561** [P1] [Deps: `CAP-NOTIFY`] Voice/chat: “Show the current status of reminders and notifications and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0562** [P1] [Deps: `CAP-NOTIFY`] Voice/chat: “Explain the current state of reminders and notifications and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0563** [P1] [Deps: `CAP-NOTIFY`] Voice/chat: “Compare the selected reminders and notifications items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0564** [P1] [Deps: `CAP-NOTIFY`] Voice/chat: “Find a user-specified item in reminders and notifications within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0565** [P1] [Deps: `CAP-NOTIFY`] Voice/chat: “Open the selected reminders and notifications item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0566** [P1] [Deps: `CAP-NOTIFY`] Voice/chat: “Create a draft reminders and notifications item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0567** [P1] [Deps: `CAP-NOTIFY`] Voice/chat: “Preview the requested reminders and notifications change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0568** [P1] [Deps: `CAP-NOTIFY`] Voice/chat: “Validate the requested reminders and notifications action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0569** [P1] [Deps: `CAP-NOTIFY`] Voice/chat: “Update the selected reminders and notifications item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0570** [P1] [Deps: `CAP-NOTIFY`] Voice/chat: “Undo the last reversible reminders and notifications change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0571** [P1] [Deps: `CAP-NOTIFY`] Voice/chat: “Schedule the requested reminders and notifications action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0572** [P1] [Deps: `CAP-NOTIFY`] Voice/chat: “Pause the selected running reminders and notifications workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0573** [P2] [Deps: `CAP-NOTIFY`] Voice/chat: “Resume the selected paused reminders and notifications workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0574** [P2] [Deps: `CAP-NOTIFY`] Voice/chat: “Cancel the selected reminders and notifications operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0575** [P2] [Deps: `CAP-NOTIFY`] Voice/chat: “Summarize recent reminders and notifications activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0576** [P2] [Deps: `CAP-NOTIFY`] Voice/chat: “Export selected reminders and notifications data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0577** [P2] [Deps: `CAP-NOTIFY`] Voice/chat: “Diagnose an reminders and notifications failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0578** [P2] [Deps: `CAP-NOTIFY`] Voice/chat: “Notify the user about a confirmed reminders and notifications event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0579** [P3] [Deps: `CAP-NOTIFY`] Voice/chat: “Configure a reversible reminders and notifications preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0580** [P3] [Deps: `CAP-NOTIFY`] Voice/chat: “Plan a multi-step reminders and notifications request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 30. Automation and schedules

**Dependency:** `CAP-AUTOMATION`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Preview trigger, scope and effects; pause/disable quickly; external or destructive steps need approval. Save redacted evidence for each completed item.

- [ ] **JF-0581** [P1] [Deps: `CAP-AUTOMATION`] Voice/chat: “Show the current status of automation and schedules and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0582** [P1] [Deps: `CAP-AUTOMATION`] Voice/chat: “Explain the current state of automation and schedules and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0583** [P1] [Deps: `CAP-AUTOMATION`] Voice/chat: “Compare the selected automation and schedules items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0584** [P1] [Deps: `CAP-AUTOMATION`] Voice/chat: “Find a user-specified item in automation and schedules within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0585** [P1] [Deps: `CAP-AUTOMATION`] Voice/chat: “Open the selected automation and schedules item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0586** [P1] [Deps: `CAP-AUTOMATION`] Voice/chat: “Create a draft automation and schedules item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0587** [P1] [Deps: `CAP-AUTOMATION`] Voice/chat: “Preview the requested automation and schedules change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0588** [P1] [Deps: `CAP-AUTOMATION`] Voice/chat: “Validate the requested automation and schedules action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0589** [P1] [Deps: `CAP-AUTOMATION`] Voice/chat: “Update the selected automation and schedules item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0590** [P1] [Deps: `CAP-AUTOMATION`] Voice/chat: “Undo the last reversible automation and schedules change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0591** [P1] [Deps: `CAP-AUTOMATION`] Voice/chat: “Schedule the requested automation and schedules action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0592** [P1] [Deps: `CAP-AUTOMATION`] Voice/chat: “Pause the selected running automation and schedules workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0593** [P2] [Deps: `CAP-AUTOMATION`] Voice/chat: “Resume the selected paused automation and schedules workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0594** [P2] [Deps: `CAP-AUTOMATION`] Voice/chat: “Cancel the selected automation and schedules operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0595** [P2] [Deps: `CAP-AUTOMATION`] Voice/chat: “Summarize recent automation and schedules activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0596** [P2] [Deps: `CAP-AUTOMATION`] Voice/chat: “Export selected automation and schedules data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0597** [P2] [Deps: `CAP-AUTOMATION`] Voice/chat: “Diagnose an automation and schedules failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0598** [P2] [Deps: `CAP-AUTOMATION`] Voice/chat: “Notify the user about a confirmed automation and schedules event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0599** [P3] [Deps: `CAP-AUTOMATION`] Voice/chat: “Configure a reversible automation and schedules preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0600** [P3] [Deps: `CAP-AUTOMATION`] Voice/chat: “Plan a multi-step automation and schedules request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 31. Email and message drafts

**Dependency:** `CAP-MAIL`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Draft by default; sending requires explicit confirmation of recipients, content and account. Save redacted evidence for each completed item.

- [ ] **JF-0601** [P1] [Deps: `CAP-MAIL`] Voice/chat: “Show the current status of email and message drafts and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0602** [P1] [Deps: `CAP-MAIL`] Voice/chat: “Explain the current state of email and message drafts and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0603** [P1] [Deps: `CAP-MAIL`] Voice/chat: “Compare the selected email and message drafts items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0604** [P1] [Deps: `CAP-MAIL`] Voice/chat: “Find a user-specified item in email and message drafts within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0605** [P1] [Deps: `CAP-MAIL`] Voice/chat: “Open the selected email and message drafts item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0606** [P1] [Deps: `CAP-MAIL`] Voice/chat: “Create a draft email and message drafts item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0607** [P1] [Deps: `CAP-MAIL`] Voice/chat: “Preview the requested email and message drafts change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0608** [P1] [Deps: `CAP-MAIL`] Voice/chat: “Validate the requested email and message drafts action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0609** [P1] [Deps: `CAP-MAIL`] Voice/chat: “Update the selected email and message drafts item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0610** [P1] [Deps: `CAP-MAIL`] Voice/chat: “Undo the last reversible email and message drafts change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0611** [P1] [Deps: `CAP-MAIL`] Voice/chat: “Schedule the requested email and message drafts action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0612** [P1] [Deps: `CAP-MAIL`] Voice/chat: “Pause the selected running email and message drafts workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0613** [P2] [Deps: `CAP-MAIL`] Voice/chat: “Resume the selected paused email and message drafts workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0614** [P2] [Deps: `CAP-MAIL`] Voice/chat: “Cancel the selected email and message drafts operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0615** [P2] [Deps: `CAP-MAIL`] Voice/chat: “Summarize recent email and message drafts activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0616** [P2] [Deps: `CAP-MAIL`] Voice/chat: “Export selected email and message drafts data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0617** [P2] [Deps: `CAP-MAIL`] Voice/chat: “Diagnose an email and message drafts failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0618** [P2] [Deps: `CAP-MAIL`] Voice/chat: “Notify the user about a confirmed email and message drafts event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0619** [P3] [Deps: `CAP-MAIL`] Voice/chat: “Configure a reversible email and message drafts preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0620** [P3] [Deps: `CAP-MAIL`] Voice/chat: “Plan a multi-step email and message drafts request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 32. Contacts and address book

**Dependency:** `CAP-CONTACTS`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Return only fields needed for the request; edits and sharing require confirmation. Save redacted evidence for each completed item.

- [ ] **JF-0621** [P1] [Deps: `CAP-CONTACTS`] Voice/chat: “Show the current status of contacts and address book and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0622** [P1] [Deps: `CAP-CONTACTS`] Voice/chat: “Explain the current state of contacts and address book and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0623** [P1] [Deps: `CAP-CONTACTS`] Voice/chat: “Compare the selected contacts and address book items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0624** [P1] [Deps: `CAP-CONTACTS`] Voice/chat: “Find a user-specified item in contacts and address book within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0625** [P1] [Deps: `CAP-CONTACTS`] Voice/chat: “Open the selected contacts and address book item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0626** [P1] [Deps: `CAP-CONTACTS`] Voice/chat: “Create a draft contacts and address book item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0627** [P1] [Deps: `CAP-CONTACTS`] Voice/chat: “Preview the requested contacts and address book change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0628** [P1] [Deps: `CAP-CONTACTS`] Voice/chat: “Validate the requested contacts and address book action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0629** [P1] [Deps: `CAP-CONTACTS`] Voice/chat: “Update the selected contacts and address book item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0630** [P1] [Deps: `CAP-CONTACTS`] Voice/chat: “Undo the last reversible contacts and address book change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0631** [P1] [Deps: `CAP-CONTACTS`] Voice/chat: “Schedule the requested contacts and address book action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0632** [P1] [Deps: `CAP-CONTACTS`] Voice/chat: “Pause the selected running contacts and address book workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0633** [P2] [Deps: `CAP-CONTACTS`] Voice/chat: “Resume the selected paused contacts and address book workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0634** [P2] [Deps: `CAP-CONTACTS`] Voice/chat: “Cancel the selected contacts and address book operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0635** [P2] [Deps: `CAP-CONTACTS`] Voice/chat: “Summarize recent contacts and address book activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0636** [P2] [Deps: `CAP-CONTACTS`] Voice/chat: “Export selected contacts and address book data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0637** [P2] [Deps: `CAP-CONTACTS`] Voice/chat: “Diagnose an contacts and address book failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0638** [P2] [Deps: `CAP-CONTACTS`] Voice/chat: “Notify the user about a confirmed contacts and address book event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0639** [P3] [Deps: `CAP-CONTACTS`] Voice/chat: “Configure a reversible contacts and address book preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0640** [P3] [Deps: `CAP-CONTACTS`] Voice/chat: “Plan a multi-step contacts and address book request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 33. Notes and personal records

**Dependency:** `CAP-NOTES`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Keep data private, attributable and editable; confirm permanent deletion. Save redacted evidence for each completed item.

- [ ] **JF-0641** [P1] [Deps: `CAP-NOTES`] Voice/chat: “Show the current status of notes and personal records and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0642** [P1] [Deps: `CAP-NOTES`] Voice/chat: “Explain the current state of notes and personal records and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0643** [P1] [Deps: `CAP-NOTES`] Voice/chat: “Compare the selected notes and personal records items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0644** [P1] [Deps: `CAP-NOTES`] Voice/chat: “Find a user-specified item in notes and personal records within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0645** [P1] [Deps: `CAP-NOTES`] Voice/chat: “Open the selected notes and personal records item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0646** [P1] [Deps: `CAP-NOTES`] Voice/chat: “Create a draft notes and personal records item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0647** [P1] [Deps: `CAP-NOTES`] Voice/chat: “Preview the requested notes and personal records change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0648** [P1] [Deps: `CAP-NOTES`] Voice/chat: “Validate the requested notes and personal records action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0649** [P1] [Deps: `CAP-NOTES`] Voice/chat: “Update the selected notes and personal records item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0650** [P1] [Deps: `CAP-NOTES`] Voice/chat: “Undo the last reversible notes and personal records change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0651** [P1] [Deps: `CAP-NOTES`] Voice/chat: “Schedule the requested notes and personal records action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0652** [P1] [Deps: `CAP-NOTES`] Voice/chat: “Pause the selected running notes and personal records workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0653** [P2] [Deps: `CAP-NOTES`] Voice/chat: “Resume the selected paused notes and personal records workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0654** [P2] [Deps: `CAP-NOTES`] Voice/chat: “Cancel the selected notes and personal records operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0655** [P2] [Deps: `CAP-NOTES`] Voice/chat: “Summarize recent notes and personal records activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0656** [P2] [Deps: `CAP-NOTES`] Voice/chat: “Export selected notes and personal records data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0657** [P2] [Deps: `CAP-NOTES`] Voice/chat: “Diagnose an notes and personal records failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0658** [P2] [Deps: `CAP-NOTES`] Voice/chat: “Notify the user about a confirmed notes and personal records event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0659** [P3] [Deps: `CAP-NOTES`] Voice/chat: “Configure a reversible notes and personal records preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0660** [P3] [Deps: `CAP-NOTES`] Voice/chat: “Plan a multi-step notes and personal records request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 34. Personal routines and planning

**Dependency:** `CAP-PERSONAL`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Use only user-provided or authorized data; distinguish suggestions from actions taken. Save redacted evidence for each completed item.

- [ ] **JF-0661** [P1] [Deps: `CAP-PERSONAL`] Voice/chat: “Show the current status of personal routines and planning and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0662** [P1] [Deps: `CAP-PERSONAL`] Voice/chat: “Explain the current state of personal routines and planning and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0663** [P1] [Deps: `CAP-PERSONAL`] Voice/chat: “Compare the selected personal routines and planning items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0664** [P1] [Deps: `CAP-PERSONAL`] Voice/chat: “Find a user-specified item in personal routines and planning within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0665** [P1] [Deps: `CAP-PERSONAL`] Voice/chat: “Open the selected personal routines and planning item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0666** [P1] [Deps: `CAP-PERSONAL`] Voice/chat: “Create a draft personal routines and planning item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0667** [P1] [Deps: `CAP-PERSONAL`] Voice/chat: “Preview the requested personal routines and planning change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0668** [P1] [Deps: `CAP-PERSONAL`] Voice/chat: “Validate the requested personal routines and planning action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0669** [P1] [Deps: `CAP-PERSONAL`] Voice/chat: “Update the selected personal routines and planning item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0670** [P1] [Deps: `CAP-PERSONAL`] Voice/chat: “Undo the last reversible personal routines and planning change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0671** [P1] [Deps: `CAP-PERSONAL`] Voice/chat: “Schedule the requested personal routines and planning action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0672** [P1] [Deps: `CAP-PERSONAL`] Voice/chat: “Pause the selected running personal routines and planning workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0673** [P2] [Deps: `CAP-PERSONAL`] Voice/chat: “Resume the selected paused personal routines and planning workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0674** [P2] [Deps: `CAP-PERSONAL`] Voice/chat: “Cancel the selected personal routines and planning operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0675** [P2] [Deps: `CAP-PERSONAL`] Voice/chat: “Summarize recent personal routines and planning activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0676** [P2] [Deps: `CAP-PERSONAL`] Voice/chat: “Export selected personal routines and planning data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0677** [P2] [Deps: `CAP-PERSONAL`] Voice/chat: “Diagnose an personal routines and planning failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0678** [P2] [Deps: `CAP-PERSONAL`] Voice/chat: “Notify the user about a confirmed personal routines and planning event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0679** [P3] [Deps: `CAP-PERSONAL`] Voice/chat: “Configure a reversible personal routines and planning preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0680** [P3] [Deps: `CAP-PERSONAL`] Voice/chat: “Plan a multi-step personal routines and planning request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 35. Smart home controls

**Dependency:** `CAP-HOME`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Check device identity and current state; safety-critical or access-control changes require confirmation. Save redacted evidence for each completed item.

- [ ] **JF-0681** [P1] [Deps: `CAP-HOME`] Voice/chat: “Show the current status of smart home controls and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0682** [P1] [Deps: `CAP-HOME`] Voice/chat: “Explain the current state of smart home controls and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0683** [P1] [Deps: `CAP-HOME`] Voice/chat: “Compare the selected smart home controls items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0684** [P1] [Deps: `CAP-HOME`] Voice/chat: “Find a user-specified item in smart home controls within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0685** [P1] [Deps: `CAP-HOME`] Voice/chat: “Open the selected smart home controls item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0686** [P1] [Deps: `CAP-HOME`] Voice/chat: “Create a draft smart home controls item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0687** [P1] [Deps: `CAP-HOME`] Voice/chat: “Preview the requested smart home controls change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0688** [P1] [Deps: `CAP-HOME`] Voice/chat: “Validate the requested smart home controls action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0689** [P1] [Deps: `CAP-HOME`] Voice/chat: “Update the selected smart home controls item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0690** [P1] [Deps: `CAP-HOME`] Voice/chat: “Undo the last reversible smart home controls change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0691** [P1] [Deps: `CAP-HOME`] Voice/chat: “Schedule the requested smart home controls action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0692** [P1] [Deps: `CAP-HOME`] Voice/chat: “Pause the selected running smart home controls workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0693** [P2] [Deps: `CAP-HOME`] Voice/chat: “Resume the selected paused smart home controls workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0694** [P2] [Deps: `CAP-HOME`] Voice/chat: “Cancel the selected smart home controls operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0695** [P2] [Deps: `CAP-HOME`] Voice/chat: “Summarize recent smart home controls activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0696** [P2] [Deps: `CAP-HOME`] Voice/chat: “Export selected smart home controls data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0697** [P2] [Deps: `CAP-HOME`] Voice/chat: “Diagnose an smart home controls failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0698** [P2] [Deps: `CAP-HOME`] Voice/chat: “Notify the user about a confirmed smart home controls event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0699** [P3] [Deps: `CAP-HOME`] Voice/chat: “Configure a reversible smart home controls preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0700** [P3] [Deps: `CAP-HOME`] Voice/chat: “Plan a multi-step smart home controls request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 36. Sensors and environment

**Dependency:** `CAP-SENSORS`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Use the existing hardware owner; label simulated, stale, disconnected and measured readings distinctly. Save redacted evidence for each completed item.

- [ ] **JF-0701** [P1] [Deps: `CAP-SENSORS`] Voice/chat: “Show the current status of sensors and environment and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0702** [P1] [Deps: `CAP-SENSORS`] Voice/chat: “Explain the current state of sensors and environment and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0703** [P1] [Deps: `CAP-SENSORS`] Voice/chat: “Compare the selected sensors and environment items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0704** [P1] [Deps: `CAP-SENSORS`] Voice/chat: “Find a user-specified item in sensors and environment within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0705** [P1] [Deps: `CAP-SENSORS`] Voice/chat: “Open the selected sensors and environment item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0706** [P1] [Deps: `CAP-SENSORS`] Voice/chat: “Create a draft sensors and environment item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0707** [P1] [Deps: `CAP-SENSORS`] Voice/chat: “Preview the requested sensors and environment change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0708** [P1] [Deps: `CAP-SENSORS`] Voice/chat: “Validate the requested sensors and environment action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0709** [P1] [Deps: `CAP-SENSORS`] Voice/chat: “Update the selected sensors and environment item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0710** [P1] [Deps: `CAP-SENSORS`] Voice/chat: “Undo the last reversible sensors and environment change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0711** [P1] [Deps: `CAP-SENSORS`] Voice/chat: “Schedule the requested sensors and environment action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0712** [P1] [Deps: `CAP-SENSORS`] Voice/chat: “Pause the selected running sensors and environment workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0713** [P2] [Deps: `CAP-SENSORS`] Voice/chat: “Resume the selected paused sensors and environment workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0714** [P2] [Deps: `CAP-SENSORS`] Voice/chat: “Cancel the selected sensors and environment operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0715** [P2] [Deps: `CAP-SENSORS`] Voice/chat: “Summarize recent sensors and environment activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0716** [P2] [Deps: `CAP-SENSORS`] Voice/chat: “Export selected sensors and environment data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0717** [P2] [Deps: `CAP-SENSORS`] Voice/chat: “Diagnose an sensors and environment failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0718** [P2] [Deps: `CAP-SENSORS`] Voice/chat: “Notify the user about a confirmed sensors and environment event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0719** [P3] [Deps: `CAP-SENSORS`] Voice/chat: “Configure a reversible sensors and environment preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0720** [P3] [Deps: `CAP-SENSORS`] Voice/chat: “Plan a multi-step sensors and environment request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 37. Robot simulation and safety

**Dependency:** `CAP-ROBOT-SIM`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Plan and test in simulation only; never dispatch real motion from this roadmap execution. Save redacted evidence for each completed item.

- [ ] **JF-0721** [P1] [Deps: `CAP-ROBOT-SIM`] Voice/chat: “Show the current status of robot simulation and safety and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0722** [P1] [Deps: `CAP-ROBOT-SIM`] Voice/chat: “Explain the current state of robot simulation and safety and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0723** [P1] [Deps: `CAP-ROBOT-SIM`] Voice/chat: “Compare the selected robot simulation and safety items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0724** [P1] [Deps: `CAP-ROBOT-SIM`] Voice/chat: “Find a user-specified item in robot simulation and safety within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0725** [P1] [Deps: `CAP-ROBOT-SIM`] Voice/chat: “Open the selected robot simulation and safety item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0726** [P1] [Deps: `CAP-ROBOT-SIM`] Voice/chat: “Create a draft robot simulation and safety item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0727** [P1] [Deps: `CAP-ROBOT-SIM`] Voice/chat: “Preview the requested robot simulation and safety change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0728** [P1] [Deps: `CAP-ROBOT-SIM`] Voice/chat: “Validate the requested robot simulation and safety action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0729** [P1] [Deps: `CAP-ROBOT-SIM`] Voice/chat: “Update the selected robot simulation and safety item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0730** [P1] [Deps: `CAP-ROBOT-SIM`] Voice/chat: “Undo the last reversible robot simulation and safety change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0731** [P1] [Deps: `CAP-ROBOT-SIM`] Voice/chat: “Schedule the requested robot simulation and safety action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0732** [P1] [Deps: `CAP-ROBOT-SIM`] Voice/chat: “Pause the selected running robot simulation and safety workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0733** [P2] [Deps: `CAP-ROBOT-SIM`] Voice/chat: “Resume the selected paused robot simulation and safety workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0734** [P2] [Deps: `CAP-ROBOT-SIM`] Voice/chat: “Cancel the selected robot simulation and safety operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0735** [P2] [Deps: `CAP-ROBOT-SIM`] Voice/chat: “Summarize recent robot simulation and safety activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0736** [P2] [Deps: `CAP-ROBOT-SIM`] Voice/chat: “Export selected robot simulation and safety data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0737** [P2] [Deps: `CAP-ROBOT-SIM`] Voice/chat: “Diagnose an robot simulation and safety failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0738** [P2] [Deps: `CAP-ROBOT-SIM`] Voice/chat: “Notify the user about a confirmed robot simulation and safety event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0739** [P3] [Deps: `CAP-ROBOT-SIM`] Voice/chat: “Configure a reversible robot simulation and safety preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0740** [P3] [Deps: `CAP-ROBOT-SIM`] Voice/chat: “Plan a multi-step robot simulation and safety request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 38. Camera and visual input

**Dependency:** `CAP-CAMERA`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Use the established camera owner and explicit capture indicator; do not retain images without authorization. Save redacted evidence for each completed item.

- [ ] **JF-0741** [P1] [Deps: `CAP-CAMERA`] Voice/chat: “Show the current status of camera and visual input and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0742** [P1] [Deps: `CAP-CAMERA`] Voice/chat: “Explain the current state of camera and visual input and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0743** [P1] [Deps: `CAP-CAMERA`] Voice/chat: “Compare the selected camera and visual input items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0744** [P1] [Deps: `CAP-CAMERA`] Voice/chat: “Find a user-specified item in camera and visual input within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0745** [P1] [Deps: `CAP-CAMERA`] Voice/chat: “Open the selected camera and visual input item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0746** [P1] [Deps: `CAP-CAMERA`] Voice/chat: “Create a draft camera and visual input item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0747** [P1] [Deps: `CAP-CAMERA`] Voice/chat: “Preview the requested camera and visual input change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0748** [P1] [Deps: `CAP-CAMERA`] Voice/chat: “Validate the requested camera and visual input action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0749** [P1] [Deps: `CAP-CAMERA`] Voice/chat: “Update the selected camera and visual input item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0750** [P1] [Deps: `CAP-CAMERA`] Voice/chat: “Undo the last reversible camera and visual input change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0751** [P1] [Deps: `CAP-CAMERA`] Voice/chat: “Schedule the requested camera and visual input action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0752** [P1] [Deps: `CAP-CAMERA`] Voice/chat: “Pause the selected running camera and visual input workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0753** [P2] [Deps: `CAP-CAMERA`] Voice/chat: “Resume the selected paused camera and visual input workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0754** [P2] [Deps: `CAP-CAMERA`] Voice/chat: “Cancel the selected camera and visual input operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0755** [P2] [Deps: `CAP-CAMERA`] Voice/chat: “Summarize recent camera and visual input activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0756** [P2] [Deps: `CAP-CAMERA`] Voice/chat: “Export selected camera and visual input data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0757** [P2] [Deps: `CAP-CAMERA`] Voice/chat: “Diagnose an camera and visual input failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0758** [P2] [Deps: `CAP-CAMERA`] Voice/chat: “Notify the user about a confirmed camera and visual input event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0759** [P3] [Deps: `CAP-CAMERA`] Voice/chat: “Configure a reversible camera and visual input preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0760** [P3] [Deps: `CAP-CAMERA`] Voice/chat: “Plan a multi-step camera and visual input request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 39. Audio devices and media

**Dependency:** `CAP-AUDIO`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Use the selected output/input device and a single owner; do not record or play sensitive media unexpectedly. Save redacted evidence for each completed item.

- [ ] **JF-0761** [P1] [Deps: `CAP-AUDIO`] Voice/chat: “Show the current status of audio devices and media and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0762** [P1] [Deps: `CAP-AUDIO`] Voice/chat: “Explain the current state of audio devices and media and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0763** [P1] [Deps: `CAP-AUDIO`] Voice/chat: “Compare the selected audio devices and media items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0764** [P1] [Deps: `CAP-AUDIO`] Voice/chat: “Find a user-specified item in audio devices and media within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0765** [P1] [Deps: `CAP-AUDIO`] Voice/chat: “Open the selected audio devices and media item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0766** [P1] [Deps: `CAP-AUDIO`] Voice/chat: “Create a draft audio devices and media item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0767** [P1] [Deps: `CAP-AUDIO`] Voice/chat: “Preview the requested audio devices and media change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0768** [P1] [Deps: `CAP-AUDIO`] Voice/chat: “Validate the requested audio devices and media action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0769** [P1] [Deps: `CAP-AUDIO`] Voice/chat: “Update the selected audio devices and media item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0770** [P1] [Deps: `CAP-AUDIO`] Voice/chat: “Undo the last reversible audio devices and media change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0771** [P1] [Deps: `CAP-AUDIO`] Voice/chat: “Schedule the requested audio devices and media action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0772** [P1] [Deps: `CAP-AUDIO`] Voice/chat: “Pause the selected running audio devices and media workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0773** [P2] [Deps: `CAP-AUDIO`] Voice/chat: “Resume the selected paused audio devices and media workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0774** [P2] [Deps: `CAP-AUDIO`] Voice/chat: “Cancel the selected audio devices and media operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0775** [P2] [Deps: `CAP-AUDIO`] Voice/chat: “Summarize recent audio devices and media activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0776** [P2] [Deps: `CAP-AUDIO`] Voice/chat: “Export selected audio devices and media data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0777** [P2] [Deps: `CAP-AUDIO`] Voice/chat: “Diagnose an audio devices and media failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0778** [P2] [Deps: `CAP-AUDIO`] Voice/chat: “Notify the user about a confirmed audio devices and media event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0779** [P3] [Deps: `CAP-AUDIO`] Voice/chat: “Configure a reversible audio devices and media preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0780** [P3] [Deps: `CAP-AUDIO`] Voice/chat: “Plan a multi-step audio devices and media request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 40. Cross-device notifications

**Dependency:** `CAP-DEVICES`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Pair devices explicitly, authenticate each target and disclose which device receives information. Save redacted evidence for each completed item.

- [ ] **JF-0781** [P1] [Deps: `CAP-DEVICES`] Voice/chat: “Show the current status of cross-device notifications and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0782** [P1] [Deps: `CAP-DEVICES`] Voice/chat: “Explain the current state of cross-device notifications and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0783** [P1] [Deps: `CAP-DEVICES`] Voice/chat: “Compare the selected cross-device notifications items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0784** [P1] [Deps: `CAP-DEVICES`] Voice/chat: “Find a user-specified item in cross-device notifications within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0785** [P1] [Deps: `CAP-DEVICES`] Voice/chat: “Open the selected cross-device notifications item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0786** [P1] [Deps: `CAP-DEVICES`] Voice/chat: “Create a draft cross-device notifications item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0787** [P1] [Deps: `CAP-DEVICES`] Voice/chat: “Preview the requested cross-device notifications change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0788** [P1] [Deps: `CAP-DEVICES`] Voice/chat: “Validate the requested cross-device notifications action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0789** [P1] [Deps: `CAP-DEVICES`] Voice/chat: “Update the selected cross-device notifications item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0790** [P1] [Deps: `CAP-DEVICES`] Voice/chat: “Undo the last reversible cross-device notifications change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0791** [P1] [Deps: `CAP-DEVICES`] Voice/chat: “Schedule the requested cross-device notifications action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0792** [P1] [Deps: `CAP-DEVICES`] Voice/chat: “Pause the selected running cross-device notifications workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0793** [P2] [Deps: `CAP-DEVICES`] Voice/chat: “Resume the selected paused cross-device notifications workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0794** [P2] [Deps: `CAP-DEVICES`] Voice/chat: “Cancel the selected cross-device notifications operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0795** [P2] [Deps: `CAP-DEVICES`] Voice/chat: “Summarize recent cross-device notifications activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0796** [P2] [Deps: `CAP-DEVICES`] Voice/chat: “Export selected cross-device notifications data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0797** [P2] [Deps: `CAP-DEVICES`] Voice/chat: “Diagnose an cross-device notifications failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0798** [P2] [Deps: `CAP-DEVICES`] Voice/chat: “Notify the user about a confirmed cross-device notifications event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0799** [P3] [Deps: `CAP-DEVICES`] Voice/chat: “Configure a reversible cross-device notifications preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0800** [P3] [Deps: `CAP-DEVICES`] Voice/chat: “Plan a multi-step cross-device notifications request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 41. Privacy and data controls

**Dependency:** `CAP-PRIVACY`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Apply data minimization, retention choices and visible capture indicators; never export secrets. Save redacted evidence for each completed item.

- [ ] **JF-0801** [P1] [Deps: `CAP-PRIVACY`] Voice/chat: “Show the current status of privacy and data controls and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0802** [P1] [Deps: `CAP-PRIVACY`] Voice/chat: “Explain the current state of privacy and data controls and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0803** [P1] [Deps: `CAP-PRIVACY`] Voice/chat: “Compare the selected privacy and data controls items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0804** [P1] [Deps: `CAP-PRIVACY`] Voice/chat: “Find a user-specified item in privacy and data controls within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0805** [P1] [Deps: `CAP-PRIVACY`] Voice/chat: “Open the selected privacy and data controls item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0806** [P1] [Deps: `CAP-PRIVACY`] Voice/chat: “Create a draft privacy and data controls item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0807** [P1] [Deps: `CAP-PRIVACY`] Voice/chat: “Preview the requested privacy and data controls change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0808** [P1] [Deps: `CAP-PRIVACY`] Voice/chat: “Validate the requested privacy and data controls action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0809** [P1] [Deps: `CAP-PRIVACY`] Voice/chat: “Update the selected privacy and data controls item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0810** [P1] [Deps: `CAP-PRIVACY`] Voice/chat: “Undo the last reversible privacy and data controls change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0811** [P1] [Deps: `CAP-PRIVACY`] Voice/chat: “Schedule the requested privacy and data controls action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0812** [P1] [Deps: `CAP-PRIVACY`] Voice/chat: “Pause the selected running privacy and data controls workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0813** [P2] [Deps: `CAP-PRIVACY`] Voice/chat: “Resume the selected paused privacy and data controls workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0814** [P2] [Deps: `CAP-PRIVACY`] Voice/chat: “Cancel the selected privacy and data controls operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0815** [P2] [Deps: `CAP-PRIVACY`] Voice/chat: “Summarize recent privacy and data controls activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0816** [P2] [Deps: `CAP-PRIVACY`] Voice/chat: “Export selected privacy and data controls data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0817** [P2] [Deps: `CAP-PRIVACY`] Voice/chat: “Diagnose an privacy and data controls failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0818** [P2] [Deps: `CAP-PRIVACY`] Voice/chat: “Notify the user about a confirmed privacy and data controls event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0819** [P3] [Deps: `CAP-PRIVACY`] Voice/chat: “Configure a reversible privacy and data controls preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0820** [P3] [Deps: `CAP-PRIVACY`] Voice/chat: “Plan a multi-step privacy and data controls request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 42. Backup and recovery

**Dependency:** `CAP-BACKUP`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Verify destination, scope and restore point; never overwrite the only copy without approval. Save redacted evidence for each completed item.

- [ ] **JF-0821** [P1] [Deps: `CAP-BACKUP`] Voice/chat: “Show the current status of backup and recovery and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0822** [P1] [Deps: `CAP-BACKUP`] Voice/chat: “Explain the current state of backup and recovery and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0823** [P1] [Deps: `CAP-BACKUP`] Voice/chat: “Compare the selected backup and recovery items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0824** [P1] [Deps: `CAP-BACKUP`] Voice/chat: “Find a user-specified item in backup and recovery within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0825** [P1] [Deps: `CAP-BACKUP`] Voice/chat: “Open the selected backup and recovery item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0826** [P1] [Deps: `CAP-BACKUP`] Voice/chat: “Create a draft backup and recovery item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0827** [P1] [Deps: `CAP-BACKUP`] Voice/chat: “Preview the requested backup and recovery change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0828** [P1] [Deps: `CAP-BACKUP`] Voice/chat: “Validate the requested backup and recovery action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0829** [P1] [Deps: `CAP-BACKUP`] Voice/chat: “Update the selected backup and recovery item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0830** [P1] [Deps: `CAP-BACKUP`] Voice/chat: “Undo the last reversible backup and recovery change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0831** [P1] [Deps: `CAP-BACKUP`] Voice/chat: “Schedule the requested backup and recovery action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0832** [P1] [Deps: `CAP-BACKUP`] Voice/chat: “Pause the selected running backup and recovery workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0833** [P2] [Deps: `CAP-BACKUP`] Voice/chat: “Resume the selected paused backup and recovery workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0834** [P2] [Deps: `CAP-BACKUP`] Voice/chat: “Cancel the selected backup and recovery operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0835** [P2] [Deps: `CAP-BACKUP`] Voice/chat: “Summarize recent backup and recovery activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0836** [P2] [Deps: `CAP-BACKUP`] Voice/chat: “Export selected backup and recovery data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0837** [P2] [Deps: `CAP-BACKUP`] Voice/chat: “Diagnose an backup and recovery failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0838** [P2] [Deps: `CAP-BACKUP`] Voice/chat: “Notify the user about a confirmed backup and recovery event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0839** [P3] [Deps: `CAP-BACKUP`] Voice/chat: “Configure a reversible backup and recovery preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0840** [P3] [Deps: `CAP-BACKUP`] Voice/chat: “Plan a multi-step backup and recovery request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 43. Network and connectivity

**Dependency:** `CAP-NETWORK`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Read network state safely; do not expose services or change firewall/router settings without approval. Save redacted evidence for each completed item.

- [ ] **JF-0841** [P1] [Deps: `CAP-NETWORK`] Voice/chat: “Show the current status of network and connectivity and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0842** [P1] [Deps: `CAP-NETWORK`] Voice/chat: “Explain the current state of network and connectivity and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0843** [P1] [Deps: `CAP-NETWORK`] Voice/chat: “Compare the selected network and connectivity items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0844** [P1] [Deps: `CAP-NETWORK`] Voice/chat: “Find a user-specified item in network and connectivity within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0845** [P1] [Deps: `CAP-NETWORK`] Voice/chat: “Open the selected network and connectivity item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0846** [P1] [Deps: `CAP-NETWORK`] Voice/chat: “Create a draft network and connectivity item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0847** [P1] [Deps: `CAP-NETWORK`] Voice/chat: “Preview the requested network and connectivity change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0848** [P1] [Deps: `CAP-NETWORK`] Voice/chat: “Validate the requested network and connectivity action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0849** [P1] [Deps: `CAP-NETWORK`] Voice/chat: “Update the selected network and connectivity item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0850** [P1] [Deps: `CAP-NETWORK`] Voice/chat: “Undo the last reversible network and connectivity change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0851** [P1] [Deps: `CAP-NETWORK`] Voice/chat: “Schedule the requested network and connectivity action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0852** [P1] [Deps: `CAP-NETWORK`] Voice/chat: “Pause the selected running network and connectivity workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0853** [P2] [Deps: `CAP-NETWORK`] Voice/chat: “Resume the selected paused network and connectivity workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0854** [P2] [Deps: `CAP-NETWORK`] Voice/chat: “Cancel the selected network and connectivity operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0855** [P2] [Deps: `CAP-NETWORK`] Voice/chat: “Summarize recent network and connectivity activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0856** [P2] [Deps: `CAP-NETWORK`] Voice/chat: “Export selected network and connectivity data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0857** [P2] [Deps: `CAP-NETWORK`] Voice/chat: “Diagnose an network and connectivity failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0858** [P2] [Deps: `CAP-NETWORK`] Voice/chat: “Notify the user about a confirmed network and connectivity event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0859** [P3] [Deps: `CAP-NETWORK`] Voice/chat: “Configure a reversible network and connectivity preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0860** [P3] [Deps: `CAP-NETWORK`] Voice/chat: “Plan a multi-step network and connectivity request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 44. Printers and peripherals

**Dependency:** `CAP-PERIPHERALS`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Verify target device and job content; confirm before printing or sharing sensitive documents. Save redacted evidence for each completed item.

- [ ] **JF-0861** [P1] [Deps: `CAP-PERIPHERALS`] Voice/chat: “Show the current status of printers and peripherals and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0862** [P1] [Deps: `CAP-PERIPHERALS`] Voice/chat: “Explain the current state of printers and peripherals and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0863** [P1] [Deps: `CAP-PERIPHERALS`] Voice/chat: “Compare the selected printers and peripherals items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0864** [P1] [Deps: `CAP-PERIPHERALS`] Voice/chat: “Find a user-specified item in printers and peripherals within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0865** [P1] [Deps: `CAP-PERIPHERALS`] Voice/chat: “Open the selected printers and peripherals item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0866** [P1] [Deps: `CAP-PERIPHERALS`] Voice/chat: “Create a draft printers and peripherals item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0867** [P1] [Deps: `CAP-PERIPHERALS`] Voice/chat: “Preview the requested printers and peripherals change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0868** [P1] [Deps: `CAP-PERIPHERALS`] Voice/chat: “Validate the requested printers and peripherals action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0869** [P1] [Deps: `CAP-PERIPHERALS`] Voice/chat: “Update the selected printers and peripherals item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0870** [P1] [Deps: `CAP-PERIPHERALS`] Voice/chat: “Undo the last reversible printers and peripherals change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0871** [P1] [Deps: `CAP-PERIPHERALS`] Voice/chat: “Schedule the requested printers and peripherals action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0872** [P1] [Deps: `CAP-PERIPHERALS`] Voice/chat: “Pause the selected running printers and peripherals workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0873** [P2] [Deps: `CAP-PERIPHERALS`] Voice/chat: “Resume the selected paused printers and peripherals workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0874** [P2] [Deps: `CAP-PERIPHERALS`] Voice/chat: “Cancel the selected printers and peripherals operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0875** [P2] [Deps: `CAP-PERIPHERALS`] Voice/chat: “Summarize recent printers and peripherals activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0876** [P2] [Deps: `CAP-PERIPHERALS`] Voice/chat: “Export selected printers and peripherals data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0877** [P2] [Deps: `CAP-PERIPHERALS`] Voice/chat: “Diagnose an printers and peripherals failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0878** [P2] [Deps: `CAP-PERIPHERALS`] Voice/chat: “Notify the user about a confirmed printers and peripherals event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0879** [P3] [Deps: `CAP-PERIPHERALS`] Voice/chat: “Configure a reversible printers and peripherals preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0880** [P3] [Deps: `CAP-PERIPHERALS`] Voice/chat: “Plan a multi-step printers and peripherals request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 45. Software inventory and installation

**Dependency:** `CAP-PACKAGES`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Inventory is read-only; installation/removal and privileged package actions require scoped approval. Save redacted evidence for each completed item.

- [ ] **JF-0881** [P1] [Deps: `CAP-PACKAGES`] Voice/chat: “Show the current status of software inventory and installation and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0882** [P1] [Deps: `CAP-PACKAGES`] Voice/chat: “Explain the current state of software inventory and installation and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0883** [P1] [Deps: `CAP-PACKAGES`] Voice/chat: “Compare the selected software inventory and installation items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0884** [P1] [Deps: `CAP-PACKAGES`] Voice/chat: “Find a user-specified item in software inventory and installation within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0885** [P1] [Deps: `CAP-PACKAGES`] Voice/chat: “Open the selected software inventory and installation item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0886** [P1] [Deps: `CAP-PACKAGES`] Voice/chat: “Create a draft software inventory and installation item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0887** [P1] [Deps: `CAP-PACKAGES`] Voice/chat: “Preview the requested software inventory and installation change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0888** [P1] [Deps: `CAP-PACKAGES`] Voice/chat: “Validate the requested software inventory and installation action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0889** [P1] [Deps: `CAP-PACKAGES`] Voice/chat: “Update the selected software inventory and installation item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0890** [P1] [Deps: `CAP-PACKAGES`] Voice/chat: “Undo the last reversible software inventory and installation change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0891** [P1] [Deps: `CAP-PACKAGES`] Voice/chat: “Schedule the requested software inventory and installation action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0892** [P1] [Deps: `CAP-PACKAGES`] Voice/chat: “Pause the selected running software inventory and installation workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0893** [P2] [Deps: `CAP-PACKAGES`] Voice/chat: “Resume the selected paused software inventory and installation workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0894** [P2] [Deps: `CAP-PACKAGES`] Voice/chat: “Cancel the selected software inventory and installation operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0895** [P2] [Deps: `CAP-PACKAGES`] Voice/chat: “Summarize recent software inventory and installation activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0896** [P2] [Deps: `CAP-PACKAGES`] Voice/chat: “Export selected software inventory and installation data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0897** [P2] [Deps: `CAP-PACKAGES`] Voice/chat: “Diagnose an software inventory and installation failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0898** [P2] [Deps: `CAP-PACKAGES`] Voice/chat: “Notify the user about a confirmed software inventory and installation event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0899** [P3] [Deps: `CAP-PACKAGES`] Voice/chat: “Configure a reversible software inventory and installation preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0900** [P3] [Deps: `CAP-PACKAGES`] Voice/chat: “Plan a multi-step software inventory and installation request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 46. Updates and rollback

**Dependency:** `CAP-UPDATES`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Check signatures, compatibility and backups; stage changes and require confirmation before applying. Save redacted evidence for each completed item.

- [ ] **JF-0901** [P1] [Deps: `CAP-UPDATES`] Voice/chat: “Show the current status of updates and rollback and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0902** [P1] [Deps: `CAP-UPDATES`] Voice/chat: “Explain the current state of updates and rollback and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0903** [P1] [Deps: `CAP-UPDATES`] Voice/chat: “Compare the selected updates and rollback items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0904** [P1] [Deps: `CAP-UPDATES`] Voice/chat: “Find a user-specified item in updates and rollback within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0905** [P1] [Deps: `CAP-UPDATES`] Voice/chat: “Open the selected updates and rollback item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0906** [P1] [Deps: `CAP-UPDATES`] Voice/chat: “Create a draft updates and rollback item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0907** [P1] [Deps: `CAP-UPDATES`] Voice/chat: “Preview the requested updates and rollback change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0908** [P1] [Deps: `CAP-UPDATES`] Voice/chat: “Validate the requested updates and rollback action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0909** [P1] [Deps: `CAP-UPDATES`] Voice/chat: “Update the selected updates and rollback item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0910** [P1] [Deps: `CAP-UPDATES`] Voice/chat: “Undo the last reversible updates and rollback change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0911** [P1] [Deps: `CAP-UPDATES`] Voice/chat: “Schedule the requested updates and rollback action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0912** [P1] [Deps: `CAP-UPDATES`] Voice/chat: “Pause the selected running updates and rollback workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0913** [P2] [Deps: `CAP-UPDATES`] Voice/chat: “Resume the selected paused updates and rollback workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0914** [P2] [Deps: `CAP-UPDATES`] Voice/chat: “Cancel the selected updates and rollback operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0915** [P2] [Deps: `CAP-UPDATES`] Voice/chat: “Summarize recent updates and rollback activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0916** [P2] [Deps: `CAP-UPDATES`] Voice/chat: “Export selected updates and rollback data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0917** [P2] [Deps: `CAP-UPDATES`] Voice/chat: “Diagnose an updates and rollback failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0918** [P2] [Deps: `CAP-UPDATES`] Voice/chat: “Notify the user about a confirmed updates and rollback event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0919** [P3] [Deps: `CAP-UPDATES`] Voice/chat: “Configure a reversible updates and rollback preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0920** [P3] [Deps: `CAP-UPDATES`] Voice/chat: “Plan a multi-step updates and rollback request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 47. Logs and diagnostics

**Dependency:** `CAP-DIAGNOSTICS`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Redact secrets and personal content; diagnostics never silently change system configuration. Save redacted evidence for each completed item.

- [ ] **JF-0921** [P1] [Deps: `CAP-DIAGNOSTICS`] Voice/chat: “Show the current status of logs and diagnostics and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0922** [P1] [Deps: `CAP-DIAGNOSTICS`] Voice/chat: “Explain the current state of logs and diagnostics and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0923** [P1] [Deps: `CAP-DIAGNOSTICS`] Voice/chat: “Compare the selected logs and diagnostics items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0924** [P1] [Deps: `CAP-DIAGNOSTICS`] Voice/chat: “Find a user-specified item in logs and diagnostics within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0925** [P1] [Deps: `CAP-DIAGNOSTICS`] Voice/chat: “Open the selected logs and diagnostics item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0926** [P1] [Deps: `CAP-DIAGNOSTICS`] Voice/chat: “Create a draft logs and diagnostics item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0927** [P1] [Deps: `CAP-DIAGNOSTICS`] Voice/chat: “Preview the requested logs and diagnostics change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0928** [P1] [Deps: `CAP-DIAGNOSTICS`] Voice/chat: “Validate the requested logs and diagnostics action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0929** [P1] [Deps: `CAP-DIAGNOSTICS`] Voice/chat: “Update the selected logs and diagnostics item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0930** [P1] [Deps: `CAP-DIAGNOSTICS`] Voice/chat: “Undo the last reversible logs and diagnostics change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0931** [P1] [Deps: `CAP-DIAGNOSTICS`] Voice/chat: “Schedule the requested logs and diagnostics action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0932** [P1] [Deps: `CAP-DIAGNOSTICS`] Voice/chat: “Pause the selected running logs and diagnostics workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0933** [P2] [Deps: `CAP-DIAGNOSTICS`] Voice/chat: “Resume the selected paused logs and diagnostics workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0934** [P2] [Deps: `CAP-DIAGNOSTICS`] Voice/chat: “Cancel the selected logs and diagnostics operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0935** [P2] [Deps: `CAP-DIAGNOSTICS`] Voice/chat: “Summarize recent logs and diagnostics activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0936** [P2] [Deps: `CAP-DIAGNOSTICS`] Voice/chat: “Export selected logs and diagnostics data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0937** [P2] [Deps: `CAP-DIAGNOSTICS`] Voice/chat: “Diagnose an logs and diagnostics failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0938** [P2] [Deps: `CAP-DIAGNOSTICS`] Voice/chat: “Notify the user about a confirmed logs and diagnostics event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0939** [P3] [Deps: `CAP-DIAGNOSTICS`] Voice/chat: “Configure a reversible logs and diagnostics preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0940** [P3] [Deps: `CAP-DIAGNOSTICS`] Voice/chat: “Plan a multi-step logs and diagnostics request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 48. Health and performance

**Dependency:** `CAP-HEALTH`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Measure with named sources and timestamps; do not claim health from HTTP reachability alone. Save redacted evidence for each completed item.

- [ ] **JF-0941** [P1] [Deps: `CAP-HEALTH`] Voice/chat: “Show the current status of health and performance and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0942** [P1] [Deps: `CAP-HEALTH`] Voice/chat: “Explain the current state of health and performance and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0943** [P1] [Deps: `CAP-HEALTH`] Voice/chat: “Compare the selected health and performance items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0944** [P1] [Deps: `CAP-HEALTH`] Voice/chat: “Find a user-specified item in health and performance within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0945** [P1] [Deps: `CAP-HEALTH`] Voice/chat: “Open the selected health and performance item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0946** [P1] [Deps: `CAP-HEALTH`] Voice/chat: “Create a draft health and performance item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0947** [P1] [Deps: `CAP-HEALTH`] Voice/chat: “Preview the requested health and performance change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0948** [P1] [Deps: `CAP-HEALTH`] Voice/chat: “Validate the requested health and performance action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0949** [P1] [Deps: `CAP-HEALTH`] Voice/chat: “Update the selected health and performance item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0950** [P1] [Deps: `CAP-HEALTH`] Voice/chat: “Undo the last reversible health and performance change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0951** [P1] [Deps: `CAP-HEALTH`] Voice/chat: “Schedule the requested health and performance action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0952** [P1] [Deps: `CAP-HEALTH`] Voice/chat: “Pause the selected running health and performance workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0953** [P2] [Deps: `CAP-HEALTH`] Voice/chat: “Resume the selected paused health and performance workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0954** [P2] [Deps: `CAP-HEALTH`] Voice/chat: “Cancel the selected health and performance operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0955** [P2] [Deps: `CAP-HEALTH`] Voice/chat: “Summarize recent health and performance activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0956** [P2] [Deps: `CAP-HEALTH`] Voice/chat: “Export selected health and performance data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0957** [P2] [Deps: `CAP-HEALTH`] Voice/chat: “Diagnose an health and performance failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0958** [P2] [Deps: `CAP-HEALTH`] Voice/chat: “Notify the user about a confirmed health and performance event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0959** [P3] [Deps: `CAP-HEALTH`] Voice/chat: “Configure a reversible health and performance preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0960** [P3] [Deps: `CAP-HEALTH`] Voice/chat: “Plan a multi-step health and performance request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 49. Power and energy

**Dependency:** `CAP-POWER`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Report observed values; power-off, reboot and actuator changes require explicit confirmation. Save redacted evidence for each completed item.

- [ ] **JF-0961** [P1] [Deps: `CAP-POWER`] Voice/chat: “Show the current status of power and energy and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0962** [P1] [Deps: `CAP-POWER`] Voice/chat: “Explain the current state of power and energy and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0963** [P1] [Deps: `CAP-POWER`] Voice/chat: “Compare the selected power and energy items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0964** [P1] [Deps: `CAP-POWER`] Voice/chat: “Find a user-specified item in power and energy within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0965** [P1] [Deps: `CAP-POWER`] Voice/chat: “Open the selected power and energy item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0966** [P1] [Deps: `CAP-POWER`] Voice/chat: “Create a draft power and energy item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0967** [P1] [Deps: `CAP-POWER`] Voice/chat: “Preview the requested power and energy change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0968** [P1] [Deps: `CAP-POWER`] Voice/chat: “Validate the requested power and energy action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0969** [P1] [Deps: `CAP-POWER`] Voice/chat: “Update the selected power and energy item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0970** [P1] [Deps: `CAP-POWER`] Voice/chat: “Undo the last reversible power and energy change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0971** [P1] [Deps: `CAP-POWER`] Voice/chat: “Schedule the requested power and energy action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0972** [P1] [Deps: `CAP-POWER`] Voice/chat: “Pause the selected running power and energy workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0973** [P2] [Deps: `CAP-POWER`] Voice/chat: “Resume the selected paused power and energy workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0974** [P2] [Deps: `CAP-POWER`] Voice/chat: “Cancel the selected power and energy operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0975** [P2] [Deps: `CAP-POWER`] Voice/chat: “Summarize recent power and energy activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0976** [P2] [Deps: `CAP-POWER`] Voice/chat: “Export selected power and energy data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0977** [P2] [Deps: `CAP-POWER`] Voice/chat: “Diagnose an power and energy failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0978** [P2] [Deps: `CAP-POWER`] Voice/chat: “Notify the user about a confirmed power and energy event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0979** [P3] [Deps: `CAP-POWER`] Voice/chat: “Configure a reversible power and energy preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0980** [P3] [Deps: `CAP-POWER`] Voice/chat: “Plan a multi-step power and energy request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 50. Portability and synchronization

**Dependency:** `CAP-SYNC`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Keep the Pi and personal laptop trust zones separate; synchronize only selected paths and fields. Save redacted evidence for each completed item.

- [ ] **JF-0981** [P1] [Deps: `CAP-SYNC`] Voice/chat: “Show the current status of portability and synchronization and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0982** [P1] [Deps: `CAP-SYNC`] Voice/chat: “Explain the current state of portability and synchronization and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0983** [P1] [Deps: `CAP-SYNC`] Voice/chat: “Compare the selected portability and synchronization items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0984** [P1] [Deps: `CAP-SYNC`] Voice/chat: “Find a user-specified item in portability and synchronization within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0985** [P1] [Deps: `CAP-SYNC`] Voice/chat: “Open the selected portability and synchronization item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0986** [P1] [Deps: `CAP-SYNC`] Voice/chat: “Create a draft portability and synchronization item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0987** [P1] [Deps: `CAP-SYNC`] Voice/chat: “Preview the requested portability and synchronization change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0988** [P1] [Deps: `CAP-SYNC`] Voice/chat: “Validate the requested portability and synchronization action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0989** [P1] [Deps: `CAP-SYNC`] Voice/chat: “Update the selected portability and synchronization item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0990** [P1] [Deps: `CAP-SYNC`] Voice/chat: “Undo the last reversible portability and synchronization change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0991** [P1] [Deps: `CAP-SYNC`] Voice/chat: “Schedule the requested portability and synchronization action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0992** [P1] [Deps: `CAP-SYNC`] Voice/chat: “Pause the selected running portability and synchronization workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0993** [P2] [Deps: `CAP-SYNC`] Voice/chat: “Resume the selected paused portability and synchronization workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0994** [P2] [Deps: `CAP-SYNC`] Voice/chat: “Cancel the selected portability and synchronization operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0995** [P2] [Deps: `CAP-SYNC`] Voice/chat: “Summarize recent portability and synchronization activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0996** [P2] [Deps: `CAP-SYNC`] Voice/chat: “Export selected portability and synchronization data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0997** [P2] [Deps: `CAP-SYNC`] Voice/chat: “Diagnose an portability and synchronization failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0998** [P2] [Deps: `CAP-SYNC`] Voice/chat: “Notify the user about a confirmed portability and synchronization event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-0999** [P3] [Deps: `CAP-SYNC`] Voice/chat: “Configure a reversible portability and synchronization preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-1000** [P3] [Deps: `CAP-SYNC`] Voice/chat: “Plan a multi-step portability and synchronization request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.

### 51. Policy and administrator controls

**Dependency:** `CAP-POLICY`. **Domain acceptance gate:** execute each request via the applicable real adapter; assert correct target, scope and result; include denied, unavailable, timeout and cancellation cases where meaningful. Verify the boundary: Enforce backend policy and role checks; voice/chat cannot grant itself privileges or bypass denial. Save redacted evidence for each completed item.

- [ ] **JF-1001** [P1] [Deps: `CAP-POLICY`] Voice/chat: “Show the current status of policy and administrator controls and identify its source and timestamp.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-1002** [P1] [Deps: `CAP-POLICY`] Voice/chat: “Explain the current state of policy and administrator controls and distinguish observed facts from inference.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-1003** [P1] [Deps: `CAP-POLICY`] Voice/chat: “Compare the selected policy and administrator controls items and list the fields used in the comparison.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-1004** [P1] [Deps: `CAP-POLICY`] Voice/chat: “Find a user-specified item in policy and administrator controls within the authorized scope and return its location.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-1005** [P1] [Deps: `CAP-POLICY`] Voice/chat: “Open the selected policy and administrator controls item through its registered, authorized interface.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-1006** [P1] [Deps: `CAP-POLICY`] Voice/chat: “Create a draft policy and administrator controls item with the user’s stated fields and show a review preview.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-1007** [P1] [Deps: `CAP-POLICY`] Voice/chat: “Preview the requested policy and administrator controls change and enumerate affected objects before applying it.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-1008** [P1] [Deps: `CAP-POLICY`] Voice/chat: “Validate the requested policy and administrator controls action against permissions, available adapters and current state.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-1009** [P1] [Deps: `CAP-POLICY`] Voice/chat: “Update the selected policy and administrator controls item after showing the exact proposed before-and-after values.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-1010** [P1] [Deps: `CAP-POLICY`] Voice/chat: “Undo the last reversible policy and administrator controls change when a verified inverse operation is available.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-1011** [P1] [Deps: `CAP-POLICY`] Voice/chat: “Schedule the requested policy and administrator controls action using an explicit time zone and confirmed trigger.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-1012** [P1] [Deps: `CAP-POLICY`] Voice/chat: “Pause the selected running policy and administrator controls workflow and confirm the backend reports it paused.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-1013** [P2] [Deps: `CAP-POLICY`] Voice/chat: “Resume the selected paused policy and administrator controls workflow after checking its current inputs and permissions.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-1014** [P2] [Deps: `CAP-POLICY`] Voice/chat: “Cancel the selected policy and administrator controls operation and confirm cancellation from its authoritative owner.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-1015** [P2] [Deps: `CAP-POLICY`] Voice/chat: “Summarize recent policy and administrator controls activity with links or identifiers for the underlying records.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-1016** [P2] [Deps: `CAP-POLICY`] Voice/chat: “Export selected policy and administrator controls data to a user-chosen destination after previewing scope and format.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-1017** [P2] [Deps: `CAP-POLICY`] Voice/chat: “Diagnose an policy and administrator controls failure using redacted logs and return evidence-backed next steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-1018** [P2] [Deps: `CAP-POLICY`] Voice/chat: “Notify the user about a confirmed policy and administrator controls event through the explicitly selected channel.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-1019** [P3] [Deps: `CAP-POLICY`] Voice/chat: “Configure a reversible policy and administrator controls preference and report whether the setting was persisted.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.
- [ ] **JF-1020** [P3] [Deps: `CAP-POLICY`] Voice/chat: “Plan a multi-step policy and administrator controls request, list dependencies and approvals, then wait before consequential steps.” Acceptance: correct intent and scope, real owner confirms the outcome, and denial/unavailable paths leave no side effect; evidence linked in the completion ledger.


## Reconciliation checkpoint · 22 November 2026

- Imported PLAN2, FEATURES2, PROMPT2 and Documents-source supplemental requirements without renumbering. Source snapshots/hashes: docs/jarvis-execution/imports/2026-11-22/.
- Added offline plan checker and mirrored-main sync. Checks reject duplicate IDs, stale status, evidence-free completion and missing/outside evidence paths. Suggestions are not a dependency solver or execution authorization.
- Continued JRV-0539 prerequisite: absent/invalid target asks for visible account label before observation or input. Duplicate-label disambiguation and actual selection remain open.
- 51 focused tests passed in 2.37s; git diff --check passed. Evidence: docs/jarvis-execution/evidence/2026-11-22-plan-merge/verification.json.
- No UI gates passed, live feature checked, service deployed or database modified. No paid/provider/device calls.
- Next: inspect existing observation adapters for account candidates and stable targets; continue JRV-0539 then JRV-0527–JRV-0530. Preserve the existing uncommitted source changes.

## Account observation checkpoint · 22 November 2026

- Added managed-browser read-only `list_youtube_accounts` and `resolve_youtube_account`; explicit scope prevents mistaking this for desktop Chrome. No session started automatically.
- Narrow visible account-item extraction rejects unsupported origins/invalid data. Duplicate exact labels require clarification; a unique match never implies active-account verification.
- Natural language examples: `Jarvis, list YouTube accounts`; `resolve YouTube account named "Work Team"`. Existing chat/voice router and dispatcher route to the same backend.
- Focused regressions: 76 passed in 5.90s, including isolated Chromium fixture DOM extraction, existing account guards and router regressions. No live YouTube or native input.
- Evidence: docs/jarvis-execution/evidence/2026-11-22-account-observation/verification.json. No checkboxes completed; no UI phase promoted.
- Next: JRV-0527 session-bound managed-menu opening/observation, then JRV-0529/0530 candidate selection and active-label verification. Native signed-in Chrome remains a distinct unresolved session boundary; never transfer managed DOM coordinates into native clicks.
