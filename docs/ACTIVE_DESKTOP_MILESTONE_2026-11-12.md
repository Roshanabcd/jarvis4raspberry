# Active desktop assistance — 12 November 2026

JARVIS now has an explicit dashboard activation flow that combines screen sharing, reuse of the existing voice owner, and spoken chat replies. This is an incremental implementation, not verification that every JARVIS subsystem or arbitrary task works.

## Using active mode

After deployment, open `http://127.0.0.1:8000`, select **AI Chat**, and use **Activate JARVIS**. Choose the screen or window in the browser's sharing picker. The microphone option reuses the existing voice service; it does not open a browser microphone stream. The speaker option enables spoken chat replies.

The dashboard shows a live preview and uploads a bounded frame about every three seconds. **Read screen text** uses local Tesseract OCR. **Ask about screen** sends the latest frame to local Ollama/Moondream. Neither mode executes instructions found in the image. The returned text is untrusted and may be wrong. These controls do not automatically attach screen contents to every chat or voice request.

**Stop active mode**, the browser's Stop Sharing control, or closing the dashboard releases the browser stream. A 30-second heartbeat lease stops session-owned voice resources and clears the stored frame after disconnection. Voice services that were already running retain their prior ownership. A separately managed voice daemon is reported as an external owner; this does not prove that it is currently listening or unmuted.

The existing **Computer Use** tab provides X11 mouse, keyboard, window, and screenshot controls. It operates the host desktop, which may differ from a selected browser tab or window. Those existing controls were not comprehensively validated by this increment. Wayland input control is not implemented here.

## Implemented and repaired

- Single active browser session, unguessable session token, loopback/Host/Origin checks, explicit dashboard header, bounded image upload/dimensions, fresh-frame checks, and expiry after disconnection.
- Frames are normalized in memory. The new capture handler does not create screenshot files. OCR sends image bytes over standard input and reads standard output.
- One vision analysis at a time, with a 120-second inference timeout; a separate OCR slot has a 20-second timeout. Revoked sessions cannot retrieve completed results.
- Browser cleanup handles denied permission, an interrupted picker, a competing tab, stopped sharing, and late asynchronous responses.
- Auto-Speak now reaches the chat API. Browser speech delivery avoids simultaneous system playback. Missing audio produces an explicit audio error rather than a fake playable asset.
- eSpeak staging uses standard input, tolerates a longer bounded startup, and returns failure if no audio file was produced. Staging failure never invokes a side-effectful direct speech fallback.
- Push-to-talk and the voice start endpoint do not create a second capture while the dedicated daemon owns the microphone. Daemon detection supplies the correct user-bus environment when called from a system service and fails closed when ownership cannot be determined.
- Neural chat uses the voice session's PIN-gated authorization role. Model discovery retains the configured chat model instead of choosing the first discovered vision model.
- The source service unit now uses the project Python environment. The previously prepared localhost binding is retained. The deployment script backs up the installed unit, validates readiness, and restores the previous unit on failure; it does not roll back application source changes.

## Research and design evidence

Browser capture requires a user gesture and a fresh user-selected source; activation cannot silently grant screen permissions. See [MDN getDisplayMedia](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getDisplayMedia).

