const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
class Element {
  constructor(tag='div') { this.tag=tag; this.children=[]; this.listeners={}; this.style={}; this.value=''; this._text=''; }
  set textContent(text) { this._text=text; this.children=[]; }
  get textContent() { return this._text+this.children.map(c=>c.textContent).join(' '); }
  set innerHTML(_) { throw Error('Unsafe HTML'); }
  appendChild(c) { this.children.push(c); }
  replaceChildren() { this.children=[]; this._text=''; }
  addEventListener(name,fn) { this.listeners[name]=fn; }
}
function setup(responder) {
  const nodes={};
  for(const id of ['form','input','submit','feedback','list','refresh']) nodes['background-task-'+id]=new Element();
  const calls=[], timers=[];
  const context=vm.createContext({AbortSignal:{timeout:()=>({})},crypto:{randomUUID:()=> 'synthetic-uuid'},
    fetch:async(url,init)=>{calls.push({url,init});return responder(url,init);},
    setTimeout:fn=>{timers.push(fn);return timers.length;},clearTimeout(){}});
  vm.runInContext(fs.readFileSync('apps/dashboard/static/background-tasks.js','utf8'),context);
  const mounted=context.JarvisBackgroundTasks.mount({getElementById:id=>nodes[id],createElement:tag=>new Element(tag)});
  return {nodes,calls,timers,mounted};
}
const response=(data,status=200)=>({ok:status<400,status,json:async()=>data});
const settle=()=>new Promise(resolve=>setImmediate(resolve));
test('accepted task permits chat and safely renders response text',async()=>{
  let submitted=false;
  const ui=setup((url,init)=>{
    if(init.method==='POST'){submitted=true;return response({job_id:'task-1',status:'accepted'});}
    return response({jobs:submitted?[{job_id:'task-1',status:'succeeded',result_available:true,response:'<img src=x onerror=attack()> completed'}]:[]});
  });
  await settle(); ui.nodes['background-task-input'].value='Summarize a topic';
  await ui.mounted.send({preventDefault(){}});
  const sent=ui.calls.find(c=>c.init.method==='POST');
  assert.deepEqual(JSON.parse(sent.init.body),{transcript:'Summarize a topic'});
  assert.equal(sent.init.headers['Idempotency-Key'],'synthetic-uuid');
  assert.equal(ui.nodes['background-task-submit'].disabled,false);
  assert.match(ui.nodes['background-task-feedback'].textContent,/keep chatting/);
  assert.match(ui.nodes['background-task-list'].textContent,/<img src=x onerror=attack\(\)>/);
});
test('uncertain submissions only retry explicitly with the same idempotency token',async()=>{
  const ui=setup((url,init)=>{if(init.method==='POST')throw Error('lost connection');return response({jobs:[]});});
  await settle();ui.nodes['background-task-input'].value='My task';
  await ui.mounted.send({preventDefault(){}});
  assert.match(ui.nodes['background-task-feedback'].textContent,/could not be confirmed/);
  assert.equal(ui.calls.filter(c=>c.init.method==='POST').length,1);
  await ui.mounted.send({preventDefault(){}});
  const posts=ui.calls.filter(c=>c.init.method==='POST');
  assert.equal(posts[0].init.headers['Idempotency-Key'],posts[1].init.headers['Idempotency-Key']);
  ui.nodes['background-task-input'].value='Different task';
  await ui.mounted.send({preventDefault(){}});
  assert.equal(ui.calls.filter(c=>c.init.method==='POST').length,2);
});
test('cancel encodes job ID and rejected cancellation does not claim success',async()=>{
  const ui=setup((url,init)=>response(init.method==='POST'?{}:{jobs:[{job_id:'a/b',status:'running'}]},init.method==='POST'?403:200));
  await settle();
  const button=ui.nodes['background-task-list'].children[0].children.find(c=>c.tag==='button');
  await button.listeners.click();
  assert.equal(ui.calls.at(-1).url,'/api/task-jobs/a%2Fb/cancel');
  assert.match(ui.nodes['background-task-feedback'].textContent,/could not be confirmed/);
});
test('restored interruption exposes no retry or false completion and polls only active work',async()=>{
  const ui=setup(()=>response({jobs:[{job_id:'restored',status:'interrupted',error_code:'sensitive upstream detail'}]}));
  await settle();
  assert.match(ui.nodes['background-task-list'].textContent,/Interrupted by restart/);
  assert.doesNotMatch(ui.nodes['background-task-list'].textContent,/sensitive upstream|Completed/);
  assert.equal(ui.timers.length,0);
});

test('failed task exposes error reason, working retry and dismiss actions',async()=>{
  const ui=setup((url,init)=>{
    if(init?.method==='POST') return response({job_id:'retried-1',status:'accepted'});
    if(init?.method==='DELETE') return response({status:'ok',dismissed:true});
    return response({jobs:[{job_id:'tjob_failed_1',status:'failed',error_detail:'Model provider returned no response'}]});
  });
  await settle();
  assert.match(ui.nodes['background-task-list'].textContent,/Model provider returned no response/);
  const actions=ui.nodes['background-task-list'].children[0].children.find(c=>c.children&&c.children.some(b=>b.textContent==='Retry task'));
  assert.ok(actions,'Actions container must be present for failed task');
  const retryBtn=actions.children.find(c=>c.textContent==='Retry task');
  const dismissBtn=actions.children.find(c=>c.textContent==='Dismiss task');
  await retryBtn.listeners.click();
  assert.ok(ui.calls.some(c=>c.url==='/api/task-jobs/tjob_failed_1/retry'&&c.init.method==='POST'));
  await dismissBtn.listeners.click();
  assert.ok(ui.calls.some(c=>c.url==='/api/task-jobs/tjob_failed_1'&&c.init.method==='DELETE'));
});

