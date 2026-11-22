(function (root) {
  'use strict';
  const doc = root.document;
  if (!doc?.getElementById('cc-hero')) return;
  const byId = id => doc.getElementById(id);
  const text = (id, value) => { const el = byId(id); if (el) el.textContent = String(value); };
  const read = (key, fallback) => { try { return root.localStorage.getItem('jarvis.home.' + key) || fallback; } catch (_) { return fallback; } };
  const save = (key, value) => { try { root.localStorage.setItem('jarvis.home.' + key, value); } catch (_) {} };

  // --- Avatar & Digital Human Setup ---
  const avatarBox = byId('cc-avatar-box');
  const avatarMount = byId('cc-hero-avatar');
  let activeChar = read('character', root.localStorage.getItem('jarvis_avatar') || 'aria');

  function initAvatar() {
    if (root.jarvisAvatar && avatarMount) {
      root.jarvisAvatar.setAvatarType(activeChar === 'atlas' ? 'atlas' : 'aria');
      root.jarvisAvatar.mount(avatarMount);
      if (activeChar === 'classic') {
        avatarBox?.classList.add('classic-mode');
        if (avatarMount) avatarMount.style.display = 'none';
      } else {
        avatarBox?.classList.remove('classic-mode');
        if (avatarMount) avatarMount.style.display = 'flex';
      }
    }
  }

  // --- Voice Controls & Audio Routing ---
  const output = byId('cc-voice-output'), voice = byId('cc-browser-voice'), rate = byId('cc-voice-rate');
  const charSelect = byId('cc-character-select'), neuralVoice = byId('cc-neural-voice');

  if (output) output.value = ['server', 'browser', 'off'].includes(read('output', 'server')) ? read('output', 'server') : 'server';
  if (rate) rate.value = String(Math.max(.6, Math.min(1.5, Number(read('rate', '1')) || 1)));
  if (charSelect) charSelect.value = activeChar;
  if (neuralVoice) neuralVoice.value = read('neural_voice', activeChar === 'atlas' ? 'en-US-GuyNeural' : 'en-US-AriaNeural');

  let voices = [], speechGeneration = 0, speaking = false, refreshing = false, wasOnline = false;
  let wakeState = 'Checking', lastChatText = '';

  function state(kind, label) {
    const hero = byId('cc-hero');
    if (hero) hero.dataset.state = kind;
    text('cc-state', label);
    if (root.jarvisAvatar && activeChar !== 'classic') {
      root.jarvisAvatar.setState(kind);
    }
  }

  function idleState() {
    if (speaking) return;
    if (byId('chat-send-btn')?.disabled) state('thinking', 'Thinking');
    else if (!wasOnline) state('offline', 'Connection unavailable');
    else if (['LISTENING_SPEECH', 'WAKE_DETECTED', 'FOLLOW_UP_STANDBY'].includes(wakeState)) state('listening', 'Listening');
    else state('idle', 'Ready');

    if (root.jarvisAvatar && activeChar !== 'classic') {
      root.jarvisAvatar.setMouthShape('closed');
    }
  }

  function stopBrowserSpeech() {
    speechGeneration++;
    root.speechSynthesis?.cancel();
    speaking = false;
    idleState();
  }

  function loadVoices() {
    if (!voice) return;
    voices = root.speechSynthesis?.getVoices() || [];
    const preferred = read('voice', '');
    voice.replaceChildren();
    const option = doc.createElement('option'); option.value = ''; option.textContent = 'Default browser voice'; voice.appendChild(option);
    for (const item of voices) {
      const el = doc.createElement('option');
      el.value = item.voiceURI;
      el.textContent = `${item.name} · ${item.lang}`;
      voice.appendChild(el);
    }
    voice.value = voices.some(item => item.voiceURI === preferred) ? preferred : '';
    voice.disabled = !root.speechSynthesis;
    if (!root.speechSynthesis) text('cc-voice-feedback', 'Browser speech is unavailable. Using JARVIS Neural Engine.');
  }

  function speak(message) {
    if (!root.speechSynthesis || !root.SpeechSynthesisUtterance) {
      text('cc-voice-feedback', 'Browser speech is unavailable. Using JARVIS voice engine.');
      return;
    }
    stopBrowserSpeech();
    const player = byId('jarvis-audio-player'); if (player) player.pause();
    const generation = speechGeneration;
    const remaining = [];
    let rest = String(message);
    while (rest.length > 300) {
      const space = rest.lastIndexOf(' ', 300);
      const cut = space > 150 ? space + 1 : 300;
      remaining.push(rest.slice(0, cut));
      rest = rest.slice(cut);
    }
    if (rest) remaining.push(rest);
    function next() {
      if (generation !== speechGeneration) return;
      const part = remaining.shift();
      if (!part) { speaking = false; idleState(); return; }
      const utterance = new root.SpeechSynthesisUtterance(part);
      utterance.rate = Number(rate?.value || 1);
      const selected = voices.find(item => item.voiceURI === voice?.value);
      if (selected) { utterance.voice = selected; utterance.lang = selected.lang; }
      utterance.onstart = () => { if (generation === speechGeneration) { speaking = true; state('speaking', 'Speaking'); } };
      utterance.onend = () => { if (generation === speechGeneration) next(); };
      utterance.onerror = () => {
        if (generation === speechGeneration) {
          speaking = false;
          text('cc-voice-feedback', 'Browser voice playback failed. Falling back to JARVIS voice engine.');
          idleState();
        }
      };
      root.speechSynthesis.speak(utterance);
    }
    next();
  }

  root.jarvisHome = { speak, stopBrowserSpeech, browserVoiceEnabled: () => output?.value === 'browser' };

  function updatePreferences() {
    if (output) save('output', output.value);
    if (rate) { save('rate', rate.value); text('cc-rate-value', rate.value + '×'); }
    if (voice) save('voice', voice.value);
    if (charSelect) save('character', charSelect.value);
    if (neuralVoice) save('neural_voice', neuralVoice.value);
    const autoSpeak = byId('chat-auto-speak');
    if (autoSpeak && output) autoSpeak.checked = output.value !== 'off';
  }

  if (charSelect) {
    charSelect.addEventListener('change', () => {
      activeChar = charSelect.value;
      save('character', activeChar);
      root.localStorage.setItem('jarvis_avatar', activeChar);
      if (activeChar === 'classic') {
        avatarBox?.classList.add('classic-mode');
        if (avatarMount) avatarMount.style.display = 'none';
      } else {
        avatarBox?.classList.remove('classic-mode');
        if (avatarMount) avatarMount.style.display = 'flex';
        root.jarvisAvatar?.setAvatarType(activeChar === 'atlas' ? 'atlas' : 'aria');
        if (neuralVoice) {
          neuralVoice.value = activeChar === 'atlas' ? 'en-US-GuyNeural' : 'en-US-AriaNeural';
          save('neural_voice', neuralVoice.value);
        }
      }
      idleState();
    });
  }

  if (neuralVoice) {
    neuralVoice.addEventListener('change', () => {
      save('neural_voice', neuralVoice.value);
    });
  }

  for (const el of [output, voice, rate]) {
    el?.addEventListener('change', () => { stopBrowserSpeech(); updatePreferences(); });
  }
  rate?.addEventListener('input', () => text('cc-rate-value', rate.value + '×'));
  byId('cc-preview-voice')?.addEventListener('click', () => {
    const selChar = activeChar === 'atlas' ? 'Atlas' : 'Aria';
    speak(`Hello. I am ${selChar}. All JARVIS OS systems are online and ready.`);
  });

  root.speechSynthesis?.addEventListener('voiceschanged', loadVoices);
  loadVoices();
  updatePreferences();
  initAvatar();

  // Model selection sync
  const model = byId('cc-ai-model'), chatModel = byId('chat-model-select');
  function syncModels() {
    if (!model || !chatModel) return;
    model.replaceChildren(...Array.from(chatModel.options, option => option.cloneNode(true)));
    model.value = chatModel.value;
  }
  if (chatModel) {
    new root.MutationObserver(syncModels).observe(chatModel, { childList: true });
    chatModel.addEventListener('change', () => { if (model) model.value = chatModel.value; });
  }
  if (model) {
    model.addEventListener('change', async () => {
      model.disabled = true;
      if (chatModel) chatModel.value = model.value;
      try {
        if (root.switchChatModel) await root.switchChatModel(model.value);
        if (root.initChatModels) await root.initChatModels();
      } finally {
        syncModels();
        model.disabled = false;
      }
    });
  }
  syncModels();

  // Microphone capture with real status reporting, active turn monitoring, and barge-in
  let voiceMonitorInterval = null;
  let isDictating = false;

  root.addEventListener('jarvis:voice_stage', (e) => {
    const d = e.detail;
    const stage = d?.stage;
    const details = d?.details || {};
    if (!stage) return;
    if (stage === 'LISTENING_SPEECH') {
      state('listening', 'Listening…');
      text('cc-caption', details.rms ? ('Listening to microphone (RMS: ' + Math.round(details.rms) + ')… Speak now.') : 'Listening to ReSpeaker microphone… Speak now.');
      text('cc-chat-feedback', 'Listening… Speak your command.');
    } else if (stage === 'HEARD') {
      state('listening', 'Hearing speech…');
      const heardText = details.text || details.transcript || '';
      text('cc-caption', heardText ? ('Heard: "' + heardText + '"') : 'Speech detected… Transcribing…');
      text('cc-chat-feedback', heardText ? ('Heard: "' + heardText + '"') : 'Speech detected… Transcribing…');
      if (details.is_dictation || isDictating) {
        if (heardText) {
          const targetInput = (doc.activeElement?.id === 'chat-in') ? byId('chat-in') : byId('cc-message');
          if (targetInput) {
            targetInput.value = (targetInput.value ? targetInput.value + ' ' : '') + heardText;
            targetInput.dispatchEvent(new Event('input', { bubbles: true }));
            targetInput.focus();
          }
        }
        isDictating = false;
        [byId('cc-dictate-btn'), byId('chat-dictate-btn')].forEach(b => b?.classList.remove('pulsing'));
        text('cc-chat-feedback', heardText ? `Dictated: "${heardText}"` : 'Dictation finished');
      }
    } else if (stage === 'THINKING') {
      state('thinking', 'Thinking…');
      text('cc-caption', 'Thinking… Processing your voice command.');
      text('cc-chat-feedback', 'Thinking… Processing command.');
    } else if (stage === 'SPEAKING') {
      state('speaking', 'Speaking');
      if (details.text) text('cc-caption', details.text);
      text('cc-chat-feedback', 'Speaking response…');
    } else if (stage === 'READY') {
      if (isDictating) {
        isDictating = false;
        [byId('cc-dictate-btn'), byId('chat-dictate-btn')].forEach(b => b?.classList.remove('pulsing'));
      }
      syncConversation();
      idleState();
    } else if (stage === 'ERROR') {
      if (isDictating) {
        isDictating = false;
        [byId('cc-dictate-btn'), byId('chat-dictate-btn')].forEach(b => b?.classList.remove('pulsing'));
      }
      state('error', 'Voice error');
      text('cc-caption', '⚠️ Voice error: ' + (details.error || 'Failed'));
      text('cc-chat-feedback', '⚠️ Voice error: ' + (details.error || 'Failed'));
    }
  });

  root.addEventListener('jarvis:voice_state', (e) => {
    const d = e.detail;
    const wsState = d?.state || d?.voice_state;
    if (!wsState) return;
    wakeState = wsState;
    text('h-voice', wakeState.replaceAll('_', ' '));
    text('cc-wake', 'Voice: ' + wakeState.replaceAll('_', ' ').toLowerCase());

    if (wsState === 'LISTENING_SPEECH') {
      state('listening', 'Listening…');
      text('cc-caption', 'Listening to ReSpeaker microphone… Speak now.');
      text('cc-chat-feedback', 'Listening… Speak your command.');
    } else if (wsState === 'STREAMING_TRANSCRIPTION') {
      state('listening', 'Hearing speech…');
      text('cc-caption', 'Hearing speech…');
      text('cc-chat-feedback', 'Hearing speech…');
    } else if (wsState === 'SILENCE_COUNTDOWN') {
      text('cc-caption', 'Silence detected, finalizing command…');
    } else if (wsState === 'COMMAND_SUBMITTED' || wsState === 'PROCESSING_AGENT') {
      state('thinking', 'Thinking…');
      text('cc-caption', 'Thinking… Processing your voice command.');
      text('cc-chat-feedback', 'Processing voice command…');
    } else if (wsState === 'SPEAKING_RESPONSE') {
      state('speaking', 'Speaking');
    } else if (wsState === 'FOLLOW_UP_STANDBY') {
      state('listening', 'Listening (follow-up)');
      text('cc-caption', 'Listening for follow-up command…');
    } else if (wsState === 'STANDBY_LISTENING') {
      if (!speaking) idleState();
    } else if (wsState === 'ERROR') {
      state('error', 'Voice error');
      text('cc-caption', '⚠️ Microphone capture error — check ReSpeaker Lite connection.');
    }
  });

  byId('cc-speak')?.addEventListener('click', async () => {
    // 1. Barge-in: if currently speaking, interrupt immediately
    if (speaking) {
      stopBrowserSpeech();
      const player = byId('jarvis-audio-player');
      if (player) { player.pause(); player.currentTime = 0; }
      try {
        await root.fetch('/api/voice/interrupt', { method: 'POST', headers: { 'X-Jarvis-Client': 'dashboard' } });
      } catch (_) {}
      speaking = false;
      state('listening', 'Listening…');
      text('cc-caption', 'Barge-in: speech stopped. Listening…');
      text('cc-chat-feedback', 'Barge-in: speech stopped. Listening…');
    } else {
      state('listening', 'Listening…');
      text('cc-caption', 'Listening to ReSpeaker microphone… Speak now.');
      text('cc-chat-feedback', 'Listening to ReSpeaker microphone… Speak now.');
    }

    if (voiceMonitorInterval) {
      clearInterval(voiceMonitorInterval);
      voiceMonitorInterval = null;
    }

    try {
      const outcome = await root.toggleVoiceRecord();
      if (outcome?.status === 'accepted') {
        state('listening', 'Listening…');
        text('cc-chat-feedback', 'Listening to ReSpeaker microphone… Speak now.');

        let pollCount = 0;
        let hasStartedTurn = false;
        const maxPolls = 100; // 30 seconds at 300ms
        voiceMonitorInterval = setInterval(async () => {
          pollCount++;
          if (pollCount > maxPolls) {
            clearInterval(voiceMonitorInterval);
            voiceMonitorInterval = null;
            syncConversation();
            idleState();
            return;
          }
          try {
            const st = await get('/api/voice/wake_status');
            const wsState = st?.state;
            if (wsState) {
              wakeState = wsState;
              text('h-voice', wakeState.replaceAll('_', ' '));
              text('cc-wake', 'Voice: ' + wakeState.replaceAll('_', ' ').toLowerCase());
            }
            if (st?.mic_disconnected || (st?.capture_status === 'failed' && st?.recorder_failures >= 3)) {
              state('error', 'Mic error');
              text('cc-caption', '⚠️ Microphone disconnected — check ReSpeaker Lite USB cable.');
              text('cc-chat-feedback', '⚠️ Microphone disconnected — check ReSpeaker Lite USB cable.');
              return;
            }
            if (['LISTENING_SPEECH', 'STREAMING_TRANSCRIPTION', 'SILENCE_COUNTDOWN', 'COMMAND_SUBMITTED', 'PROCESSING_AGENT', 'SPEAKING_RESPONSE'].includes(wsState)) {
              hasStartedTurn = true;
            }
            if (wsState === 'LISTENING_SPEECH') {
              state('listening', 'Listening…');
              text('cc-caption', 'Listening to ReSpeaker microphone… Speak now.');
              text('cc-chat-feedback', 'Listening… Speak your command.');
            } else if (wsState === 'STREAMING_TRANSCRIPTION') {
              state('listening', 'Hearing speech…');
              text('cc-caption', 'Hearing speech…');
              text('cc-chat-feedback', 'Hearing speech…');
            } else if (wsState === 'SILENCE_COUNTDOWN') {
              text('cc-caption', 'Silence detected, finalizing command…');
              text('cc-chat-feedback', 'Silence detected, finalizing command…');
            } else if (wsState === 'COMMAND_SUBMITTED' || wsState === 'PROCESSING_AGENT') {
              state('thinking', 'Thinking…');
              text('cc-caption', 'Thinking… Processing your voice command.');
              text('cc-chat-feedback', 'Processing voice command…');
            } else if (wsState === 'SPEAKING_RESPONSE') {
              state('speaking', 'Speaking');
              text('cc-chat-feedback', 'Speaking response…');
              if (st?.last_response) text('cc-caption', st.last_response);
            } else if (wsState === 'FOLLOW_UP_STANDBY' || wsState === 'STANDBY_LISTENING') {
              if (hasStartedTurn) {
                clearInterval(voiceMonitorInterval);
                voiceMonitorInterval = null;
                syncConversation();
                if (st?.last_response) text('cc-caption', st.last_response);
                idleState();
              }
            }
          } catch (_) {}
        }, 300);
      } else {
        const msg = outcome?.message || 'Voice outcome unavailable.';
        text('cc-caption', msg);
        text('cc-chat-feedback', msg);
        syncConversation();
        idleState();
      }
    } catch (err) {
      const msg = 'Microphone error: ' + (err.message || 'Check microphone');
      text('cc-caption', msg);
      text('cc-chat-feedback', msg);
      syncConversation();
      idleState();
    }
  });

  byId('cc-chat-form')?.addEventListener('submit', async event => {
    event.preventDefault();
    const input = byId('cc-message'), message = input ? input.value.trim() : '';
    if (!message) {
      // Empty input: engage Real-Time Voice Chat
      byId('cc-speak')?.click();
      return;
    }
    if (byId('chat-send-btn')?.disabled) {
      text('cc-chat-feedback', 'A reply is still in progress. Wait or stop it in Chat.');
      return;
    }
    // Barge-in: Preempt any active speech when sending a new chat message
    if (speaking) {
      stopBrowserSpeech();
      const player = byId('jarvis-audio-player');
      if (player) { player.pause(); player.currentTime = 0; }
      try {
        await root.fetch('/api/voice/interrupt', { method: 'POST', headers: { 'X-Jarvis-Client': 'dashboard' } });
      } catch (_) {}
      speaking = false;
    }
    const chatIn = byId('chat-in');
    if (chatIn) {
      chatIn.value = message;
      chatIn.dispatchEvent(new Event('input', { bubbles: true }));
    }
    if (input) {
      input.value = '';
      input.dispatchEvent(new Event('input', { bubbles: true }));
    }
    const sendBtn = byId('cc-send');
    if (sendBtn) sendBtn.disabled = true;
    text('cc-chat-feedback', 'Message received. Working on it…');
    state('thinking', 'Thinking...');
    try {
      if (root.sendChat) await root.sendChat();
      text('cc-chat-feedback', byId('chat-status-badge')?.textContent || 'Message sent');
    } finally {
      if (sendBtn) sendBtn.disabled = false;
      syncConversation();
      idleState();
    }
  });

  function syncConversation() {
    const chatBox = byId('chat-box');
    if (!chatBox) return;
    const messages = Array.from(chatBox.querySelectorAll('.msg')).slice(-6);
    if (messages.length) {
      const area = byId('cc-conversation');
      if (area) {
        area.replaceChildren();
        let lastRenderedText = null;
        let lastRenderedRole = null;
        for (const message of messages) {
          const contentEl = message.querySelector('.msg-content');
          const body = contentEl ? (contentEl.innerText || contentEl.textContent || '') : '';
          const assistant = message.classList.contains('jarvis');
          const role = assistant ? 'assistant' : 'user';
          // Deduplicate consecutive identical messages in Home conversation area
          if (role === lastRenderedRole && body.trim() === lastRenderedText?.trim()) {
            continue;
          }
          lastRenderedRole = role;
          lastRenderedText = body;

          const row = doc.createElement('p');
          row.dataset.role = role;
          const label = doc.createElement('strong');
          label.textContent = assistant ? (activeChar === 'atlas' ? 'ATLAS' : 'JARVIS') : 'You';
          row.appendChild(label);
          row.appendChild(doc.createTextNode(body));
          area.appendChild(row);
          if (assistant && body.trim()) lastChatText = body;
        }
        area.scrollTop = area.scrollHeight;
      }
      if (lastChatText) text('cc-caption', lastChatText);
    }
    idleState();
  }

  // --- ChatGPT-Style Pill Composers Controller ---
  function updatePillState(inputEl, btnEl) {
    if (!inputEl || !btnEl) return;
    const hasText = inputEl.value.trim().length > 0;
    const waveformIcon = btnEl.querySelector('.icon-waveform');
    const sendIcon = btnEl.querySelector('.icon-send');
    if (hasText) {
      btnEl.classList.remove('waveform-mode');
      btnEl.classList.add('send-mode');
      btnEl.title = 'Send message';
      btnEl.setAttribute('aria-label', 'Send message');
      if (waveformIcon) waveformIcon.style.display = 'none';
      if (sendIcon) sendIcon.style.display = 'block';
    } else {
      btnEl.classList.add('waveform-mode');
      btnEl.classList.remove('send-mode');
      btnEl.title = 'Real-Time Voice Chat';
      btnEl.setAttribute('aria-label', 'Real-Time Voice Chat');
      if (waveformIcon) waveformIcon.style.display = 'block';
      if (sendIcon) sendIcon.style.display = 'none';
    }
  }

  function initPillComposers() {
    const ccInput = byId('cc-message');
    const ccSendBtn = byId('cc-send');
    const chatInput = byId('chat-in');
    const chatSendBtn = byId('chat-send-btn');

    // Input listeners to toggle waveform vs send mode
    if (ccInput && ccSendBtn) {
      ccInput.addEventListener('input', () => updatePillState(ccInput, ccSendBtn));
      updatePillState(ccInput, ccSendBtn);
    }
    if (chatInput && chatSendBtn) {
      chatInput.addEventListener('input', () => updatePillState(chatInput, chatSendBtn));
      updatePillState(chatInput, chatSendBtn);
    }

    // Enter key handling
    ccInput?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (ccInput.value.trim()) {
          byId('cc-chat-form')?.requestSubmit();
        }
      }
    });

    chatInput?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (chatInput.value.trim() && root.sendChat) {
          root.sendChat();
        }
      }
    });

    // Chat tab send / waveform button click
    chatSendBtn?.addEventListener('click', (e) => {
      const msg = chatInput ? chatInput.value.trim() : '';
      if (!msg) {
        e.preventDefault();
        // Engage Real-Time Voice Chat
        const mic = byId('mic-btn');
        if (mic) mic.click();
        else byId('cc-speak')?.click();
      } else {
        if (root.sendChat) root.sendChat();
      }
    });

    // Think Toggle Controller
    function toggleThink() {
      root.jarvisThinkingMode = !root.jarvisThinkingMode;
      const active = Boolean(root.jarvisThinkingMode);
      ['cc-think-btn', 'chat-think-btn'].forEach(id => {
        const b = byId(id);
        if (b) {
          b.classList.toggle('active', active);
          b.setAttribute('aria-pressed', active ? 'true' : 'false');
        }
      });
      text('cc-chat-feedback', active ? 'Thinking mode enabled (deep reasoning)' : 'Thinking mode disabled');
    }
    byId('cc-think-btn')?.addEventListener('click', toggleThink);
    byId('chat-think-btn')?.addEventListener('click', toggleThink);

    // Dictate Controller
    async function handleDictateToggle(target) {
      const dictateBtns = [byId('cc-dictate-btn'), byId('chat-dictate-btn')];
      const inputEl = target === 'home' ? ccInput : chatInput;

      if (isDictating) {
        isDictating = false;
        dictateBtns.forEach(b => b?.classList.remove('pulsing'));
        text('cc-chat-feedback', 'Dictation stopped.');
        try {
          await root.fetch('/api/voice/dictate/stop', {
            method: 'POST',
            headers: { 'X-Jarvis-Client': 'dashboard' }
          });
        } catch (_) {}
        return;
      }

      isDictating = true;
      dictateBtns.forEach(b => b?.classList.add('pulsing'));
      text('cc-chat-feedback', 'Listening for dictation… Speak now.');
      state('listening', 'Dictating…');

      try {
        const res = await root.fetch('/api/voice/dictate', {
          method: 'POST',
          headers: { 'X-Jarvis-Client': 'dashboard' }
        });
        if (!res.ok) throw new Error('Dictate request failed');
        const data = await res.json();
        if (data.mode === 'standalone_dictate' && data.text) {
          if (inputEl) {
            inputEl.value = (inputEl.value ? inputEl.value + ' ' : '') + data.text;
            inputEl.dispatchEvent(new Event('input', { bubbles: true }));
            inputEl.focus();
          }
          isDictating = false;
          dictateBtns.forEach(b => b?.classList.remove('pulsing'));
          text('cc-chat-feedback', `Transcribed: "${data.text}"`);
          idleState();
        }
      } catch (err) {
        isDictating = false;
        dictateBtns.forEach(b => b?.classList.remove('pulsing'));
        text('cc-chat-feedback', 'Dictation unavailable: ' + err.message);
        idleState();
      }
    }

    byId('cc-dictate-btn')?.addEventListener('click', () => handleDictateToggle('home'));
    byId('chat-dictate-btn')?.addEventListener('click', () => handleDictateToggle('chat'));

    // Plus popover toggle
    function togglePlusMenu(menuId, btnId) {
      const menu = byId(menuId);
      const btn = byId(btnId);
      if (!menu || !btn) return;
      const isHidden = menu.hidden;
      doc.querySelectorAll('.pill-popover-menu').forEach(m => m.hidden = true);
      doc.querySelectorAll('.pill-plus-btn').forEach(b => b.setAttribute('aria-expanded', 'false'));
      if (isHidden) {
        menu.hidden = false;
        btn.setAttribute('aria-expanded', 'true');
      }
    }

    byId('cc-plus-btn')?.addEventListener('click', (e) => {
      e.stopPropagation();
      togglePlusMenu('cc-plus-menu', 'cc-plus-btn');
    });
    byId('chat-plus-btn')?.addEventListener('click', (e) => {
      e.stopPropagation();
      togglePlusMenu('chat-plus-menu', 'chat-plus-btn');
    });

    doc.addEventListener('click', (e) => {
      if (!e.target.closest('.pill-plus-wrapper')) {
        doc.querySelectorAll('.pill-popover-menu').forEach(m => m.hidden = true);
        doc.querySelectorAll('.pill-plus-btn').forEach(b => b.setAttribute('aria-expanded', 'false'));
      }
    });
  }

  root.triggerPillAttach = function(target) {
    let fileIn = byId('pill-file-input');
    if (!fileIn) {
      fileIn = doc.createElement('input');
      fileIn.type = 'file';
      fileIn.id = 'pill-file-input';
      fileIn.style.display = 'none';
      doc.body.appendChild(fileIn);
    }
    fileIn.onchange = (e) => {
      const file = e.target.files?.[0];
      if (!file) return;
      const inputEl = target === 'home' ? byId('cc-message') : byId('chat-in');
      if (inputEl) {
        inputEl.value = (inputEl.value ? inputEl.value + ' ' : '') + `[Attached: ${file.name}]`;
        inputEl.dispatchEvent(new Event('input', { bubbles: true }));
        inputEl.focus();
      }
      text('cc-chat-feedback', `Attached: ${file.name}`);
    };
    fileIn.click();
    doc.querySelectorAll('.pill-popover-menu').forEach(m => m.hidden = true);
  };

  root.triggerPillScreenShot = async function(target) {
    doc.querySelectorAll('.pill-popover-menu').forEach(m => m.hidden = true);
    text('cc-chat-feedback', 'Capturing screen…');
    if (target === 'chat' && typeof root.diagnoseDesktopScreen === 'function') {
      await root.diagnoseDesktopScreen();
    } else {
      try {
        const res = await root.fetch('/api/active-desktop/diagnose-screen', {
          method: 'POST',
          headers: { 'X-Jarvis-Client': 'dashboard' }
        });
        if (res.ok) {
          const d = await res.json();
          const inputEl = byId('cc-message');
          if (inputEl) {
            inputEl.value = (inputEl.value ? inputEl.value + ' ' : '') + `[Screen: ${d.active_window?.title || 'Desktop'}]`;
            inputEl.dispatchEvent(new Event('input', { bubbles: true }));
          }
          text('cc-chat-feedback', d.spoken_summary || 'Screen captured.');
        } else {
          text('cc-chat-feedback', 'Screen capture failed.');
        }
      } catch (err) {
        text('cc-chat-feedback', 'Screen capture unavailable.');
      }
    }
  };

  root.triggerPillAppsCheck = async function(target) {
    doc.querySelectorAll('.pill-popover-menu').forEach(m => m.hidden = true);
    text('cc-chat-feedback', 'Checking running PC apps…');
    try {
      const res = await root.fetch('/api/active-desktop/snapshot', {
        headers: { 'X-Jarvis-Client': 'dashboard' }
      });
      if (res.ok) {
        const d = await res.json();
        const openCount = d.open_windows_count || (d.open_windows ? d.open_windows.length : 0);
        const appName = d.active_window?.app || 'Desktop';
        const msg = `Running apps: ${openCount} windows detected (Active: ${appName}).`;
        if (target === 'home') {
          const inputEl = byId('cc-message');
          if (inputEl) {
            inputEl.value = (inputEl.value ? inputEl.value + ' ' : '') + `Check open apps: active is ${appName}`;
            inputEl.dispatchEvent(new Event('input', { bubbles: true }));
          }
          text('cc-chat-feedback', msg);
        } else {
          if (typeof root.addMsg === 'function') {
            root.addMsg('jarvis', `🖥️ **Running PC Apps Report**\n\n- **Active Window:** ${appName} (${d.active_window?.title || ''})\n- **Open Windows:** ${openCount} windows active.`);
          }
        }
      } else {
        text('cc-chat-feedback', 'Could not inspect running apps.');
      }
    } catch (err) {
      text('cc-chat-feedback', 'Apps check unavailable.');
    }
  };

  initPillComposers();

  const chatBox = byId('chat-box');
  if (chatBox) new root.MutationObserver(syncConversation).observe(chatBox, { subtree: true, childList: true, characterData: true });
  const chatSendBtn = byId('chat-send-btn');
  if (chatSendBtn) new root.MutationObserver(idleState).observe(chatSendBtn, { attributes: true, attributeFilter: ['disabled'] });

  // Audio player and Lip-Sync Connection
  const player = byId('jarvis-audio-player');
  if (player) {
    player.addEventListener('playing', () => {
      speaking = true;
      state('speaking', 'Speaking');
      if (root.jarvisAvatar && activeChar !== 'classic') {
        try {
          root.jarvisAvatar.lipSync.connectAudioElement(player);
        } catch (_) {}
      }
    });
    for (const event of ['ended', 'pause', 'error']) {
      player.addEventListener(event, () => {
        speaking = false;
        if (root.jarvisAvatar) root.jarvisAvatar.setMouthShape('closed');
        idleState();
      });
    }
  }

  function clock() {
    const now = new Date();
    text('cc-date', now.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' }));
    text('cc-clock', now.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' }));
  }

  async function get(path) {
    const res = await root.fetch(path, { headers: { 'X-Jarvis-Client': 'dashboard' }, signal: root.AbortSignal.timeout(8000) });
    if (!res.ok) throw Error('Unavailable');
    return res.json();
  }

  function rows(id, items, empty) {
    const area = byId(id);
    if (!area) return;
    area.replaceChildren();
    if (!items.length) { area.textContent = empty; area.classList.add('cc-subtle'); return; }
    for (const [name, status] of items.slice(0, 4)) {
      const row = doc.createElement('div'); row.className = 'cc-list-row';
      const label = doc.createElement('span'); label.textContent = name;
      const badge = doc.createElement('span'); badge.className = 'cc-badge'; badge.textContent = status;
      row.append(label, badge); area.appendChild(row);
    }
  }

  function renderTasks(jobs, empty) {
    const area = byId('cc-tasks');
    if (!area) return;
    area.replaceChildren();
    if (!Array.isArray(jobs) || !jobs.length) {
      area.textContent = empty;
      area.classList.add('cc-subtle');
      return;
    }
    area.classList.remove('cc-subtle');
    for (const job of jobs.slice(0, 4)) {
      const card = doc.createElement('div');
      card.style.cssText = 'border-bottom:1px solid #183344;padding:8px 0';
      const row = doc.createElement('div');
      row.className = 'cc-list-row';
      row.style.cssText = 'border-bottom:none;padding:0;cursor:pointer';
      const labelCol = doc.createElement('div');
      labelCol.style.cssText = 'min-width:0;flex:1;margin-right:8px;text-align:left';
      
      const title = doc.createElement('div');
      title.style.cssText = 'font-size:0.82rem;font-weight:600;color:#e2e8f0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis';
      const rawTitle = job.name || job.prompt || job.description || job.task || '';
      title.textContent = rawTitle ? (rawTitle.length > 32 ? rawTitle.slice(0, 32) + '…' : rawTitle) : ('Task ' + (job.job_id || '').slice(-6));
      
      const meta = doc.createElement('div');
      meta.style.cssText = 'font-size:0.7rem;color:#64748b;margin-top:2px';
      const timeStr = job.created_at ? new Date(job.created_at * 1000).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : 'Active';
      meta.textContent = `${timeStr} · ${(job.job_id || '').slice(0, 8)}`;
      
      labelCol.append(title, meta);

      const badge = doc.createElement('span');
      const st = (job.status || 'pending').toLowerCase();
      badge.className = 'cc-badge ' + (st === 'completed' || st === 'success' || st === 'succeeded' ? 'live' : (st === 'failed' ? 'warn' : ''));
      badge.textContent = job.status || 'pending';

      row.append(labelCol, badge);
      card.appendChild(row);

      const detailBox = doc.createElement('div');
      detailBox.className = 'cc-task-detail';
      detailBox.style.cssText = 'display:none;margin-top:6px;padding:8px;background:rgba(15,23,42,0.6);border-radius:4px;font-size:0.75rem;color:#94a3b8';

      if (st === 'failed') {
        const reasonP = doc.createElement('div');
        reasonP.style.cssText = 'color:#f87171;margin-bottom:6px;word-break:break-word';
        reasonP.textContent = 'Failure reason: ' + (job.error_detail || job.error_reason || job.error_code || 'Model provider execution failed');
        detailBox.appendChild(reasonP);

        const actions = doc.createElement('div');
        actions.style.cssText = 'display:flex;gap:6px;margin-top:6px';

        const retryBtn = doc.createElement('button');
        retryBtn.type = 'button';
        retryBtn.className = 'btn dark';
        retryBtn.style.cssText = 'padding:2px 8px;font-size:0.72rem;background:#1e293b;color:#38bdf8;border:1px solid #38bdf8;cursor:pointer';
        retryBtn.textContent = 'Retry';
        retryBtn.addEventListener('click', async (e) => {
          e.stopPropagation();
          retryBtn.disabled = true;
          retryBtn.textContent = 'Retrying…';
          try {
            await root.fetch(`/api/task-jobs/${encodeURIComponent(job.job_id)}/retry`, {
              method: 'POST',
              headers: { 'X-Jarvis-Client': 'dashboard' }
            });
            await refresh();
          } catch (err) {
            retryBtn.textContent = 'Retry failed';
            retryBtn.disabled = false;
          }
        });

        const dismissBtn = doc.createElement('button');
        dismissBtn.type = 'button';
        dismissBtn.className = 'btn dark';
        dismissBtn.style.cssText = 'padding:2px 8px;font-size:0.72rem;background:#1e293b;color:#94a3b8;border:1px solid #475569;cursor:pointer';
        dismissBtn.textContent = 'Dismiss / Clear';
        dismissBtn.addEventListener('click', async (e) => {
          e.stopPropagation();
          dismissBtn.disabled = true;
          dismissBtn.textContent = 'Clearing…';
          try {
            await root.fetch(`/api/task-jobs/${encodeURIComponent(job.job_id)}`, {
              method: 'DELETE',
              headers: { 'X-Jarvis-Client': 'dashboard' }
            });
            await refresh();
          } catch (err) {
            dismissBtn.textContent = 'Clear failed';
            dismissBtn.disabled = false;
          }
        });

        actions.append(retryBtn, dismissBtn);
        detailBox.appendChild(actions);
      } else if (job.response || job.result_available) {
        const respP = doc.createElement('div');
        respP.style.cssText = 'color:#e2e8f0;white-space:pre-wrap;margin-bottom:6px;max-height:120px;overflow-y:auto';
        respP.textContent = 'Result: ' + (job.response || 'Completed');
        detailBox.appendChild(respP);

        const dismissBtn = doc.createElement('button');
        dismissBtn.type = 'button';
        dismissBtn.className = 'btn dark';
        dismissBtn.style.cssText = 'padding:2px 8px;font-size:0.72rem;background:#1e293b;color:#94a3b8;border:1px solid #475569;cursor:pointer';
        dismissBtn.textContent = 'Dismiss / Clear';
        dismissBtn.addEventListener('click', async (e) => {
          e.stopPropagation();
          dismissBtn.disabled = true;
          try {
            await root.fetch(`/api/task-jobs/${encodeURIComponent(job.job_id)}`, {
              method: 'DELETE',
              headers: { 'X-Jarvis-Client': 'dashboard' }
            });
            await refresh();
          } catch (err) {
            dismissBtn.disabled = false;
          }
        });
        detailBox.appendChild(dismissBtn);
      } else {
        const statP = doc.createElement('div');
        statP.textContent = `Status: ${job.status || 'Active'} · Progress: ${job.progress || 'working'}`;
        detailBox.appendChild(statP);
      }

      row.addEventListener('click', () => {
        detailBox.style.display = detailBox.style.display === 'none' ? 'block' : 'none';
      });

      card.appendChild(detailBox);
      area.appendChild(card);
    }
  }

  async function refresh() {
    if (refreshing || doc.hidden) return;
    refreshing = true;
    try {
      const results = await Promise.allSettled([
        get('/api/system'),
        get('/api/voice/wake_status'),
        get('/api/chat/providers'),
        get('/api/task-jobs'),
        get('/api/automations/tasks'),
        get('/api/memory/stats')
      ]);
      const value = i => results[i].status === 'fulfilled' ? results[i].value : null;
      const sys = value(0); wasOnline = !!sys;
      text('cc-connection', sys ? 'Service online' : 'Service unavailable');
      text('cc-system-status', sys ? 'Live' : 'Unavailable');

      for (const [key, id] of [['cpu_usage_pct', 'cpu'], ['ram_pct', 'ram'], ['disk_pct', 'disk']]) {
        const reading = sys?.[key], valid = typeof reading === 'number' && Number.isFinite(reading);
        text('h-' + id, valid ? reading.toFixed(1) + '%' : '—');
        const meter = byId('cc-' + id + '-meter');
        if (meter) { meter.value = valid ? reading : 0; meter.hidden = !valid; }
      }
      text('h-temp', typeof sys?.temp_c === 'number' ? sys.temp_c.toFixed(1) + '°C' : 'Unavailable');
      text('cc-host', sys?.hostname || 'Unavailable');
      text('cc-uptime', sys?.uptime_str || '—');
      text('h-robot', sys?.robot_state || 'Unverified');

      wakeState = value(1)?.state || 'Unavailable';
      text('h-voice', wakeState.replaceAll('_', ' '));
      text('cc-wake', 'Voice: ' + wakeState.replaceAll('_', ' ').toLowerCase());

      const providers = value(2), selected = providers?.active_provider;
      text('cc-provider', selected ? 'AI: ' + selected : 'AI: unavailable');
      text('cc-model-name', providers?.active_model || 'Model status unavailable');
      const provList = Array.isArray(providers?.providers) ? providers.providers : [];
      const flmapi = provList.find(p => p.name === 'freellmapi');
      const flmInfo = flmapi ? `\n[GATEWAY] FreeLLMAPI ${flmapi.available ? 'Online (' + (flmapi.models?.length || 0) + ' models)' : 'Offline'}` : '';
      text('cc-terminal', sys ? `[HOST] ${sys.os || 'Local'} · ${sys.arch || ''}\n[UPTIME] ${sys.uptime_str || 'Unknown'}\n[AI] ${selected || 'Unavailable'} (${providers?.active_model || 'default'})${flmInfo}\n[WORKSPACE] Ready to open\nCommands run only when requested.` : '[JARVIS] Service status unavailable.');

      const jobs = value(3)?.jobs;
      renderTasks(jobs, jobs ? 'No background tasks yet.' : 'Task history unavailable.');

      const schedules = value(4)?.tasks;
      rows('cc-schedules', Array.isArray(schedules) ? schedules.map(item => [item.name, item.schedule || 'Saved']) : [], schedules ? 'No schedules saved.' : 'Schedules unavailable.');
      text('cc-automation-count', Array.isArray(schedules) ? schedules.filter(item => item.enabled).length : '—');

      const memory = value(5);
      const count = memory?.total_memories ?? memory?.total_entries ?? memory?.total ?? memory?.count;
      text('cc-memory', typeof count === 'number' ? count.toLocaleString() : 'Unavailable');

      idleState();
    } finally { refreshing = false; }
  }

  root.syncCharacterSelection = function(val) {
    activeChar = val;
    save('character', val);
    root.localStorage.setItem('jarvis_avatar', val);
    const heroChar = byId('cc-char-select');
    if (heroChar && heroChar.value !== val) heroChar.value = val;
    const voiceTabChar = byId('voice-tab-char-select');
    if (voiceTabChar && voiceTabChar.value !== val) voiceTabChar.value = val;

    if (val === 'classic') {
      avatarBox?.classList.add('classic-mode');
      if (avatarMount) avatarMount.style.display = 'none';
    } else {
      avatarBox?.classList.remove('classic-mode');
      if (avatarMount) avatarMount.style.display = 'flex';
      root.jarvisAvatar?.setAvatarType(val === 'atlas' ? 'atlas' : 'aria');
      const voiceVal = val === 'atlas' ? 'en-US-GuyNeural' : 'en-US-AriaNeural';
      if (neuralVoice) neuralVoice.value = voiceVal;
      const voiceTabVoice = byId('voice-tab-voice-select');
      if (voiceTabVoice) voiceTabVoice.value = voiceVal;
      save('neural_voice', voiceVal);
    }
    idleState();
  };

  root.syncVoiceSelection = function(val) {
    if (neuralVoice) neuralVoice.value = val;
    const voiceTabVoice = byId('voice-tab-voice-select');
    if (voiceTabVoice && voiceTabVoice.value !== val) voiceTabVoice.value = val;
    save('neural_voice', val);
  };

  root.testAvatarVoice = function(charName) {
    const isAtlas = charName === 'atlas';
    root.syncCharacterSelection(charName);
    const textMsg = isAtlas
      ? "Atlas tactical audio subsystem online. Viseme lip-sync active."
      : "Aria neural voice engine operational. High-definition speech synthesis ready.";
    speak(textMsg);
  };

  root.toggleWakeWordEngine = async function() {
    const btn = byId('voice-tab-wake-toggle');
    const statusEl = byId('voice-tab-wake-status');
    const isCurrentlyArmed = statusEl && statusEl.textContent.includes('ARMED') && !statusEl.textContent.includes('DISARMED');
    const enable = !isCurrentlyArmed;
    try {
      const res = await fetch('/api/voice/wake_word/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: enable, enable: enable })
      });
      const data = await res.json();
      if (data.status === 'ok') {
        if (statusEl) {
          statusEl.textContent = enable ? '🟢 ARMED' : '⚪ DISARMED';
          statusEl.style.color = enable ? 'var(--green)' : 'var(--muted)';
        }
        if (btn) btn.textContent = enable ? 'Disable Wake Word' : 'Enable Wake Word';
      }
    } catch (e) {
      console.error('Failed to toggle wake word:', e);
    }
  };

  clock();
  root.setInterval(clock, 30000);
  refresh();
  root.setInterval(refresh, 12000);
  doc.addEventListener('visibilitychange', () => { if (!doc.hidden) refresh(); });
})(window);
