# PROJECT JARVIS OS
## MASTER ANTIGRAVITY IMPLEMENTATION PROMPT
### Futuristic AI Dashboard + Human-Like Speaking Avatar + Real AI Conversation

You are the principal software architect, senior frontend engineer, AI integration engineer, voice interaction engineer, UI/UX designer, and test engineer for my existing JARVIS AI / Agent / OS project.

**EXECUTION ENVIRONMENT:** Google Antigravity (AGY)

**PRIMARY MISSION:**

Upgrade my existing JARVIS project into a futuristic AI operating system using the supplied dashboard reference image and Gemini-generated React UI prototype.

The result must include a beautiful, human-like AI assistant avatar that can communicate with me through real AI-generated conversations, both by text and voice.

This is an implementation task inside my existing project, not a request for another standalone demonstration.

## 1. CRITICAL PROJECT RULES

1. Inspect the existing project before editing.
2. Identify its actual frontend, backend, voice engine, provider adapters, databases, API routes, and existing agent orchestration.
3. Never delete or downgrade working features unnecessarily.
4. Preserve existing functionality, settings, integrations, project history, and user data.
5. Reuse existing services and architecture wherever possible.
6. Do not replace the entire application with the Gemini prototype.
7. Integrate the new design incrementally into the existing codebase.
8. Do not invent backend endpoints or claim simulated features are operational.
9. Do not execute destructive shell commands without explicit approval.
10. Do not expose API keys in frontend files.
11. Do not overwrite unrelated user changes.
12. Keep modifications modular, testable, and reversible.
13. Create reviewable Git commits at verified milestones when the repository state allows.
14. Do not run OpenAI Codex CLI or depend on Codex execution because my current quota is exhausted.
15. Other existing provider adapters may remain installed, but they must not be invoked without availability and authorization checks.
16. Use Google Antigravity as the primary development agent for this assignment.

I want one autonomous development workflow rather than submitting a new prompt for every stage.

Do not stop after every ordinary phase. Maintain checkpoints and continue with the next safe task automatically.

Request my input only for important permissions, missing credentials, significant architectural choices, unavailable essential assets, or potentially destructive operations.

## 2. INPUT REFERENCES

I am providing two design resources:

**REFERENCE A: JARVIS DASHBOARD IMAGE**

This is the primary visual design target.

It shows:
- A futuristic dark JARVIS control center.
- A prominent holographic female AI avatar.
- Cyan and purple lighting.
- Animated speaking waveform.
- Conversation panel.
- Tasks and agents.
- Terminal and coding activity.
- System status.
- Calendar and reminders.
- Connected devices and sensors.
- Memory and knowledge.
- App integrations.
- Automation center.

Study the actual reference image and reproduce its overall appearance as closely as reasonably possible while making it responsive and functional.

Do not simply embed the reference image as a dashboard background.

Build genuine React/UI components for each visible section.

**REFERENCE B: `jarvis_os_futuristic_ai_interface.tsx`**

This is the Gemini-generated frontend prototype.
Saved in: `docs/jarvis-ui/references/jarvis_os_futuristic_ai_interface.tsx`

It contains useful starting points, including:
- HumanAIAvatar
- Female avatar ARIA
- Male avatar ATLAS
- Avatar states
- Mouth-shape animations
- Browser speech synthesis
- Browser speech recognition
- Interactive chat
- Audio waveform
- Theme management
- Dashboard components

Inspect the actual supplied source file.

Extract and improve useful code rather than blindly copying the whole prototype.

**IMPORTANT:** The Gemini prototype uses `generateSimulatedReply()` for fake conversations.

Replace this behavior in normal JARVIS conversation mode with real requests to the existing AI backend.

Do not integrate its fake terminal, robot telemetry, or agent execution as genuine functionality.

If either reference file is not accessible inside Antigravity, locate it in the workspace or report the precise missing resource. Do not fabricate its contents.

## 3. DESIRED JARVIS UI DESIGN

Create a polished futuristic interface inspired by the supplied screenshot.

### Visual theme

Background: `#050B16`

Secondary background: `#0B1525`

Glass panels: `rgba(16,30,48,0.78)`

