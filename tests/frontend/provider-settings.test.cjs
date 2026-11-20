const test = require('node:test');
const assert = require('node:assert/strict');
const {mount} = require('../../apps/dashboard/static/provider-settings.js');

class Element {
  constructor(tag, doc) { this.tagName = tag; this.ownerDocument = doc; this.children = []; this.attributes = {}; this.listeners = {}; this.value = ''; this._text = ''; }
  set textContent(text) { this._text = text; this.children = []; }
  get textContent() { return this._text + this.children.map(child => child.textContent).join(' '); }
  set innerHTML(_) { throw new Error('Untrusted HTML insertion is prohibited'); }
  appendChild(child) { child.parent = this; this.children.push(child); return child; }
  replaceChildren() { this.children = []; this._text = ''; this.value = ''; }
  setAttribute(name, value) { this.attributes[name] = value; }
  addEventListener(name, fn) { this.listeners[name] = fn; }
  removeEventListener(name) { delete this.listeners[name]; }
  remove() { if (this.parent) this.parent.children = this.parent.children.filter(child => child !== this); }
}
const metadata = () => ({providers: [
  {name:'openai', model:'gpt:test', models:['gpt:test','gpt:new'], active:true, available:true, enabled:true, credential_configured:true, verification:'not_tested'},
  {name:'groq', model:'groq:test', models:['groq:test'], active:false, available:false, enabled:true, credential_configured:false},
  {name:'ollama', model:'local:latest', models:['local:latest'], active:false, available:true, enabled:true, credential_configured:null}
], active_provider:'openai', active_model:'gpt:test'});
function response(data, status = 200) { return {ok:status >= 200 && status < 300, status, json:async()=>data}; }
function setup(responder, extra = {}) {
  const doc = {createElement:tag=>new Element(tag,doc)};
  const root = new Element('div', doc);
  const calls = [];
  const controller = mount(root, {...extra, fetch:async(url, options)=>{
    calls.push({url,options});
    return responder ? responder(url,options,calls.length) : response(metadata());
  }});
  const all = () => {
    const found = [];
    function walk(el) { found.push(el); el.children.forEach(walk); }
    walk(root); return found;
  };
  return {root, calls, controller, all,
    find:label=>all().find(el=>el.attributes['aria-label'] === label),
    button:text=>all().find(el=>el.tagName === 'button' && el.textContent === text),
    feedback:()=>all().find(el=>el.attributes['aria-live'] === 'polite')};
}

test('mount reads metadata only; configured is never displayed as tested', async()=>{
  const ui = setup(); await ui.controller.ready;
  assert.equal(ui.calls.length,1);
  assert.equal(ui.calls[0].url,'/api/chat/providers');
  assert.match(ui.root.textContent,/openai: Credentials configured; backend available; Not tested/);
  assert.match(ui.root.textContent,/groq: API key not configured/);
  assert.match(ui.root.textContent,/ollama: Local provider/);
  assert.equal(ui.button('Test selected cloud provider').disabled,true);
});

test('successful switch handles colon model and confirms echoed active selection', async()=>{
  let notification;
  const ui = setup((url,options)=>response(url.endsWith('/model') ? {success:true,active_provider:'openai',active_model:'gpt:new'} : metadata()), {onSelectionChange:value=>{notification=value;}});
  await ui.controller.ready;
  assert.equal(await ui.controller.switchModel('openai','gpt:new'),true);
  assert.deepEqual(JSON.parse(ui.calls[1].options.body),{provider:'openai',model:'gpt:new'});
  assert.deepEqual(notification,{provider:'openai',model:'gpt:new'});
  assert.match(ui.root.textContent,/Active selection: openai \/ gpt:new/);
  assert.match(ui.feedback().textContent,/Generation has not been tested/);
});

test('false or mismatched switch response preserves last confirmed selection', async()=>{
  for (const reply of [{success:false}, {success:true,active_provider:'ollama',active_model:'local:latest'}]) {
    const ui = setup(url=>response(url.endsWith('/model') ? reply : metadata()));
    await ui.controller.ready;
    assert.equal(await ui.controller.switchModel('openai','gpt:new'),false);
    assert.match(ui.feedback().textContent,/not confirmed/);
    assert.match(ui.root.textContent,/Active selection: openai \/ gpt:test/);
    assert.equal(ui.find('AI model').value,'gpt:test');
  }
});

test('unauthorized or unavailable providers never send test requests', async()=>{
  const ui = setup(); await ui.controller.ready;
  assert.equal(await ui.controller.testSelected(),false);
  assert.match(ui.feedback().textContent,/authorization is required/);
  ui.find('AI provider').value = 'groq';
  assert.equal(await ui.controller.testSelected(),false);
  assert.equal(ui.calls.length,1);
});

