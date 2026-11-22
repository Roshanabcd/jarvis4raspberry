const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const html = fs.readFileSync(path.join(__dirname, '../../apps/dashboard/static/index.html'), 'utf8');
const css = fs.readFileSync(path.join(__dirname, '../../apps/dashboard/static/control-center.css'), 'utf8');

test('HTML: Home tab has ChatGPT-style pill composer with proper elements', () => {
  assert.ok(html.includes('id="cc-pill-composer"'), 'cc-pill-composer exists');
  assert.ok(html.includes('class="chatgpt-pill-composer"'), 'chatgpt-pill-composer class used');
  assert.ok(html.includes('id="cc-plus-btn"'), 'cc-plus-btn exists');
  assert.ok(html.includes('id="cc-plus-menu"'), 'cc-plus-menu exists');
  assert.ok(html.includes('id="cc-message"'), 'cc-message input exists');
  assert.ok(html.includes('placeholder="Ask JARVIS..."'), 'cc-message has placeholder "Ask JARVIS..."');
  assert.ok(html.includes('id="cc-think-btn"'), 'cc-think-btn exists');
  assert.ok(html.includes('id="cc-dictate-btn"'), 'cc-dictate-btn exists');
  assert.ok(html.includes('id="cc-send"'), 'cc-send exists');
  assert.ok(html.includes('class="pill-circle-btn waveform-mode"'), 'cc-send starts in waveform-mode');
});

test('HTML: Chat tab has ChatGPT-style pill composer with proper elements', () => {
  assert.ok(html.includes('id="chat-pill-composer"'), 'chat-pill-composer exists');
  assert.ok(html.includes('id="chat-plus-btn"'), 'chat-plus-btn exists');
  assert.ok(html.includes('id="chat-plus-menu"'), 'chat-plus-menu exists');
  assert.ok(html.includes('id="chat-in"'), 'chat-in input exists');
  assert.ok(html.includes('id="chat-think-btn"'), 'chat-think-btn exists');
  assert.ok(html.includes('id="chat-dictate-btn"'), 'chat-dictate-btn exists');
  assert.ok(html.includes('id="chat-send-btn"'), 'chat-send-btn exists');
});

test('HTML: Quick actions popover menu includes all 3 options', () => {
  assert.ok(html.includes('triggerPillAttach('), 'Attach file action present');
  assert.ok(html.includes('triggerPillScreenShot('), 'Capture screen action present');
  assert.ok(html.includes('triggerPillAppsCheck('), 'Check PC apps action present');
  assert.ok(html.includes('Attach File / Image'), 'Attach File label present');
  assert.ok(html.includes('Capture Current Screen'), 'Capture Screen label present');
  assert.ok(html.includes('Check Running PC Apps'), 'Check Apps label present');
});

test('CSS: .chatgpt-pill-composer has rounded pill style and #1b222c background', () => {
  assert.ok(css.includes('.chatgpt-pill-composer'), 'CSS contains .chatgpt-pill-composer');
  assert.ok(css.includes('border-radius: 9999px') || css.includes('border-radius:9999px'), 'border-radius 9999px present');
  assert.ok(css.includes('#1b222c'), 'Dark pill background #1b222c present');
  assert.ok(css.includes('.pill-think-btn.active'), 'Think button active state styled');
  assert.ok(css.includes('.pill-dictate-btn.pulsing'), 'Dictate button pulsing animation styled');
  assert.ok(css.includes('.pill-circle-btn.waveform-mode'), 'Waveform mode styled');
  assert.ok(css.includes('.pill-circle-btn.send-mode'), 'Send mode styled');
});

test('JS: addMsg deduplicates consecutive identical messages', () => {
  const addMsgSrc = html.slice(html.indexOf('function addMsg('), html.indexOf('function attachAudioToBubble('));
  assert.ok(addMsgSrc.includes('Deduplicate identical consecutive messages'), 'addMsg contains consecutive deduplication');
  assert.ok(addMsgSrc.includes('lastContent === text.trim()'), 'addMsg compares text against last bubble');
});