Electric cyan: `#00D9FF`

Neon blue: `#218BFF`

Holographic purple: `#9868FF`

Success green: `#25E6A2`

Primary text: `#F0F8FF`

Secondary text: `#97AEC7`

Use:
- Premium glassmorphism
- High-quality UI typography
- Neon edge lighting
- Subtle animated gradients
- Holographic HUD elements
- Professional card layouts
- Smooth transitions
- Responsive navigation
- Elegant hover interactions
- Animated voice waveforms
- Consistent icons
- Readable contrast

Do not create a generic administration dashboard.

### Main page layout

**Top header**
- JARVIS OS branding
- Control Center
- Workspace
- Agents
- Memory
- Integrations
- Search
- Notifications
- Settings
- Date and time
- Connection status

**Left sidebar**
- Dashboard
- AI Chat
- Voice Assistant
- Agents
- Tasks
- Automation
- Developer Workspace
- Terminal
- Calendar
- Memory
- Knowledge
- Devices
- Robot Control
- Integrations
- Settings

**Central AI interaction area**
- JARVIS title
- Human-like AI avatar
- Voice activity indicator
- Animated audio waveform
- Speaking/listening state
- Microphone control
- AI response subtitles
- Chat input
- Voice selection
- Avatar selector

**Surrounding panels**
- Live conversation
- Agent activity
- Tasks and automations
- Terminal
- System telemetry
- Calendar and reminders
- Memory and knowledge
- Devices and sensors
- App integrations

The central AI avatar must be the most visually prominent element.

## 4. HUMAN-LIKE AI AVATAR — HIGHEST VISUAL PRIORITY

I want an AI that looks like a digital human and behaves like a speaking assistant.

Do not replace the avatar with a circular orb, abstract particle sphere, emoji, or static icon.

### Female avatar

Name: ARIA

Appearance:
- Professional futuristic adult female-presenting digital human
- Attractive but appropriate character design
- Expressive face
- High-quality eyes and hair
- Futuristic holographic outfit
- Cyan and purple accents
- Friendly appearance
- Natural idle animation

### Male avatar

Name: ATLAS

Appearance:
- Professional futuristic adult male-presenting digital human
- Friendly and intelligent expression
- Expressive facial features
- Futuristic clothing
- Subtle holographic lighting
- Natural idle movement

### Required avatar behavior

Implement these visual states:

1. Idle
2. Listening
3. Thinking
4. Speaking
5. Happy
6. Error
7. Offline

During speech, the avatar must:
- Move its mouth.
- Blink naturally.
- Make subtle head movements.
- Display matching subtitles.
- Animate the speech waveform.
- Return to idle when speech ends.

### Avatar technology

First inspect the Gemini SVG avatar implementation.

Determine whether it can be improved sufficiently or whether a compatible VRM/glTF-based avatar is needed for the desired appearance.

Prefer a high-quality rigged 3D avatar using an existing compatible rendering solution if suitable licensed assets are available.

Do not pretend a basic SVG face is photorealistic.

Do not download unlicensed character models or copyrighted assets without permission.

If suitable 3D assets are unavailable:
- Preserve and improve the working SVG avatar.
- Implement proper reusable avatar component architecture.
- Provide a clear asset requirement report.
- Make future 3D avatar replacement straightforward.

Keep the rendering lightweight enough for my HP Pavilion Ryzen 5 5625U laptop with 8 GB RAM and integrated AMD Radeon graphics.

Also provide an appropriate low-performance mode for Raspberry Pi-class hardware.

## 5. CONNECT REAL AI CHATTING

**THIS IS THE HIGHEST FUNCTIONAL PRIORITY.**

My existing JARVIS should support actual open-ended conversation.

The Gemini prototype currently contains simulated response logic.

Remove that simulated logic from the normal production chat path.

### Required conversation flow

User types or speaks a question.

JARVIS receives the question.

The existing JARVIS backend sends it to an available AI provider or local model.

The AI generates a meaningful response.

The response appears in the chat interface.

The assistant speaks that response aloud when voice output is enabled.

The avatar animates during speech.

The conversation is retained using the existing conversation storage when available.

### AI provider integration

