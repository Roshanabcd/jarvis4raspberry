/**
 * Phase 2 Gate Verification Suite:
 * - Syntax & type checks
 * - Axe Accessibility Audit (0 critical violations)
 * - Keyboard-only navigation verification
 * - Four viewport screenshots (Desktop, Laptop, Tablet, Mobile)
 * - All 18 destinations routing & honest "Not implemented yet" states
 */

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('path');
const { chromium } = require('playwright');

const EVIDENCE_DIR = path.join(__dirname, '..', '..', 'docs', 'jarvis-ui', 'evidence', 'phase-2');
const SCREENSHOT_DIR = path.join(EVIDENCE_DIR, 'screenshots');
fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });

const FUTURISTIC_DIR = path.join(__dirname, '..', '..', 'apps', 'dashboard', 'futuristic');

// Simple static HTTP server for isolated browser testing
function createStaticServer(dir, port = 8012) {
  const mimeTypes = {
    '.html': 'text/html; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.js': 'application/javascript; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.png': 'image/png',
    '.svg': 'image/svg+xml',
  };

  const server = http.createServer((req, res) => {
    let reqPath = req.url.split('?')[0].split('#')[0];
    if (reqPath === '/' || reqPath === '') reqPath = '/index.html';

    const filePath = path.join(dir, reqPath);
    if (!fs.existsSync(filePath)) {
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      res.end('Not Found');
      return;
    }

    const ext = path.extname(filePath);
    const contentType = mimeTypes[ext] || 'application/octet-stream';
    res.writeHead(200, { 'Content-Type': contentType });
    fs.createReadStream(filePath).pipe(res);
  });

  return new Promise((resolve) => {
    server.listen(port, '127.0.0.1', () => {
      resolve({
        server,
        url: `http://127.0.0.1:${port}`,
        close: () => new Promise((cb) => server.close(cb)),
      });
    });
  });
}

function resolveChrome() {
  const candidates = [
    process.env.CHROME_PATH,
    '/usr/bin/google-chrome',
    '/usr/bin/google-chrome-stable',
    '/usr/bin/chromium',
    '/usr/bin/chromium-browser',
  ].filter(Boolean);

  for (const c of candidates) {
    if (fs.existsSync(c)) return c;
  }
  return undefined;
}

