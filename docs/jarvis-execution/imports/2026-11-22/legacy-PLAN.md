# JARVIS master execution plan

Updated: 22 November 2026. Owner: current implementation agent. Target: reliable Linux assistant on Raspberry Pi 5 with voice/chat access to registered capabilities, not unlimited autonomous authority.

## Read this first — every model, every session

This root PLAN.md is the continuation index and feature ledger. AGENTS.md remains authoritative. docs/jarvis-ui/PLAN.md retains UI gates and historical evidence; docs/JARVIS_PI_CONTROL_PHASES.md contains detailed control prompts. Never replace or reset those records. Read CLAUDE.md/CLAUDE2.md and the audit report/issue JSON/roadmap before editing affected subsystems.

The user requested this expanded plan and continuation on 22 November. Proceed with ordinary scoped improvements while preserving dirty changes. This does not authorize privileged operations, auth/secrets/schema changes, dependencies needing approval, paid calls, external messages or hardware motion. Keep one physical device owner. Use project venv and existing services/adapters. Do not read secrets. A model's lack of quota does not authorize spending through another provider.

## Resume protocol

1. Read this ledger, the Next action below, the UI phase plan, Git state and applicable instructions. Preserve all existing user work.
2. Skip COMPLETE items unless new evidence indicates a regression; mark a regressed item REOPENED with the evidence. REVIEW means inspect existing implementation first: do not rebuild it.
3. Follow the current authorized workstream and dependencies. Select its first eligible unfinished item. If blocked, record reason and required decision; work on another independent authorized item only if the UI gates permit it. Never bypass approval because another model previously wrote a proposal.
4. Inspect code and baseline tests; implement one cohesive item. Reuse the stack. No new service, registry, database or device owner merely to add a feature.
5. Run focused checks after changes. Use fake media and isolated fixtures; separate fixture, live-provider and physical results. Broaden checks at integration milestones.
6. Update the row status and append a checkpoint with files, exact test command/results, source revision, evidence path, remaining gaps and next ID. Update related issue/UI records when their scope changes. New dependencies need license/size/reason and approvals where required.
7. COMPLETE requires all applicable acceptance checks, evidence and preserved regression behavior. Code only = IMPLEMENTED; offline tests only = VERIFIED_OFFLINE; live checks with outstanding criteria = VERIFIED_LIVE. Historical success is not fresh acceptance.
8. Checkpoint explicit owned paths only. Never stage another contributor's changes, push without approval or silently weaken a test. If quota/context runs short, save a handoff BEFORE stopping. Never claim full completion because the remaining work is blocked.

States: REVIEW (existing implementation needs assessment), TODO, IN_PROGRESS, IMPLEMENTED, VERIFIED_OFFLINE, VERIFIED_LIVE, BLOCKED, COMPLETE, REOPENED. Every feature initially REVIEW unless backed by evidence here. This does not erase prior implementation or UI verification; reconcile existing evidence before doing more work.

## Voice/chat contract for every capability

Each executable feature must have a registered intent/tool, validated arguments, clear permission policy, observable task ID/stage/result, cancellation where applicable and a test through the real dispatcher. Expose it via chat and the existing voice transcript path; do not build a separate voice executor. Ask for missing targets. Acknowledge queued work without pretending it finished. Sensitive confirmation may require a secure UI even when the request originated by voice; never accept arbitrary nearby speech as administrator authentication. Unsupported actions explain why. New features are proposed, reviewed, implemented and verified, not downloaded and executed blindly from model output.

## Priorities and ordering

P0 = truthfulness, security and continuity; P1 = dependable daily operation; P2 = advanced capabilities and polish. Work in order: continuity setup → truthful results → scoped-control review → desktop/browser → chat/tasks → approved voice acceptance → Pi deployment → advanced modules → release. Security review runs alongside design, but implementation requiring approval waits. Existing UI phase 5 remains blocked on real assets; the previously recorded voice exception remains narrow. The user's continuation permits the scoped truthful-reporting repair; it does not mark any original gate verified. Final release must reconcile both plans.

## Next action

J004–J006: inspect existing browser observation/target selection adapters before replacing guessed account coordinates; require an explicit intended identity and verify page state. Do not treat a menu opening as account selection. Continue J007 cancellation coverage across remaining browser actions. J001–J003 have offline account-path evidence, not whole-desktop/live completion. No auth, stored-session, privilege or real-account operations without required scope. The next worker should read the checkpoint below and preserve mixed uncommitted code.

