# Audit implementation sprints

1. **Access and reliability.** Use disposable guest and operator sessions. Compare allowed reads with protected controls. Verify expected guest denials and authorized success using benign test data. Review console and HTTP observations in the master report before promoting them to bugs.
2. **Shell and interaction.** Review UX-001 through UX-006, including catalog counts and category controls. Run each issue’s verification test at 1440×900 and 1280×720. Save keyboard focus and dialog evidence.
3. **AI and media.** Benchmark two-turn recall, code generation, diagnostics and a scheduling clarification. Record provider, first-token and completion times, expected answer, actual answer and failure UI. Check speech notifications with isolated media sinks. Start optimization only after profiling on Pi 5.
4. **Regression and polish.** Enumerate actual routes, catalog entries and modal triggers. Compare screenshots, keyboard behavior, overflow, request failures and reconnect feedback at both sizes. Preserve historical captures and record runtime, role and revision for each new run.

## Issue ownership and exit checks

| Sprint | Issue IDs | Completion evidence |
|---|---|---|
| 1 | BUG-001, BUG-002 | Verify guest and operator display with delayed identity data. Repeat the passing offline tab check against a stable running build. |
| 2 | UX-001 through UX-006 | Verify keyboard activation, inline launch denial, post-save feedback and manifest counts against populated test data. |
| 3 | AI-001 | Use an installed text model. Record actual answers and elapsed times for recall and code generation, then check recovery with the provider unavailable. |
| 4 | All nine | Compare the baseline captures with the fixed build and attach evidence for each remaining verification criterion. |

FreeLLMAPI is optional. Offline checks use the project checkout. Live inference requires a reachable configured provider.

## Current execution order and dependencies

1. Reconcile this queue with PLAN.md before advancing. Phase 5 remains blocked for real avatar assets; the recorded user exception permits voice repairs with an honest 2D fallback, not marking the original 3D gate passed.
2. Finish the existing catalog registration correction (BUG-003), preserving module engines and permissions. Then record the live deployment result after an authorized reload.
3. Within the approved audit follow-up scope, verify delayed identity display (BUG-001), launch-denial feedback (UX-002), settings feedback (UX-003), and operator keyboard activation (UX-004) using intercepted responses. Change implementation only if the check exposes a defect.
4. Retain UX-001, BUG-002 and UX-006 as verified_offline until deployment evidence meets their outstanding criteria. Complete the populated-catalog check for UX-005.
5. For AI-001, use a confirmed available text model; a vision-only model or a configured provider name is not evidence of conversational readiness. Preserve drafts and expose failure without inventing a reply. Live inference requires the existing approval/availability constraints.
6. Resume voice acceptance and local wake-word implementation from docs/CODEX_VOICE_CONTINUATION.md. Native runtime/model installation remains a separate approval boundary. Physical speech/speaker checks and provider-independent browser checks must be reported separately.

The original nine audit issues remain tracked. BUG-003 is an additional deployment finding. Do not restart completed audits or label all 42 modules operational from their health responses alone.
