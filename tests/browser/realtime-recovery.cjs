// Real Chromium rendering against a disposable streaming server; no devices or keys.
const test = require('node:test');
const assert = require('node:assert/strict');
const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require('playwright');

test('real browser shows receipt before reply and sends cancellation to server', async () => {
  const executablePath = ['/usr/bin/google-chrome','/usr/bin/chromium','/usr/bin/chromium-browser'].find(fs.existsSync);
  assert.ok(executablePath, 'A local Chromium binary is required');
  const cancelled = [];
  let requests = 0;
  const staticFiles = {'/':'index.html','/active-desktop.js':'active-desktop.js','/provider-settings.js':'provider-settings.js'};
  const server = http.createServer(async (req,res) => {
    if (req.url === '/api/chat/stream') {
      const id = `browser-${++requests}`;
      res.writeHead(200, {'Content-Type':'text/event-stream'});
      const emit = event => res.write('data: '+JSON.stringify(event)+'\n\n');
      emit({type:'accepted'}); emit({type:'start',request_id:id});
      const progress = setTimeout(()=>emit({type:'progress',stage:'model_inferring'}), 100);
      const answer = setTimeout(()=>{
        emit({type:'token',content:'Hello from the verified browser test.'});
        emit({type:'done',provider:'test'}); res.end();
      }, requests === 1 ? 1400 : 10000);
      res.on('close',()=>{clearTimeout(progress);clearTimeout(answer);});
      return;
    }
    if (req.url === '/api/chat/cancel') {
      let data=''; for await (const chunk of req) data+=chunk;
      cancelled.push(JSON.parse(data));
      res.setHeader('Content-Type','application/json'); res.end('{"status":"ok"}'); return;
    }
    if (staticFiles[req.url]) {
      res.setHeader('Content-Type', req.url==='/' ? 'text/html' : 'text/javascript');
      res.end(fs.readFileSync(path.join('apps/dashboard/static',staticFiles[req.url]))); return;
    }
    res.setHeader('Content-Type','application/json');
    if (req.url === '/api/chat/providers') {
      res.end(JSON.stringify({providers:[{name:'ollama',model:'test',models:['test'],active:true,available:true}],active_provider:'ollama',active_model:'test'}));
    } else res.end('{}');
  });
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const origin=`http://127.0.0.1:${server.address().port}`;
  let browser;
  try {
    browser=await chromium.launch({executablePath,headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
    const page=await browser.newPage();
    await page.route('**/*',route=>route.request().url().startsWith(origin) ? route.continue() : route.abort());
    await page.goto(origin);
    await page.evaluate(()=>showTab('chat'));
    await page.locator('#chat-ai-setup').click();
    assert.equal(await page.locator('#key-openrouter').isVisible(),true);
    await page.evaluate(()=>showTab('chat'));
    await page.locator('#chat-auto-speak').uncheck();
    await page.locator('#chat-in').fill('hello');
    await page.locator('#chat-send-btn').click();
    await page.waitForFunction(()=>document.querySelector('.chat-progress')?.textContent.includes('selected AI model'));
    assert.equal(await page.locator('#chat-send-btn').isDisabled(),true);
    await page.waitForFunction(()=>document.querySelector('.msg.jarvis .msg-content')?.textContent.includes('Hello from the verified browser test'));
    assert.equal(await page.locator('#chat-send-btn').isDisabled(),false);
    await page.locator('#chat-in').fill('slow request');
    await page.locator('#chat-send-btn').click();
    await page.waitForFunction(()=>document.querySelectorAll('.chat-progress')[1]?.textContent.includes('selected AI model'));
    await page.locator('#cancel-chat-btn').click();
    await page.waitForFunction(()=>Array.from(document.querySelectorAll('.msg-content')).some(el=>el.textContent.includes('Stopped waiting')));
    assert.deepEqual(cancelled,[{request_id:'browser-2'}]);
  } finally {
    if(browser)await browser.close();
    await new Promise(resolve=>server.close(resolve));
  }
});
