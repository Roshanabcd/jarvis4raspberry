# JARVIS — Resume from the durable master plan

This prompt is for Antigravity, Claude Code, Codex, GitHub Copilot, or any future coding assistant that can access my Raspberry Pi JARVIS checkout.

**Repository:** https://github.com/Roshanabcd/jarvis4raspberry

You are continuing an existing JARVIS project. DO NOT rebuild it from scratch. Read `AGENTS.md` and the root `PLAN.md` first, then `docs/jarvis-ui/PLAN.md`, relevant specifications, and the latest checkpoint. Preserve all working features, Git changes, hardware ownership and permission gates.

Use `python scripts/plan_tracker.py --summary` and `python scripts/plan_tracker.py --next 10` if the optional tracker has been installed. These commands are only hints: verify actual dependency status, source checkout, branch, current service owner and existing tests before selecting a task.

Work on the highest-priority eligible unchecked `JRV-XXXX` feature, or the smallest prerequisite vertical slice. First determine whether it is already implemented. If so, run focused tests and any required real Pi acceptance instead of rewriting it. On proof, mark its checkbox in PLAN.md as `[x]` and append `status: verified_live` or accurately scoped `verified_offline`, revision, date and evidence path. If incomplete, record `implemented_pending_verification`, `blocked`, or `in_progress` and continue safely. Never mark completed based only on mocked tests or a dashboard badge.

For each edit, record changed paths, test commands, actual outcomes, and proof in `docs/jarvis-execution/`. Do not expose secrets, escalate to unrestricted root, automate payment or send messages without consent, bypass website authentication, or issue physical motor commands during automated testing. Follow AGENTS.md approval conditions. Do not push or deploy without required approval.

Use Antigravity first for normal work, local models and already-provisioned tools where adequate, and only use paid coding agents as explicitly available. If a model's context or quota is low, write a handoff with completed IDs, current task, Git state, blockers, next eligible ID and verification evidence. Finish with the exact text:

Resume: continue per PLAN.md.

A new session must be opened to continue if quota/session ends; the plan cannot itself invoke or authorize another model.
