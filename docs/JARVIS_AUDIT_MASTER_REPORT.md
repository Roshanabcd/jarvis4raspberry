# JARVIS OS audit · 21 November 2026

## Current handoff review · 21 November 2026

The historical page observations and screenshots below are preserved. Current issue status is maintained in JARVIS_BUGS_AND_IMPROVEMENTS.json; do not interpret historical completion statements as fresh acceptance. The original nine findings remain open or verified_offline, and deployment finding BUG-003 is now tracked separately.

The authorized core restart succeeded: health returned OK, the catalog exposed 45 apps, and the suite reported 42 mounted modules. All 25 new extension UI and health routes returned HTTP 200. These observations verify reachability only. The catalog nevertheless marked those 25 interfaces in_development because its route inspection missed nested FastAPI routers. The five-test correction is now integrated into the current source, pending deployment verification. Live human speech, audible output, offline wake detection and representative AI task quality remain unverified in this checkpoint.

The roadmap now separates already implemented fixes from outstanding checks. Handoff copies are synchronized; generic orchestration examples do not authorize installs, extra daemons, spending or privileged actions. Preserve current user changes and historical evidence.

## Implementation follow-up

The original observations and 92 screenshots below describe the audit baseline. The current checkout passed an isolated Chromium routing check for all 23 tabs at 1440×900 and 1280×720. ArrowDown moved focus to Apps, and Space activated a category at both sizes. The connected browser ran the shell with intercepted backend requests. This verifies frontend navigation independently of provider, identity and device availability.

Three focused Ollama provider tests passed. An empty installed-model list is now treated as unavailable. Automatic selection prefers an alternative to Moondream when the configured model is missing. End-to-end generation, timing and recall still require a running local model. The issue database records implementation and verification separately.

Scope: current uncommitted feature/jarvis-ui checkout. The connected browser reached the dashboard, enumerated 22 sidebar tabs and confirmed #estop-btn visible and enabled. Account has a separate entry point.

## Verdict

Flagship readiness is unproven. The shell provides discoverable sections and an accessible emergency-stop label. Inconsistent keyboard navigation and blocking feedback undermine routine use. Numeric UI, UX, reliability, AI, performance and RBAC grades are withheld where representative tasks were not measured.

## Page evidence

Source locations refer to apps/dashboard/static/index.html. Captures document rendered state only. Widths are CSS pixels. Control counts include hidden controls.

| View | Panel / source line | Evidence | Measured panel overflow (1440 / 1280) |
|---|---|---|---|
| home | #tab-home · 1025 | [home-1280](audit-screenshots/home-1280.png) · [home-1440](audit-screenshots/home-1440.png) | 0 / unavailable |
| apps | #tab-apps · 2135 | [apps-1280](audit-screenshots/apps-1280.png) · [apps-1440](audit-screenshots/apps-1440.png) | 0 / 0 |
| chat | #tab-chat · 1088 | [chat-1280](audit-screenshots/chat-1280.png) · [chat-1440](audit-screenshots/chat-1440.png) | 0 / 0 |
| voice | #tab-voice · 1174 | [voice-1280](audit-screenshots/voice-1280.png) · [voice-1440](audit-screenshots/voice-1440.png) | 0 / 0 |
| aistudio | #tab-aistudio · 1368 | [aistudio-1280](audit-screenshots/aistudio-1280.png) · [aistudio-1440](audit-screenshots/aistudio-1440.png) | 0 / 0 |
| vision | #tab-vision · 1413 | [vision-1280](audit-screenshots/vision-1280.png) · [vision-1440](audit-screenshots/vision-1440.png) | 0 / 0 |
| robot | #tab-robot · 1496 | [robot-1280](audit-screenshots/robot-1280.png) · [robot-1440](audit-screenshots/robot-1440.png) | 0 / 0 |
| sensors | #tab-sensors · 1539 | [sensors-1280](audit-screenshots/sensors-1280.png) · [sensors-1440](audit-screenshots/sensors-1440.png) | 0 / 0 |
| memory | #tab-memory · 1547 | [memory-1280](audit-screenshots/memory-1280.png) · [memory-1440](audit-screenshots/memory-1440.png) | 0 / 0 |
| automations | #tab-automations · 1569 | [automations-1280](audit-screenshots/automations-1280.png) · [automations-1440](audit-screenshots/automations-1440.png) | 0 / 0 |
| tools | #tab-tools · 1581 | [tools-1280](audit-screenshots/tools-1280.png) · [tools-1440](audit-screenshots/tools-1440.png) | 0 / 0 |
| integrations | #tab-integrations · 1618 | [integrations-1280](audit-screenshots/integrations-1280.png) · [integrations-1440](audit-screenshots/integrations-1440.png) | 0 / 0 |
| system | #tab-system · 1659 | [system-1280](audit-screenshots/system-1280.png) · [system-1440](audit-screenshots/system-1440.png) | 0 / 0 |
| logs | #tab-logs · 1667 | [logs-1280](audit-screenshots/logs-1280.png) · [logs-1440](audit-screenshots/logs-1440.png) | 0 / 0 |
| desktop | #tab-desktop · 1702 | [desktop-1280](audit-screenshots/desktop-1280.png) · [desktop-1440](audit-screenshots/desktop-1440.png) | 0 / 0 |
| computer | #tab-computer · 1835 | [computer-1280](audit-screenshots/computer-1280.png) · [computer-1440](audit-screenshots/computer-1440.png) | 0 / 0 |
| agents | #tab-agents · 2011 | [agents-1280](audit-screenshots/agents-1280.png) · [agents-1440](audit-screenshots/agents-1440.png) | 0 / 0 |
| developer | #tab-developer · 2302 | [developer-1280](audit-screenshots/developer-1280.png) · [developer-1440](audit-screenshots/developer-1440.png) | 0 / 0 |
| youtube | #tab-youtube · 2468 | Failed transition: [youtube-1280](audit-screenshots/youtube-1280.png) · [youtube-1440](audit-screenshots/youtube-1440.png) | unavailable / unavailable |
| documents | #tab-documents · 3096 | Failed transition: [documents-1280](audit-screenshots/documents-1280.png) · [documents-1440](audit-screenshots/documents-1440.png) | unavailable / unavailable |
| research | #tab-research · 2735 | Failed transition: [research-1280](audit-screenshots/research-1280.png) · [research-1440](audit-screenshots/research-1440.png) | unavailable / unavailable |
| settings | #tab-settings · 1675 | [settings-1280](audit-screenshots/settings-1280.png) · [settings-1440](audit-screenshots/settings-1440.png) | 0 / 0 |
| account | #hdr-user-pill · 888 | [account-1280](audit-screenshots/account-1280.png) · [account-1440](audit-screenshots/account-1440.png) · [account-popover](audit-screenshots/account-popover.png) | unavailable / unavailable |