## Acceptance and evidence rules

Each row's observable outcome is a minimum acceptance criterion. Additionally require input validation, denied/unavailable/error/cancel paths where applicable, integration through chat/tool routing, and preservation of working UI behavior. Live and physical features need operator-authorized acceptance on the named device/revision. Save new evidence without overwriting old evidence. No secrets, raw private transcripts or private screenshots in evidence. Proposed latency targets must be measured before promises are made.

The 180 entries below are acceptance units, not a claim that 180 features are missing. Review existing implementations and reuse verified evidence. Do not inflate the count with aliases or duplicate modules. Optional hardware remains BLOCKED until actual prerequisites and approval exist; a blocker is not completion.

## Reliability and truthful results

Priority: P0. Dependencies: none.

| ID | Feature | Acceptance outcome | Status | Evidence / blocker |
|---|---|---|---|---|
| J001 | Stop false account-switch success | Report unverified when the selected account was not observed | VERIFIED_OFFLINE | docs/jarvis-ui/evidence/control-roadmap-2026-11-22/verification.json; live dispatch/UI acceptance pending. |
| J002 | Check window focus | Abort input when both supported focus attempts fail | VERIFIED_OFFLINE | docs/jarvis-ui/evidence/control-focus-input-2026-11-22/verification.json; account workflow only; other actions/live acceptance open. |
| J003 | Check input delivery | Return failure when an input adapter rejects the action | VERIFIED_OFFLINE | docs/jarvis-ui/evidence/control-focus-input-2026-11-22/verification.json; account workflow only; other actions/live acceptance open. |
| J004 | Verify account identity | Compare requested account with observed active identity | REVIEW | Assess current implementation; no new acceptance claimed. |
| J005 | Reject ambiguous account requests | Ask which account without guessing | REVIEW | Assess current implementation; no new acceptance claimed. |
| J006 | Separate menu opening from selection | Report menu opened only after observation | REVIEW | Assess current implementation; no new acceptance claimed. |
| J007 | Cancel between desktop steps | No later input after cancellation | IN_PROGRESS | Account-step cancellation verified offline in control-focus-input-2026-11-22; other action paths remain open. |
| J008 | Expose partial task results | Retain completed steps and identify failed step | REVIEW | Assess current implementation; no new acceptance claimed. |
| J009 | Preserve failed chat drafts | Retry retains the original user request | REVIEW | Assess current implementation; no new acceptance claimed. |
| J010 | Track result provenance | Show tool and observation supporting completion | REVIEW | Assess current implementation; no new acceptance claimed. |

## Scoped system control

Priority: P0. Dependencies: approval for security changes; first group.

| ID | Feature | Acceptance outcome | Status | Evidence / blocker |
|---|---|---|---|---|
| J011 | Trace terminal callers | Document endpoint-to-executor permission checks | REVIEW | Assess current implementation; no new acceptance claimed. |
| J012 | Remove client approval bypass | Client confirm boolean cannot authorize execution | REVIEW | Assess current implementation; no new acceptance claimed. |
| J013 | Bind approval to actor | Another session cannot redeem a grant | REVIEW | Assess current implementation; no new acceptance claimed. |
| J014 | Bind approval to exact action | Changed arguments or cwd reject the grant | REVIEW | Assess current implementation; no new acceptance claimed. |
| J015 | Expire approvals | Expired grants never execute | REVIEW | Assess current implementation; no new acceptance claimed. |
| J016 | Prevent approval replay | Second use is rejected before execution | REVIEW | Assess current implementation; no new acceptance claimed. |
| J017 | Allowlisted service control | Only reviewed units and operations accepted | REVIEW | Assess current implementation; no new acceptance claimed. |
| J018 | Structured privileged helper | Fixed executable and validated arguments only | REVIEW | Assess current implementation; no new acceptance claimed. |
| J019 | Redacted audit trail | Decision and outcome recorded without credentials | REVIEW | Assess current implementation; no new acceptance claimed. |
| J020 | Reviewable rollback | Prepare and test reversal in a disposable environment | REVIEW | Assess current implementation; no new acceptance claimed. |

## Desktop observation and input

Priority: P1. Dependencies: first group.