The native input layer is X11-specific; xdotool documents limitations under Wayland. See [xdotool](https://github.com/jordansissel/xdotool).

Ollama accepts base64 image data for vision inference. See [Ollama vision](https://docs.ollama.com/capabilities/vision). Local model installation alone did not establish reliable inference in this environment.

Tesseract supports image input from stdin and text output to stdout, allowing this OCR path to avoid writing screen images to disk. See the [Tesseract command manual](https://github.com/tesseract-ocr/tesseract/blob/main/doc/tesseract.1.asc).

## Verified outcomes

- Chrome: dashboard active-mode controls rendered; activation with capture disabled and subsequent shutdown changed the UI correctly. The actual browser screen-picker approval/capture remains a manual acceptance check.
- Microphone/speaker hardware was detected, and the dedicated voice daemon was active. This is not end-to-end verification of recognition or an acoustic speaker measurement.
- After the operator installed eSpeak, local synthesis produced playable WAV audio. A 1.92-second test phrase was sent through the real `pw-play` command, which exited with status 0. The voice is a local fallback, not a verified clone.
- A direct Moondream test correctly identified a solid red image, but shared-frame tests returned empty answers. Increasing context helped one direct check but did not resolve the general problem. Qwen 3.5 4B timed out while loading within the 180-second diagnostic bound. **Visual question-answering remains unreliable; errors are reported explicitly.**
- Bash, Python, dashboard JavaScript, service-unit syntax, and Git whitespace checks passed.
- Final automated regression: **98 Python tests passed in 5.57 seconds**, spanning active sessions, chat/audio delivery, agent execution, providers, app construction, security, and voice. **Five frontend lifecycle tests passed** with Node's test runner.
- Operator installed eSpeak and Tesseract and applied the service update. The deployed service was independently verified active, with port 8000 listening on **127.0.0.1** and the new desktop status endpoint returning HTTP 200.
- The deployed OCR endpoint correctly read a generated terminal frame: `ModuleNotFoundError: No module named 'demo_module'`. This test used a synthetic frame rather than capturing personal screen content.
- The deployed chat endpoint answered `2 + 2` as `4`, synthesized eSpeak audio, and served a valid **3.04-second WAV** over its audio endpoint. This verifies the deterministic calculator and audio delivery, not general neural reasoning.
- The live acceptance session stopped successfully and returned to inactive state.

## Deployment and remaining acceptance

### Voice delivery and status follow-up

- The voice daemon submits a command once. A timeout, connection failure, HTTP
  error, invalid JSON, or empty result now leaves completion explicitly unverified;
  it no longer falls back to a second local execution that could repeat an action.
  This does not provide durable exactly-once execution or automatic recovery.
- The daemon publishes a private, atomic status file every two seconds. It contains
  state, running/muted flags, timestamp, and process ID; no transcripts or identity
  data. Readers reject malformed data and samples older than ten seconds.
- Both voice status routes use the external owner's fresh telemetry. Missing
  telemetry produces an unknown state, rather than the idle backend's state.
  Backend-owned voice retains its existing status interface.
- Live verification confirmed the running daemon and `/api/voice/status` reported
  `STANDBY_LISTENING`, `capture_owner: voice_daemon`, and fresh telemetry. Active
  desktop status returned HTTP 200 and inactive. These are process/state checks,
  not proof of successful microphone recognition.
- Follow-up regression: **117 Python tests passed in 2.61 seconds** and **five
  frontend lifecycle tests passed**. Python compilation and Git whitespace checks
  passed. Failure cases use mocks; no extra microphone capture was launched.
- After the operator restarted the core service, live verification confirmed both
  `/api/voice/status` and `/api/voice/wake_status` returned HTTP 200 and agreed on
  `STANDBY_LISTENING` with `capture_owner: voice_daemon`. Telemetry ages were
  1.4 and 1.5 seconds. Both services were active; port 8000 remained bound to
  `127.0.0.1`. Desktop sharing remained inactive. The final dashboard header
  status correction is now deployed.

Review `services/jarvis-core.service` and `scripts/deploy_local_service.sh` before applying privileged changes. The operator completed the approved Tesseract installation and service deployment. The updated unit and live API were independently verified afterward.

Remaining manual acceptance:

1. Select the intended screen/window in the browser sharing picker, confirm its preview, and verify that Stop Sharing releases it.
2. Confirm the existing voice daemon hears the wake phrase, transcribes a command, and speaks a reply without a second capture owner.
3. Validate native mouse and keyboard operations against a disposable test window. No unattended clicks, typing, or terminal execution were performed for this milestone.

Unavailable sensors, robot actuation, general visual reasoning, voice cloning, cross-process voice mute control, and arbitrary automatic feature installation are not certified by this milestone. Hardware remains disarmed; no motor actions were tested.