## Local AI trial and remediation

**AI-001 · P1-High.** Selected ollama:moondream:latest. Two memory prompts ended with explicit provider errors at 22.065 s and 23.130 s. Code generation still pending at 25 s. Model uptime and hardware cause unknown. Verify model readiness and task suitability, expose timeout and cancellation state, and offer an explicitly chosen alternative. Test a warm available route and an unavailable fixture. Check reply content and terminal UI state separately, and record first-token and completion latency. The two failed turns did not establish memory recall accuracy. Diagnostics, scheduling, spoken output and tool execution remain unverified.

## Prioritized fixes

### BUG-001 · Account markup announces ADMIN before the identity service confirms the role. This is a misleading display, with no evidence of a backend privilege grant.

P1-High · apps/dashboard/static/index.html:3299 · #account-role-badge

Reproduce: Inspect initial account HTML before profile hydration. Expected: Unknown role displays Pending or Unavailable. Fix: Render a neutral initial badge and enable privileged controls only after confirmation. Verify: Delay the identity response and verify no ADMIN badge appears for an unverified operator.

### BUG-002 · YouTube, Documents, Research and Account failed to display during both viewport passes. Cause under investigation.

P1-High · apps/dashboard/static/index.html:3736 · nav [data-tab]

Reproduce: Click the named sidebar button and wait for the matching panel. Expected: Selected panel becomes visible and usable. Fix: Inspect panel ancestry and the selected state alongside service health. Verify: For every nav button click and expect the matching panel to be visible.

### UX-001 · Sidebar keyboard handler supports Left and Right but omits Up and Down for vertical navigation.

P2-Medium · apps/dashboard/static/index.html:3784 · nav[role=tablist]

Reproduce: Focus a sidebar tab Press ArrowDown Expected: Focus and selection advance one row. Fix: Support vertical arrow keys and expose the orientation. Verify: Focus Dashboard, press ArrowDown, expect Apps to be focused and selected.

### UX-002 · When the notification service is unavailable, launch denial uses a blocking native dialog in the launch handler.

P2-Medium · apps/dashboard/static/index.html:4006 · #tab-apps

Reproduce: Exercise an adapter denial using a test fixture. Expected: Denial reason stays in app context. Fix: Render a persistent inline error and restore focus to Launch. Verify: Assert zero dialog events and an accessible denial reason.

### UX-004 · Sidebar account shortcut is a clickable div without native keyboard activation.

P2-Medium · apps/dashboard/static/index.html:1010 · #sidebar-operator-card

Reproduce: Navigate the dashboard shortcuts with Tab Try activating the sidebar operator card using Enter. Expected: Keyboard users can open the same profile shortcut. Fix: Use a button with a visible focus indicator. Verify: Locate the shortcut by button role, focus, press Enter and assert profile is visible.

### UX-005 · Category filters use clickable divs without keyboard semantics.

P2-Medium · apps/dashboard/static/index.html:2215 · #apps-category-pills

Reproduce: Tab through the catalog filters and try selecting a category. Expected: Every category is keyboard operable. Fix: Use buttons with aria-pressed. Verify: Focus a category by role, press Space and check filtered results.

### UX-006 · Catalog counts in static filter labels disagree with the live grid of 45 Details buttons, including 20 under Available.

P2-Medium · apps/dashboard/static/index.html:2204 · #apps-status-select

Reproduce: Count visible Details buttons with All and Available selected. Expected: Filter counts match the current catalog. Fix: Derive counts and search placeholder from manifest data. Verify: Assert filter count equals matching grid card count.

### UX-003 · Saving settings uses a blocking native alert for success.

P3-Polish · apps/dashboard/static/index.html:6231 · #tab-settings

Reproduce: In an isolated test profile save a reversible preference. Expected: Save confirmation permits continued keyboard interaction. Fix: Use the shared status notification. Verify: Wait for success status and assert no native dialog.

## Visual review and design priorities

The captured views share a recognisable dark shell, persistent navigation and cyan control accents. Magenta regions are privacy masks inserted by Playwright. The captures use full-page mode, so panel height is more informative than thumbnail scale.