| ID | Feature | Acceptance outcome | Status | Evidence / blocker |
|---|---|---|---|---|
| J021 | Discover desktop session | Report actual X11 or Wayland support | REVIEW | Assess current implementation; no new acceptance claimed. |
| J022 | Detect capture availability | Unavailable state explains missing permission or display | REVIEW | Assess current implementation; no new acceptance claimed. |
| J023 | Fresh screenshot observation | Attach capture timestamp and reject stale action targets | REVIEW | Assess current implementation; no new acceptance claimed. |
| J024 | Screen text extraction | Return text with source region and extraction failures | REVIEW | Assess current implementation; no new acceptance claimed. |
| J025 | Window listing | Return actual open windows with stable handles | REVIEW | Assess current implementation; no new acceptance claimed. |
| J026 | Window activation | Confirm active window before typing | REVIEW | Assess current implementation; no new acceptance claimed. |
| J027 | Coordinate scaling | Handle viewport and display scale correctly | REVIEW | Assess current implementation; no new acceptance claimed. |
| J028 | Keyboard automation | Release held keys on failure and cancellation | REVIEW | Assess current implementation; no new acceptance claimed. |
| J029 | Mouse automation | Validate bounds and release buttons reliably | REVIEW | Assess current implementation; no new acceptance claimed. |
| J030 | Desktop action serialization | Two jobs cannot interleave keyboard or mouse input | REVIEW | Assess current implementation; no new acceptance claimed. |

## Browser and accounts

Priority: P1. Dependencies: desktop group; approval for persistent sessions.

| ID | Feature | Acceptance outcome | Status | Evidence / blocker |
|---|---|---|---|---|
| J031 | Named automation profiles | User explicitly selects an app-owned profile | REVIEW | Assess current implementation; no new acceptance claimed. |
| J032 | Separate profile and account | Clarify browser profile versus website identity | REVIEW | Assess current implementation; no new acceptance claimed. |
| J033 | Profile locking | Concurrent launch cannot corrupt a profile | REVIEW | Assess current implementation; no new acceptance claimed. |
| J034 | Verified navigation | Confirm requested origin and visible page | REVIEW | Assess current implementation; no new acceptance claimed. |
| J035 | Semantic element targeting | Use observed labels or DOM targets before coordinates | REVIEW | Assess current implementation; no new acceptance claimed. |
| J036 | Multi-tab selection | Select intended tab using observed title and origin | REVIEW | Assess current implementation; no new acceptance claimed. |
| J037 | Login handoff | Pause for operator login without collecting passwords | REVIEW | Assess current implementation; no new acceptance claimed. |
| J038 | MFA handoff | Resume only after observed successful operator authentication | REVIEW | Assess current implementation; no new acceptance claimed. |
| J039 | Account-switch fixture coverage | Test multiple identities and failed selections | REVIEW | Assess current implementation; no new acceptance claimed. |
| J040 | Download containment | Validate destination and reject path traversal | REVIEW | Assess current implementation; no new acceptance claimed. |

## Real-time chat and providers

Priority: P1. Dependencies: first group.

| ID | Feature | Acceptance outcome | Status | Evidence / blocker |
|---|---|---|---|---|
| J041 | Prompt acknowledgment | Show accepted status before long-running work | REVIEW | Assess current implementation; no new acceptance claimed. |
| J042 | Token streaming | Render incremental provider output | REVIEW | Assess current implementation; no new acceptance claimed. |
| J043 | Provider deadline | Bound connection and generation waits | REVIEW | Assess current implementation; no new acceptance claimed. |
| J044 | Available model selection | Use confirmed text-capable installed or cloud model | REVIEW | Assess current implementation; no new acceptance claimed. |
| J045 | Bounded fallback | Avoid repeated failing providers and paid automatic fallback | REVIEW | Assess current implementation; no new acceptance claimed. |
| J046 | Conversation continuity | Maintain relevant turns within context budget | REVIEW | Assess current implementation; no new acceptance claimed. |
| J047 | Cancel generation | Stop output and suppress late completion | REVIEW | Assess current implementation; no new acceptance claimed. |
| J048 | Reconnect recovery | Recover job status without duplicate execution | REVIEW | Assess current implementation; no new acceptance claimed. |
| J049 | Provider diagnostics | Show masked configuration and actual probe status | REVIEW | Assess current implementation; no new acceptance claimed. |
| J050 | Latency benchmark | Record sample count and first-token and completion distributions | REVIEW | Assess current implementation; no new acceptance claimed. |

## Voice conversation

Priority: P1. Dependencies: existing phase 6; approval for pipeline changes.

