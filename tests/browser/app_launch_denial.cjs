// MOCK backend. One browser, no network or hardware actions.
const {chromium}=require('playwright');
const fs=require('fs'),crypto=require('crypto');
(async()=>{
 const path=require('path');
 const root=path.resolve(__dirname,'../..');
 const output=fs.mkdtempSync(path.join(require('os').tmpdir(),'jarvis-launch-denial-'));
 console.log('Evidence:',output);
 const html=fs.readFileSync(root+'/apps/dashboard/static/index.html','utf8');
 const code=html.slice(html.indexOf('async function launchApp('),html.indexOf('function showAppRoadmap('));
 const browser=await chromium.launch({executablePath:'/usr/bin/google-chrome',headless:true,args:['--no-sandbox','--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream','--mute-audio']});
 try{
 const page=await browser.newPage();let dialogs=0;
 page.on('dialog',async d=>{dialogs++;await d.dismiss();});
 await page.route('**/*',r=>r.abort());
 const results=[];
 for(const width of [1440,1280]){
  await page.setViewportSize({width,height:width===1440?900:720});
  await page.setContent('<h1>MOCK launch-denial fixture</h1><button id="btn-launch-extension-28">Open app</button><p id="apps-launch-status" role="status" aria-live="polite"></p>');
  await page.addScriptTag({content:code});
  await page.evaluate(()=>{window.jarvisNotify=undefined;window.fetch=async()=>({ok:false,status:403,json:async()=>({detail:'MOCK: operator permission required'})});const b=document.querySelector('button');b.onclick=e=>launchApp('extension-28',e);});
  await page.click('button');
  await page.waitForFunction(()=>document.querySelector('[role=status]').textContent.includes('MOCK: operator permission required'));
  const focused=await page.evaluate(()=>document.activeElement===document.querySelector('button'));
  if(!focused||dialogs)throw Error('Launch-denial regression');
  await page.screenshot({path:path.join(output,'launch-denial-'+width+'.png')});
  results.push({width,height:width===1440?900:720,persistent_denial:true,focus_restored:focused,dialogs});
 }
 fs.writeFileSync(path.join(output,'result.json'),JSON.stringify({fixture:'MOCK API; no service actions',source_sha256:crypto.createHash('sha256').update(html).digest('hex'),results},null,2));
 console.log(JSON.stringify(results));
 }finally{await browser.close();}
})().catch(e=>{console.error(e.message);process.exitCode=1;});
