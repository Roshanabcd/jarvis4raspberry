const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('apps/dashboard/static/active-desktop.js', 'utf8');

function setup({denied = false, delayed = false, failedStart = false, detail = 'Another tab is active',
                captureError, secure = true, width = 80, emptyBlob = false, delayFrame = false,
                delayStop = false} = {}) {
  const elements = new Map(), calls = [], callbacks = new Map();
  let stopped = 0, release, releaseFrame, releaseStop;
  const element = id => {
    if (!elements.has(id)) {
      elements.set(id, {
        checked: true,
        disabled: false,
        hidden: true,
        textContent: '',
        value: '',
        classList: {
          _classes: new Set(),
          add(...names) { names.forEach(n => this._classes.add(n)); },
          remove(...names) { names.forEach(n => this._classes.delete(n)); },
          contains(name) { return this._classes.has(name); },
        },
        dataset: {},
        attributes: {},
        setAttribute(name, value) { this.attributes[name] = String(value); },
        getAttribute(name) { return this.attributes[name]; },
        addEventListener(name, fn) { callbacks.set(`${id}:${name}`, fn); },
        videoWidth: width,
        videoHeight: 40,
        play: async () => {},
        closest() { return element('active-desktop-panel'); },
      });
    }
    return elements.get(id);
  };
  const track = {stop: () => stopped++, addEventListener: (name, fn) => callbacks.set(name, fn)};
  const stream = {getTracks: () => [track], getVideoTracks: () => [track]};
  const window = {isSecureContext: secure, addEventListener: (name, fn) => callbacks.set(name, fn)};
  const sandbox = {
    window,
    document: {
      readyState: 'complete',
      getElementById: element,
      createElement: () => ({getContext: () => ({drawImage() {}}), toBlob: fn => fn(emptyBlob ? null : {})}),
      addEventListener() {},
    },
    navigator: {mediaDevices: {getDisplayMedia: async () => {
      if (captureError) throw captureError;
      if (denied) throw new Error('Permission denied');
      if (delayed) return new Promise(resolve => {release = () => resolve(stream);});
      return stream;
    }}},
    fetch: async (url, options) => {
      calls.push({url, options});
      if (delayFrame && String(url).endsWith('/frame')) {
        await new Promise(resolve => { releaseFrame = resolve; });
      }
      if (delayStop && String(url).endsWith('/stop')) {
        await new Promise(resolve => { releaseStop = resolve; });
      }
      if (failedStart && String(url).endsWith('/start')) {
        return {ok: false, json: async () => ({detail})};
      }
      if (String(url).endsWith('/describe')) {
        return {ok: true, json: async () => ({description: 'A terminal window.', note: 'Local vision result.'})};
      }
      if (String(url).endsWith('/read-text')) {
        return {ok: true, json: async () => ({text: 'hello', note: 'OCR note.'})};
      }
      return {
        ok: true,
        json: async () => ({
          token: 'test-token',
          options: {speaker: true},
          microphone: {state: 'listening'},
          screen: 'receiving',
        }),
      };
    },
    setTimeout: fn => { callbacks.set('frame-timer', fn); return 1; },
    setInterval: () => 2,
    clearTimeout() {},
    clearInterval() {},
    stopSpeech() {},
  };
  vm.runInNewContext(source, sandbox);
  return {api: window.jarvisDesktop, element, calls, callbacks, release: () => release(),
          releaseFrame: () => releaseFrame(), releaseStop: () => releaseStop(), stopped: () => stopped};
}

test('activation uploads frames and stop releases tracks and sends revocation', async () => {
  const t = setup(); await t.api.start();
  assert(t.calls.some(c => c.url.endsWith('/frame')));
  assert.equal(t.element('active-desktop-banner').hidden, false);
  assert.equal(t.element('active-desktop-banner').getAttribute('aria-hidden'), 'false');
  assert.equal(t.element('active-desktop-status').classList.contains('is-ok'), true);
  await t.api.stop();
  assert.equal(t.stopped(), 1);
  assert(t.calls.some(c => c.url.endsWith('/stop')));
  assert.equal(t.element('active-desktop-banner').hidden, true);
  assert.equal(t.element('active-desktop-banner').getAttribute('aria-hidden'), 'true');
});

test('denied sharing never starts the backend or microphone', async () => {
  const t = setup({denied: true}); await t.api.start();
  assert.equal(t.calls.length, 0);
  assert.match(t.element('active-desktop-status').textContent, /Permission denied/);
  assert.equal(t.element('active-desktop-status').classList.contains('is-error'), true);
  assert.equal(t.element('active-desktop-status').getAttribute('role'), 'alert');
  assert.equal(t.element('active-desktop-start').disabled, false);
});

test('stopping while the picker is pending releases late streams', async () => {
  const t = setup({delayed: true}); const start = t.api.start();
  await t.api.stop(); t.release(); await start;
  assert.equal(t.stopped(), 1);
  assert.equal(t.calls.length, 0);
});