Inspect existing adapters for:
- Google Gemini
- OpenAI
- OpenRouter
- Local LLMs
- Other configured AI inference services

Reuse functioning provider integrations.

Do not assume CLI subscriptions provide API credits or inference endpoints.

Because my Codex quota is exhausted, do not require Codex CLI to power voice conversations.

Implement provider availability checks and graceful fallback among providers actually configured and authorized.

### Conversation requirements

- Real AI responses
- Multi-turn conversation
- Conversation history
- Context management
- Streaming responses where available
- Model/provider status
- Stop generation
- Retry response
- Error handling
- Provider fallback
- Message timestamps
- Text and voice interaction through one conversation system

Make conversation work independently of the avatar so that text chat remains usable during voice or rendering failures.

## 6. REAL-TIME VOICE ENGINE

Integrate the avatar with the existing JARVIS voice infrastructure.

Inspect current speech recognition and speech synthesis implementations before replacing anything.

### Speech-to-text

Support:
- Browser microphone permission
- Start listening
- Stop listening
- Real voice transcription
- Transcription error handling
- Microphone status indicator
- Language selection where supported

Use an existing local or cloud speech recognition service if already implemented.

Browser SpeechRecognition can be a fallback where available.

### Text-to-speech

Support:
- Real spoken AI responses
- Voice selection
- Speech speed
- Mute/unmute
- Stop speaking
- Audio playback state
- Subtitles
- Voice interruption

Use an existing JARVIS TTS service if available.

Browser SpeechSynthesis may be retained as a fallback.

### Lip synchronization

Use speech-provider phoneme or viseme timing when available.

Otherwise use appropriate audio/cadence-driven approximate mouth movement and explicitly document the limitation.

The animated mouth should only indicate active speech when speech or an intentional silent animation is actually occurring.

### Full voice pipeline

Microphone → Speech recognition → AI backend → Generated response → TTS → Avatar animation → Spoken output.

Handle:
- Permission denied
- Audio unavailable
- TTS errors
- Provider timeouts
- Network disconnection
- Interrupted responses
- Repeated rapid interactions

Prevent duplicate replies, overlapping speech, race conditions, and feedback loops where the assistant hears its own audio.

## 7. REUSE EXISTING MULTI-AGENT INFRASTRUCTURE

Do not rebuild or replace the existing JARVIS multi-agent orchestrator unnecessarily.

Connect the new UI to the current agent management services.

Show:
- Connected agent names
- Provider information
- Current task
- Real execution status
- Progress where measurable
- Logs
- Errors
- Task history

Do not display fabricated percentages as real progress.

Implement appropriate UI controls for supported actions:
- Assign task
- Pause
- Resume
- Cancel
- View results

Respect existing authentication and execution permissions.

Do not invoke Codex during this implementation unless I separately authorize its use after quota recovery.

Preserve existing provider adapters for future use.

## 8. REST OF DASHBOARD

Implement or integrate the remaining dashboard modules using existing backend capabilities.

### System monitoring

Real metrics where available:
- CPU
- RAM
- Disk
- GPU
- Temperature
- Network
- Backend health

Show "Unavailable" when a measurement cannot be obtained.

### Developer workspace

Reuse existing:
- Terminal service
- Project explorer
- Logs
- Git integration
- Test reporting
- Developer API
- Agent activity

Keep risky terminal commands subject to proper sandbox and approval checks.

### Memory

Connect to existing conversation and knowledge storage.

Do not replace the database without a documented migration.

### Automations

Connect existing workflow engines and scheduled task services.

### Robot controls

Preserve Raspberry Pi 5 and ESP32-S3 integration architecture.

Do not send real motor commands during frontend testing.

Use simulation for unconnected hardware and clearly label it.

Physical controls require capability checks, explicit authorization, safe defaults, and an emergency-stop mechanism.

### Integrations

Show genuine status for connected services.

Do not display demo integrations as active.

## 9. RESPONSIVE AND PERFORMANCE REQUIREMENTS

Support:
- 1920×1080 desktop
- 1366×768 laptop
- Tablet
- Mobile

The avatar should remain visually prominent without covering conversation controls.

