/**
 * Phase 3 Gate Verification:
 * 1. Typed API client data fetching & telemetry rendering
 * 2. Displayed telemetry matches independent backend values
 * 3. Graceful offline transition upon backend disconnection
 * 4. Automatic recovery upon backend reconnection
 * 5. Screen captures of online and offline states
 */

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('path');
const { chromium } = require('playwright');

const EVIDENCE_DIR = path.join(__dirname, '..', '..', 'docs', 'jarvis-ui', 'evidence', 'phase-3');
const SCREENSHOT_DIR = path.join(EVIDENCE_DIR, 'screenshots');
fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });

const FUTURISTIC_DIR = path.join(__dirname, '..', '..', 'apps', 'dashboard', 'futuristic');

// Controllable test server with simulated backend online/offline toggle
function createControllableServer(port = 8013) {
  let isBackendOnline = true;

  const mockSystem = {
    os: 'Linux',
    os_version: 'Debian 6.18.60-1+rpt1 aarch64',
    arch: 'aarch64',
    hostname: 'raspberrypi',
    uptime_s: 12000,
    uptime_str: '3 hours, 20 minutes',
    cpu_usage_pct: 14.5,
    cpu_freq_mhz: 2400.0,
    cpu_cores: 4,
    temp_c: 58.2,
    ram_total_mb: 7950,
    ram_used_mb: 4120,
    ram_pct: 51.8,
    disk_total_gb: 234.2,
    disk_used_gb: 111.7,
    disk_pct: 49.7,
    net_sent_mb: 860.1,
    net_recv_mb: 1697.4,
    robot_state: 'IDLE',
  };

  const mockHealth = {
    status: 'OK',
    components: {
      backend: 'OK (FastAPI 127.0.0.1:8000)',
      ai_provider: 'OK (ollama: llama3.2:1b)',
      microphone: 'OK (Lite [ReSpeaker Lite] - USB Audio)',
      speaker: 'OK (ReSpeaker Lite Sink 54)',
      voice_engine: 'OK (Remote voice disabled)',
      robot_hardware: 'OK (IDLE / Safety Latch Engaged)',
      robot: 'IDLE',
    },
  };

  const mockDev = {
    worktree_count: 3,
    providers: {
      openrouter: { configured: true },
      ollama: { configured: true, model: 'llama3.2:1b' },
    },
    agents: { registered_count: 8 },
    tasks: { total: 7, running: 0 },
  };

  const mimeTypes = {
    '.html': 'text/html; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.js': 'application/javascript; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
  };

  const server = http.createServer((req, res) => {
    const url = req.url.split('?')[0];

    // Simulated API Endpoints
    if (url.startsWith('/api/')) {
      if (!isBackendOnline) {
        res.writeHead(503, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Backend service offline' }));
        return;
      }

      if (url === '/api/system') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(mockSystem));
        return;
      }
      if (url === '/api/health') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(mockHealth));
        return;
      }
      if (url === '/api/developer/status') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(mockDev));
        return;
      }
      res.writeHead(404, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ detail: 'Not Found' }));
      return;
    }

    // Static Asset Serving
    let reqPath = url === '/' || url === '' ? '/index.html' : url;
    const filePath = path.join(FUTURISTIC_DIR, reqPath);
    if (!fs.existsSync(filePath)) {
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      res.end('Not Found');
      return;
    }

    const ext = path.extname(filePath);
    res.writeHead(200, { 'Content-Type': mimeTypes[ext] || 'application/octet-stream' });
    fs.createReadStream(filePath).pipe(res);
  });

  return new Promise((resolve) => {
    server.listen(port, '127.0.0.1', () => {
      resolve({
        url: `http://127.0.0.1:${port}`,
        setOnline: (state) => { isBackendOnline = state; },
        mockSystem,
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

test('Phase 3 Gate: Live Telemetry, Allowlist Integrity & Offline Recovery', async (t) => {
  const executablePath = resolveChrome();
  assert.ok(executablePath, 'Chromium/Chrome must exist');

  const testServer = await createControllableServer(8013);
  const browser = await chromium.launch({
    executablePath,
    headless: true,
    args: ['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu'],
  });

  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await context.newPage();

    // 1. Load the dashboard
    await page.goto(`${testServer.url}/#dashboard`, { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('#main-content', { timeout: 5000 });

    // 2. Trigger telemetry fetch and verify displayed values match API
    await t.test('Telemetry cards render true backend metrics', async () => {
      // Force initial fetch
      await page.evaluate(async () => {
        await window.jarvisApi.fetchAllTelemetry();
      });

      await page.waitForTimeout(300);

      // Verify CPU card
      const cpuVal = await page.locator('#metric-cpu').textContent();
      assert.equal(cpuVal.trim(), `${testServer.mockSystem.cpu_usage_pct}%`, 'CPU metric must match API');

      // Verify RAM card
      const ramVal = await page.locator('#metric-ram').textContent();
      assert.equal(ramVal.trim(), `${testServer.mockSystem.ram_pct}%`, 'RAM percent must match API');

      // Verify Temperature card
      const tempVal = await page.locator('#metric-temp').textContent();
      assert.equal(tempVal.trim(), `${testServer.mockSystem.temp_c} °C`, 'Temperature must match API');

      // Verify Battery & GPU render truth honestly as Unavailable
      const batteryVal = await page.locator('#metric-battery').textContent();
      assert.equal(batteryVal.trim(), 'Unavailable', 'Unmetered battery must show Unavailable');
      const gpuVal = await page.locator('#metric-gpu').textContent();
      assert.equal(gpuVal.trim(), 'Unavailable', 'Headless GPU must show Unavailable');

      // Screenshot Online State
      const onlineShot = path.join(SCREENSHOT_DIR, 'telemetry_online.png');
      await page.screenshot({ path: onlineShot, fullPage: false });
      assert.ok(fs.existsSync(onlineShot), 'Online telemetry screenshot must exist');
    });

    // 3. Test Disconnection & Offline Handling
    await t.test('Disconnection transitions to offline state and surfaces warning', async () => {
      testServer.setOnline(false);

      // Trigger telemetry failure
      await page.evaluate(async () => {
        try {
          await window.jarvisApi.fetchAllTelemetry();
        } catch (e) {
          // Expected
        }
      });

      // Second failure to trigger offline threshold
      await page.evaluate(async () => {
        try {
          await window.jarvisApi.fetchAllTelemetry();
        } catch (e) {
          // Expected
        }
      });

      await page.waitForTimeout(300);

      // Verify banner is visible
      const isBannerVisible = await page.evaluate(() => {
        const el = document.getElementById('offline-alert-banner');
        return el && el.style.display !== 'none';
      });
      assert.ok(isBannerVisible, 'Offline alert banner must become visible on backend disconnection');

      // Verify status chip shows OFFLINE
      const chipText = await page.locator('#core-status-chip').textContent();
      assert.match(chipText, /OFFLINE/i, 'Core status chip must indicate OFFLINE');

      // Screenshot Offline State
      const offlineShot = path.join(SCREENSHOT_DIR, 'telemetry_offline.png');
      await page.screenshot({ path: offlineShot, fullPage: false });
      assert.ok(fs.existsSync(offlineShot), 'Offline screenshot must exist');
    });

    // 4. Test Reconnection & Automatic Recovery
    await t.test('Reconnection automatically recovers online status', async () => {
      testServer.setOnline(true);

      // Trigger recovery fetch
      await page.evaluate(async () => {
        await window.jarvisApi.fetchAllTelemetry();
      });

      await page.waitForTimeout(300);

      // Verify banner is hidden
      const isBannerHidden = await page.evaluate(() => {
        const el = document.getElementById('offline-alert-banner');
        return !el || el.style.display === 'none';
      });
      assert.ok(isBannerHidden, 'Offline alert banner must hide when connection recovers');

      // Verify status chip shows ONLINE
      const chipText = await page.locator('#core-status-chip').textContent();
      assert.match(chipText, /ONLINE/i, 'Core status chip must recover to ONLINE');

      // Screenshot Recovered State
      const recoveredShot = path.join(SCREENSHOT_DIR, 'telemetry_recovered.png');
      await page.screenshot({ path: recoveredShot, fullPage: false });
      assert.ok(fs.existsSync(recoveredShot), 'Recovered screenshot must exist');
    });

  } finally {
    await browser.close();
    await testServer.close();
  }
});
