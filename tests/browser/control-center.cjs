// Real browser / synthetic API. Does not touch live devices or accounts.
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const http=require('node:http');
const path=require('node:path');
const {chromium}=require('playwright');
test('control center connects chat, browser voice, tasks and responsive layout',async()=>{
  const requests=[];
  const staticRoot=path.resolve('apps/dashboard/static');
  const allowed=new Set(['index.html','active-desktop.js','provider-settings.js','background-tasks.js','control-center.js','control-center.css','assets/jarvis-design-reference.png']);
  const server=http.createServer(async(req,res)=>{
    const name=req.url==='/'?'index.html':req.url.slice(1);
    if(allowed.has(name)){
      res.setHeader('Content-Type',name.endsWith('.js')?'text/javascript':name.endsWith('.css')?'text/css':name.endsWith('.png')?'image/png':'text/html');
      res.end(fs.readFileSync(path.join(staticRoot,name)));return;
    }
    if(req.url==='/api/chat/stream'){
      let data='';for await(const chunk of req)data+=chunk;
      requests.push(JSON.parse(data));
      res.setHeader('Content-Type','text/event-stream');
      for(const event of [{type:'accepted'},{type:'start',request_id:'test'},{type:'token',content:'A real reply from the test API.'},{type:'done',provider:'nvidia'}])res.write('data: '+JSON.stringify(event)+'\n\n');
      res.end();return;
    }
    const fixtures={
      '/api/system':{os:'Linux',arch:'x86_64',hostname:'Test computer',uptime_str:'2h',cpu_usage_pct:18,ram_pct:42,disk_pct:28,temp_c:36,robot_state:'DISARMED'},
      '/api/chat/providers':{providers:[{name:'nvidia',model:'test-model',models:['test-model'],active:true,available:true}],active_provider:'nvidia',active_model:'test-model'},
      '/api/voice/wake_status':{state:'STANDBY_LISTENING'},
      '/api/task-jobs':{jobs:[{job_id:'tjob_test',status:'interrupted'}]},
      '/api/automations/tasks':{tasks:[]},'/api/memory/stats':{total_memories:12},
    };
    res.setHeader('Content-Type','application/json');res.end(JSON.stringify(fixtures[req.url]||{}));
  });
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const origin=`http://127.0.0.1:${server.address().port}`;
  const executablePath=['/usr/bin/google-chrome','/usr/bin/chromium','/usr/bin/chromium-browser'].find(fs.existsSync);
  const browser=await chromium.launch({executablePath,headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
  try{
    const page=await browser.newPage({viewport:{width:1672,height:1050}});
    const errors=[];page.on('pageerror',err=>errors.push(err.message));
    await page.addInitScript(()=>{
      window.__spoken=[];
      window.SpeechSynthesisUtterance=class {constructor(text){this.text=text;}};
      Object.defineProperty(window,'speechSynthesis',{value:{getVoices:()=>[{name:'Test voice',lang:'en-GB',voiceURI:'test-voice'}],addEventListener(){},cancel(){},speak(utter){window.__spoken.push(utter.text);utter.onstart?.();setTimeout(()=>utter.onend?.(),20);}}});
    });
    await page.route('**/*',route=>route.request().url().startsWith(origin)?route.continue():route.abort());
    await page.goto(origin,{waitUntil:'domcontentloaded',timeout:60000});
    await page.waitForFunction(()=>document.getElementById('cc-system-status').textContent==='Live');
    assert.equal(await page.locator('#cc-memory').textContent(),'12');
    await page.screenshot({path:'/tmp/jarvis-control-center-desktop.png',fullPage:true});
    await page.locator('.cc-voice-settings summary').click();
    await page.locator('#cc-voice-output').selectOption('browser');
    await page.locator('#cc-browser-voice').selectOption('test-voice');
    await page.locator('#cc-preview-voice').click();
    assert.equal(await page.evaluate(()=>window.__spoken.length),1,JSON.stringify({errors,feedback:await page.locator('#cc-voice-feedback').textContent()}));
    await page.locator('#cc-message').fill('Explain a harmless topic');
    await page.locator('#cc-send').click();
    await page.waitForFunction(()=>document.getElementById('cc-caption').textContent.includes('A real reply'));
    assert.equal(requests.length,1);assert.equal(requests[0].speak,false);
    await page.waitForFunction(()=>window.__spoken.length===2);
    assert.match(await page.locator('#cc-tasks').textContent(),/interrupted/);
    await page.locator('.cc-voice-settings summary').click();
    await page.evaluate(()=>window.scrollTo(0,0));
    await page.screenshot({path:'/tmp/jarvis-control-center-desktop.png',fullPage:true});
    for(const width of [1280,900,390]){
      await page.setViewportSize({width,height:900});
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,`No horizontal overflow at ${width}`);
      assert.equal(await page.locator('#cc-message').isVisible(),true);
    }
    await page.screenshot({path:'/tmp/jarvis-control-center-mobile.png',fullPage:true});
    await page.locator('#nav-chat').click();
    await page.locator('#chat-mode').selectOption('conversation');
    await page.locator('#chat-in').fill('Stream an explanation');
    await page.locator('#chat-send-btn').click();
    await page.waitForFunction(()=>!document.getElementById('chat-send-btn').disabled);
    assert.equal(requests.at(-1).use_tools,false);
    assert.deepEqual(errors,[]);
  }finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
});