| View | Assessment and improvement |
|---|---|
| Dashboard | The central assistant is a clear focal point. Reduce competition from equally weighted status cards and give the current task priority. |
| Apps | Dense repeated cards turn the catalog into a long scan. Keep filters in reach, compute counts from returned manifests and surface unavailable states before launch. |
| Chat | At 1440×900 the panel alone measured 1097 px. Keep the composer in view and collapse secondary controls while reading responses. |
| Voice | The desktop panel measured 2117 px. Group active input, output and a single test action first. Put model and fallback diagnostics in expandable sections. |
| AI Studio | Input and output are easy to distinguish. Give empty output a clear next action and announce generation progress. |
| Vision | Preserve the feed as the largest element. Report feed availability and overlay availability independently. Masked imagery cannot establish camera quality. |
| Robot | Direction controls and sliders are easy to distinguish. Place arming state and limits beside the controls they govern. Actuation was outside the run. |
| Sensors | A short table leaves room for more detail. Keep a timestamp and availability reason beside each reading. |
| Memory | The long list dominates the screen. Limit initial results and make search context visible while scrolling. |
| Automations | The sparse table is scannable. Distinguish next run, last result and disabled state. |
| Tools | Preserve the split between selection and execution. Describe inputs and permissions before the run control. |
| Integrations | Distinguish adapter verification, configuration and service reachability. Masked fields prevent assessing their contents. |
| System | Dense diagnostic output requires interpretation. Lead with measured CPU, memory, timestamp and availability, with raw diagnostics below. |
| Logs | A uniform stream makes failures hard to find. Add severity and time filters and a pause control for reading. |
| Desktop | Group launch controls separately from current session status. Give failed launches a persistent reason. |
| Computer Use | Separate session, target and approval state visually. Place action feedback beside the instruction field. |
| Agents | Show current task, owner, elapsed time and latest verified outcome before configuration. |
| Account | The requested panel did not appear in the original live shell. Captures named account-1280 and account-1440 show the attempted transition, not a working profile. |
| Developer | The dense workspace needs a clear current task and last action. Keep its panel independent from every other route. |
| YouTube, Research, Documents | The browser found all three panels nested in #tab-developer. Selecting a child hides the ancestor. Fix DOM nesting and verify every destination from another tab. |
| Settings | Provide inline success feedback and preserve focus after saving. |

## Catalog and coverage

All 45 Details buttons in the live Apps grid were opened. Search with a guaranteed nonmatch returned zero Details buttons. Available returned 20, planned returned zero. The measured unit is Details buttons, not a count of verified working apps. The account popover opened. App launches, favorites persistence, role-specific forms, all secondary drawers, every category, spoken notifications and real hardware were not verified. The original browser and the fresh Chromium session served different shell revisions during the audit. Freeze the build before comparing screenshots or attributing intermittent failures. No PIN or session token is included.

## Provisional scorecard

These are reviewer judgments on the sampled shell. An unmeasured dimension has no numeric score.

| Dimension | /100 | Basis |
|---|---:|---|
| UI design | 60 | Consistent shell and focal colors, with dense small controls and long settings surfaces. |
| UX flow | 45 | Catalog search and details worked. Four requested transitions failed in the sampled shell. |
| Functional reliability | Unscored | Runtime changed and repeated connection failures affected API checks. |
| AI quality | Unscored | A representative task suite was not completed. |
| Performance | Unscored | No stable Pi CPU, frame-time or latency baseline. |
| Security/RBAC | Unscored | Initial role badge is misleading. Authorization needs separate guest/admin response assertions. |

### App detail and shell captures

[account-popover](audit-screenshots/account-popover.png) · [app-detail-0](audit-screenshots/app-detail-0.png) · [app-detail-1](audit-screenshots/app-detail-1.png) · [app-detail-10](audit-screenshots/app-detail-10.png) · [app-detail-11](audit-screenshots/app-detail-11.png) · [app-detail-12](audit-screenshots/app-detail-12.png) · [app-detail-13](audit-screenshots/app-detail-13.png) · [app-detail-14](audit-screenshots/app-detail-14.png) · [app-detail-15](audit-screenshots/app-detail-15.png) · [app-detail-16](audit-screenshots/app-detail-16.png) · [app-detail-17](audit-screenshots/app-detail-17.png) · [app-detail-18](audit-screenshots/app-detail-18.png) · [app-detail-19](audit-screenshots/app-detail-19.png) · [app-detail-2](audit-screenshots/app-detail-2.png) · [app-detail-20](audit-screenshots/app-detail-20.png) · [app-detail-21](audit-screenshots/app-detail-21.png) · [app-detail-22](audit-screenshots/app-detail-22.png) · [app-detail-23](audit-screenshots/app-detail-23.png) · [app-detail-24](audit-screenshots/app-detail-24.png) · [app-detail-25](audit-screenshots/app-detail-25.png) · [app-detail-26](audit-screenshots/app-detail-26.png) · [app-detail-27](audit-screenshots/app-detail-27.png) · [app-detail-28](audit-screenshots/app-detail-28.png) · [app-detail-29](audit-screenshots/app-detail-29.png) · [app-detail-3](audit-screenshots/app-detail-3.png) · [app-detail-30](audit-screenshots/app-detail-30.png) · [app-detail-31](audit-screenshots/app-detail-31.png) · [app-detail-32](audit-screenshots/app-detail-32.png) · [app-detail-33](audit-screenshots/app-detail-33.png) · [app-detail-34](audit-screenshots/app-detail-34.png) · [app-detail-35](audit-screenshots/app-detail-35.png) · [app-detail-36](audit-screenshots/app-detail-36.png) · [app-detail-37](audit-screenshots/app-detail-37.png) · [app-detail-38](audit-screenshots/app-detail-38.png) · [app-detail-39](audit-screenshots/app-detail-39.png) · [app-detail-4](audit-screenshots/app-detail-4.png) · [app-detail-40](audit-screenshots/app-detail-40.png) · [app-detail-41](audit-screenshots/app-detail-41.png) · [app-detail-42](audit-screenshots/app-detail-42.png) · [app-detail-43](audit-screenshots/app-detail-43.png) · [app-detail-44](audit-screenshots/app-detail-44.png) · [app-detail-5](audit-screenshots/app-detail-5.png) · [app-detail-6](audit-screenshots/app-detail-6.png) · [app-detail-7](audit-screenshots/app-detail-7.png) · [app-detail-8](audit-screenshots/app-detail-8.png) · [app-detail-9](audit-screenshots/app-detail-9.png)
## AI, media and access coverage

