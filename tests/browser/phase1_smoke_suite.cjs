/**
 * Phase 1 Smoke Suite: Regression Harness for all 21 FEATURES.md destinations.
 * Tests the unchanged application at http://127.0.0.1:8000 and captures
 * baseline screenshots at 4 viewports (Desktop, Laptop, Tablet, Mobile).
 */
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('path');
const { chromium } = require('playwright');

const EVIDENCE_DIR = path.join(__dirname, '..', '..', 'docs', 'jarvis-ui', 'evidence', 'phase-1');
const SCREENSHOT_DIR = path.join(EVIDENCE_DIR, 'screenshots');
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

const ALL_DESTINATIONS = [
  { tab: 'home', navId: 'nav-home', panelId: 'tab-home', title: 'Home' },
  { tab: 'apps', navId: 'nav-apps', panelId: 'tab-apps', title: 'Apps Center' },
  { tab: 'chat', navId: 'nav-chat', panelId: 'tab-chat', title: 'AI Chat' },
  { tab: 'voice', navId: 'nav-voice', panelId: 'tab-voice', title: 'Voice' },
  { tab: 'aistudio', navId: 'nav-aistudio', panelId: 'tab-aistudio', title: 'AI Studio' },
  { tab: 'vision', navId: 'nav-vision', panelId: 'tab-vision', title: 'Vision' },
  { tab: 'robot', navId: 'nav-robot', panelId: 'tab-robot', title: 'Robot' },
  { tab: 'sensors', navId: 'nav-sensors', panelId: 'tab-sensors', title: 'Sensors' },
  { tab: 'memory', navId: 'nav-memory', panelId: 'tab-memory', title: 'Memory' },
  { tab: 'automations', navId: 'nav-automations', panelId: 'tab-automations', title: 'Automations' },
  { tab: 'tools', navId: 'nav-tools', panelId: 'tab-tools', title: 'Tools' },
  { tab: 'integrations', navId: 'nav-integrations', panelId: 'tab-integrations', title: 'Integrations' },
  { tab: 'system', navId: 'nav-system', panelId: 'tab-system', title: 'System' },
  { tab: 'logs', navId: 'nav-logs', panelId: 'tab-logs', title: 'Logs' },
  { tab: 'desktop', navId: 'nav-desktop', panelId: 'tab-desktop', title: 'Desktop & Terminal' },
  { tab: 'computer', navId: 'nav-computer', panelId: 'tab-computer', title: 'Computer Use' },
  { tab: 'agents', navId: 'nav-agents', panelId: 'tab-agents', title: 'AI Agents' },
  { tab: 'developer', navId: 'nav-developer', panelId: 'tab-developer', title: 'Developer Hub' },
  { tab: 'youtube', navId: 'nav-youtube', panelId: 'tab-youtube', title: 'YouTube AI' },
  { tab: 'research', navId: 'nav-research', panelId: 'tab-research', title: 'Research Assistant' },
  { tab: 'settings', navId: 'nav-settings', panelId: 'tab-settings', title: 'Settings' },
];

test('Phase 1 Smoke Suite: 21 Destinations Regression & Viewport Verification', async (t) => {
  const executablePath = resolveChrome();
  assert.ok(executablePath, 'Chromium/Chrome executable must be found on the system');

  const browser = await chromium.launch({
    executablePath,
    headless: true,
    args: ['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu'],
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
  });
  const page = await context.newPage();

  const results = {
    testedTabs: [],
    breakpoints: [],
    timestamp: new Date().toISOString(),
  };

  try {
    // 1. Visit root dashboard on unchanged live app
    const res = await page.goto('http://127.0.0.1:8000', {
      waitUntil: 'domcontentloaded',
      timeout: 15000,
    });
    assert.equal(res.status(), 200, 'Root dashboard must return HTTP 200');

    // Verify main landmarks
    await page.waitForSelector('#nav-home', { timeout: 5000 });
    await page.waitForSelector('#tab-home.active', { timeout: 5000 });

    // 2. Test every destination in FEATURES.md
    for (const dest of ALL_DESTINATIONS) {
      await t.test(`Navigate to ${dest.title} (#${dest.panelId})`, async () => {
        const navBtn = page.locator(`#${dest.navId}`);
        assert.ok(await navBtn.count() > 0, `Navigation button #${dest.navId} must exist`);

        await navBtn.click();
        const panel = page.locator(`#${dest.panelId}`);
        await panel.waitFor({ state: 'attached', timeout: 5000 });

        // Ensure the panel has the 'active' class
        const hasActiveClass = await panel.evaluate((el) => el.classList.contains('active'));
        assert.ok(hasActiveClass, `Tab #${dest.panelId} must become active on click`);

        results.testedTabs.push({
          destination: dest.title,
          tabId: dest.panelId,
          navId: dest.navId,
          verified: true,
        });
      });
    }

    // Return to home for screenshots
    await page.click('#nav-home');
    await page.waitForTimeout(300);

    // 3. Viewport Breakpoint Verification & Screenshots
    const breakpoints = [
      { name: 'desktop_1920x1080', width: 1920, height: 1080 },
      { name: 'laptop_1366x768', width: 1366, height: 768 },
      { name: 'tablet_768x1024', width: 768, height: 1024 },
      { name: 'mobile_375x667', width: 375, height: 667 },
    ];

    for (const bp of breakpoints) {
      await t.test(`Capture baseline screenshot at ${bp.name}`, async () => {
        await page.setViewportSize({ width: bp.width, height: bp.height });
        await page.waitForTimeout(400);

        const screenshotPath = path.join(SCREENSHOT_DIR, `baseline_${bp.name}.png`);
        await page.screenshot({ path: screenshotPath, fullPage: false });

        assert.ok(fs.existsSync(screenshotPath), `Screenshot for ${bp.name} must exist`);
        const stats = fs.statSync(screenshotPath);
        assert.ok(stats.size > 1000, `Screenshot file size must be non-empty (>1KB)`);

        results.breakpoints.push({
          viewport: bp.name,
          dimensions: `${bp.width}x${bp.height}`,
          screenshot: `baseline_${bp.name}.png`,
          bytes: stats.size,
        });
      });
    }

    // Save test execution evidence
    const evidenceJsonPath = path.join(EVIDENCE_DIR, 'smoke_report.json');
    fs.writeFileSync(evidenceJsonPath, JSON.stringify(results, null, 2), 'utf8');

  } finally {
    await browser.close();
  }
});
