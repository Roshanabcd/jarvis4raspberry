

# Repository audit handoff

Read AGENTS.md, docs/JARVIS_AUDIT_MASTER_REPORT.md, docs/JARVIS_BUGS_AND_IMPROVEMENTS.json and docs/AI_BUILD_ROADMAP.md before selecting work. Follow docs/jarvis-ui/SPEC.md and the gates in docs/jarvis-ui/PLAN.md. Use one browser worker by default, maximum two, and fake media. Only assert E-STOP visibility and enabled state. Never click it or send a real motion command. Preserve existing changes, show real availability and record evidence at 1440×900 and 1280×720.

The provider-independent UI regression command is `venv/bin/python tests/browser/audit_handoff.py`. Set `CHROME_BIN` when using an installed Chromium executable. It uses intercepted backend responses. For local model discovery, run `venv/bin/python -m pytest -q tests/unit/test_provider_integrations.py -k ollama`.

## Audit continuation policy · 21 November 2026

- Authoritative engineering rules: AGENTS.md. Phase gates: docs/jarvis-ui/PLAN.md and SPEC.md. The issue queue does not bypass phase gates or approval requirements.
- Authoritative findings: docs/JARVIS_AUDIT_MASTER_REPORT.md; machine-readable status: docs/JARVIS_BUGS_AND_IMPROVEMENTS.json; implementation order: docs/AI_BUILD_ROADMAP.md.
- Root audit documents and files ending in 2.md are synchronized handoff copies, not competing instruction sets. Update both copies when editing their shared content.
- The operator approved preserving and building on the current uncommitted changes. This is not permission to discard changes, alter secrets/authentication, install native dependencies or perform privileged/external actions.
- Keep one owner per worktree/device. Do not start a second backend on port 8000. Check the existing service owner before deployment; a foreground-server command is not a restart procedure for a system service.
- Distinguish implemented, verified_offline, verified_live and resolved. HTTP 200, route registration and a passing mock test do not establish working inference, authorized actions or hardware operation.
- Preserve historical evidence. New captures belong in a new evidence directory with source revision, viewport, fixture/live classification and result; never overwrite baseline screenshots.
- Run focused checks after relevant changes. Run broader regressions at integration milestones, not repeatedly without a new reason. Keep incomplete or blocked issues open.