| ID | Feature | Acceptance outcome | Status | Evidence / blocker |
|---|---|---|---|---|
| J051 | Single capture owner | Reuse existing microphone service and IPC | REVIEW | Assess current implementation; no new acceptance claimed. |
| J052 | Single playback owner | Do not double-speak through browser and server | REVIEW | Assess current implementation; no new acceptance claimed. |
| J053 | Push-to-talk | Capture only within the explicit recording session | REVIEW | Assess current implementation; no new acceptance claimed. |
| J054 | Microphone permission failure | Show actionable failure without hidden fallback | REVIEW | Assess current implementation; no new acceptance claimed. |
| J055 | Privacy indicator | Accurately show listening and muted states | REVIEW | Assess current implementation; no new acceptance claimed. |
| J056 | Offline wake capability | Label offline only after verified local detection | REVIEW | Assess current implementation; no new acceptance claimed. |
| J057 | Wake false-trigger evaluation | Record false accepts and misses with approved samples | REVIEW | Assess current implementation; no new acceptance claimed. |
| J058 | Barge-in | Stop current speech when an allowed interruption occurs | REVIEW | Assess current implementation; no new acceptance claimed. |
| J059 | Long-task spoken updates | Speak acceptance and actual final result once each | REVIEW | Assess current implementation; no new acceptance claimed. |
| J060 | Device reconnect | Recover one owner after microphone or speaker reconnect | REVIEW | Assess current implementation; no new acceptance claimed. |

## Tasks and scheduling

Priority: P1. Dependencies: scoped system control and chat.

| ID | Feature | Acceptance outcome | Status | Evidence / blocker |
|---|---|---|---|---|
| J061 | Durable task IDs | Same job ID across chat progress and result | REVIEW | Assess current implementation; no new acceptance claimed. |
| J062 | Bounded task queue | Backpressure prevents unbounded work | REVIEW | Assess current implementation; no new acceptance claimed. |
| J063 | Independent concurrency | Two unrelated safe tasks can progress | REVIEW | Assess current implementation; no new acceptance claimed. |
| J064 | Resource locking | Serialize shared device and browser access | REVIEW | Assess current implementation; no new acceptance claimed. |
| J065 | Task cancellation | Stop descendants and release resource locks | REVIEW | Assess current implementation; no new acceptance claimed. |
| J066 | Idempotent submission | Duplicate request does not duplicate side effects | REVIEW | Assess current implementation; no new acceptance claimed. |
| J067 | Crash recovery | Restore safe job state without replaying privileged work | REVIEW | Assess current implementation; no new acceptance claimed. |
| J068 | Time-zone scheduling | Show explicit zone and correct scheduled instant | REVIEW | Assess current implementation; no new acceptance claimed. |
| J069 | Missed-run policy | Explain skipped or deferred runs after downtime | REVIEW | Assess current implementation; no new acceptance claimed. |
| J070 | Task dependency graph | Run prerequisites before dependent steps | REVIEW | Assess current implementation; no new acceptance claimed. |

## Developer and repair assistant

Priority: P1. Dependencies: scoped system control and tasks.

| ID | Feature | Acceptance outcome | Status | Evidence / blocker |
|---|---|---|---|---|
| J071 | Approved workspace roots | Reject reads and writes outside selected project | REVIEW | Assess current implementation; no new acceptance claimed. |
| J072 | Repository inspection | Summarize branch and diff without secrets | REVIEW | Assess current implementation; no new acceptance claimed. |
| J073 | Error explanation | Explain captured exit status and relevant output | REVIEW | Assess current implementation; no new acceptance claimed. |
| J074 | Repair proposal | Present exact patch and affected files | REVIEW | Assess current implementation; no new acceptance claimed. |
| J075 | Patch application | Apply reviewed scoped edit preserving user changes | REVIEW | Assess current implementation; no new acceptance claimed. |
| J076 | Focused test execution | Run relevant checks and report actual outcomes | REVIEW | Assess current implementation; no new acceptance claimed. |
| J077 | Build diagnosis | Distinguish environment failure from code failure | REVIEW | Assess current implementation; no new acceptance claimed. |
| J078 | Regression avoidance | Compare with baseline and preserve passing behavior | REVIEW | Assess current implementation; no new acceptance claimed. |
| J079 | Bounded repair attempts | Stop repeated failures with concrete handoff | REVIEW | Assess current implementation; no new acceptance claimed. |
| J080 | CLI adapter discovery | Distinguish installed authenticated headless and IDE-only tools | REVIEW | Assess current implementation; no new acceptance claimed. |