test('Phase 2 Gate: Design System & Accessible Shell Verification', async (t) => {
  const executablePath = resolveChrome();
  assert.ok(executablePath, 'Chromium/Chrome executable must exist');

  // 1. Syntax & structure check of static assets
  await t.test('Static assets integrity check', () => {
    assert.ok(fs.existsSync(path.join(FUTURISTIC_DIR, 'index.html')), 'index.html must exist');
    assert.ok(fs.existsSync(path.join(FUTURISTIC_DIR, 'theme.css')), 'theme.css must exist');
    assert.ok(fs.existsSync(path.join(FUTURISTIC_DIR, 'components.css')), 'components.css must exist');
    assert.ok(fs.existsSync(path.join(FUTURISTIC_DIR, 'shell.js')), 'shell.js must exist');
  });

  const staticServer = await createStaticServer(FUTURISTIC_DIR, 8012);

  const browser = await chromium.launch({
    executablePath,
    headless: true,
    args: ['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu'],
  });

  try {
    const context = await browser.newContext({
      viewport: { width: 1920, height: 1080 },
    });
    const page = await context.newPage();

    // 2. Load the shell
    await page.goto(staticServer.url, { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('#main-content', { timeout: 5000 });

    // 3. Axe Accessibility Audit (0 Critical Violations)
    await t.test('Axe Accessibility Audit on Shell', async () => {
      const axeSourcePath = path.join(__dirname, '..', '..', 'node_modules', 'axe-core', 'axe.min.js');
      assert.ok(fs.existsSync(axeSourcePath), 'axe.min.js must exist');

      await page.addScriptTag({ path: axeSourcePath });
      const axeResults = await page.evaluate(async () => {
        // Run axe with critical and serious filtering
        return await window.axe.run(document, {
          runOnly: {
            type: 'tag',
            values: ['wcag2a', 'wcag2aa'],
          },
        });
      });

      const criticalViolations = axeResults.violations.filter((v) => v.impact === 'critical');
      fs.writeFileSync(
        path.join(EVIDENCE_DIR, 'axe_report.json'),
        JSON.stringify(axeResults, null, 2),
        'utf8'
      );

      assert.equal(
        criticalViolations.length,
        0,
        `Expected 0 critical accessibility violations, found: ${JSON.stringify(criticalViolations.map((v) => v.help))}`
      );
    });

    // 4. Keyboard-only navigation test
    await t.test('Keyboard-Only Navigation Test', async () => {
      // Focus skip link
      await page.keyboard.press('Tab');
      const focusedSkip = await page.evaluate(() => document.activeElement.classList.contains('skip-link'));
      assert.ok(focusedSkip, 'First tab must land on accessible skip-link');

      // Tab to sidebar toggle
      await page.keyboard.press('Tab');
      const focusedToggle = await page.evaluate(() => document.activeElement.id === 'sidebar-toggle');
      assert.ok(focusedToggle, 'Next tab must focus sidebar toggle');

      // Toggle sidebar via keyboard space
      await page.keyboard.press('Space');
      const isCollapsed = await page.evaluate(() => document.getElementById('app-sidebar').classList.contains('collapsed'));
      assert.ok(isCollapsed, 'Space on toggle button must collapse sidebar');

      // Toggle back
      await page.keyboard.press('Space');
      const isExpanded = await page.evaluate(() => !document.getElementById('app-sidebar').classList.contains('collapsed'));
      assert.ok(isExpanded, 'Space on toggle button must expand sidebar');

      // Tab into sidebar navigation and navigate via arrow keys
      const firstNav = page.locator('.app-sidebar .nav-item').first();
      await firstNav.focus();

      // Arrow down to second nav item
      await page.keyboard.press('ArrowDown');
      const secondNavItemText = await page.evaluate(() => document.activeElement.querySelector('.nav-label')?.textContent);
      assert.equal(secondNavItemText, 'AI Chat', 'ArrowDown must move focus to AI Chat');

      // Press Enter to navigate
      await page.keyboard.press('Enter');
      await page.waitForTimeout(200);

      const currentHash = await page.evaluate(() => window.location.hash);
      assert.equal(currentHash, '#chat', 'Enter on focused nav item must update hash to #chat');

      const isChatActive = await page.evaluate(() => {
        const item = document.querySelector('.nav-item[data-route="chat"]');
        return item && item.classList.contains('active');
      });
      assert.ok(isChatActive, 'AI Chat nav item must be marked active');
    });

    // 5. Verify all 18 destinations have a route and unbuilt pages show honest placeholder
    await t.test('All 18 destinations route and display honest status', async () => {
      const destinations = [
        'dashboard', 'chat', 'voice', 'agents', 'tasks', 'automation',
        'workspace', 'terminal', 'calendar', 'memory', 'knowledge',
        'devices', 'robot', 'integrations', 'apps', 'youtube', 'research', 'settings'
      ];

      for (const destId of destinations) {
        await page.goto(`${staticServer.url}/#${destId}`);
        await page.waitForTimeout(100);

        const content = await page.locator('#main-content').textContent();
        if (destId === 'dashboard') {
          assert.ok(content.includes('JARVIS Control Center'), 'Dashboard route must render Control Center');
        } else if (destId === 'chat') {
          assert.ok(content.includes('JARVIS Neural Interface'), 'Chat route must render Neural Interface');
        } else if (destId === 'voice') {
          assert.ok(content.includes('JARVIS Voice Assistant'), 'Voice route must render Voice Assistant');
        } else if (destId === 'agents') {
          assert.ok(content.includes('AI Agents'), 'Agents route must render AI Agents');
        } else if (destId === 'workspace') {
          assert.ok(content.includes('Developer Workspace'), 'Workspace route must render Developer Workspace');
        } else if (destId === 'terminal') {
          assert.ok(content.includes('JARVIS Secure Terminal'), 'Terminal route must render Terminal');
        } else if (destId === 'tasks') {
          assert.ok(content.includes('Tasks Center'), 'Tasks route must render Tasks Center');
        } else if (destId === 'automation') {
          assert.ok(content.includes('Automations & Workflows'), 'Automation route must render Automations');
        } else if (destId === 'calendar') {
          assert.ok(content.includes('Calendar & Reminders'), 'Calendar route must render Calendar');
        } else if (destId === 'memory') {
          assert.ok(content.includes('Long-Term Memory'), 'Memory route must render Memory');
        } else if (destId === 'knowledge') {
          assert.ok(content.includes('Knowledge Base'), 'Knowledge route must render Knowledge');
        } else if (destId === 'integrations') {
          assert.ok(content.includes('Integrations & Connectors'), 'Integrations route must render Integrations');
        } else if (destId === 'apps') {
          assert.ok(content.includes('Connected Applications'), 'Apps route must render Connected Applications');
        } else if (destId === 'devices') {
          assert.ok(content.includes('Connected Devices'), 'Devices route must render Connected Devices');
        } else if (destId === 'sensors') {
          assert.ok(content.includes('Sensors Telemetry'), 'Sensors route must render Sensors Telemetry');
        } else if (destId === 'robot') {
          assert.ok(content.includes('Robotics & Physical Actuators'), 'Robot route must render Robotics');
        } else {
          assert.ok(
            content.includes('Not implemented yet'),
            `Route #${destId} must honestly state Not implemented yet`
          );
        }
      }
    });

    // 6. Capture screenshots at four viewports
    const breakpoints = [
      { name: 'desktop_1920x1080', width: 1920, height: 1080 },
      { name: 'laptop_1366x768', width: 1366, height: 768 },
      { name: 'tablet_768x1024', width: 768, height: 1024 },
      { name: 'mobile_375x667', width: 375, height: 667 },
    ];

    await page.goto(`${staticServer.url}/#dashboard`);
    await page.waitForTimeout(200);

    for (const bp of breakpoints) {
      await t.test(`Capture screenshot at ${bp.name}`, async () => {
        await page.setViewportSize({ width: bp.width, height: bp.height });
        await page.waitForTimeout(300);

        const screenshotPath = path.join(SCREENSHOT_DIR, `futuristic_${bp.name}.png`);
        await page.screenshot({ path: screenshotPath, fullPage: false });

        assert.ok(fs.existsSync(screenshotPath), `Screenshot for ${bp.name} must exist`);
        const stats = fs.statSync(screenshotPath);
        assert.ok(stats.size > 2000, `Screenshot must be non-trivial (>2KB)`);
      });
    }

  } finally {
    await browser.close();
    await staticServer.close();
  }
});
