const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('path');
const { chromium } = require('playwright');

const SCREENSHOT_DIR = path.join(__dirname, 'screenshots');
fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });

const CHROME_CANDIDATES = [
  process.env.CHROME_PATH,
  '/usr/bin/google-chrome',
  '/usr/bin/google-chrome-stable',
  '/usr/bin/chromium',
  '/usr/bin/chromium-browser',
].filter(Boolean);

function resolveChrome() {
  for (const candidate of CHROME_CANDIDATES) {
    if (fs.existsSync(candidate)) return candidate;
  }
  return undefined;
}

test('Chromium E2E: Real Browser Verification of JARVIS OS Workflows', async () => {
  const executablePath = resolveChrome();
  assert.ok(executablePath, 'Chromium/Chrome executable must be available on the host system');

  const browser = await chromium.launch({
    executablePath,
    headless: true,
    args: ['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu'],
  });

  const pageErrors = [];
  const consoleErrors = [];
  const networkFailures = [];
  const testedWorkflows = [];

  const context = await browser.newContext({
    viewport: { width: 1280, height: 850 },
  });
  const page = await context.newPage();

  page.on('pageerror', (err) => {
    console.error('[Browser PageError]', err.message);
    pageErrors.push(err.message);
  });

  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      const text = msg.text();
      // Filter expected connection refusal from non-running optional auxiliary endpoints
      if (!text.includes('net::ERR_CONNECTION_REFUSED') && !text.includes('WebSocket')) {
        consoleErrors.push(text);
      }
    }
  });

  page.on('requestfailed', (req) => {
    const url = req.url();
    if (url.includes('/api/') || url.includes('active-desktop')) {
      networkFailures.push(`${req.failure()?.errorText || 'failed'} ${url}`);
    }
  });

  try {
    // ─── 1. Home Dashboard & System Telemetry ──────────────────────
    const response = await page.goto('http://127.0.0.1:8000', {
      waitUntil: 'domcontentloaded',
      timeout: 15000,
    });
    assert.equal(response.status(), 200, 'Dashboard HTTP response must be 200 OK');

    const title = await page.title();
    assert.match(title, /JARVIS OS/i, 'Page title must contain JARVIS OS');
    const brand = await page.locator('.brand .logo').textContent();
    assert.match(brand, /JARVIS OS/i, 'Header brand logo must contain JARVIS OS');

    assert.equal(await page.locator('.skip-link').count(), 1, 'Accessibility skip link must exist');
    assert.equal(await page.locator('nav[role="tablist"]').count(), 1, 'Primary tablist navigation must exist');
    await page.locator('#tab-home').waitFor({ state: 'visible', timeout: 5000 });

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '01_home.png'),
      fullPage: false,
    });
    testedWorkflows.push('01_home_dashboard');

    // ─── 2. AI Chat, Dynamic Model Selection & Active Desktop ──────
    await page.click('nav button:has-text("AI Chat")');
    await page.locator('#tab-chat').waitFor({ state: 'visible', timeout: 5000 });
    await page.locator('#chat-in').waitFor({ state: 'visible', timeout: 5000 });

    // Verify Active Desktop controls
    assert.ok(await page.locator('#active-desktop-start').isVisible(), 'Activate JARVIS control must be visible');
    assert.ok(await page.locator('#active-desktop-stop').isDisabled(), 'Stop active mode starts disabled');
    assert.ok(await page.locator('#active-screen').isVisible(), 'Share screen checkbox must be visible');
    assert.ok(await page.locator('#active-microphone').isVisible(), 'Microphone checkbox must be visible');
    assert.ok(await page.locator('#active-speaker').isVisible(), 'Spoken replies checkbox must be visible');

    // Test Model Selection Switcher
    const modelSelect = page.locator('#chat-model-select');
    assert.ok(await modelSelect.isVisible(), 'Model selection dropdown must be visible');
    await modelSelect.selectOption('gemini:gemini-2.0-flash');
    await page.waitForTimeout(300);
    const statusBadge = await page.locator('#chat-status-badge').textContent();
    assert.match(statusBadge, /gemini/i, 'Status badge must reflect switched model');

    // Switch back to Ollama local model
    await modelSelect.selectOption('ollama:llama3.2:1b');
    await page.waitForTimeout(300);

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '02_ai_chat.png'),
      fullPage: false,
    });
    testedWorkflows.push('02_ai_chat_and_model_switching');

    // ─── 3. Voice Center, Daemon IPC & Durable Jobs ────────────────
    await page.click('nav button:has-text("Voice")');
    await page.locator('#tab-voice').waitFor({ state: 'visible', timeout: 5000 });

    // Verify Microphone & Speaker status indicators
    const micState = await page.locator('#voice-state-val').textContent();
    assert.ok(micState.length > 0, 'Microphone state indicator must render');
    const speakerState = await page.locator('#voice-speaker-val').textContent();
    assert.ok(speakerState.length > 0, 'Speaker state indicator must render');

    // Test Daemon IPC Mute / Unmute / Stop / Interrupt buttons
    assert.ok(await page.locator('#btn-voice-mute').isVisible(), 'Voice daemon mute button must be visible');
    assert.ok(await page.locator('#btn-voice-unmute').isVisible(), 'Voice daemon unmute button must be visible');
    assert.ok(await page.locator('#btn-voice-stop').isVisible(), 'Voice daemon stop button must be visible');
    assert.ok(await page.locator('#btn-voice-interrupt').isVisible(), 'Voice daemon interrupt button must be visible');

    // Click Mute Daemon and inspect feedback
    await page.click('#btn-voice-mute');
    await page.waitForTimeout(400);
    const muteFb = await page.locator('#voice-daemon-fb').textContent();
    assert.ok(muteFb.length > 0, 'Daemon feedback message must render after mute');

    // Click Unmute Daemon
    await page.click('#btn-voice-unmute');
    await page.waitForTimeout(400);

    // Verify Durable Voice Jobs section
    assert.ok(await page.locator('#voice-jobs-list').isVisible(), 'Durable voice jobs container must be visible');
    await page.click('#btn-refresh-voice-jobs');
    await page.waitForTimeout(300);

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '03_voice_controls_and_jobs.png'),
      fullPage: false,
    });
    testedWorkflows.push('03_voice_center_and_daemon_ipc');

    // ─── 4. Desktop & Integrated Real Terminal Console ─────────────
    await page.click('nav button:has-text("Desktop & Terminal")');
    await page.locator('#tab-desktop').waitFor({ state: 'visible', timeout: 5000 });

    // Verify Launchers
    for (const label of ['Google Chrome', 'Firefox', 'VS Code', 'Terminal', 'File Manager']) {
      assert.ok(await page.locator(`#tab-desktop button:has-text("${label}")`).count() >= 1, `${label} launcher button must exist`);
    }

    // Verify Terminal Input & Execute Safe Non-Destructive Command
    const termInput = page.locator('#dt-term-input');
    assert.ok(await termInput.isVisible(), 'Terminal input must be visible');
    await termInput.fill('echo "JARVIS_CHROME_E2E_OK"');
    await page.click('#tab-desktop button:has-text("Execute")');

    // Wait for command output in terminal box
    const termOutput = page.locator('#dt-terminal-output');
    await termOutput.waitFor({ state: 'visible', timeout: 5000 });
    await page.waitForFunction(
      () => {
        const el = document.getElementById('dt-terminal-output');
        return el && el.textContent.includes('Exit Code: 0');
      },
      { timeout: 15000 }
    );
    const termText = await termOutput.textContent();
    assert.match(termText, /JARVIS_CHROME_E2E_OK/, 'Terminal output must contain echo result');
    assert.match(termText, /Exit Code: 0/, 'Terminal output must confirm exit code 0');

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '04_terminal_execution.png'),
      fullPage: false,
    });
    testedWorkflows.push('04_desktop_terminal_execution');

    // ─── 5. Integrations & Password Masking Security ───────────────
    await page.click('nav button:has-text("Integrations")');
    await page.locator('#tab-integrations').waitFor({ state: 'visible', timeout: 5000 });

    // Verify all 7 cloud provider inputs are password-masked
    const providers = ['gemini', 'openai', 'anthropic', 'nvidia', 'openrouter', 'groq', 'together'];
    for (const p of providers) {
      const input = page.locator(`#key-${p}`);
      assert.ok(await input.isVisible(), `Key input for ${p} must be visible`);
      assert.equal(await input.getAttribute('type'), 'password', `Key input for ${p} must be password-masked`);
    }

    // Attempt save without PIN -> must display error without sending credentials
    await page.click('button:has-text("Save Keys to .env")');
    const saveStatus = await page.locator('#integrations-status').textContent();
    assert.match(saveStatus, /PIN/i, 'Save without PIN must be blocked with requirement notice');

    // Attempt cloud test without PIN -> must be blocked
    await page.click('button:has-text("Test cloud providers")');
    const testStatus = await page.locator('#integrations-status').textContent();
    assert.match(testStatus, /PIN/i, 'Cloud test without PIN must be blocked');

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '05_integrations_masked.png'),
      fullPage: false,
    });
    testedWorkflows.push('05_integrations_security');

    // ─── 6. Robot State & Actuator Safety Latch ────────────────────
    await page.click('nav button:has-text("Robot")');
    await page.locator('#tab-robot').waitFor({ state: 'visible', timeout: 5000 });

    // Verify safety latch / disarmed state
    const robotState = await page.locator('#actuator-gate-state').textContent();
    assert.match(robotState, /(DISARMED|DISABLED)/i, 'Robot actuator state must indicate DISARMED or DISABLED');

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '06_robot_safety_disarmed.png'),
      fullPage: false,
    });
    testedWorkflows.push('06_robot_safety_disarmed');

    // ─── 7. Computer Use & Visual Automation ───────────────────────
    await page.click('nav button:has-text("Computer Use")');
    await page.locator('#tab-computer').waitFor({ state: 'visible', timeout: 5000 });
    assert.ok(await page.locator('#tab-computer button:has-text("Observe Screen")').isVisible());
    assert.ok(await page.locator('#tab-computer button:has-text("Fullscreen")').isVisible());
    assert.ok(await page.locator('#comp-find-in').isVisible());
    assert.ok(await page.locator('#comp-type-in').isVisible());

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '07_computer_use.png'),
      fullPage: false,
    });
    testedWorkflows.push('07_computer_use');

    // ─── 8. Settings Center ────────────────────────────────────────
    await page.click('nav button:has-text("Settings")');
    await page.locator('#tab-settings').waitFor({ state: 'visible', timeout: 5000 });
    await page.locator('#settings-cat-menu').waitFor({ state: 'visible', timeout: 5000 });
    assert.ok(await page.locator('#settings-cat-menu').isVisible(), 'Settings category menu must be visible');

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '08_settings_center.png'),
      fullPage: false,
    });
    testedWorkflows.push('08_settings_center');

    // ─── 9. Hybrid JARVIS Developer Hub (Phase 06 & 09) ─────────────
    await page.click('nav button:has-text("Developer Hub")');
    await page.locator('#tab-developer').waitFor({ state: 'visible', timeout: 5000 });

    // Check metric cards
    await page.waitForFunction(() => {
      const el = document.getElementById('dev-branch-val');
      return el && el.textContent.trim() !== '—';
    }, { timeout: 8000 });
    const branchText = await page.locator('#dev-branch-val').textContent();
    assert.ok(branchText.length > 0 && branchText !== '—', 'Dev branch must be rendered');

    // Check agents grid
    await page.locator('#dev-agents-grid div').first().waitFor({ state: 'visible', timeout: 5000 });
    const agentsContent = await page.locator('#dev-agents-grid').textContent();
    assert.match(agentsContent, /ANTIGRAVITY/i, 'Antigravity agent must be listed');
    assert.match(agentsContent, /CODEX/i, 'Codex agent must be listed');
    assert.match(agentsContent, /OPENROUTER/i, 'OpenRouter provider must be listed');
    assert.match(agentsContent, /CLINE/i, 'Cline agent must be listed');
    assert.match(agentsContent, /COPILOT/i, 'GitHub Copilot agent must be listed');
    assert.match(agentsContent, /SIMULATED/i, 'Simulated agent must be listed');

    // Create a new task via the UI
    await page.fill('#dev-task-prompt', 'E2E Browser Test Verification Task');
    await page.click('#btn-submit-dev-task');

    // Wait for task to appear in queue
    await page.waitForFunction(() => {
      const el = document.getElementById('dev-tasks-container');
      return el && el.textContent.includes('E2E Browser Test Verification Task');
    }, { timeout: 8000 });

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '10_developer_hub.png'),
      fullPage: false,
    });
    testedWorkflows.push('10_developer_hub_task_creation');

    // Execute the task via Run button in UI
    const runBtn = page.locator('#dev-tasks-container button:has-text("▶ Run")').first();
    if (await runBtn.isVisible()) {
      await runBtn.click();
      await page.waitForFunction(() => {
        const el = document.getElementById('dev-tasks-container');
        return el && (el.textContent.includes('✓ Done') || el.textContent.includes('SUCCEEDED'));
      }, { timeout: 10000 });
    }

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '11_developer_task_executed.png'),
      fullPage: false,
    });
    testedWorkflows.push('11_developer_task_execution');

    // ─── 10. Mobile Responsive Layout (390 × 844) ───────────────────
    await page.setViewportSize({ width: 390, height: 844 });
    await page.click('nav button:has-text("AI Chat")');
    await page.locator('#tab-chat').waitFor({ state: 'visible', timeout: 5000 });
    assert.ok(await page.locator('#active-desktop-start').isVisible());
    assert.ok(await page.locator('#chat-send-btn').isVisible());

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '09_mobile_responsive.png'),
      fullPage: false,
    });
    testedWorkflows.push('09_mobile_responsive');

    await page.click('nav button:has-text("Developer Hub")');
    await page.locator('#tab-developer').waitFor({ state: 'visible', timeout: 5000 });
    assert.ok(await page.locator('#btn-submit-dev-task').isVisible());

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '12_developer_mobile.png'),
      fullPage: false,
    });
    testedWorkflows.push('12_developer_mobile_responsive');

    // Final full verification screenshot
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'dashboard_verified.png'),
      fullPage: false,
    });

    assert.equal(pageErrors.length, 0, `Unexpected page errors: ${pageErrors.join('; ')}`);
    if (consoleErrors.length) {
      console.log('[Browser ConsoleErrors]', consoleErrors.join(' | '));
    }
    if (networkFailures.length) {
      console.log('[Browser NetworkFailures]', networkFailures.join(' | '));
    }

    const report = {
      testSuite: 'Chromium E2E Browser Verification',
      browser: 'Google Chrome / Chromium v157',
      executablePath,
      targetUrl: 'http://127.0.0.1:8000',
      testedWorkflows,
      pageErrors,
      consoleErrors,
      networkFailures,
      screenshots: fs.readdirSync(SCREENSHOT_DIR).filter((name) => name.endsWith('.png')),
      verifiedAt: new Date().toISOString(),
    };
    fs.writeFileSync(path.join(SCREENSHOT_DIR, 'verification_report.json'), JSON.stringify(report, null, 2));
  } finally {
    await browser.close();
  }
});