## Knowledge and memory

Priority: P2. Dependencies: chat; storage changes require approval.

| ID | Feature | Acceptance outcome | Status | Evidence / blocker |
|---|---|---|---|---|
| J081 | Document import | Validate format size and user-selected path | REVIEW | Assess current implementation; no new acceptance claimed. |
| J082 | Document text extraction | Report unsupported or unreadable pages | REVIEW | Assess current implementation; no new acceptance claimed. |
| J083 | Grounded document answers | Cite source passages and page locations | REVIEW | Assess current implementation; no new acceptance claimed. |
| J084 | Hybrid document search | Return ranked matches with source metadata | REVIEW | Assess current implementation; no new acceptance claimed. |
| J085 | Memory consent | Save persistent personal facts only through explicit controls | REVIEW | Assess current implementation; no new acceptance claimed. |
| J086 | Memory correction | User can inspect and correct an existing fact | REVIEW | Assess current implementation; no new acceptance claimed. |
| J087 | Memory deletion | Confirm requested deletion and verify removal | REVIEW | Assess current implementation; no new acceptance claimed. |
| J088 | Context isolation | Separate projects and users at retrieval boundary | REVIEW | Assess current implementation; no new acceptance claimed. |
| J089 | Retention controls | Explain and enforce configured retention | REVIEW | Assess current implementation; no new acceptance claimed. |
| J090 | Prompt-injection handling | Treat retrieved text as data not tool authority | REVIEW | Assess current implementation; no new acceptance claimed. |

## Research and information

Priority: P2. Dependencies: chat and tasks; approved network use.

| ID | Feature | Acceptance outcome | Status | Evidence / blocker |
|---|---|---|---|---|
| J091 | Web search adapter | Return real results with source URLs | REVIEW | Assess current implementation; no new acceptance claimed. |
| J092 | Source extraction | Handle unreadable or blocked pages honestly | REVIEW | Assess current implementation; no new acceptance claimed. |
| J093 | Evidence synthesis | Distinguish supported claims from inference | REVIEW | Assess current implementation; no new acceptance claimed. |
| J094 | Citation verification | Cited source supports the associated claim | REVIEW | Assess current implementation; no new acceptance claimed. |
| J095 | Date-aware research | Record publication and retrieval dates | REVIEW | Assess current implementation; no new acceptance claimed. |
| J096 | Contradiction reporting | Present conflicting evidence rather than invent consensus | REVIEW | Assess current implementation; no new acceptance claimed. |
| J097 | Research budgets | Bound requests time and token spending | REVIEW | Assess current implementation; no new acceptance claimed. |
| J098 | PDF research | Extract permitted documents with page references | REVIEW | Assess current implementation; no new acceptance claimed. |
| J099 | Research export | Export a sourced report to an approved path | REVIEW | Assess current implementation; no new acceptance claimed. |
| J100 | Research continuation | Resume from saved sources without duplicate requests | REVIEW | Assess current implementation; no new acceptance claimed. |

## Personal productivity

Priority: P2. Dependencies: tasks; external writes need approval.

| ID | Feature | Acceptance outcome | Status | Evidence / blocker |
|---|---|---|---|---|
| J101 | Daily planning | Create reviewable priorities from actual tasks | REVIEW | Assess current implementation; no new acceptance claimed. |
| J102 | Reminder creation | Confirm scheduled time and returned identifier | REVIEW | Assess current implementation; no new acceptance claimed. |
| J103 | Calendar availability | Use authorized calendar data only | REVIEW | Assess current implementation; no new acceptance claimed. |
| J104 | Calendar event proposal | Show exact attendees time and description before write | REVIEW | Assess current implementation; no new acceptance claimed. |
| J105 | Meeting preparation | Summarize selected material without unrelated private data | REVIEW | Assess current implementation; no new acceptance claimed. |
| J106 | Email drafting | Create a reviewable draft without automatic sending | REVIEW | Assess current implementation; no new acceptance claimed. |
| J107 | Email send approval | Send only approved recipients and content | REVIEW | Assess current implementation; no new acceptance claimed. |
| J108 | Study planning | Generate milestones tied to available study time | REVIEW | Assess current implementation; no new acceptance claimed. |
| J109 | Interview practice | Provide questions and grounded feedback | REVIEW | Assess current implementation; no new acceptance claimed. |
| J110 | Resume matching | Compare supplied qualifications without inventing experience | REVIEW | Assess current implementation; no new acceptance claimed. |

