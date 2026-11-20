(function (root) {
  'use strict';
  const doc = root.document;
  if (!doc?.getElementById('cc-hero')) return;
  const byId = id => doc.getElementById(id);
  const text = (id, value) => { const el=byId(id); if(el) el.textContent=String(value); };
  const read = (key, fallback) => { try{return root.localStorage.getItem('jarvis.home.'+key)||fallback;}catch(_){return fallback;} };
  const save = (key, value) => { try{root.localStorage.setItem('jarvis.home.'+key,value);}catch(_){} };
  const output=byId('cc-voice-output'), voice=byId('cc-browser-voice'), rate=byId('cc-voice-rate');
  output.value=['server','browser','off'].includes(read('output','server'))?read('output','server'):'server';
  rate.value=String(Math.max(.6,Math.min(1.5,Number(read('rate','1'))||1)));
  let voices=[], speechGeneration=0, speaking=false, refreshing=false, wasOnline=false;
  let wakeState='Checking', lastChatText='';
  function state(kind, label) { byId('cc-hero').dataset.state=kind; text('cc-state',label); }
  function idleState() {
    if(speaking) return;
    if(byId('chat-send-btn')?.disabled) state('thinking','Thinking');
    else if(!wasOnline) state('offline','Connection unavailable');
    else if(['LISTENING_SPEECH','WAKE_DETECTED','FOLLOW_UP_STANDBY'].includes(wakeState)) state('listening','Listening');
    else state('idle','Ready');
  }
  function stopBrowserSpeech() {
    speechGeneration++;
    root.speechSynthesis?.cancel();
    speaking=false;
    idleState();
  }
  function loadVoices() {
    voices=root.speechSynthesis?.getVoices()||[];
    const preferred=read('voice','');
    voice.replaceChildren();
    const option=doc.createElement('option'); option.value=''; option.textContent='Default browser voice'; voice.appendChild(option);
    for(const item of voices) { const el=doc.createElement('option'); el.value=item.voiceURI; el.textContent=`${item.name} · ${item.lang}`; voice.appendChild(el); }
    voice.value=voices.some(item=>item.voiceURI===preferred)?preferred:'';
    voice.disabled=!root.speechSynthesis;
    if(!root.speechSynthesis) text('cc-voice-feedback','Browser speech is unavailable. Select the JARVIS voice engine.');
  }
  function speak(message) {
    if(!root.speechSynthesis || !root.SpeechSynthesisUtterance) { text('cc-voice-feedback','Browser speech is unavailable. Use the JARVIS voice engine.'); return; }
    stopBrowserSpeech();
    const player=byId('jarvis-audio-player'); if(player) player.pause();
    const generation=speechGeneration;
    // Short utterances avoid browser engines dropping long answers. Playback
    // state comes from actual speech events, never a timed visual substitute.
    const remaining=[];
    let rest=String(message);
    while(rest.length>300){const space=rest.lastIndexOf(' ',300);const cut=space>150?space+1:300;remaining.push(rest.slice(0,cut));rest=rest.slice(cut);}
    if(rest)remaining.push(rest);
    function next() {
      if(generation!==speechGeneration) return;
      const part=remaining.shift();
      if(!part) { speaking=false; idleState(); return; }
      const utterance=new root.SpeechSynthesisUtterance(part);
      utterance.rate=Number(rate.value);
      const selected=voices.find(item=>item.voiceURI===voice.value);
      if(selected) {utterance.voice=selected;utterance.lang=selected.lang;}
      utterance.onstart=()=>{if(generation===speechGeneration){speaking=true;state('speaking','Speaking');}};
      utterance.onend=()=>{if(generation===speechGeneration)next();};
      utterance.onerror=()=>{if(generation===speechGeneration){speaking=false;text('cc-voice-feedback','Browser voice could not play. Try another voice or the JARVIS voice engine.');idleState();}};
      root.speechSynthesis.speak(utterance);
    }
    next();
  }
  root.jarvisHome={speak,stopBrowserSpeech,browserVoiceEnabled:()=>output.value==='browser'};
  function updatePreferences() {
    save('output',output.value);save('rate',rate.value);save('voice',voice.value);
    text('cc-rate-value',rate.value+'×');
    byId('chat-auto-speak').checked=output.value!=='off';
  }
  for(const el of [output,voice,rate]) el.addEventListener('change',()=>{stopBrowserSpeech();updatePreferences();});
  rate.addEventListener('input',()=>text('cc-rate-value',rate.value+'×'));
  byId('cc-preview-voice').addEventListener('click',()=>speak('Hello. I am JARVIS. Ready when you are.'));
  root.speechSynthesis?.addEventListener('voiceschanged',loadVoices);
  loadVoices();updatePreferences();
  const model=byId('cc-ai-model'), chatModel=byId('chat-model-select');
  function syncModels(){model.replaceChildren(...Array.from(chatModel.options, option=>option.cloneNode(true)));model.value=chatModel.value;}
  new root.MutationObserver(syncModels).observe(chatModel,{childList:true});
  chatModel.addEventListener('change',()=>{model.value=chatModel.value;});
  model.addEventListener('change',async()=>{model.disabled=true;chatModel.value=model.value;try{await root.switchChatModel(model.value);await root.initChatModels();}finally{syncModels();model.disabled=false;}});
  syncModels();
  byId('cc-speak').addEventListener('click',async()=>{text('cc-chat-feedback','Listening through the existing JARVIS microphone service…');await root.toggleVoiceRecord();text('cc-chat-feedback','Voice request finished. Check the conversation for the result.');syncConversation();});
  byId('cc-chat-form').addEventListener('submit',async event=>{
    event.preventDefault();
    const input=byId('cc-message'), message=input.value.trim();
    if(!message)return;
    if(byId('chat-send-btn').disabled){text('cc-chat-feedback','A reply is still in progress. Wait or stop it in Chat.');return;}
    byId('chat-in').value=message;input.value='';byId('cc-send').disabled=true;
    text('cc-chat-feedback','Message received. Working on it…');
    try{await root.sendChat();text('cc-chat-feedback',byId('chat-status-badge').textContent);}
    finally{byId('cc-send').disabled=false;syncConversation();}
  });
  function syncConversation() {
    const messages=Array.from(byId('chat-box').querySelectorAll('.msg')).slice(-6);
    if(messages.length) {
      const area=byId('cc-conversation');area.replaceChildren();
      for(const message of messages) {
        const body=message.querySelector('.msg-content')?.textContent||'';
        const assistant=message.classList.contains('jarvis');
        const row=doc.createElement('p');row.dataset.role=assistant?'assistant':'user';
        const label=doc.createElement('strong');label.textContent=assistant?'JARVIS':'You';row.appendChild(label);
        row.appendChild(doc.createTextNode(body));area.appendChild(row);
        if(assistant && body.trim())lastChatText=body;
      }
      area.scrollTop=area.scrollHeight;
      if(lastChatText)text('cc-caption',lastChatText);
    }
    idleState();
  }
  new root.MutationObserver(syncConversation).observe(byId('chat-box'),{subtree:true,childList:true,characterData:true});
  new root.MutationObserver(idleState).observe(byId('chat-send-btn'),{attributes:true,attributeFilter:['disabled']});
  const player=byId('jarvis-audio-player');
  player.addEventListener('playing',()=>{speaking=true;state('speaking','Speaking');});
  for(const event of ['ended','pause','error']) player.addEventListener(event,()=>{speaking=false;idleState();});
  function clock() {const now=new Date();text('cc-date',now.toLocaleDateString(undefined,{weekday:'short',month:'short',day:'numeric'}));text('cc-clock',now.toLocaleTimeString(undefined,{hour:'2-digit',minute:'2-digit'}));}
  async function get(path) {const res=await root.fetch(path,{headers:{'X-Jarvis-Client':'dashboard'},signal:root.AbortSignal.timeout(8000)});if(!res.ok)throw Error('Unavailable');return res.json();}
  function rows(id, items, empty) {
    const area=byId(id);area.replaceChildren();
    if(!items.length){area.textContent=empty;area.classList.add('cc-subtle');return;}
    for(const [name,status] of items.slice(0,4)){const row=doc.createElement('div');row.className='cc-list-row';const label=doc.createElement('span');label.textContent=name;const badge=doc.createElement('span');badge.className='cc-badge';badge.textContent=status;row.append(label,badge);area.appendChild(row);}
  }
  async function refresh() {
    if(refreshing||doc.hidden)return;
    refreshing=true;
    try {
      const results=await Promise.allSettled([get('/api/system'),get('/api/voice/wake_status'),get('/api/chat/providers'),get('/api/task-jobs'),get('/api/automations/tasks'),get('/api/memory/stats')]);
      const value=i=>results[i].status==='fulfilled'?results[i].value:null;
      const sys=value(0);wasOnline=!!sys;
      text('cc-connection',sys?'Service online':'Service unavailable');text('cc-system-status',sys?'Live':'Unavailable');
      for(const [key,id] of [['cpu_usage_pct','cpu'],['ram_pct','ram'],['disk_pct','disk']]) {
        const reading=sys?.[key],valid=typeof reading==='number'&&Number.isFinite(reading);
        text('h-'+id,valid?reading.toFixed(1)+'%':'—');byId('cc-'+id+'-meter').value=valid?reading:0;byId('cc-'+id+'-meter').hidden=!valid;
      }
      text('h-temp',typeof sys?.temp_c==='number'?sys.temp_c.toFixed(1)+'°C':'Unavailable');text('cc-host',sys?.hostname||'Unavailable');text('cc-uptime',sys?.uptime_str||'—');text('h-robot',sys?.robot_state||'Unverified');
      wakeState=value(1)?.state||'Unavailable';text('h-voice',wakeState.replaceAll('_',' '));text('cc-wake','Voice: '+wakeState.replaceAll('_',' ').toLowerCase());
      const providers=value(2), selected=providers?.active_provider;
      text('cc-provider',selected?'AI: '+selected:'AI: unavailable');text('cc-model-name',providers?.active_model||'Model status unavailable');
      text('cc-terminal',sys?`[HOST] ${sys.os||'Local'} · ${sys.arch||''}\n[UPTIME] ${sys.uptime_str||'Unknown'}\n[AI] ${selected||'Unavailable'}\n[WORKSPACE] Ready to open\nCommands run only when requested.`:'[JARVIS] Service status unavailable.');
      const jobs=value(3)?.jobs;
      rows('cc-tasks',Array.isArray(jobs)?jobs.map(job=>[job.job_id,job.status]):[],jobs?'No background tasks yet.':'Task history unavailable.');
      const schedules=value(4)?.tasks;
      rows('cc-schedules',Array.isArray(schedules)?schedules.map(item=>[item.name,item.schedule||'Saved']):[],schedules?'No schedules saved.':'Schedules unavailable.');
      text('cc-automation-count',Array.isArray(schedules)?schedules.filter(item=>item.enabled).length:'—');
      const memory=value(5);const count=memory?.total_memories??memory?.total_entries??memory?.total??memory?.count;
      text('cc-memory',typeof count==='number'?count.toLocaleString():'Unavailable');
      idleState();
    } finally {refreshing=false;}
  }
  clock();root.setInterval(clock,30000);refresh();root.setInterval(refresh,12000);
  doc.addEventListener('visibilitychange',()=>{if(!doc.hidden)refresh();});
})(window);
