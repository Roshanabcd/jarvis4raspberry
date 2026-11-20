# Agent execution increment — 2026-11-11

This increment repairs model-driven execution; it does not establish a fully autonomous OS or arbitrary self-installation.

## Implemented

- OpenAI-compatible Chat Completions adapters send function schemas and decode native calls. Invalid JSON/non-object arguments return provider errors.
- The neural task loop discovers schemas from the live registry, filtered by the caller's role. This exposes registered capabilities without adding intent phrases for every possible request.
- Every model-selected call is checked against the advertised inventory and current role; extra arguments and model-provided confirmation are rejected. Execution goes through registry validation, permissions, safety checks, and audit logging without a legacy bypass.
- Assistant function calls and matching result IDs are preserved across rounds.
- Failed inference retries another available provider, at most once per provider. Five rounds and eight calls per round bound model-driven execution; this is not a wall-clock deadline.
- Reaching the round limit produces an explicit incomplete result. Exceptions retain the tools already attempted.
- Both chat endpoints support provider/model selection. SSE with `use_tools=true` uses the shared task loop, emitting a start event before work and the final response afterward. `use_tools=false` preserves direct token streaming and suppresses deterministic actions as well as neural tool execution.
- The system prompt asks for evidence-based results and, for missing capabilities, research plus an integration plan including dependencies, credentials/scopes, tests, and rollback. This is model guidance, not an installer or proof that research succeeded.

The native call format follows [official OpenAI function-calling documentation](https://developers.openai.com/api/docs/guides/function-calling).

## Validation

Command: `venv/bin/python -m pytest tests/unit/test_agent_execution.py tests/unit/test_phase1_chat_engine.py::TestMultiProviderRegistry -q`

Result: **22 passed in 1.34 seconds** (15 new isolated regressions plus seven existing provider tests). Providers and tool actions in the new regressions are mocked; no live inference or physical operation is established by this result.

`git diff --check` passed. Changed Python modules compiled successfully.

A broader run including chat endpoints, security-hardening tests, and the app factory exceeded a 55-second bound after 18 progress markers; exit status 124. A separate security run stalled after the isolated tests and was interrupted. These runs do not establish passing API/startup regressions. Earlier milestone reports also document startup/testing delays; the cause of these particular stalls has not been established.

## Remaining work

- Live end-to-end acceptance with configured model credentials/local model availability, authenticated user sessions, dashboard, voice, and devices.
- Native tool calling for Gemini and Anthropic (these adapters still return text-only results). Ollama uses its existing textual TOOL_CALL protocol with fuller schemas; actual model reliability needs live evaluation.
- Progress events per tool, cancellation during a blocking provider request, concurrency/session locking, and wall-clock task deadlines.
- Concrete extension packaging, isolated installation, trusted approval handoff, tests, deployment, and rollback for new integrations. No arbitrary online installation or source-code self-modification was enabled.
- Verification that legacy deterministic/compound routes apply the same identity boundaries as the neural route; they retain their existing execution policies.

Existing user changes were preserved. No credentials were printed, services restarted, packages installed, or actuators enabled.
