// Offline fixtures only: no browser capture, network or real playback.
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
function setup(api={}) {
  let captures=0, spoken=0;
  const window={addEventListener(){},jarvisApi:api,jarvisAvatar:{setState(){},setMouthShape(){}},speechSynthesis:{cancel(){},speak(){spoken++;}}};
  const context=vm.createContext({window,document:{getElementById:()=>null},navigator:{mediaDevices:{getUserMedia(){captures++;throw Error('Competing capture');}}},console,performance,setTimeout:fn=>{fn();return 1;},clearInterval(){},cancelAnimationFrame(){}});
  vm.runInContext(fs.readFileSync('apps/dashboard/futuristic/voice.js','utf8'),context);
  const voice=window.jarvisVoice;
  voice.updateView=()=>{};voice.hideErrorBanner=()=>{};
  voice.playAudioUrl=()=>{spoken++;};
  return {voice,window,captures:()=>captures,spoken:()=>spoken};
}
test('microphone delegates to existing owner without browser capture',async()=>{
  let requests=0;
  const ui=setup({pushToTalk:async()=>{requests++;return {status:'accepted'};}});
  await ui.voice.startListening();await ui.voice.startListening();
  assert.equal(requests,1);assert.equal(ui.captures(),0);
  assert.equal(ui.voice.state,'processing');
  assert.match(ui.voice.currentSubtitles.status,/Waiting/);
});
test('one command creates no additional synthesis or browser playback',async()=>{
  let commands=0,syntheses=0;
  const statuses=['queued','playing','completed'];
  const ui=setup({sendVoiceCommand:async()=>{commands++;return {status:'ok',response:'Reply',job_id:'job-1',audio_url:'/unused.wav'};},getVoiceJob:async()=>({job:{status:statuses.shift()}}),synthesizeSpeech:async()=>{syntheses++;}});
  await ui.voice.handleUserVoiceInput('A request');
  assert.equal(commands,1);assert.equal(syntheses,0);assert.equal(ui.spoken(),0);
  assert.equal(ui.voice.currentSubtitles.status,'System playback completed');
});
test('empty replies are failures rather than invented success',async()=>{
  const ui=setup({sendVoiceCommand:async()=>({status:'ok'})});
  await ui.voice.handleUserVoiceInput('My request');
  assert.equal(ui.voice.state,'error');assert.equal(ui.spoken(),0);
  assert.doesNotMatch(ui.voice.currentSubtitles.text,/Command processed/);
});
test('interrupt while inference is pending cancels its late job',async()=>{
  let resolve;const cancelled=[];
  const ui=setup({sendVoiceCommand:()=>new Promise(done=>{resolve=done;}),cancelVoiceJob:async id=>cancelled.push(id),interruptVoice:async()=>({status:'ok'})});
  const pending=ui.voice.handleUserVoiceInput('A request');
  await ui.voice.interrupt();
  resolve({status:'ok',response:'Late reply',job_id:'late-job'});
  await pending;
  assert.deepEqual(cancelled,['late-job']);assert.equal(ui.spoken(),0);
});
test('listen_once response is not submitted for inference twice',async()=>{
  let repeated=0;
  const ui=setup({listenOnce:async()=>({status:'ok',response:'Already answered',transcribed:'hello',job_id:'existing'}),getVoiceJob:async()=>({job:{status:'completed'}}),sendVoiceCommand:async()=>{repeated++;}});
  await ui.voice.runBackendListenOnce();assert.equal(repeated,0);assert.equal(ui.spoken(),0);
});
test('failed system delivery remains failed and never falls back to extra playback',async()=>{
  const ui=setup({sendVoiceCommand:async()=>({status:'ok',response:'Reply',job_id:'failed'}),getVoiceJob:async()=>({job:{status:'failed',error:'private detail'}})});
  await ui.voice.handleUserVoiceInput('A request');
  assert.equal(ui.voice.state,'error');assert.equal(ui.spoken(),0);
  assert.equal(ui.voice.currentSubtitles.status,'Speech delivery failed');
  assert.doesNotMatch(ui.voice.currentSubtitles.text,/private detail/);
});

test('late capture acceptance cannot undo mute',async()=>{
  let resolve,mutes=0;
  const ui=setup({pushToTalk:()=>new Promise(done=>{resolve=done;}),muteVoice:async()=>{mutes++;},interruptVoice:async()=>({status:'ok'})});
  const pending=ui.voice.startListening();
  await ui.voice.mute();
  const count=mutes;
  resolve({status:'accepted'});await pending;
  assert.equal(ui.voice.isMuted,true);assert.equal(mutes,count+1);assert.equal(ui.captures(),0);
  assert.equal(ui.voice.captureRequested,false);
});

test('standby before daemon accepts capture does not dismiss pending request',async()=>{
  let state='STANDBY_LISTENING';
  const ui=setup({pushToTalk:async()=>({status:'accepted'}),getVoiceStatus:async()=>({muted:false}),getWakeStatus:async()=>({state})});
  await ui.voice.startListening();await ui.voice.refreshStatus();
  assert.equal(ui.voice.captureRequested,true);
  state='LISTENING_SPEECH';await ui.voice.refreshStatus();
  assert.equal(ui.voice.state,'listening');
  state='STREAMING_TRANSCRIPTION';await ui.voice.refreshStatus();
  assert.equal(ui.voice.state,'processing');
  state='FOLLOW_UP_STANDBY';await ui.voice.refreshStatus();
  assert.equal(ui.voice.captureRequested,false);
  assert.doesNotMatch(ui.voice.currentSubtitles.status,/complete/i);
});
test('late status poll cannot undo mute',async()=>{
  let resolve;
  const ui=setup({getVoiceStatus:()=>new Promise(done=>{resolve=done;}),muteVoice:async()=>{},interruptVoice:async()=>{}});
  const pending=ui.voice.refreshStatus();await ui.voice.mute();
  resolve({muted:false});await pending;
  assert.equal(ui.voice.isMuted,true);assert.equal(ui.voice.state,'muted');
});
test('capture failure and status timeout remain explicit, without resubmission',async()=>{
  const ui=setup({pushToTalk:async()=>({status:'accepted'}),getVoiceStatus:async()=>({muted:false}),getWakeStatus:async()=>({state:'STANDBY_LISTENING'})});
  await ui.voice.startListening();ui.voice.captureDeadline=0;await ui.voice.refreshStatus();
  assert.equal(ui.voice.state,'error');assert.match(ui.voice.currentSubtitles.status,/timeout/);
});
