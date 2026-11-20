const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const html = fs.readFileSync('apps/dashboard/static/index.html', 'utf8');
const start = html.indexOf('function formatApiDetail');
const end = html.indexOf('// ─── Tab Navigation');
assert.ok(start > 0 && end > start, 'UI feedback helpers must exist in dashboard HTML');
const source = html.slice(start, end);

function setup() {
  const nodes = new Map();
  const makeNode = () => ({
    textContent: '',
    className: '',
    attributes: {},
    classList: {
      _classes: new Set(),
      add(...names) { names.forEach(n => this._classes.add(n)); },
      remove(...names) { names.forEach(n => this._classes.delete(n)); },
      contains(name) { return this._classes.has(name); },
    },
    setAttribute(name, value) { this.attributes[name] = String(value); },
    getAttribute(name) { return this.attributes[name]; },
    appendChild(child) { this.children = this.children || []; this.children.push(child); },
    remove() { this.removed = true; },
    children: [],
  });
  const get = id => {
    if (!nodes.has(id)) nodes.set(id, makeNode());
    return nodes.get(id);
  };
  const created = [];
  const context = vm.createContext({
    document: {
      getElementById: get,
      createElement: (tag) => {
        const el = makeNode();
        el.tagName = tag;
        created.push(el);
        return el;
      },
    },
    setTimeout: (fn) => { fn(); return 1; },
    String,
    Array,
    JSON,
  });
  vm.runInContext(source + '\nthis.formatApiDetail = formatApiDetail;\nthis.showUiFeedback = showUiFeedback;\nthis.setStatusTone = setStatusTone;', context);
  return {context, get, created};
}

test('formatApiDetail flattens FastAPI validation arrays', () => {
  const {context} = setup();
  assert.equal(context.formatApiDetail('plain'), 'plain');
  assert.equal(context.formatApiDetail([{msg: 'bad pin'}, {message: 'retry'}]), 'bad pin; retry');
  assert.equal(context.formatApiDetail({msg: 'denied'}), 'denied');
});

test('showUiFeedback paints status tone and toast alert on errors', () => {
  const {context, get, created} = setup();
  context.showUiFeedback('Launch failed: offline', {tone: 'error', statusId: 'dt-desktop-feedback', toast: true});
  const status = get('dt-desktop-feedback');
  assert.equal(status.textContent, 'Launch failed: offline');
  assert.equal(status.classList.contains('is-error'), true);
  assert.equal(status.getAttribute('role'), 'alert');
  assert.equal(created.length, 1);
  assert.equal(created[0].getAttribute('role'), 'alert');
  assert.match(created[0].className, /ui-toast/);
  assert.match(created[0].className, /error/);
});

test('showUiFeedback can update status without toast', () => {
  const {context, get, created} = setup();
  context.showUiFeedback('Screenshot captured.', {tone: 'ok', statusId: 'comp-action-feedback', toast: false});
  assert.equal(get('comp-action-feedback').textContent, 'Screenshot captured.');
  assert.equal(get('comp-action-feedback').classList.contains('is-ok'), true);
  assert.equal(created.length, 0);
});

test('dashboard markup keeps desktop and computer controls with a11y landmarks', () => {
  assert.match(html, /id="main-content"/);
  assert.match(html, /class="skip-link"/);
  assert.match(html, /id="tab-desktop"/);
  assert.match(html, /id="tab-computer"/);
  assert.match(html, /id="active-desktop-start"/);
  assert.match(html, /id="active-desktop-panel"/);
  assert.match(html, /role="tablist"/);
  assert.match(html, /aria-live="polite"/);
  assert.match(html, /prefers-reduced-motion/);
  assert.match(html, /id="dt-desktop-feedback"/);
  assert.match(html, /id="comp-action-feedback"/);
});