## Media and accessibility

Priority: P2. Dependencies: chat and voice.

| ID | Feature | Acceptance outcome | Status | Evidence / blocker |
|---|---|---|---|---|
| J111 | YouTube transcript summary | Use available authorized transcript and timestamps | REVIEW | Assess current implementation; no new acceptance claimed. |
| J112 | Media controls | Verify intended player before play or pause | REVIEW | Assess current implementation; no new acceptance claimed. |
| J113 | Content drafting | Create requested text with editable output | REVIEW | Assess current implementation; no new acceptance claimed. |
| J114 | Speech translation | Display source and translated text with uncertainty | REVIEW | Assess current implementation; no new acceptance claimed. |
| J115 | Language selection | Use supported locale without false availability | REVIEW | Assess current implementation; no new acceptance claimed. |
| J116 | Speech speed controls | Apply actual backend-supported speed setting | REVIEW | Assess current implementation; no new acceptance claimed. |
| J117 | Captions | Show current utterance and completed text | REVIEW | Assess current implementation; no new acceptance claimed. |
| J118 | Keyboard navigation | Operate all supported controls without mouse | REVIEW | Assess current implementation; no new acceptance claimed. |
| J119 | Screen-reader semantics | Label controls and announce status changes | REVIEW | Assess current implementation; no new acceptance claimed. |
| J120 | Reduced-motion mode | Respect motion preference without hiding task state | REVIEW | Assess current implementation; no new acceptance claimed. |

## Pi operations and deployment

Priority: P1. Dependencies: scoped system control.

| ID | Feature | Acceptance outcome | Status | Evidence / blocker |
|---|---|---|---|---|
| J121 | Platform inventory | Report actual OS architecture Python and RAM | REVIEW | Assess current implementation; no new acceptance claimed. |
| J122 | Read-only telemetry | Show measured CPU memory disk and temperature | REVIEW | Assess current implementation; no new acceptance claimed. |
| J123 | Thermal awareness | Reduce optional heavy jobs at configured limits | REVIEW | Assess current implementation; no new acceptance claimed. |
| J124 | Inference resource budget | Bound heavy inference concurrency from measured capacity | REVIEW | Assess current implementation; no new acceptance claimed. |
| J125 | Disk pressure handling | Warn and refuse unsafe growth without deleting user data | REVIEW | Assess current implementation; no new acceptance claimed. |
| J126 | Single backend service | Ensure one authorized owner for the configured port | REVIEW | Assess current implementation; no new acceptance claimed. |
| J127 | Localhost defaults | Expose no remote control listener by default | REVIEW | Assess current implementation; no new acceptance claimed. |
| J128 | Deployment proposal | Record exact revision checks and rollback steps | REVIEW | Assess current implementation; no new acceptance claimed. |
| J129 | Health versus readiness | Distinguish responding service from usable capabilities | REVIEW | Assess current implementation; no new acceptance claimed. |
| J130 | Recovery documentation | Provide operator steps tested in disposable deployment | REVIEW | Assess current implementation; no new acceptance claimed. |

## Hardware and robotics

Priority: P2. Dependencies: device ownership; simulation first.

| ID | Feature | Acceptance outcome | Status | Evidence / blocker |
|---|---|---|---|---|
| J131 | Device capability inventory | Detected absent and unknown are distinct | REVIEW | Assess current implementation; no new acceptance claimed. |
| J132 | ReSpeaker status | Reuse owner and show actual connection state | REVIEW | Assess current implementation; no new acceptance claimed. |
| J133 | Camera ownership | Never start a competing capture process | REVIEW | Assess current implementation; no new acceptance claimed. |
| J134 | ESP32 connection status | Confirm adapter response rather than configured address | REVIEW | Assess current implementation; no new acceptance claimed. |
| J135 | Sensor readings | Include units timestamp and unavailable state | REVIEW | Assess current implementation; no new acceptance claimed. |
| J136 | Simulation mode | Clearly separate simulated and physical endpoints | REVIEW | Assess current implementation; no new acceptance claimed. |
| J137 | Motion disarmed default | No movement on startup or model suggestion | REVIEW | Assess current implementation; no new acceptance claimed. |
| J138 | Motion bounds | Validate limits in existing backend in simulation | REVIEW | Assess current implementation; no new acceptance claimed. |
| J139 | Watchdog behavior | Simulated link loss leads to safe stopped state | REVIEW | Assess current implementation; no new acceptance claimed. |
| J140 | Emergency-stop acceptance | Test latch in simulation; live UI visibility only | REVIEW | Assess current implementation; no new acceptance claimed. |

