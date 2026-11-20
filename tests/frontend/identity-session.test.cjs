const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync('apps/dashboard/static/index.html', 'utf8');
const badge = html.slice(html.indexOf('let dashboardIdentityRole ='),html.indexOf('async function checkCameraStatus()'));
const actions = html.slice(html.indexOf('async function enrollAdminSubmit()'),html.indexOf('// ─── Robot Actuator Subsystem'));
function setup(responder) {
  const nodes={};
  for(const id of ['verify-pin-input','verify-pin-result','hdr-user-pill','enroll-admin-name','enroll-admin-pin','enroll-admin-pin-confirm','enroll-admin-confirm-chk','enroll-admin-use-camera','enroll-admin-msg']) nodes[id]={value:'',textContent:'',checked:false};
  const calls=[];
  const context=vm.createContext({document:{getElementById:id=>nodes[id]},setInterval:()=>{},
    loadIdentityStatus:async()=>{},fetch:async(url,options)=>{calls.push({url,options});return responder(url,options);}});
  vm.runInContext(badge+'\n'+actions,context);
  return {context,nodes,calls};
}
test('PIN login updates role from verified server response and clears input',async()=>{
  const {context,nodes,calls}=setup(()=>({ok:true,json:async()=>({success:true,authorization_role:'ADMIN',active_user:{display_name:'Operator'}})}));
  nodes['verify-pin-input'].value='fake-pin';
  await context.verifyAdminPinSubmit();
  assert.match(nodes['hdr-user-pill'].textContent,/Operator \(ADMIN\)/);
  assert.equal(nodes['verify-pin-input'].value,'');
  assert.equal(calls[0].options.headers['X-Jarvis-Client'],'dashboard');
});
test('rejected PIN is visible without granting admin',async()=>{
  const {context,nodes}=setup(()=>({ok:false,json:async()=>({detail:'Incorrect PIN'})}));
  nodes['verify-pin-input'].value='wrong';
  await context.verifyAdminPinSubmit();
  assert.equal(nodes['verify-pin-result'].textContent,'Incorrect PIN');
  assert.equal(nodes['verify-pin-input'].value,'');
  assert.doesNotMatch(nodes['hdr-user-pill'].textContent,/ADMIN/);
});
test('PIN-only setup is explicit and does not request a camera',async()=>{
  const {context,nodes,calls}=setup(()=>({ok:true,json:async()=>({success:true,signed_in:true})}));
  nodes['enroll-admin-name'].value='Operator';
  nodes['enroll-admin-pin'].value=nodes['enroll-admin-pin-confirm'].value='fake-pin';
  nodes['enroll-admin-confirm-chk'].checked=true;
  await context.enrollAdminSubmit();
  const payload=JSON.parse(calls[0].options.body);
  assert.equal(payload.pin_only,true);
  assert.equal(payload.capture_camera,false);
  assert.equal(payload.confirmed,true);
  assert.equal(nodes['enroll-admin-pin'].value,'');
  assert.equal(nodes['enroll-admin-pin-confirm'].value,'');
});
test('expired session updates header and gives sign-in guidance',async()=>{
  const {context,nodes}=setup(()=>({ok:true,json:async()=>({authorization_role:'GUEST',active_user:{display_name:'Guest',role:'GUEST'}})}));
  context.updateHeaderUserPill('Operator','ADMIN');
  await context.refreshIdentityBadge();
  assert.match(nodes['hdr-user-pill'].textContent,/Guest \(GUEST\)/);
  assert.match(nodes['verify-pin-result'].textContent,/session ended/);
});