test('backend conflict releases acquired screen and surfaces detail', async () => {
  const t = setup({failedStart: true, detail: [{msg: 'Another tab is active'}]});
  await t.api.start();
  assert.equal(t.stopped(), 1);
  assert.equal(t.element('active-desktop-banner').hidden, true);
  assert.match(t.element('active-desktop-status').textContent, /Another tab is active/);
  assert.equal(t.element('active-desktop-status').classList.contains('is-error'), true);
});

test('browser stop-sharing event revokes the session', async () => {
  const t = setup(); await t.api.start(); await t.callbacks.get('ended')();
  assert(t.calls.some(c => c.url.endsWith('/stop')));
  assert.equal(t.element('active-desktop-preview').srcObject, null);
});

test('Enter on question triggers describe when enabled', async () => {
  const t = setup();
  await t.api.start();
  t.element('active-desktop-question').value = 'What error is on screen?';
  const handler = t.callbacks.get('active-desktop-question:keydown');
  assert.ok(handler, 'question input should bind Enter handler');
  handler({key: 'Enter', preventDefault() {}});
  await new Promise(resolve => setTimeout(resolve, 0));
  assert(t.calls.some(c => c.url.endsWith('/describe')));
  assert.match(t.element('active-desktop-answer').textContent, /terminal window/i);
  assert.equal(t.element('active-desktop-answer').classList.contains('is-ok'), true);
});

test('screen actions wait for the first successfully transferred frame', async () => {
  const t = setup({width: 0});
  await t.api.start();
  assert.equal(t.element('active-desktop-describe').disabled, true);
  await t.api.describe();
  assert.equal(t.calls.filter(c => c.url.endsWith('/describe')).length, 0);
  t.element('active-desktop-preview').videoWidth = 80;
  await t.callbacks.get('frame-timer')();
  assert.equal(t.element('active-desktop-describe').disabled, false);
});

test('describe and OCR each transfer a current screen frame first', async () => {
  const t = setup();
  await t.api.start();
  await t.api.describe();
  await t.api.readText();
  assert.deepEqual(t.calls.map(c => c.url.split('/').pop()),
    ['start', 'frame', 'frame', 'describe', 'frame', 'read-text']);
});

test('permission rejection and insecure pages give actionable errors without activation', async () => {
  for (const options of [{captureError: {name: 'NotAllowedError'}}, {secure: false}]) {
    const t = setup(options);
    await t.api.start();
    assert.equal(t.calls.length, 0);
    assert.match(t.element('active-desktop-status').textContent, /permission was denied|http:\/\/localhost/);
  }
});

test('failed frame encoding releases capture and revokes the backend session', async () => {
  const t = setup({emptyBlob: true});
  await t.api.start();
  assert.equal(t.stopped(), 1);
  assert(t.calls.some(c => c.url.endsWith('/stop')));
  assert.match(t.element('active-desktop-status').textContent, /could not create a screen frame/);
});

test('a late ended event from a previous stream cannot stop a new session', async () => {
  const t = setup();
  await t.api.start();
  const ended = t.callbacks.get('ended');
  await t.api.stop();
  await t.api.start();
  await ended();
  assert.equal(t.element('active-desktop-banner').hidden, false);
  assert.equal(t.calls.filter(c => c.url.endsWith('/stop')).length, 1);
});

test('a pending upload cannot enable controls or schedule uploads after stop', async () => {
  const t = setup({delayFrame: true});
  const starting = t.api.start();
  await new Promise(resolve => setImmediate(resolve));
  await t.api.stop();
  t.releaseFrame();
  await starting;
  assert.equal(t.element('active-desktop-describe').disabled, true);
  assert.equal(t.callbacks.has('frame-timer'), false);
});

test('analysis and the periodic uploader share one pending frame transfer', async () => {
  const t = setup({delayFrame: true});
  const starting = t.api.start();
  await new Promise(resolve => setImmediate(resolve));
  t.releaseFrame();
  await starting;
  const describing = t.api.describe();
  const periodic = t.callbacks.get('frame-timer')();
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(t.calls.filter(c => c.url.endsWith('/frame')).length, 2);
  assert.equal(t.calls.filter(c => c.url.endsWith('/describe')).length, 0);
  assert.equal(t.element('active-desktop-read-text').disabled, true);
  t.releaseFrame();
  await Promise.all([describing, periodic]);
  assert.equal(t.calls.filter(c => c.url.endsWith('/describe')).length, 1);
  assert.equal(t.element('active-desktop-read-text').disabled, false);
});

test('a delayed stop response cannot replace the new session status', async () => {
  const t = setup({delayStop: true});
  await t.api.start();
  const stopping = t.api.stop();
  await t.api.start();
  t.releaseStop();
  await stopping;
  assert.match(t.element('active-desktop-status').textContent, /JARVIS active/);
});
