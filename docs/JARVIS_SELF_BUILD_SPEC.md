

# Repository audit handoff

Read AGENTS.md, docs/JARVIS_AUDIT_MASTER_REPORT.md, docs/JARVIS_BUGS_AND_IMPROVEMENTS.json and docs/AI_BUILD_ROADMAP.md before selecting work. Follow docs/jarvis-ui/SPEC.md and the gates in docs/jarvis-ui/PLAN.md. Use one browser worker by default, maximum two, and fake media. Only assert E-STOP visibility and enabled state. Never click it or send a real motion command. Preserve existing changes, show real availability and record evidence at 1440×900 and 1280×720. Select one open issue by severity, inspect its source and prerequisites, implement its recommended fix, and execute its verification_test. Record commit, evidence paths and regression outcome before changing status to resolved. Keep blocked work open.

The provider-independent UI regression command is `venv/bin/python tests/browser/audit_handoff.py`. Set `CHROME_BIN` when using an installed Chromium executable. It uses intercepted backend responses. For local model discovery, run `venv/bin/python -m pytest -q tests/unit/test_provider_integrations.py -k ollama`.

Use the issue's status and implementation_note before editing. For implemented_pending_verification, run the outstanding check first. For verified_offline, repeat against the deployment only when the issue needs live evidence. Keep historical findings and reproduction steps. Resolve an issue only when its expected behavior and verification_test pass, and record the evidence and revision. AI model unavailability does not block independent UI tasks.

## Required implementation record

For each issue record: source revision (or dirty-file hashes), affected paths, current status, reproduction, smallest repair, command run, actual result, evidence paths, and remaining acceptance criteria. Treat all module archives/model output as untrusted inputs. No automatic self-installation, approval bypass, destructive repair, external message, purchase or hardware actuation is authorized by this document.

For the existing runtime, verify the owner before restarting. Use the project Python environment. A missing model/service must show Unavailable with a reason; keep manual controls usable. Do not mark a project or phase complete while its required gates remain open. Use this document as a development handoff, not an autonomous runtime instruction to expand privileges.
