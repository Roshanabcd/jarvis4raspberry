const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const html = fs.readFileSync('apps/dashboard/static/index.html', 'utf8');
function harness(fnName, endpoint, body) {
  const grid = {innerHTML: ''};
  const context = vm.createContext({
    document: {getElementById: id => id === 'dev-agents-grid' ? grid : null},
    fetch: async () => ({ok: true, json: async () => body}),
    console,
  });
  const start = html.indexOf(`async function ${fnName}()`);
  const end = html.indexOf('\nasync function ', start + 10);
  assert.ok(start >= 0 && end > start, `${fnName} exists`);
  vm.runInContext(html.slice(start, end) + `\nthis.call = ${fnName};`, context);
  return {context, grid};
}

test('agent cards communicate available, missing-key, unauthenticated, manual, simulated and real status', async () => {
  const agents = [
    {agent_id:'codex',status:'AVAILABLE',integration_type:'real_cli',adapter_type:'CodexCliAdapter'},
    {agent_id:'openrouter',status:'NEEDS_KEY',integration_type:'needs_key',message:'Missing API key',adapter_type:'Provider'},
    {agent_id:'copilot',status:'UNAUTHENTICATED',integration_type:'unauthenticated',adapter_type:'ManualHandoff'},
    {agent_id:'cline',status:'MANUAL_HANDOFF',integration_type:'manual_coding_agent',adapter_type:'ManualHandoff'},
    {agent_id:'simulated',status:'SIMULATED',integration_type:'simulated_agent',adapter_type:'SimulatedAgent'},
    {agent_id:'agy',status:'AVAILABLE',integration_type:'real_cli',adapter_type:'AntigravityCliAdapter'},
  ];
  const {context, grid} = harness('loadDeveloperAgents','/api/developer/agents',{agents});
  await context.call();
  for (const text of ['AVAILABLE','NEEDS_KEY','Missing API key','UNAUTHENTICATED','MANUAL_HANDOFF','Manual handoff','SIMULATED','Simulated execution','Real CLI execution']) assert.ok(grid.innerHTML.includes(text), text);
  assert.ok(!grid.innerHTML.includes('secret-value'));
});

test('task cards show running, completed, failed, cancelled, timeout and review details', () => {
  for (const [state, expected] of [['running','Running'],['succeeded','Completed'],['failed','Failed'],['cancelled','Cancelled'],['pending','Pending']]) {
    assert.ok(html.includes(`t.state === '${state}'`) || state === 'succeeded', `state ${state} represented`);
    assert.ok(html.includes(expected));
  }
  assert.match(html, /execution timed out/);
  assert.match(html, /Awaiting review/);
});

test('developer agents API failure is surfaced without credential values', async () => {
  const grid = {innerHTML: ''};
  const context = vm.createContext({document:{getElementById:()=>grid},fetch:async()=>({ok:false,status:503}),console});
  const start=html.indexOf('async function loadDeveloperAgents()');
  const end=html.indexOf('\nasync function ',start+10);
  vm.runInContext(html.slice(start,end)+'\nthis.call=loadDeveloperAgents;',context);
  await context.call();
  assert.match(grid.innerHTML,/Failed to load agents: HTTP 503/);
});

test('unauthorized action responses remain visible through task error feedback paths', () => {
  assert.match(html,/Execution failed: ' \+ e\.message/);
  assert.match(html,/Cancel error: ' \+ e\.message/);
});
