# Admin sign-in, provider settings, and voice delivery

## Implemented

Administrator PIN verification now establishes the same expiring session used by
the dashboard, chat authorization, and voice service. Previously it verified the
PIN without changing the active Guest identity. The dashboard has explicit sign-in
and sign-out actions and refreshes the displayed role when a session expires.
Automatic voice identification preserves a valid PIN session without capturing a
camera frame or extending the session. Face recognition alone does not grant
administrator authority. Individual privileged settings changes still require a
fresh PIN and explicit confirmation.

First-time setup supports an explicit PIN-only account; a camera is optional.
Setup cannot overwrite an existing administrator. Account files are saved
atomically with private permissions, and failed saves do not leave a phantom
administrator in memory. Existing accounts and PINs were not changed by this work.

Integrations now includes a provider panel with configured/disabled/available
states, confirmed model selection, and an explicit single-provider generation
test. A configured key is not presented as a passed test. Errors are displayed
without raw provider responses or credentials. Saving replacements continues to
use the existing protected Integrations form. No credentials from chat were saved
or sent to collaborators.

Voice commands submit inference once and enqueue one reply. A bounded lazy worker
serializes delivery, records queued/synthesizing/playing/completed/failed/cancelled
states, and preserves confirmed task results if the audio queue rejects delivery.
Cancellation cannot resurrect a finished job or stop a newer reply through a stale
ownership token. Playback completion uses the actual child-process result;
playback waits release the lock so interruption remains possible. WAV duration
sets both the playback allowance and the microphone-pause lease, avoiding a fixed
15-second cutoff or a 10-second capture pause on long replies. Unknown formats
use a bounded conservative allowance. The owning player renews its lease every
ten seconds so the capture daemon's 30-second telemetry freshness limit does not
expire during a long answer; a superseded player cannot renew the new owner's
lease.

The voice-job panel renders reply text as text, has explicit failure messages,
encodes cancellation identifiers, and reports rejected cancellation requests.

## Work ownership and external CLI results

- Codex/root: administrator session and setup repairs, integration, voice-job UI,
  playback-lease correction, focused regressions, live checks, and documentation.
- Provider UI delegate: provider-settings module and tests. Antigravity CLI was
  dispatched in isolated sanitized staging, but its first headless run denied
  command permissions and produced no edits. A later code-only attempt had no
  verified final result. The delivered module is the delegate's reviewed local
  implementation; it is not claimed as successful Antigravity-generated output.
- Voice delegate/Copilot: authenticated Copilot CLI produced scoped edits after a
  tool-configuration retry. The delegate reviewed and corrected them before
  integration. No credentials, biometric data, or private runtime stores were
  included in the dispatch.

## Observed live behavior

Final affected regressions: **138 Python tests passed in 6.73 seconds** and
**45 frontend tests passed**. Dashboard JavaScript syntax and Git whitespace
checks passed. Identity tests use a temporary private account store; playback
tests mock devices. These totals cover the affected areas, not every subsystem.
After adding lease renewal, the affected delivery/daemon/chat-audio tests passed
**61 tests in 2.59 seconds**, including ownership and long-reply regressions.
Python compilation and whitespace checks also passed after that final change.

Read-only checks found an existing administrator, Guest authority while signed
out, no PIN lockout, and the new logout, PIN-only enrollment schema, and queued
voice-command route loaded in the service. No actual administrator login was
attempted, because the user's PIN must remain local. To sign in, open the Guest
badge, then use **Sign in as administrator** with the existing PIN. Sessions
expire after five minutes. Refresh the page to load the new dashboard controls.
The provider module and updated voice-job UI were served over HTTP 200 with their
new content confirmed. After the user authenticated the restart, systemd reported
the core active/running with PID 6167 and start time 19 November 2026, 02:30:52 GMT,
later than the final speech-manager edit at 02:24:50 GMT. OpenAPI, identity status,
and voice status returned HTTP 200 from the new process. The queued voice route
and logout route were present, and voice status loaded the speech manager. The
final playback changes are therefore loaded. The existing voice daemon reported
standby listening, microphone ownership, and unmuted state; telemetry alone does
not establish transcription accuracy, speaker audibility, or acoustic acceptance.

Ollama was available with `llama3.2:1b`. Gemini, OpenAI, Anthropic, NVIDIA,
OpenRouter, Groq, and Together all reported no usable configured credential.
Consequently no live cloud inference result can be certified.

One explicit local model-only probe (`use_tools=false`, no speech, no fallback)
asked "What is 17 plus 25? Reply with only the number." It returned "32" after
23.46 seconds. A separate normal tool-enabled request, "calculate 17 + 25",
returned the verified calculator result **42** in **0.04 seconds**. This is a
concrete model-quality limitation, not evidence that general answers are reliable.

## Remaining work

The queue and job history are in-process and do not survive a core restart.
Cancellation prevents further delivery but cannot abort synthesis already running
inside a provider call. Direct chat/browser audio paths retain their existing
interfaces. Real microphone transcription, wake-word accuracy, acoustic feedback,
and speaker audibility need a coordinated acceptance session with the sole capture
owner. Automated playback tests use mocks and are not hardware evidence.

Replace credentials exposed in chat using the local Integrations form; do not
reuse or reproduce them in reports. Then run explicit provider smoke tests and
compare response quality and latency before choosing a default model. General
reasoning quality, durable jobs, and broader application acceptance remain open;
this milestone is not a claim that the whole project is complete.
