# Provider and voice reliability — 12 November 2026

## Findings and repairs

The Integrations form previously displayed success without checking HTTP status,
and did not send the administrator headers required by the settings API. The user
confirmed entering keys through that form. Read-only inspection of the project
configuration and running service found placeholder OpenAI/Google credentials,
and no usable NVIDIA or other cloud key. No credential values were printed.

The repaired form sends the existing administrator authorization headers, reports
rejection, clears the PIN after each action, and preserves blank/masked keys.
Saved secrets are fully masked on retrieval. Environment updates use a private
atomic file with quoted values; failed persistence does not activate new keys.
Successful saves refresh provider objects while preserving conversations and the
selected model. Existing providers and user configuration are preserved.

OpenRouter, Groq, and Together now have provider registrations and Integrations
fields. `POST /api/chat/providers/test` requires fresh administrator authorization
and sends one short synthetic completion request. Results distinguish missing
credentials, disabled providers, authentication/access errors, unavailable
model/endpoint, quota/rate limits, request failures, empty/unexpected answers, and
a successful marker response. Tests do not execute model-requested tools.
`scripts/check_ai_providers.py` provides the same credential-free report locally;
network calls require its `--live` option.

Gemini now uses Google's OpenAI-compatible endpoint instead of sending only the
last user message and discarding tools. The adapter preserves system/context
messages, tool definitions, call IDs, and opaque tool-call metadata for signed
continuations. Local history timestamps are excluded from remote message payloads.
Provider HTTP errors no longer expose raw upstream bodies through this transport.
See [Google's compatibility documentation](https://ai.google.dev/gemini-api/docs/openai)
and [OpenAI's tool-call protocol](https://developers.openai.com/api/docs/guides/function-calling).
OpenRouter's adapter uses its compatible API base; see its
[official quickstart](https://openrouter.ai/docs/quickstart).

Ollama checks now have a five-second availability cache. Model-size-dependent
180–240-second timeout overrides were removed; requests respect their configured
timeout (default 45 seconds) and remaining inference budget. The agent loop checks
a 75-second budget between rounds, and cloud adapters receive the remaining
timeout. This is not a strict global deadline for arbitrary tool calls or streaming
connections. The voice daemon's HTTP allowance is 95 seconds rather than expiring
after 20 seconds while the backend is still inferring. Its no-replay behavior is
preserved after uncertain results.

The voice command endpoint returns its text before background synthesis/playback.
It broadcasts the text once and does not send a second browser-autoplay copy of
system audio. Direct legacy callers retain synchronous speech behavior. Empty
answers and AI exceptions now report failure instead of echoing the command as
though it succeeded. Background speech is not a durable job queue or a completed
cross-process voice-control implementation.

## Verification

- **135 Python tests passed in 3.31 seconds** across provider integrations, voice
  delivery, desktop sessions, agent execution, APIs, authorization, and speech.
  After the final message-metadata filtering change, **44 affected provider/agent
  tests passed in 1.87 seconds**. These are overlapping test runs, not 179 unique
  tests.
- **Nine frontend tests passed**, including denied saves, explicit PIN headers,
  masked-key preservation, missing-key reporting, and desktop lifecycle cleanup.
- An additional **70 focused Python tests passed** after the recorder and
  terminal-assistance increment; the final changed-area subset passed **43
  tests**. `npm run test:desktop` passed all nine frontend tests.
- Python compilation, complete inline dashboard JavaScript syntax, and
  `git diff --check` passed.
- The configuration-only cloud diagnostic runner reports **missing_key for Gemini, OpenAI,
  Anthropic, NVIDIA, OpenRouter, Groq, and Together**. No cloud model completion
  was verified. Placeholder credentials were not sent to provider APIs.
- A direct synthetic `llama3.2:1b` cold-start test, limited to 16 output tokens,
  **timed out after 25.04 seconds**. The installed model and reachable Ollama API
  do not establish usable local inference performance.
- The operator restarted the core after the tested update. The existing user
  voice service was restarted without creating a competing capture owner.
- Live `/api/chat/providers` lists the new providers and correctly reports missing
  credentials. Integration key fields are fully masked. The diagnostic endpoint
  rejects an unauthenticated probe with HTTP 428 as intended.
- Live `/api/voice/command` returned the correct result for `2 + 2` in **89 ms**.
  Subsequent speech diagnostics reported staged cached audio with **23.75 ms**
  synthesis/staging latency. This verifies the deterministic command and background
  delivery path; it does not measure cloud inference, real microphone recognition,
  or whether the user heard the audio.
- Core and voice services are active. Wake status reports the dedicated daemon
  with fresh telemetry. Port 8000 remains bound to **127.0.0.1**.

## What the operator needs to do

1. Refresh `http://127.0.0.1:8000` and open **Integrations**.
2. Enter the real keys locally and the existing administrator PIN, then save.
   Blank fields keep saved keys. Do not put credentials in a chat or handoff file.
3. Enter the PIN again and click **Test cloud providers**. The action sends a small
   synthetic prompt to each configured provider and can consume API credit.
4. In AI Chat, select a provider/model that passed. Key presence is not proof of
   account credit, model access, streaming, or tool-call support.

## Remaining work and reproduction command

An opt-in `scripts/jarvis-run -- <command> <args...>` wrapper now executes only
the explicit argv without `shell=True`, preserves the child exit code, and
creates a bounded, mode-600 local diagnostic task for non-zero exits. Captured
stdout/stderr is redacted before persistence; no repair, install, history scrape,
or cloud transmission is automatic. The task contains conservative diagnosis
hints and requires reviewed follow-up work. Interactive TTY behavior remains a
limitation because captured output is piped for failure evidence.

End-to-end acoustic voice acceptance, cross-process mute/barge-in and speaker
feedback, durable voice jobs, improved
intent/compound routing, uniform tool authorization, and reliable vision remain
open. Static model lists can be outdated. Anthropic does not yet implement a
complete native tool cycle. Generic custom endpoint validation and broader
provider/model parameter negotiation also need review.

The actionable continuation instructions are in
[`ANTIGRAVITY_CONTINUATION_PROMPT.md`](ANTIGRAVITY_CONTINUATION_PROMPT.md).

## 2026-11-14 — Provider tool cycle, cross-process voice reliability, and terminal assistance

- **Anthropic native tool calling:** Implemented `input_schema` tool definitions, `tool_use`
  parsing, `tool_result` continuation formatting in user blocks, and SSE streaming token delta
  handling in `AnthropicProvider`.
- **Configurable model IDs:** Models are configurable via environment variables
  (`GEMINI_MODEL`, `OPENAI_MODEL`, `ANTHROPIC_MODEL`, `NVIDIA_MODEL`, `OPENROUTER_MODEL`,
  `GROQ_MODEL`, `TOGETHER_MODEL`) and configuration files.
- **Failover visibility and explicit selection protection:** `JARVISBrain.chat` never silently
  switches to another provider when the user or caller explicitly selected a provider.
  Explicit provider errors are reported immediately.
- **Cross-process daemon control:** Added `apps/voice/daemon_control.py`. Core sends `mute`,
  `unmute`, `stop`, `barge_in`, and `push_to_talk` via secure permissions-checked local runtime files
  under `/run/user/<uid>/jarvis/voice-control.json` directly to the active voice daemon.
- **Cross-process speaker feedback guard:** Added `apps/voice/playback_state.py`. Shared
  playback leases across processes allow the daemon's VAD and wake-word loop to detect
  when physical speakers are actively playing audio, eliminating acoustic feedback loops.
- **Microphone failure backoff:** When `pw-record` exits with non-zero status (such as when
  no capture device is attached), `WakeWordEngine` applies exponential backoff up to 4.0s
  to eliminate CPU spinning and log storms.
- **Durable voice jobs:** Added `apps/voice/voice_jobs.py`. Tracks asynchronous speech
  synthesis and playback jobs with unique IDs (`vjob_*`), lifecycle states (`queued`,
  `synthesizing`, `playing`, `completed`, `cancelled`, `failed`), and cancellation to prevent
  overlapping playback. Exposed at `/api/voice/jobs`.
- **Terminal failure assistance workflows:** Extended `tools/terminal_failure.py` and
  `scripts/jarvis-run` with inspection (`--inspect`), exact reproduction (`--reproduce`),
  minimal-diff proposals (`--propose`), confirmation-gated patch application (`--apply --confirm`),
  automatic checkpoint backup (`<file>.orig.<task_id>`), rollback (`--rollback`), workspace
  boundary security enforcement, and recursion protection.

### Verification (14 November 2026)

- **153 Python unit tests passed in 3.10 seconds** across provider integrations, voice daemon
  delivery, terminal failure assistance, active desktop, agent execution, and speech manager.
- **Nine frontend desktop tests passed in 0.28 seconds** (`npm run test:desktop`).
- Python compilation across all modules and `git diff --check` passed cleanly with zero errors.
- Provider configuration runner confirmed missing credentials across cloud providers safely without
  transmitting keys or sending unauthenticated network requests.

```bash
venv/bin/python -m pytest tests/unit/test_provider_integrations.py tests/unit/test_voice_daemon_delivery.py tests/unit/test_active_desktop.py tests/unit/test_chat_audio_delivery.py tests/unit/test_agent_execution.py tests/unit/test_phase1_chat_engine.py tests/unit/test_app_factory.py tests/unit/test_security_hardening_milestone.py tests/unit/test_phase9_voice_session_security.py tests/voice/test_speech_manager.py tests/voice/test_gradio_tts.py tests/voice/test_colab_registration.py tests/voice/test_colab_runner.py tests/unit/test_terminal_failure_assistance.py -q
npm run test:desktop
venv/bin/python scripts/check_ai_providers.py
```

Add `--live` to the last command only when intentionally sending diagnostic
requests to configured cloud services. Do not run hardware tests indiscriminately
while the existing voice/camera owners are active.
