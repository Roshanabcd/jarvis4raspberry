const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync('apps/dashboard/static/index.html', 'utf8');
const source = html.slice(html.indexOf('const integrationProviders ='), html.indexOf('// ─── System Telemetry'));
function setup(responder) {
  const nodes = {};
  for (const id of ['key-openai','key-gemini','key-anthropic','key-nvidia','key-openrouter','key-groq','key-together','url-hf-space','integrations-admin-pin','integrations-status']) nodes[id] = {value:'',textContent:''};
  const calls = [];
  const context = vm.createContext({ document:{getElementById:id=>nodes[id]},
    fetch:async (url, options)=>{calls.push({url, options}); return responder(url, options);}, initChatModels:async()=>{} });
  vm.runInContext(source, context);
  return {context,nodes,calls};
}
test('rejected save reports failure and clears PIN', async()=>{
  const {context,nodes}=setup(()=>({ok:false,status:401,json:async()=>({detail:'Administrator verification failed'})}));
  nodes['integrations-admin-pin'].value='test-pin';
  nodes['key-openai'].value='test-key';
  await context.saveIntegrations();
  assert.match(nodes['integrations-status'].textContent,/Save failed: Administrator/);
  assert.equal(nodes['integrations-admin-pin'].value,'');
  assert.equal(nodes['key-openai'].value,'test-key'); // permit correcting PIN without retyping key
});
test('save sends explicit admin authorization and excludes masks', async()=>{
  const {context,nodes,calls}=setup((url,options)=>({ok:true,status:200,json:async()=>options?{status:'ok'}:{settings:{openrouter_api_key:'********'}}}));
  nodes['integrations-admin-pin'].value='test-pin';
  nodes['key-openai'].value='abcd****xyz';
  nodes['key-openrouter'].value='test-router-key';
  await context.saveIntegrations();
  const request=calls[0].options;
  assert.equal(request.headers['X-Jarvis-Admin-Pin'],'test-pin');
  assert.equal(request.headers['X-Jarvis-Admin-Confirmation'],'privileged-settings-action');
  assert.deepEqual(JSON.parse(request.body),{settings:{openrouter_api_key:'test-router-key'}});
  assert.equal(nodes['key-openrouter'].value,'');
  assert.match(nodes['key-openrouter'].placeholder,/Saved/);
});
test('missing PIN never sends credentials',async()=>{
  const {context,nodes,calls}=setup(()=>{throw Error('must not fetch');});
  nodes['key-openai'].value='test-key';
  await context.saveIntegrations();
  assert.equal(calls.length,0);
  assert.match(nodes['integrations-status'].textContent,/administrator PIN/);
});
test('cloud probe displays missing credentials without claiming success',async()=>{
  const {context,nodes,calls}=setup(()=>({ok:true,status:200,json:async()=>({status:'missing_key'})}));
  nodes['integrations-admin-pin'].value='test-pin';
  await context.testIntegrations();
  assert.equal(calls.length,7);
  assert.match(nodes['integrations-status'].textContent,/openrouter: missing_key/);
  assert.equal(nodes['integrations-admin-pin'].value,'');
});