Use lazy loading and appropriate rendering performance controls.

Avoid excessive GPU usage and memory consumption.

Implement reduced-motion support and keyboard accessibility.

Keep the UI responsive while speech synthesis, API requests, and agent updates are active.

## 10. PHASED AUTONOMOUS IMPLEMENTATION

Follow the phases below in order.

### Phase 1 — Read-Only Repository Audit

Inspect:
- Project structure
- Existing frontend
- Existing backend
- Chat endpoints
- Provider adapters
- Voice services
- Databases
- React/Vite/Tailwind setup, if present
- Existing tests
- Current Git state

Create `docs/JARVIS_UI_INTEGRATION_PLAN.md` with findings and an implementation checklist.

Do not modify core application behavior during the audit.

### Phase 2 — Preserve Existing Functionality

Run baseline checks where feasible.

Identify fragile integration points.

Use an isolated working branch if appropriate.

Do not discard existing uncommitted changes.

### Phase 3 — Futuristic UI Integration

Implement the new design system, dashboard shell, navigation, reusable components, panels, and responsive layouts.

Match the supplied reference image.

Preserve backend API compatibility.

### Phase 4 — Animated Avatar

Integrate and improve ARIA and ATLAS.

Implement avatar states, selection, animations, and performance fallbacks.

### Phase 5 — Real AI Chat

Connect the chat UI to the existing backend.

Replace simulated replies in production conversation mode.

Validate multi-turn conversation and actual model responses.

### Phase 6 — Speech and Avatar Integration

Connect microphone, speech recognition, text-to-speech, subtitles, and animated mouth movements.

Validate speech start, stop, interruption, and error recovery.

### Phase 7 — Existing JARVIS Modules

Connect remaining panels to available real services.

Leave unsupported services explicitly unavailable rather than pretending integration is complete.

### Phase 8 — Real Browser Testing

Use Playwright with an available Chromium/Chrome browser.

Verify:
- Dashboard rendering
- Navigation
- Avatar selection
- Real chat requests
- Speech playback where testable
- Avatar state transitions
- Error handling
- Responsive layout
- Console errors
- Existing feature regressions

Test both dark-theme appearance and mobile layouts.

Capture screenshots for visual comparison against the reference image.

### Phase 9 — Optimization and Final Review

Fix confirmed issues.

Remove duplicated code and unused demo integrations where safe.

Do not remove working legacy features.

Update documentation and perform final integration checks.

## 11. STRICT QUALITY GATES

Before marking a feature complete, verify its actual implementation.

For AI chat:
- Send a real prompt.
- Confirm a real backend request.
- Confirm an AI-generated response.
- Confirm conversation history behavior.

For voice:
- Verify that speech output works in a supported browser.
- Confirm subtitles.
- Confirm avatar speaking and idle states.
- Confirm interruption handling.

For the UI:
- Check viewport alignment.
- Check text readability.
- Verify interactions.
- Compare screenshots against the supplied reference.

For existing JARVIS functionality:
- Execute available regression tests.
- Report any regressions.
- Restore compatibility.

Do not claim successful testing when tests were skipped or blocked.

## 12. PROGRESS REPORTING

Maintain:

`docs/JARVIS_UI_INTEGRATION_PLAN.md`

`docs/JARVIS_UI_TEST_REPORT.md`

Record:
- Current phase
- Completed features
- Files changed
- Tests run
- Failures
- Blockers
- Next steps

If your execution session is interrupted, leave clear instructions so development can resume safely from the most recent verified checkpoint.

Do not repeatedly ask me to paste the next phase prompt.

## 13. REQUIRED FINAL RESULT

At completion, I should be able to:

1. Launch my existing JARVIS application.
2. See the futuristic dashboard based on my reference image.
3. Select the ARIA or ATLAS assistant.
4. Type a natural question and receive a real AI-generated answer.
5. Speak into my microphone.
6. Have JARVIS understand the voice input.
7. Hear the AI response.
8. Watch the avatar animate while speaking.
9. View conversation history.
10. Use my existing agent and developer tools.
11. Access other JARVIS modules without losing existing features.

Provide a final report including verified functionality, test results, remaining limitations, and exact startup commands.
