const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync('apps/dashboard/static/index.html', 'utf8');
const source = html.slice(html.indexOf('async function loadVoiceJobs()'), html.indexOf('async function testVoiceListen()'));

class Element {
  constructor(tag) { this.tag = tag; this.children = []; this.style = {}; this.listeners = {}; this._text = ''; }
  set textContent(value) { this._text = value; this.children = []; }
  get textContent() { return this._text + this.children.map(child => child.textContent).join(' '); }
  set innerHTML(value) { throw new Error('Job data must never be interpreted as HTML'); }
  appendChild(child) { this.children.push(child); }
  replaceChildren() { this.children = []; this._text = ''; }
  setAttribute() {}
  addEventListener(event, fn) { this.listeners[event] = fn; }
}
function setup(responder) {
  const nodes = {'voice-jobs-list': new Element('div'), 'voice-daemon-fb': new Element('div')};
  const calls = [];
  const context = vm.createContext({document: {getElementById: id => nodes[id], createElement: tag => new Element(tag)},
    fetch: async (url, options) => { calls.push({url, options}); return responder(url, options); }});
  vm.runInContext(source, context);
  return {context, nodes, calls};
}
const response = (data, ok = true) => ({ok, json: async () => data});

test('voice reply content is text and cancellation IDs cannot inject code or paths', async () => {
  const job = {job_id: "reply/');attack()", status: 'queued', text: '<img src=x onerror=attack()>'};
  const ui = setup(url => response(url.endsWith('/cancel') ? {status:'ok', cancelled:true} : {jobs:[job]}));
  await ui.context.loadVoiceJobs();
  assert.match(ui.nodes['voice-jobs-list'].textContent, /<img src=x onerror=attack\(\)>/);
  const row = ui.nodes['voice-jobs-list'].children[0];
  const cancel = row.children.find(el => el.tag === 'button');
  await cancel.listeners.click();
  assert.equal(ui.calls[1].url, `/api/voice/jobs/${encodeURIComponent(job.job_id)}/cancel`);
  assert.equal(ui.calls[1].options.method, 'POST');
});

test('failed delivery is visible without displaying upstream error or retrying the task', async () => {
  const ui = setup(() => response({jobs:[{job_id:'failed', status:'failed', text:'Done', error:'secret upstream detail'}]}));
  await ui.context.loadVoiceJobs();
  assert.match(ui.nodes['voice-jobs-list'].textContent, /Audio delivery failed/);
  assert.doesNotMatch(ui.nodes['voice-jobs-list'].textContent, /secret upstream/);
  assert.equal(ui.nodes['voice-jobs-list'].children[0].children.some(el => el.tag === 'button'), false);
  assert.equal(ui.calls.length, 1);
});

test('rejected cancellation reports uncertainty rather than claiming success', async () => {
  const ui = setup(() => response({}, false));
  assert.equal(await ui.context.cancelVoiceJob('job-1'), false);
  assert.match(ui.nodes['voice-daemon-fb'].textContent, /could not be confirmed/);
  assert.equal(ui.calls.length, 1);
});

test('HTTP and malformed status failures are visible', async () => {
  for (const result of [response({}, false), response({jobs:'invalid'})]) {
    const ui = setup(() => result);
    await ui.context.loadVoiceJobs();
    assert.match(ui.nodes['voice-jobs-list'].textContent, /Unable to load voice jobs/);
  }
});

test('restored interrupted voice jobs explain restart without replay controls', async () => {
  const ui = setup(() => response({jobs:[{job_id:'old-job', status:'failed', text:'', error:'Voice delivery interrupted by process restart; not replayed'}]}));
  await ui.context.loadVoiceJobs();
  assert.match(ui.nodes['voice-jobs-list'].textContent, /Earlier reply \(text not retained\)/);
  assert.match(ui.nodes['voice-jobs-list'].textContent, /Interrupted by restart/);
  assert.equal(ui.nodes['voice-jobs-list'].children[0].children.some(el => el.tag === 'button'), false);
});
