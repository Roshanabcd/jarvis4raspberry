// MOCK responses; no microphone, inference provider or speaker is used.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync('apps/dashboard/static/index.html', 'utf8');
const source = html.slice(html.indexOf('let isVoiceRecording = false;'), html.indexOf('// ─── Voice Center App'));
function setup(responses) {
  const nodes = Object.fromEntries(['mic-btn','mic-icon','mic-label','chat-status-badge'].map(id=>[id,{style:{}}]));
  const calls=[], messages=[];
  const context = vm.createContext({document:{getElementById:id=>nodes[id]},AbortSignal,
    addMsg:(...args)=>messages.push(args),
    playJarvisAudio:()=>{throw Error('Duplicate playback');},
    fetch:async(url, options)=>{calls.push({url,options});const r=responses.shift();if(r instanceof Error)throw r;return {ok:r.code<400,status:r.code,json:async()=>r.body};}});
  vm.runInContext(source,context);
  return {run:()=>context.toggleVoiceRecord(),nodes,calls,messages};
}
const noOwner={code:409,body:{}};
test('accepted owner request never opens a second recorder or claims completion',async()=>{
  const ui=setup([{code:200,body:{status:'accepted'}}]);
  const result=await ui.run();
  assert.equal(result.status,'accepted');assert.equal(ui.calls.length,1);
  assert.doesNotMatch(result.message,/finished|complete|Listening\.\.\./);
  assert.equal(ui.nodes['mic-btn'].disabled,false);
});
test('daemon ownership and capture errors are never reported as silence',async()=>{
  const ui=setup([noOwner,{code:200,body:{status:'error',message:'daemon owns the microphone'}}]);
  assert.equal((await ui.run()).status,'error');
  assert.doesNotMatch(ui.nodes['chat-status-badge'].textContent,/silence|No speech/);
});
test('confirmed no-speech response has its own outcome',async()=>{
  const ui=setup([noOwner,{code:200,body:{status:'empty'}}]);
  assert.equal((await ui.run()).status,'empty');
});
test('server-owned speech is queued once and never replayed in browser',async()=>{
  const ui=setup([noOwner,{code:200,body:{status:'ok',transcribed:'MOCK request',response:'MOCK reply',job_id:'j',audio_url:'/already-queued.wav'}}]);
  assert.equal((await ui.run()).status,'queued');assert.equal(ui.messages.length,2);
  assert.equal(ui.messages[1][2].audio_url,undefined);
});
test('permission or uncertain timeout cannot start fallback capture',async()=>{
  for(const r of [{code:403,body:{}},new Error('timeout')]) {
    const ui=setup([r]);assert.equal((await ui.run()).status,'error');assert.equal(ui.calls.length,1);
  }
});
test('text success without speech delivery remains a delivery error',async()=>{
  const ui=setup([noOwner,{code:200,body:{status:'ok',transcribed:'MOCK',response:'MOCK'}}]);
  assert.match((await ui.run()).message,/speech delivery is unavailable/);
});
