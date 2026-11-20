/* One explicit screen-sharing session. No browser microphone capture. */
(() => {
  let token = null, stream = null, timer = null, heartbeatTimer = null, generation = 0;
  let previousSpeech = false;
  let frameJob = null, screenReady = false, analysisBusy = false;
  const el = id => document.getElementById(id);

  function formatDetail(detail) {
    if (detail == null || detail === '') return '';
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      return detail.map(item => {
        if (typeof item === 'string') return item;
        if (item && typeof item === 'object') return item.msg || item.message || JSON.stringify(item);
        return String(item);
      }).join('; ');
    }
    if (typeof detail === 'object') return detail.msg || detail.message || JSON.stringify(detail);
    return String(detail);
  }

  function setTone(node, tone) {
    if (!node) return;
    node.classList.remove('is-error', 'is-ok', 'is-busy');
    if (tone === 'error') node.classList.add('is-error');
    else if (tone === 'ok') node.classList.add('is-ok');
    else if (tone === 'busy') node.classList.add('is-busy');
    node.setAttribute('role', tone === 'error' ? 'alert' : 'status');
  }

  function message(text, tone = 'info') {
    const status = el('active-desktop-status');
    if (!status) return;
    status.textContent = text;
    setTone(status, tone === 'info' ? 'ok' : tone);
  }

  function setAnswer(text, tone = 'info') {
    const answer = el('active-desktop-answer');
    if (!answer) return;
    answer.textContent = text;
    setTone(answer, tone === 'info' ? null : tone);
    if (tone === 'info' || !tone) {
      answer.classList.remove('is-error', 'is-ok', 'is-busy');
      answer.setAttribute('role', 'status');
    }
  }

  function setBusy(busy) {
    const root = el('active-desktop-panel') || el('active-desktop-heading')?.closest('section');
    if (root) root.setAttribute('aria-busy', busy ? 'true' : 'false');
    const start = el('active-desktop-start');
    if (start) start.setAttribute('aria-busy', busy ? 'true' : 'false');
  }

  const headers = () => ({'X-Jarvis-Client': 'dashboard', 'X-Jarvis-Session': token || ''});

  async function request(path, options = {}) {
    const response = await fetch('/api/active-desktop/' + path, {
      ...options, headers: {...headers(), ...(options.headers || {})}
    });
    let body = {};
    try {
      body = await response.json();
    } catch (_) {
      body = {};
    }
    if (!response.ok) {
      throw new Error(formatDetail(body.detail) || `Request failed (${response.status})`);
    }
    return body;
  }

  function releaseScreen() {
    if (stream) stream.getTracks().forEach(track => track.stop());
    stream = null;
    const preview = el('active-desktop-preview');
    if (preview) {
      preview.srcObject = null;
      preview.hidden = true;
    }
  }

  function render(state) {
    message(
      `JARVIS active · Microphone: ${state.microphone.state} · Screen: ${state.screen} · Spoken replies: ${state.options.speaker ? 'on' : 'off'}`,
      'ok'
    );
  }

  function screenActions() {
    ['active-desktop-describe', 'active-desktop-read-text'].forEach(id => {
      el(id).disabled = !screenReady || analysisBusy;
    });
  }

  function captureError(error) {
    if (error?.name === 'NotAllowedError') {
      return new Error('Screen sharing was cancelled or permission was denied. Activate JARVIS again and choose a screen or window in the browser picker.');
    }
    if (error?.name === 'NotReadableError' || error?.name === 'AbortError') {
      return new Error('The browser could not read the selected screen. Check your desktop screen-sharing permission, then choose a screen or window again.');
    }
    if (error?.name === 'InvalidStateError') {
      return new Error('Screen sharing needs an active browser tab. Return to this tab and click Activate JARVIS again.');
    }
    return error;
  }

  async function transferFrame(currentGeneration) {
    if (!token || !stream || generation !== currentGeneration) return false;
    if (frameJob?.generation === currentGeneration) return frameJob.promise;
    const video = el('active-desktop-preview');
    if (!video?.videoWidth || !video.videoHeight) return false;
    const job = {generation: currentGeneration};
    frameJob = job;
    job.promise = (async () => {
      const canvas = document.createElement('canvas');
      const scale = Math.min(1, 1280 / video.videoWidth, 720 / video.videoHeight);
      canvas.width = Math.round(video.videoWidth * scale);
      canvas.height = Math.round(video.videoHeight * scale);
      canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
      const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', 0.8));
      if (generation !== currentGeneration) return false;
      if (!blob) throw new Error('The browser could not create a screen frame. Stop sharing and select the screen again.');
      const state = await request('frame', {method: 'POST', headers: {'Content-Type': 'image/jpeg'}, body: blob});
      if (generation !== currentGeneration) return false;
      screenReady = true;
      screenActions();
      render(state);
      return true;
    })();
    try {
      return await job.promise;
    } finally {
      if (frameJob === job) frameJob = null;
    }
  }

  async function uploadFrame(currentGeneration) {
    if (!token || !stream || generation !== currentGeneration) return;
    await transferFrame(currentGeneration);
    if (generation === currentGeneration) {
      timer = setTimeout(() => uploadFrame(currentGeneration).catch(error => {
        if (generation === currentGeneration) fail(error);
      }), 3000);
    }
  }

  async function fail(error) {
    const stoppedGeneration = generation + 1;
    await stop();
    if (generation === stoppedGeneration) {
      message(`Stopped: ${error && error.message ? error.message : error}`, 'error');
    }
  }

  async function start() {
    if (token || el('active-desktop-start').disabled) return;
    const currentGeneration = ++generation;
    el('active-desktop-start').disabled = true;
    el('active-desktop-stop').disabled = false;
    setBusy(true);
    message('Starting JARVIS…', 'busy');
    ['active-screen', 'active-microphone', 'active-speaker'].forEach(id => { el(id).disabled = true; });
    try {
      const options = {
        screen: el('active-screen').checked,
        microphone: el('active-microphone').checked,
        speaker: el('active-speaker').checked
      };
      if (options.screen) {
        if (window.isSecureContext === false) {
          throw new Error('Screen sharing needs a secure browser page. Open this dashboard at http://localhost or http://127.0.0.1 on this computer.');
        }
        if (!navigator.mediaDevices?.getDisplayMedia) {
          throw new Error('Screen sharing is unavailable in this browser. Open the local dashboard in a supported browser.');
        }
        // Must precede every network await to preserve the activating click.
        let captured;
        try {
          captured = await navigator.mediaDevices.getDisplayMedia({video: {frameRate: 2}, audio: false});
        } catch (error) { throw captureError(error); }
        if (generation !== currentGeneration) { captured.getTracks().forEach(t => t.stop()); return; }
        stream = captured;
        const track = stream.getVideoTracks()[0];
        if (!track || track.readyState === 'ended') throw new Error('The selected screen is no longer available. Select a screen or window again.');
        track.addEventListener('ended', () => {
          if (generation === currentGeneration) return stop();
        });
        const preview = el('active-desktop-preview');
        preview.srcObject = stream;
        preview.hidden = false;
        await preview.play();
      }
      if (generation !== currentGeneration) return;
      const state = await request('start', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(options)
      });
      if (generation !== currentGeneration) {
        await fetch('/api/active-desktop/stop', {
          method: 'POST',
          headers: {'X-Jarvis-Client': 'dashboard', 'X-Jarvis-Session': state.token}
        });
        return;
      }
      token = state.token;
      previousSpeech = el('chat-auto-speak').checked;
      el('chat-auto-speak').checked = options.speaker;
      const banner = el('active-desktop-banner');
      banner.hidden = false;
      banner.setAttribute('aria-hidden', 'false');
      screenActions();
      setBusy(false);
      render(state);
      heartbeatTimer = setInterval(() => request('heartbeat', {method: 'POST'}).then(state => {
        if (generation === currentGeneration) render(state);
      }).catch(error => { if (generation === currentGeneration) fail(error); }), 8000);
      await uploadFrame(currentGeneration);
    } catch (error) {
      if (generation === currentGeneration) await fail(error);
    }
  }

  async function stop() {
    ++generation;
    clearTimeout(timer); clearInterval(heartbeatTimer);
    const oldToken = token; token = null;
    frameJob = null; screenReady = false; analysisBusy = false;
    releaseScreen();
    const banner = el('active-desktop-banner');
    if (banner) {
      banner.hidden = true;
      banner.setAttribute('aria-hidden', 'true');
    }
    el('active-desktop-start').disabled = false;
    ['active-screen', 'active-microphone', 'active-speaker'].forEach(id => { el(id).disabled = false; });
    el('active-desktop-stop').disabled = true;
    el('active-desktop-describe').disabled = true;
    el('active-desktop-read-text').disabled = true;
    setAnswer('');
    setBusy(false);
    message('Inactive · Screen released. Pre-existing voice services keep their prior state.', 'info');
    if (oldToken) {
      el('chat-auto-speak').checked = previousSpeech;
      if (typeof stopSpeech === 'function') stopSpeech();
      try {
        await fetch('/api/active-desktop/stop', {
          method: 'POST',
          keepalive: true,
          headers: {'X-Jarvis-Client': 'dashboard', 'X-Jarvis-Session': oldToken}
        });
      } catch (_) { /* Server lease expires even if the tab loses connectivity. */ }
    }
  }

  async function describe() {
    if (!token || !screenReady || analysisBusy) return;
    const currentGeneration = generation;
    analysisBusy = true;
    screenActions();
    setBusy(true);
    setAnswer('Reading the shared screen locally… A cold model can take up to two minutes.', 'busy');
    try {
      if (!await transferFrame(currentGeneration)) {
        throw new Error('The shared screen is not ready. Wait for the preview and try again.');
      }
      if (generation !== currentGeneration) return;
      const question = el('active-desktop-question').value.trim() ||
        'Describe the visible desktop or terminal. Read important text; say when text is unreadable.';
      const result = await request('describe', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({question})
      });
      if (generation === currentGeneration) {
        setAnswer(result.description + '\n\n' + result.note, 'ok');
      }
    } catch (error) {
      if (generation === currentGeneration) setAnswer(error.message, 'error');
    } finally {
      if (generation === currentGeneration) {
        analysisBusy = false;
        screenActions();
        setBusy(false);
      }
    }
  }

  async function readText() {
    if (!token || !screenReady || analysisBusy) return;
    const currentGeneration = generation;
    analysisBusy = true;
    screenActions();
    setBusy(true);
    setAnswer('Reading visible text locally…', 'busy');
    try {
      if (!await transferFrame(currentGeneration)) {
        throw new Error('The shared screen is not ready. Wait for the preview and try again.');
      }
      if (generation !== currentGeneration) return;
      const result = await request('read-text', {method: 'POST'});
      if (generation === currentGeneration) {
        setAnswer(
          (result.text || 'No readable text found in the shared frame.') + '\n\n' + result.note,
          'ok'
        );
      }
    } catch (error) {
      if (generation === currentGeneration) setAnswer(error.message, 'error');
    } finally {
      if (generation === currentGeneration) {
        analysisBusy = false;
        screenActions();
        setBusy(false);
      }
    }
  }

  function bindQuestionEnter() {
    const input = el('active-desktop-question');
    if (!input || input.dataset.boundEnter === '1') return;
    input.dataset.boundEnter = '1';
    input.addEventListener('keydown', (event) => {
      if (event.key !== 'Enter') return;
      event.preventDefault();
      if (!el('active-desktop-describe').disabled) describe();
    });
  }

  window.jarvisDesktop = {start, stop, describe, readText};
  window.addEventListener('pagehide', () => stop());
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bindQuestionEnter);
  } else {
    bindQuestionEnter();
  }
})();