## Security and privacy

Priority: P0. Dependencies: security changes need approval.

| ID | Feature | Acceptance outcome | Status | Evidence / blocker |
|---|---|---|---|---|
| J141 | Secret exclusion | No credentials in frontend logs evidence or commits | REVIEW | Assess current implementation; no new acceptance claimed. |
| J142 | Path containment | Resolve paths and reject traversal and escaping symlinks | REVIEW | Assess current implementation; no new acceptance claimed. |
| J143 | Untrusted tool output | Tool text cannot grant permissions or trigger execution | REVIEW | Assess current implementation; no new acceptance claimed. |
| J144 | Role enforcement | Guest cannot invoke operator-only actions | REVIEW | Assess current implementation; no new acceptance claimed. |
| J145 | Session lifecycle | Expired sessions lose protected capabilities | REVIEW | Assess current implementation; no new acceptance claimed. |
| J146 | Local request protection | Reject untrusted origins for sensitive actions | REVIEW | Assess current implementation; no new acceptance claimed. |
| J147 | Outbound action review | Approve exact message publication or upload destination | REVIEW | Assess current implementation; no new acceptance claimed. |
| J148 | Budget controls | Require explicit spending authorization and hard limits | REVIEW | Assess current implementation; no new acceptance claimed. |
| J149 | Private screen handling | Do not persist sensitive captures by default | REVIEW | Assess current implementation; no new acceptance claimed. |
| J150 | Dependency review | Record license compatibility and required approvals | REVIEW | Assess current implementation; no new acceptance claimed. |

## Dashboard and usability

Priority: P2. Dependencies: preserve UI phase gates.

| ID | Feature | Acceptance outcome | Status | Evidence / blocker |
|---|---|---|---|---|
| J151 | Real capability catalog | Available means implementation exists with honest readiness | REVIEW | Assess current implementation; no new acceptance claimed. |
| J152 | Control Center parity | Keep classic and futuristic features reachable | REVIEW | Assess current implementation; no new acceptance claimed. |
| J153 | Clear error states | Show reason retry option and preserved input | REVIEW | Assess current implementation; no new acceptance claimed. |
| J154 | Live task panel | Show actual queue progress and results | REVIEW | Assess current implementation; no new acceptance claimed. |
| J155 | Provider label accuracy | Display backend-selected provider and model | REVIEW | Assess current implementation; no new acceptance claimed. |
| J156 | Voice state accuracy | Reflect actual capture processing and playback stages | REVIEW | Assess current implementation; no new acceptance claimed. |
| J157 | Audio-reactive avatar | Animate from real playback and label correctly | REVIEW | Assess current implementation; no new acceptance claimed. |
| J158 | Licensed avatar assets | Do not mark real-avatar gate passed with placeholders | REVIEW | Assess current implementation; no new acceptance claimed. |
| J159 | Responsive layouts | Check at 1440x900 and 1280x720 plus existing mobile gates | REVIEW | Assess current implementation; no new acceptance claimed. |
| J160 | Empty and offline states | No fake metrics or successful connection indicators | REVIEW | Assess current implementation; no new acceptance claimed. |

## Module completion and extension

Priority: P2. Dependencies: capability catalog and tasks.

| ID | Feature | Acceptance outcome | Status | Evidence / blocker |
|---|---|---|---|---|
| J161 | Module inventory | Map every installed module to entrypoint and tests | REVIEW | Assess current implementation; no new acceptance claimed. |
| J162 | Coding module acceptance | Generate patch and run focused checks in disposable workspace | REVIEW | Assess current implementation; no new acceptance claimed. |
| J163 | Document module acceptance | Answer a known question with source evidence | REVIEW | Assess current implementation; no new acceptance claimed. |
| J164 | Research module acceptance | Produce a sourced answer under request budget | REVIEW | Assess current implementation; no new acceptance claimed. |
| J165 | Support module acceptance | Route a fixture ticket with honest escalation state | REVIEW | Assess current implementation; no new acceptance claimed. |
| J166 | Scraper module acceptance | Respect access constraints and return validated export | REVIEW | Assess current implementation; no new acceptance claimed. |
| J167 | Analytics module acceptance | Explain data quality and validate fixture calculations | REVIEW | Assess current implementation; no new acceptance claimed. |
| J168 | Paper-trading acceptance | Simulation only with explicit labeling and no real orders | REVIEW | Assess current implementation; no new acceptance claimed. |
| J169 | Extension proposal | Research new capability and prepare reviewed implementation plan | REVIEW | Assess current implementation; no new acceptance claimed. |
| J170 | Extension activation gate | Enable only after checks compatibility and required approval | REVIEW | Assess current implementation; no new acceptance claimed. |

