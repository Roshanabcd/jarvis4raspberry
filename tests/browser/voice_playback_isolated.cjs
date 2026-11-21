// Synthetic audio and MOCK API only. Browser output muted; no physical capture,
// inference, system playback or real service mutations.
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {chromium}=require('playwright');
test('browser playback owns one analyser, drives the mouth, and stops on completion',async(t)=>{
  const candidates=['/usr/bin/google-chrome','/usr/bin/chromium','/usr/bin/chromium-browser'];
  const browser=await chromium.launch({executablePath:candidates.find(p=>fs.existsSync(p)),headless:true,args:['--no-sandbox','--mute-audio','--autoplay-policy=no-user-gesture-required']});
  t.after(()=>browser.close());
  const page=await browser.newPage();
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/*',r=>r.fulfill({contentType:'text/html',body:'<html><body style="background:#00121f;color:#fff"><p>MOCK synthetic audio · physical output muted</p><div id="avatar" style="width:300px"></div></body></html>'}));
  await page.goto('http://127.0.0.1:9999/isolated-fixture');
  await page.addScriptTag({content:fs.readFileSync('apps/dashboard/futuristic/avatar.js','utf8')});
  await page.addScriptTag({content:fs.readFileSync('apps/dashboard/futuristic/voice.js','utf8')});
  await page.evaluate(()=>{
    window.sourceCount=0;window.shapes=[];
    const create=AudioContext.prototype.createMediaElementSource;
    AudioContext.prototype.createMediaElementSource=function(...args){window.sourceCount++;return create.apply(this,args);};
    const avatar=window.jarvisAvatar;avatar.mount(document.getElementById('avatar'));
    const mouth=avatar.setMouthShape.bind(avatar);
    avatar.setMouthShape=shape=>{window.shapes.push(shape);mouth(shape);};
    const voice=window.jarvisVoice;voice.updateView=()=>{};voice.setupAudioElement();
    const count=24000,buffer=new ArrayBuffer(44+count*2),view=new DataView(buffer);
    const str=(at,s)=>[...s].forEach((c,i)=>view.setUint8(at+i,c.charCodeAt(0)));
    str(0,'RIFF');view.setUint32(4,36+count*2,true);str(8,'WAVE');str(12,'fmt ');view.setUint32(16,16,true);
    view.setUint16(20,1,true);view.setUint16(22,1,true);view.setUint32(24,16000,true);view.setUint32(28,32000,true);
    view.setUint16(32,2,true);view.setUint16(34,16,true);str(36,'data');view.setUint32(40,count*2,true);
    let seed=123;
    for(let i=0;i<count;i++){seed=(seed*1664525+1013904223)>>>0;view.setInt16(44+i*2,((seed/4294967296)*2-1)*28000,true);}
    window.sampleUrl=URL.createObjectURL(new Blob([buffer],{type:'audio/wav'}));
    voice.playAudioUrl(window.sampleUrl,'Synthetic audio fixture');
    window.initialVoiceState=voice.state;
  });
  assert.equal(await page.evaluate(()=>window.initialVoiceState),'processing');
  await page.waitForFunction(()=>window.jarvisVoice.state==='speaking');
  await page.waitForFunction(()=>window.shapes.some(s=>s!=='closed'));
  const evidence='docs/jarvis-ui/evidence/phase-6/corrective';fs.mkdirSync(evidence,{recursive:true});
  await page.screenshot({path:path.join(evidence,'synthetic-playback.png')});
  await page.waitForFunction(()=>window.jarvisVoice.currentSubtitles.status==='Speech completed');
  assert.deepEqual(await page.evaluate(()=>({count:window.sourceCount,state:window.jarvisAvatar.state,mouth:window.jarvisAvatar.mouthShape})),{count:1,state:'idle',mouth:'closed'});
  await page.evaluate(()=>window.jarvisVoice.playAudioUrl(window.sampleUrl,'Second synthetic fixture'));
  await page.waitForFunction(()=>window.jarvisVoice.state==='speaking');
  await page.evaluate(()=>window.jarvisVoice.audioElement.pause());
  assert.equal(await page.evaluate(()=>window.jarvisAvatar.mouthShape),'closed');
  assert.equal(await page.evaluate(()=>window.sourceCount),1);
  assert.deepEqual(errors,[]);
});
