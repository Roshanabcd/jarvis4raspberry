// MOCK API metadata; no downloaded module engine, provider, hardware or service mutation.
const test=require('node:test');const assert=require('node:assert/strict');
const fs=require('node:fs');const {chromium}=require('playwright');
test('extension card opens its real local route and filters use backend category values',async(t)=>{
 const browser=await chromium.launch({executablePath:['/usr/bin/google-chrome','/usr/bin/chromium'].find(p=>fs.existsSync(p)),headless:true,args:['--no-sandbox']});
 t.after(()=>browser.close());const page=await browser.newPage();
 await page.route('**/*',route=>route.fulfill({contentType:'text/html',body:'<div id="apps"></div>'}));
 await page.goto('http://127.0.0.1:9999/catalog-fixture');
 await page.addScriptTag({content:fs.readFileSync('apps/dashboard/futuristic/operations.js','utf8')});
 await page.evaluate(async()=>{
  window.categories=[];window.jarvisShell={showToast(){}};
  window.jarvisApi={getAppsCatalog:async(q,cat)=>{window.categories.push(cat);return {applications:[{id:'extension-28',name:'MOCK Data Analyst',status:'available',category:'research_knowledge',route:'/ai-data-analyst',description:'Synthetic fixture',roadmap:'Provider readiness not verified.'}]};},launchApp:async()=>({route:'/ai-data-analyst',target_tab:null})};
  await window.jarvisOperations.renderApps(document.getElementById('apps'));
 });
 assert.match(await page.locator('#apps').innerText(),/INTERFACE REGISTERED/);
 await page.locator('[data-cat="developer_tools"]').click();
 assert.equal(await page.evaluate(()=>window.categories.at(-1)),'developer_tools');
 await Promise.all([page.waitForURL('**/ai-data-analyst'),page.locator('.btn-launch').click()]);
 assert.equal(new URL(page.url()).pathname,'/ai-data-analyst');
});

test('legacy catalog renders extension readiness safely and opens without popup',async(t)=>{
 const browser=await chromium.launch({executablePath:['/usr/bin/google-chrome','/usr/bin/chromium'].find(p=>fs.existsSync(p)),headless:true,args:['--no-sandbox']});
 t.after(()=>browser.close());const page=await browser.newPage();
 await page.route('**/*',route=>route.fulfill({contentType:'text/html',body:'<div id="apps-grid"></div>'}));
 await page.goto('http://127.0.0.1:9999/catalog-fixture');
 const html=fs.readFileSync('apps/dashboard/static/index.html','utf8');
 const start=html.indexOf('function escapeHtml(value)');const end=html.indexOf('function showAppRoadmap(',start);
 await page.addScriptTag({content:`let activeAppCategory='all';let allAppsCatalog=[{id:'extension-28',name:'MOCK Analyst',status:'available',resource_profile:'medium',category:'research_knowledge',description:'MOCK fixture',roadmap:'<img src=x onerror=alert(1)>',route:'/ai-data-analyst'}];function formatCategory(v){return v;}function loadRecentApps(){};\n`+html.slice(start,end)});
 await page.evaluate(()=>{window.popupCount=0;window.open=()=>window.popupCount++;window.fetch=async()=>({ok:true,json:async()=>({route:'/ai-data-analyst'})});renderAppsCenter();});
 assert.match(await page.locator('#apps-grid').innerText(),/INTERFACE REGISTERED/);
 assert.match(await page.locator('#apps-grid').innerText(),/<img src=x onerror=alert\(1\)>/);
 assert.equal(await page.locator('#apps-grid img').count(),0);
 await Promise.all([page.waitForURL('**/ai-data-analyst'),page.locator('button:has-text("Open")').click()]);
 assert.equal(new URL(page.url()).pathname,'/ai-data-analyst');
});
