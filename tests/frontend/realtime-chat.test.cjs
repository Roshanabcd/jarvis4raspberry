const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync('apps/dashboard/static/index.html', 'utf8');
const source = html.slice(html.indexOf('async function sendChat()'), html.indexOf('function createStreamingBubble()'));

function setup(events, beforeRead = () => {}) {
  const element = () => ({value:'', textContent:'', innerHTML:'', disabled:false, checked:false, style:{},
    children:[], classList:{add(){}}, setAttribute(){}, appendChild(el){this.children.push(el);}});
  const nodes = {};
  ['chat-in','chat-mode','chat-model-select','cancel-chat-btn','chat-send-btn','chat-auto-speak','chat-box','chat-telemetry-badge'].forEach(id => nodes[id] = element());
  nodes['chat-in'].value = 'hello'; nodes['chat-model-select'].value = 'ollama:local';
  const content = element(); const bubble = element(); bubble.querySelector = () => content;
  const calls = [], statuses = [];
  let index = 0;
  let context;
  context = vm.createContext({document:{getElementById:id=>nodes[id],createElement:element},
    AbortController, TextDecoder, performance, setTimeout:()=>1, clearTimeout(){},
    addMsg(){}, createStreamingBubble:()=>bubble, renderMarkdown:String,
    setChatStatus:(state,text)=>statuses.push({state,text}), attachAudioToBubble(){}, playJarvisAudio(){},
    fetch:async(url,options)=>{
      calls.push({url,options});
      if (url.endsWith('/cancel')) return {ok:true};
      return {ok:true,body:{getReader:()=>({read:async()=>{
        await beforeRead(index, {context,nodes});
        if (options.signal.aborted) { const err=new Error('aborted');err.name='AbortError';throw err; }
        if (index===events.length) return {done:true};
        return {done:false,value:new TextEncoder().encode('data: '+JSON.stringify(events[index++])+'\n\n')};
      }})}};
    }});
  vm.runInContext('let currentChatAbort=null,currentChatRequestId=null,lastUserMessage="";\n'+source,context);
  return {context,nodes,calls,statuses,bubble,content};
}

test('chat displays acknowledgement and progress, unlocks send before speech finishes', async()=>{
  const events=[{type:'accepted'},{type:'start',request_id:'req-1'},
    {type:'progress',stage:'model_inferring'},{type:'token',content:'Hello'},
    {type:'done',provider:'local'},{type:'audio_error',message:'No speech'}];
  const ui=setup(events,(index,{nodes})=>{if(index===5)assert.equal(nodes['chat-send-btn'].disabled,false);});
  await ui.context.sendChat();
  assert.ok(ui.statuses.some(item=>item.text==='Working…'));
  assert.ok(ui.statuses.some(item=>item.text.includes('selected AI model')));
  assert.equal(ui.content.innerHTML,'Hello');
  assert.equal(ui.nodes['chat-send-btn'].disabled,false);
});

test('Cancel reaches backend request ID and aborts local waiting', async()=>{
  const ui=setup([{type:'start',request_id:'req-9'},{type:'token',content:'late'}],(index,{context})=>{
    if(index===1)context.cancelChat();
  });
  await ui.context.sendChat();
  const cancel=ui.calls.find(call=>call.url==='/api/chat/cancel');
  assert.deepEqual(JSON.parse(cancel.options.body),{request_id:'req-9'});
  assert.match(ui.content.innerHTML,/Stopped waiting/);
  assert.doesNotMatch(ui.content.innerHTML,/late/);
});

test('stream ending without done is not displayed as completion', async()=>{
  const ui=setup([{type:'start',request_id:'req-1'}]);
  await ui.context.sendChat();
  assert.ok(ui.statuses.some(item=>item.state==='error' && item.text==='Reply interrupted'));
  assert.match(ui.bubble.children[0].textContent,/before completion was confirmed/);
});

test('failed done is shown as incomplete, never task completed', async()=>{
  const ui=setup([{type:'token',content:'Unavailable'},{type:'done',error:'timeout'}]);
  await ui.context.sendChat();
  assert.ok(ui.statuses.some(item=>item.text==='Incomplete'));
  assert.ok(!ui.statuses.some(item=>item.text==='Completed'));
});

test('conversation mode explicitly disables tool execution in request', async()=>{
  const ui=setup([{type:'token',content:'Answer'},{type:'done'}]);
  ui.nodes['chat-mode'].value='conversation';
  await ui.context.sendChat();
  assert.equal(JSON.parse(ui.calls[0].options.body).use_tools,false);
});

test('browser voice receives successful reply once without server synthesis', async()=>{
  const ui=setup([{type:'token',content:'Answer'},{type:'done'}]);
  const spoken=[];
  ui.context.jarvisHome={browserVoiceEnabled:()=>true,speak:text=>spoken.push(text)};
  ui.nodes['chat-auto-speak'].checked=true;
  await ui.context.sendChat();
  assert.equal(JSON.parse(ui.calls[0].options.body).speak,false);
  assert.deepEqual(spoken,['Answer']);
});

test('failed reply never starts browser speech', async()=>{
  const ui=setup([{type:'token',content:'Partial'},{type:'done',status:'failed'}]);
  const spoken=[];
  ui.context.jarvisHome={browserVoiceEnabled:()=>true,speak:text=>spoken.push(text)};
  ui.nodes['chat-auto-speak'].checked=true;
  await ui.context.sendChat();
  assert.deepEqual(spoken,[]);
});