test('explicit tests use authorization, configured model, and status allowlist', async()=>{
  let authorized = 0;
  let outcome = 'authentication_failed';
  const ui = setup(url=>response(url.endsWith('/test') ? {provider:'openai',model:'gpt:test',status:outcome,error:'secret-test-value'} : metadata()), {authorizeTest:async()=>{authorized++;return {'X-Jarvis-Admin-Confirmation':'privileged-settings-action'};}});
  await ui.controller.ready;
  assert.equal(authorized,0);
  ui.find('AI model').value = 'gpt:new';
  assert.equal(await ui.controller.testSelected(),false);
  assert.equal(authorized,1);
  assert.match(ui.feedback().textContent,/openai \/ gpt:test: Authentication failed/);
  assert.equal(ui.feedback().attributes.role,'alert');
  assert.doesNotMatch(ui.root.textContent,/secret-test-value/);
  assert.deepEqual(JSON.parse(ui.calls[1].options.body),{provider:'openai'});
  assert.equal(ui.calls[1].options.headers['X-Jarvis-Admin-Confirmation'],'privileged-settings-action');
  outcome = 'passed';
  assert.equal(await ui.controller.testSelected(),true);
  assert.match(ui.root.textContent,/Test passed \(gpt:test\)/);
  assert.equal(ui.find('AI model').value,'gpt:new');
  await ui.controller.refresh();
  assert.doesNotMatch(ui.root.textContent,/Test passed/);
});

test('test response for a different model cannot verify configured model', async()=>{
  const ui = setup(url=>response(url.endsWith('/test') ? {provider:'openai',model:'other',status:'passed'} : metadata()), {authorizeTest:async()=>({})});
  await ui.controller.ready;
  assert.equal(await ui.controller.testSelected(),false);
  assert.match(ui.feedback().textContent,/did not match/);
  assert.doesNotMatch(ui.root.textContent,/Test passed/);
});

test('HTTP and network failures never display raw errors or response detail', async()=>{
  for (const fail of [()=>response({detail:'secret-test-value'},401),()=>{throw Error('secret-test-value');},()=>({ok:true,json:async()=>{throw Error('secret-test-value');}})]) {
    const ui = setup((url,options,count)=>count === 1 ? response(metadata()) : fail());
    await ui.controller.ready;
    assert.equal(await ui.controller.switchModel('openai','gpt:new'),false);
    assert.equal(ui.feedback().attributes.role,'alert');
    assert.doesNotMatch(ui.root.textContent,/secret-test-value/);
  }
});

test('invalid metadata is rejected; model labels are text, never HTML', async()=>{
  const invalid = setup(()=>response({providers:[{name:'<script>',models:[]}]}));
  assert.equal(await invalid.controller.ready,false);
  assert.match(invalid.feedback().textContent,/invalid provider metadata/);
  const data = metadata();
  data.providers[0].models.push('<img src=x onerror=alert(1)>');
  const safe = setup(()=>response(data));
  assert.equal(await safe.controller.ready,true);
  assert.match(safe.find('AI model').textContent,/<img src=x/);
});

test('busy state blocks duplicate operations and destruction ignores pending results', async()=>{
  let finish;
  const ui = setup(()=>new Promise(resolve=>{finish=resolve;}));
  assert.equal(ui.button('Refresh provider status').disabled,true);
  assert.equal(await ui.controller.refresh(),false);
  assert.equal(await ui.controller.switchModel('openai','gpt:new'),false);
  assert.equal(ui.calls.length,1);
  ui.controller.destroy();
  assert.equal(ui.calls[0].options.signal.aborted,true);
  finish(response(metadata()));
  assert.equal(await ui.controller.ready,false);
  assert.equal(ui.root.children.length,0);
});

test('failed refresh invalidates previous passing probe', async()=>{
  let refreshFailed = false;
  const ui = setup(url=>url.endsWith('/test') ? response({provider:'openai',model:'gpt:test',status:'passed'}) : refreshFailed ? response({},503) : response(metadata()), {authorizeTest:async()=>({})});
  await ui.controller.ready;
  await ui.controller.testSelected();
  assert.match(ui.root.textContent,/Test passed/);
  refreshFailed = true;
  assert.equal(await ui.controller.refresh(),false);
  assert.doesNotMatch(ui.root.textContent,/Test passed/);
  assert.match(ui.feedback().textContent,/HTTP 503/);
});