## Continuity and release

Priority: P0. Dependencies: continuous; final release depends on all required groups.

| ID | Feature | Acceptance outcome | Status | Evidence / blocker |
|---|---|---|---|---|
| J171 | Persistent master roadmap | Every item has stable ID and status | COMPLETE | docs/jarvis-ui/evidence/control-roadmap-2026-11-22/verification.json; 180 unique IDs and statuses checked. |
| J172 | Evidence-linked completion | Complete only with source revision and applicable acceptance evidence | REVIEW | Assess current implementation; no new acceptance claimed. |
| J173 | Automatic roadmap validation | Detect duplicate IDs missing evidence and invalid states | REVIEW | Assess current implementation; no new acceptance claimed. |
| J174 | Model handoff | Record exact next item files checks and blockers | REVIEW | Assess current implementation; no new acceptance claimed. |
| J175 | Worktree ownership | Concurrent workers never edit the same checkout | REVIEW | Assess current implementation; no new acceptance claimed. |
| J176 | Checkpoint discipline | Commit only explicit owned paths with reviewed diff | REVIEW | Assess current implementation; no new acceptance claimed. |
| J177 | Capability regression matrix | Map existing features to preserved acceptance tests | REVIEW | Assess current implementation; no new acceptance claimed. |
| J178 | Release acceptance | Run broad regression once at integration milestone | REVIEW | Assess current implementation; no new acceptance claimed. |
| J179 | User operation guide | Explain supported commands limitations and approvals | REVIEW | Assess current implementation; no new acceptance claimed. |
| J180 | Post-release backlog | New requests become scoped items without silently reopening finished work | REVIEW | Assess current implementation; no new acceptance claimed. |

## Checkpoints and handoff

### 2026-11-22 — roadmap expansion
- Added 180 stable feature IDs, explicit acceptance criteria, status transitions and voice/chat contract.
- Preserved existing UI plan and historic evidence. Linked instruction files to this continuation index.
- Implementation checkpoint follows below; no whole-project completion or live acceptance claimed.

## After the agreed plan is complete

Only declare release completion when every required item is COMPLETE and optional exclusions are explicitly accepted by the operator with reasons. Then accept normal user tasks through the verified capabilities. Add new feature requests as new stable IDs with dependencies, scope and tests. Do not renumber historical IDs. Continue bug fixes and evidence updates without rebuilding working features. No plan can promise unlimited capabilities or automatic access to services without credentials, permissions and supported APIs.

### 2026-11-22 — J001 offline implementation checkpoint
- Account workflow now returns unverified with verified=False and an honest spoken summary instead of unconditional success.
- Added three isolated fake-backend cases; updated existing account-progress expectation to require unverified result.
- Focused check: 4 passed in 1.94s. Evidence: docs/jarvis-ui/evidence/control-roadmap-2026-11-22/verification.json, including source hashes.
- No service restart, real input, account change, provider request or physical acceptance.
- Source/test files already contained operator changes; preserved them and did not commit the mixed files.
- Next: J002/J003 focus/input failure handling, then observation-based account selection and dispatcher/UI acceptance. J001 remains VERIFIED_OFFLINE, not COMPLETE.

### 2026-11-22 — J002/J003 and account cancellation checkpoint
- Account workflow stops on failed/malformed focus acknowledgment, rejected clicks or adapter exceptions; cancellation is checked between steps.
- Dispatcher now forwards target and preserves error/unverified/cancelled results instead of forcing success. No role or authentication logic changed.
- Baseline: 4 passed in 1.99s. Final focused regression: 37 passed in 2.58s; git diff --check passed.
- Tests cover public dispatcher chat/voice sources with fake registry/native backend; no live capture, physical input, paid inference or deployment.
- Evidence/source hashes: docs/jarvis-ui/evidence/control-focus-input-2026-11-22/verification.json.
- Mixed operator changes in source files preserved; not staged or committed as an owned phase.
- Remaining: observed targets/account identity, broader desktop cancellation and operator-authorized live acceptance. Root ledger and original UI gates remain distinct.
