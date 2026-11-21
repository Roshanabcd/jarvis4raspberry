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