Provider identity, diagnostics accuracy, memory recall, tool execution, scheduling, code quality, streaming latency, speech playback and admin enforcement require live task evidence. No benchmark or hardware verification is claimed. Measure first visible token and completion separately. Compare diagnostics against timestamped telemetry and run recall using a fresh synthetic conversation. For Pi 5 instrumentation, sample CPU and resident memory during idle and active inference before changing polling intervals or model residency. Fake browser devices do not isolate backend camera or motor services.

## Browser diagnostics

Failures below are observations, including possible cancellation during navigation. Runtime event collection applies only to the instrumented session. Initial MCP navigation reported one console error.

~~~json
{
  "rows": [
    {
      "key": "home",
      "width": 1440,
      "overflow": 0,
      "height": 1170.59375,
      "controls": 30,
      "unnamed": 0,
      "panelWidth": 1228
    },
    {
      "key": "apps",
      "width": 1440,
      "overflow": 0,
      "height": 3859.5,
      "controls": 138,
      "unnamed": 0,
      "panelWidth": 1228
    },
    {
      "key": "chat",
      "width": 1440,
      "overflow": 0,
      "height": 1097,
      "controls": 177,
      "unnamed": 0,
      "panelWidth": 1228
    },
    {
      "key": "voice",
      "width": 1440,
      "overflow": 0,
      "height": 2117,
      "controls": 28,
      "unnamed": 0,
      "panelWidth": 1228
    },
    {
      "key": "aistudio",
      "width": 1440,
      "overflow": 0,
      "height": 491.0000305175781,
      "controls": 6,
      "unnamed": 0,
      "panelWidth": 1228
    },
    {
      "key": "vision",
      "width": 1440,
      "overflow": 0,
      "height": 652.078125,
      "controls": 10,
      "unnamed": 0,
      "panelWidth": 1228
    },
    {
      "key": "robot",
      "width": 1440,
      "overflow": 0,
      "height": 580,
      "controls": 18,
      "unnamed": 0,
      "panelWidth": 1228
    },
    {
      "key": "sensors",
      "width": 1440,
      "overflow": 0,
      "height": 294,
      "controls": 1,
      "unnamed": 0,
      "panelWidth": 1228
    },
    {
      "key": "memory",
      "width": 1440,
      "overflow": 0,
      "height": 2209,
      "controls": 54,
      "unnamed": 0,
      "panelWidth": 1228
    },
    {
      "key": "automations",
      "width": 1440,
      "overflow": 0,
      "height": 246,
      "controls": 5,
      "unnamed": 0,
      "panelWidth": 1228
    },
    {
      "key": "tools",
      "width": 1440,
      "overflow": 0,
      "height": 646,
      "controls": 104,
      "unnamed": 0,
      "panelWidth": 1228
    },
    {
      "key": "integrations",
      "width": 1440,
      "overflow": 0,
      "height": 991,
      "controls": 17,
      "unnamed": 0,
      "panelWidth": 1228
    },
    {
      "key": "system",
      "width": 1440,
      "overflow": 0,
      "height": 585,
      "controls": 1,
      "unnamed": 0,
      "panelWidth": 1228
    },
    {
      "key": "logs",
      "width": 1440,
      "overflow": 0,
      "height": 505,
      "controls": 1,
      "unnamed": 0,
      "panelWidth": 1228
    },
    {
      "key": "desktop",
      "width": 1440,
      "overflow": 0,
      "height": 1081.1875,
      "controls": 30,
      "unnamed": 0,
      "panelWidth": 1228
    },
    {
      "key": "computer",
      "width": 1440,
      "overflow": 0,
      "height": 1374,
      "controls": 37,
      "unnamed": 0,
      "panelWidth": 1228
    },
    {
      "key": "agents",
      "width": 1440,
      "overflow": 0,
      "height": 948,
      "controls": 13,
      "unnamed": 0,
      "panelWidth": 1228
    },
    {
      "key": "developer",
      "width": 1440,
      "overflow": 0,
      "height": 1480,
      "controls": 176,
      "unnamed": 0,
      "panelWidth": 1228
    },
    {
      "key": "youtube",
      "width": 1440,
      "error": "locator.waitFor: Timeout 1800ms exceeded.",
      "panelWidth": 1440
    },
    {
      "key": "documents",
      "width": 1440,
      "error": "locator.waitFor: Timeout 1800ms exceeded.",
      "panelWidth": 1440
    },
    {
      "key": "research",
      "width": 1440,
      "error": "locator.waitFor: Timeout 1800ms exceeded.",
      "panelWidth": 1440
    },
    {
      "key": "settings",
      "width": 1440,
      "overflow": 0,
      "height": 223,
      "controls": 6,
      "unnamed": 0,
      "panelWidth": 1228
    },
    {
      "key": "account",
      "width": 1440,
      "error": "locator.waitFor: Timeout 1800ms exceeded.",
      "panelWidth": 1440
    },
    {
      "key": "account",
      "width": 1440,
      "error": "locator.waitFor: Timeout 1800ms exceeded.",
      "panelWidth": 1440
    },
    {
      "key": "home",
      "width": 1280,
      "error": "page.screenshot: Timeout 5000ms exceeded.",
      "panelWidth": 1280
    },
    {
      "key": "apps",
      "width": 1280,
      "overflow": 0,
      "height": 518,
      "controls": 3,
      "unnamed": 0,
      "panelWidth": 1068
    },
    {
      "key": "chat",
      "width": 1280,
      "overflow": 0,
      "height": 1032,
      "controls": 177,
      "unnamed": 0,
      "panelWidth": 1068
    },
    {
      "key": "voice",
      "width": 1280,
      "overflow": 0,
      "height": 2118,
      "controls": 28,
      "unnamed": 0,
      "panelWidth": 1068
    },
    {
      "key": "aistudio",
      "width": 1280,
      "overflow": 0,
      "height": 491,
      "controls": 6,
      "unnamed": 0,
      "panelWidth": 1068
    },
    {
      "key": "vision",
      "width": 1280,
      "overflow": 0,
      "height": 594.21875,
      "controls": 10,
      "unnamed": 0,
      "panelWidth": 1068
    },
    {
      "key": "robot",
      "width": 1280,
      "overflow": 0,
      "height": 580,
      "controls": 18,
      "unnamed": 0,
      "panelWidth": 1068
    },
    {
      "key": "sensors",
      "width": 1280,
      "overflow": 0,
      "height": 103,
      "controls": 1,
      "unnamed": 0,
      "panelWidth": 1068
    },
    {
      "key": "memory",
      "width": 1280,
      "overflow": 0,
      "height": 148,
      "controls": 4,
      "unnamed": 0,
      "panelWidth": 1068
    },
    {
      "key": "automations",
      "width": 1280,
      "overflow": 0,
      "height": 143,
      "controls": 1,
      "unnamed": 0,
      "panelWidth": 1068
    },
    {
      "key": "tools",
      "width": 1280,
      "overflow": 0,
      "height": 646,
      "controls": 104,
      "unnamed": 0,
      "panelWidth": 1068
    },
    {
      "key": "integrations",
      "width": 1280,
      "overflow": 0,
      "height": 1016,
      "controls": 17,
      "unnamed": 0,
      "panelWidth": 1068
    },
    {
      "key": "system",
      "width": 1280,
      "overflow": 0,
      "height": 585,
      "controls": 1,
      "unnamed": 0,
      "panelWidth": 1068
    },
    {
      "key": "logs",
      "width": 1280,
      "overflow": 0,
      "height": 505,
      "controls": 1,
      "unnamed": 0,
      "panelWidth": 1068
    },
    {
      "key": "desktop",
      "width": 1280,
      "overflow": 0,
      "height": 1144.1875,
      "controls": 60,
      "unnamed": 0,
      "panelWidth": 1068
    },
    {
      "key": "computer",
      "width": 1280,
      "overflow": 0,
      "height": 1574,
      "controls": 44,
      "unnamed": 0,
      "panelWidth": 1068
    },
    {
      "key": "agents",
      "width": 1280,
      "overflow": 0,
      "height": 949,
      "controls": 13,
      "unnamed": 0,
      "panelWidth": 1068
    },
    {
      "key": "developer",
      "width": 1280,
      "overflow": 0,
      "height": 1068,
      "controls": 160,
      "unnamed": 0,
      "panelWidth": 1068
    },
    {
      "key": "youtube",
      "width": 1280,
      "error": "locator.waitFor: Timeout 1800ms exceeded.",
      "panelWidth": 1280
    },
    {
      "key": "documents",
      "width": 1280,
      "error": "locator.waitFor: Timeout 1800ms exceeded.",
      "panelWidth": 1280
    },
    {
      "key": "research",
      "width": 1280,
      "error": "locator.waitFor: Timeout 1800ms exceeded.",
      "panelWidth": 1280
    },
    {
      "key": "settings",
      "width": 1280,
      "overflow": 0,
      "height": 223,
      "controls": 6,
      "unnamed": 0,
      "panelWidth": 1068
    },
    {
      "key": "account",
      "width": 1280,
      "error": "locator.waitFor: Timeout 1800ms exceeded.",
      "panelWidth": 1280
    },
    {
      "key": "account",
      "width": 1280,
      "error": "locator.waitFor: Timeout 1800ms exceeded.",
      "panelWidth": 1280
    }
  ],
  "events": [
    [
      "boot",
      "console",
      "Failed to load resource: the server responded with a status of 404 (Not Found)"
    ],
    [
      "youtube",
      "ws-close",
      "/ws"
    ],
    [
      "documents",
      "failed",
      "/api/document-qa/status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "documents",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "documents",
      "failed",
      "/api/document-qa/documents",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "documents",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "documents",
      "console",
      "Failed to load documents list: TypeError: Failed to fetch\n    at loadDocumentsList (http://localhost:8000/:9057:23)\n    at refreshDocumentCe"
    ],
    [
      "documents",
      "failed",
      "/api/document-qa/collections",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "documents",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "documents",
      "console",
      "Failed to load collections: TypeError: Failed to fetch\n    at loadDocumentCollections (http://localhost:8000/:9389:23)\n    at refreshDocumen"
    ],
    [
      "documents",
      "failed",
      "/api/voice/diagnostics",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "documents",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "documents",
      "failed",
      "/api/voice/wake_status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "documents",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "research",
      "console",
      "WebSocket connection to 'ws://localhost:8000/ws' failed: Error in connection establishment: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "research",
      "ws-close",
      "/ws"
    ],
    [
      "research",
      "failed",
      "/api/identity/status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "research",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "research",
      "failed",
      "/api/voice/diagnostics",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "research",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "research",
      "failed",
      "/api/voice/wake_status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "research",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "settings",
      "failed",
      "/api/settings",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "settings",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "settings",
      "console",
      "WebSocket connection to 'ws://localhost:8000/ws' failed: Error in connection establishment: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "settings",
      "ws-close",
      "/ws"
    ],
    [
      "settings",
      "failed",
      "/api/voice/diagnostics",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "settings",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "settings",
      "failed",
      "/api/voice/wake_status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "settings",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "account",
      "failed",
      "/api/system",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "account",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "account",
      "failed",
      "/api/voice/wake_status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "account",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "account",
      "failed",
      "/api/chat/providers",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "account",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "account",
      "failed",
      "/api/task-jobs",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "account",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "account",
      "failed",
      "/api/automations/tasks",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "account",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "account",
      "failed",
      "/api/memory/stats",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "account",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "account",
      "failed",
      "/api/identity/status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "account",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "account",
      "console",
      "WebSocket connection to 'ws://localhost:8000/ws' failed: Error in connection establishment: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "account",
      "ws-close",
      "/ws"
    ],
    [
      "account",
      "failed",
      "/api/voice/diagnostics",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "account",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "account",
      "failed",
      "/api/voice/wake_status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "account",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "account",
      "console",
      "WebSocket connection to 'ws://localhost:8000/ws' failed: Error in connection establishment: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "account",
      "failed",
      "/api/identity/status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "account",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "account",
      "ws-close",
      "/ws"
    ],
    [
      "account",
      "failed",
      "/api/health",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "account",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "account",
      "failed",
      "/api/identity/status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "account",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "account",
      "failed",
      "/api/voice/diagnostics",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "account",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "account",
      "failed",
      "/api/voice/wake_status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "account",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "account",
      "console",
      "WebSocket connection to 'ws://localhost:8000/ws' failed: Error in connection establishment: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "account",
      "ws-close",
      "/ws"
    ],
    [
      "account",
      "failed",
      "/api/voice/diagnostics",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "account",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "account",
      "failed",
      "/api/voice/wake_status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "account",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "home",
      "console",
      "WebSocket connection to 'ws://localhost:8000/ws' failed: Error in connection establishment: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "home",
      "ws-close",
      "/ws"
    ],
    [
      "home",
      "failed",
      "/api/voice/diagnostics",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "home",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "home",
      "failed",
      "/api/voice/wake_status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "home",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "home",
      "failed",
      "/api/system",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "home",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "home",
      "failed",
      "/api/voice/wake_status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "home",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "home",
      "failed",
      "/api/chat/providers",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "home",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "home",
      "failed",
      "/api/task-jobs",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "home",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "home",
      "failed",
      "/api/automations/tasks",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "home",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "home",
      "failed",
      "/api/memory/stats",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "home",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "home",
      "failed",
      "/api/voice/diagnostics",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "home",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "home",
      "failed",
      "/api/voice/wake_status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "home",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "apps",
      "failed",
      "/api/identity/status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "apps",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "apps",
      "console",
      "WebSocket connection to 'ws://localhost:8000/ws' failed: Error in connection establishment: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "apps",
      "ws-close",
      "/ws"
    ],
    [
      "apps",
      "failed",
      "/api/identity/status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "apps",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "apps",
      "failed",
      "/api/apps/catalog",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "apps",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "apps",
      "console",
      "Failed to load apps catalog: TypeError: Failed to fetch\n    at loadAppsCenter (http://localhost:8000/:3844:23)"
    ],
    [
      "apps",
      "failed",
      "/api/voice/diagnostics",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "apps",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "apps",
      "failed",
      "/api/voice/wake_status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "apps",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "chat",
      "console",
      "WebSocket connection to 'ws://localhost:8000/ws' failed: Error in connection establishment: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "chat",
      "ws-close",
      "/ws"
    ],
    [
      "chat",
      "failed",
      "/api/health",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "chat",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "chat",
      "failed",
      "/api/voice/diagnostics",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "chat",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "chat",
      "failed",
      "/api/voice/wake_status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "chat",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "chat",
      "console",
      "WebSocket connection to 'ws://localhost:8000/ws' failed: Error in connection establishment: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "chat",
      "ws-close",
      "/ws"
    ],
    [
      "voice",
      "failed",
      "/api/voice/diagnostics",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "voice",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "voice",
      "failed",
      "/api/voice/wake_status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "voice",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "voice",
      "failed",
      "/api/voice/status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "voice",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "voice",
      "failed",
      "/api/system",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "voice",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "voice",
      "failed",
      "/api/voice/wake_status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "voice",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "voice",
      "failed",
      "/api/chat/providers",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "voice",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "voice",
      "failed",
      "/api/task-jobs",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "voice",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "voice",
      "failed",
      "/api/automations/tasks",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "voice",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "voice",
      "failed",
      "/api/memory/stats",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "voice",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "voice",
      "failed",
      "/api/identity/status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "voice",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "voice",
      "console",
      "WebSocket connection to 'ws://localhost:8000/ws' failed: Error in connection establishment: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "voice",
      "ws-close",
      "/ws"
    ],
    [
      "voice",
      "failed",
      "/api/voice/diagnostics",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "voice",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "voice",
      "failed",
      "/api/voice/wake_status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "voice",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "voice",
      "failed",
      "/api/voice/diagnostics",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "voice",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "aistudio",
      "failed",
      "/api/voice/wake_status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "aistudio",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "aistudio",
      "console",
      "Failed to load resource: net::ERR_INCOMPLETE_CHUNKED_ENCODING"
    ],
    [
      "aistudio",
      "failed",
      "/api/agents/discover",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "aistudio",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "aistudio",
      "console",
      "refreshAgentDiscovery error: TypeError: Failed to fetch\n    at refreshAgentDiscovery (http://localhost:8000/:7139:21)\n    at loadAgentManage"
    ],
    [
      "aistudio",
      "failed",
      "/api/youtube/config",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "aistudio",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "aistudio",
      "console",
      "Error loading YouTube Center: TypeError: Failed to fetch\n    at loadYouTubeCenter (http://localhost:8000/:7821:23)\n    at showTab (http://lo"
    ],
    [
      "aistudio",
      "failed",
      "/api/voice/diagnostics",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "aistudio",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "vision",
      "failed",
      "/api/voice/wake_status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "vision",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "vision",
      "failed",
      "/api/vision/detections",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "vision",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "vision",
      "failed",
      "/api/vision/detections",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "vision",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "vision",
      "failed",
      "/api/vision/detections",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "vision",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "vision",
      "failed",
      "/api/vision/detections",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "vision",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "vision",
      "failed",
      "/api/health",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "vision",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "vision",
      "failed",
      "/api/identity/status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "vision",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "vision",
      "failed",
      "/api/voice/diagnostics",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "vision",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "vision",
      "failed",
      "/api/voice/wake_status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "vision",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "robot",
      "failed",
      "/api/vision/detections",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "robot",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "robot",
      "failed",
      "/api/robot/state",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "robot",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "robot",
      "failed",
      "/api/system",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "robot",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "robot",
      "failed",
      "/api/voice/wake_status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "robot",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "robot",
      "failed",
      "/api/chat/providers",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "robot",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "robot",
      "failed",
      "/api/task-jobs",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "robot",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "robot",
      "failed",
      "/api/automations/tasks",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "robot",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "robot",
      "failed",
      "/api/memory/stats",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "robot",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "sensors",
      "failed",
      "/api/sensors/all",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "sensors",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "sensors",
      "failed",
      "/api/voice/diagnostics",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "sensors",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "sensors",
      "failed",
      "/api/voice/wake_status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "sensors",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "memory",
      "failed",
      "/api/memory/search",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "memory",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "memory",
      "failed",
      "/api/voice/diagnostics",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "memory",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "memory",
      "failed",
      "/api/voice/wake_status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "memory",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "automations",
      "failed",
      "/api/voice/diagnostics",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "automations",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "automations",
      "failed",
      "/api/voice/wake_status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "automations",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "automations",
      "failed",
      "/api/automations/tasks",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "automations",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "automations",
      "failed",
      "/api/identity/status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "automations",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "tools",
      "failed",
      "/api/tools",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "tools",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "tools",
      "failed",
      "/api/voice/diagnostics",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "tools",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "tools",
      "failed",
      "/api/voice/wake_status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "tools",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "tools",
      "failed",
      "/api/system",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "tools",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "tools",
      "failed",
      "/api/voice/wake_status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "tools",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "tools",
      "failed",
      "/api/chat/providers",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "tools",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "tools",
      "failed",
      "/api/task-jobs",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "tools",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "tools",
      "failed",
      "/api/automations/tasks",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "tools",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "tools",
      "failed",
      "/api/memory/stats",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "tools",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "integrations",
      "failed",
      "/api/health",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "integrations",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "integrations",
      "failed",
      "/api/voice/diagnostics",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "integrations",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "integrations",
      "failed",
      "/api/voice/wake_status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "integrations",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "integrations",
      "failed",
      "/api/settings/integrations",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "integrations",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "integrations",
      "failed",
      "/api/voice/diagnostics",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "integrations",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "integrations",
      "failed",
      "/api/voice/wake_status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "integrations",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "integrations",
      "failed",
      "/api/identity/status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "integrations",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "integrations",
      "failed",
      "/api/voice/diagnostics",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "integrations",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "integrations",
      "failed",
      "/api/voice/wake_status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "integrations",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "system",
      "failed",
      "/api/system",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "system",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "system",
      "failed",
      "/api/voice/diagnostics",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "system",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "system",
      "failed",
      "/api/voice/wake_status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "system",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "logs",
      "failed",
      "/api/logs",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "logs",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "logs",
      "failed",
      "/api/system",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "logs",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "logs",
      "failed",
      "/api/voice/wake_status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "logs",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "logs",
      "failed",
      "/api/chat/providers",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "logs",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "logs",
      "failed",
      "/api/task-jobs",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "logs",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "logs",
      "failed",
      "/api/automations/tasks",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "logs",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "logs",
      "failed",
      "/api/memory/stats",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "logs",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "logs",
      "failed",
      "/api/voice/diagnostics",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "logs",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "desktop",
      "failed",
      "/api/voice/wake_status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "desktop",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "desktop",
      "failed",
      "/api/desktop/status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "desktop",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "desktop",
      "console",
      "loadDesktopStatus error: TypeError: Failed to fetch\n    at loadDesktopStatus (http://localhost:8000/:6253:21)\n    at showTab (http://localho"
    ],
    [
      "desktop",
      "failed",
      "/api/desktop/apps",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "desktop",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "desktop",
      "console",
      "loadDesktopApps error: TypeError: Failed to fetch\n    at loadDesktopApps (http://localhost:8000/:6272:21)\n    at showTab (http://localhost:8"
    ],
    [
      "desktop",
      "failed",
      "/api/desktop/projects",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "desktop",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "desktop",
      "console",
      "loadDesktopProjects error: TypeError: Failed to fetch\n    at loadDesktopProjects (http://localhost:8000/:6307:21)\n    at showTab (http://loc"
    ],
    [
      "desktop",
      "failed",
      "/api/health",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "desktop",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "desktop",
      "failed",
      "/api/identity/status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "desktop",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "desktop",
      "failed",
      "/api/voice/diagnostics",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "desktop",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "desktop",
      "failed",
      "/api/voice/wake_status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "desktop",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "computer",
      "failed",
      "/api/computer/status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "computer",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "computer",
      "console",
      "loadComputerStatus error: TypeError: Failed to fetch\n    at loadComputerStatus (http://localhost:8000/:6710:21)\n    at showTab (http://local"
    ],
    [
      "computer",
      "failed",
      "/api/computer/history",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "computer",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "computer",
      "console",
      "loadComputerHistory error: TypeError: Failed to fetch\n    at loadComputerHistory (http://localhost:8000/:6914:21)\n    at showTab (http://loc"
    ],
    [
      "computer",
      "failed",
      "/api/voice/diagnostics",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "computer",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "computer",
      "failed",
      "/api/voice/wake_status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "computer",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "computer",
      "failed",
      "/api/voice/diagnostics",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "computer",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "computer",
      "failed",
      "/api/voice/wake_status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "computer",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "agents",
      "failed",
      "/api/agents/discover",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "agents",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "agents",
      "console",
      "refreshAgentDiscovery error: TypeError: Failed to fetch\n    at refreshAgentDiscovery (http://localhost:8000/:7139:21)\n    at loadAgentManage"
    ],
    [
      "agents",
      "failed",
      "/api/agents/permissions",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "agents",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "agents",
      "console",
      "loadAgentPermissions error: TypeError: Failed to fetch\n    at loadAgentPermissions (http://localhost:8000/:7173:21)\n    at loadAgentManager "
    ],
    [
      "agents",
      "failed",
      "/api/agents/metrics",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "agents",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "agents",
      "console",
      "loadAgentMetrics error: TypeError: Failed to fetch\n    at loadAgentMetrics (http://localhost:8000/:7258:21)\n    at loadAgentManager (http://"
    ],
    [
      "agents",
      "failed",
      "/api/agents/tasks",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "agents",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "agents",
      "console",
      "loadAgentTasks error: TypeError: Failed to fetch\n    at loadAgentTasks (http://localhost:8000/:7269:21)\n    at loadAgentManager (http://loca"
    ],
    [
      "agents",
      "failed",
      "/api/system",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "agents",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "agents",
      "failed",
      "/api/voice/wake_status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "agents",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "agents",
      "failed",
      "/api/chat/providers",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "agents",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "agents",
      "failed",
      "/api/task-jobs",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "agents",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "agents",
      "failed",
      "/api/automations/tasks",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "agents",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "agents",
      "failed",
      "/api/memory/stats",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "agents",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "agents",
      "failed",
      "/api/voice/diagnostics",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "agents",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "agents",
      "failed",
      "/api/voice/wake_status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "agents",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "agents",
      "failed",
      "/api/identity/status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "agents",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "developer",
      "failed",
      "/api/developer/status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "developer",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "developer",
      "console",
      "loadDeveloperStatus error: TypeError: Failed to fetch\n    at loadDeveloperStatus (http://localhost:8000/:7406:23)\n    at loadDeveloperCenter"
    ],
    [
      "developer",
      "failed",
      "/api/developer/agents",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "developer",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "developer",
      "failed",
      "/api/developer/tasks",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "developer",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "developer",
      "failed",
      "/api/developer/worktrees",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "developer",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "developer",
      "failed",
      "/api/developer/tests",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "developer",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "developer",
      "failed",
      "/api/voice/diagnostics",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "developer",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "developer",
      "failed",
      "/api/voice/wake_status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "developer",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "youtube",
      "failed",
      "/api/youtube/config",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "youtube",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "youtube",
      "console",
      "Error loading YouTube Center: TypeError: Failed to fetch\n    at loadYouTubeCenter (http://localhost:8000/:7821:23)\n    at showTab (http://lo"
    ],
    [
      "youtube",
      "failed",
      "/api/health",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "youtube",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "youtube",
      "failed",
      "/api/voice/diagnostics",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "youtube",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "youtube",
      "failed",
      "/api/voice/wake_status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "youtube",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "documents",
      "failed",
      "/api/document-qa/status",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "documents",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "documents",
      "failed",
      "/api/document-qa/documents",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "documents",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "documents",
      "console",
      "Failed to load documents list: TypeError: Failed to fetch\n    at loadDocumentsList (http://localhost:8000/:9057:23)\n    at refreshDocumentCe"
    ],
    [
      "documents",
      "failed",
      "/api/document-qa/collections",
      "net::ERR_CONNECTION_REFUSED"
    ],
    [
      "documents",
      "console",
      "Failed to load resource: net::ERR_CONNECTION_REFUSED"
    ],
    [
      "documents",
      "console",
      "Failed to load collections: TypeError: Failed to fetch\n    at loadDocumentCollections (http://localhost:8000/:9389:23)\n    at refreshDocumen"
    ]
  ]
}
~~~
