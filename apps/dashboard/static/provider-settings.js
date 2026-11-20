/* Provider metadata only: credentials remain in the existing integration flow. */
(function (global) {
  'use strict';
  const cloud = new Set(['openai', 'gemini', 'anthropic', 'nvidia', 'openrouter', 'groq', 'together']);
  const outcomes = Object.freeze({
    passed: 'Test passed', disabled: 'Provider disabled', missing_key: 'API key not configured',
    authentication_failed: 'Authentication failed; check the saved API key',
    access_denied: 'Access denied; check provider permissions',
    model_or_endpoint_unavailable: 'Model or endpoint unavailable',
    rate_or_quota_limited: 'Rate or quota limit reached', request_failed: 'Provider request failed',
    invalid_response: 'Invalid provider response', unexpected_answer: 'Test returned an unexpected answer',
    empty_response: 'Test returned an empty response', not_tested: 'Not tested'
  });
  const identifier = value => typeof value === 'string' && value.length > 0 && value.length <= 256 && !/[\x00-\x1f\x7f]/.test(value);

  function mount(root, options = {}) {
    if (!root || !root.ownerDocument) throw new TypeError('A container element is required');
    const doc = root.ownerDocument;
    const request = options.fetch || global.fetch.bind(global);
    const state = {providers: [], active: null, busy: false, destroyed: false, probe: null};
    let pending = null;
    const listeners = [];
    function node(tag, text) {
      const el = doc.createElement(tag);
      if (text !== undefined) el.textContent = text;
      return el;
    }
    const panel = node('section');
    panel.className = 'provider-settings';
    panel.setAttribute('aria-label', 'Provider setup and status');
    const heading = node('h3', 'AI provider and model');
    const explanation = node('p', 'Configured credentials and availability do not verify generation. A provider is tested only after an explicit successful test. OpenRouter offers the openrouter/free model route; it requires an API key and has rate limits. Select it and test before chatting.');
    const active = node('p', 'Active selection: loading');
    const list = node('ul');
    list.setAttribute('aria-label', 'Provider configuration status');
    const provider = node('select');
    provider.setAttribute('aria-label', 'AI provider');
    const model = node('select');
    model.setAttribute('aria-label', 'AI model');
    const apply = node('button', 'Use selected model');
    const refreshButton = node('button', 'Refresh provider status');
    const testButton = node('button', 'Test selected cloud provider');
    [apply, refreshButton, testButton].forEach(button => { button.type = 'button'; button.className = 'btn dark'; });
    const notice = node('p', 'Testing sends a synthetic prompt to the selected cloud provider using its configured model. Apply a model change before testing it. Administrator authorization is required.');
    const feedback = node('p');
    feedback.setAttribute('role', 'status');
    feedback.setAttribute('aria-live', 'polite');
    feedback.className = 'status-msg';
    [heading, explanation, active, list, provider, model, apply, refreshButton, testButton, notice, feedback].forEach(el => panel.appendChild(el));
    root.appendChild(panel);

    function status(message, error = false) {
      feedback.textContent = message;
      feedback.className = 'status-msg ' + (error ? 'is-error' : 'is-ok');
      feedback.setAttribute('role', error ? 'alert' : 'status');
    }
    function selected() { return state.providers.find(item => item.name === provider.value); }
    function controls() {
      const item = selected();
      const unavailable = !item || !item.enabled || item.credential_configured === false || !model.value;
      provider.disabled = state.busy || !state.providers.length;
      model.disabled = state.busy || !item;
      apply.disabled = state.busy || unavailable;
      refreshButton.disabled = state.busy;
      testButton.disabled = state.busy || unavailable || !cloud.has(item?.name) || typeof options.authorizeTest !== 'function';
      panel.setAttribute('aria-busy', String(state.busy));
    }
    function models(preferred) {
      model.replaceChildren();
      const item = selected();
      if (item) item.models.forEach(name => {
        const opt = node('option', name); opt.value = name; model.appendChild(opt);
      });
      model.value = item?.models.includes(preferred) ? preferred : (item?.models[0] || '');
      controls();
    }
    function render() {
      provider.replaceChildren();
      list.replaceChildren();
      state.providers.forEach(item => {
        const opt = node('option', item.name); opt.value = item.name; provider.appendChild(opt);
        const configuration = !item.enabled ? 'Disabled' : item.credential_configured === false ? 'API key not configured' : item.credential_configured === true ? 'Credentials configured' : 'Local provider';
        const availability = item.available ? 'backend available' : 'backend unavailable';
        const probe = state.probe?.provider === item.name ? state.probe : null;
        const verification = probe ? `${outcomes[probe.status]} (${probe.model})` : 'Not tested';
        list.appendChild(node('li', `${item.name}: ${configuration}; ${availability}; ${verification}`));
      });
      active.textContent = state.active ? `Active selection: ${state.active.provider} / ${state.active.model}` : 'Active selection: none confirmed';
      provider.value = state.active?.provider || state.providers[0]?.name || '';
      models(state.active?.model || selected()?.model);
    }
    function forgetProbe() {
      state.probe = null;
      const chosenProvider = provider.value, chosenModel = model.value;
      render();
      if (state.providers.some(item => item.name === chosenProvider)) {
        provider.value = chosenProvider; models(chosenModel);
      }
    }
    async function api(path, init) {
      pending = new AbortController();
      const timer = setTimeout(() => pending?.abort(), 30000);
      try {
        let response;
        try { response = await request(path, {...init, signal: pending.signal, credentials: 'same-origin'}); }
        catch (_) { throw new Error('Cannot reach the server. Check the connection and retry.'); }
        if (!response.ok) {
          const code = Number.isInteger(response.status) ? response.status : 0;
          const hint = code === 401 || code === 403 ? 'Administrator authorization was rejected.' : code === 429 ? 'Too many requests; retry later.' : 'The server rejected this request.';
          throw new Error(`${hint} HTTP ${code}.`);
        }
        let data;
        try { data = await response.json(); } catch (_) { throw new Error('The server returned an unreadable response.'); }
        if (!data || typeof data !== 'object' || Array.isArray(data)) throw new Error('The server returned an invalid response.');
        return data;
      } finally { clearTimeout(timer); pending = null; }
    }
    async function action(message, work) {
      if (state.busy || state.destroyed) return false;
      state.busy = true; controls(); status(message);
      try { return await work(); }
      catch (error) { if (!state.destroyed) status(error.message, true); return false; }
      finally { state.busy = false; if (!state.destroyed) controls(); }
    }
    function readProviders(data) {
      if (!Array.isArray(data.providers) || data.providers.length > 100) throw new Error('The server returned invalid provider metadata.');
      const names = new Set();
      return data.providers.map(item => {
        if (!item || !identifier(item.name) || !/^[a-z0-9_-]+$/i.test(item.name) || names.has(item.name) || !Array.isArray(item.models) || item.models.length > 500 || !item.models.every(identifier)) throw new Error('The server returned invalid provider metadata.');
        names.add(item.name);
        const choices = [...new Set(item.models)];
        if (identifier(item.model) && !choices.includes(item.model)) choices.unshift(item.model);
        return {name: item.name, model: identifier(item.model) ? item.model : '', models: choices, available: item.available === true, enabled: item.enabled !== false, credential_configured: typeof item.credential_configured === 'boolean' ? item.credential_configured : null, active: item.active === true};
      });
    }
    function refresh() {
      return action('Loading provider status…', async () => {
        forgetProbe();
        const data = await api('/api/chat/providers');
        const providers = readProviders(data);
        if (state.destroyed) return false;
        state.providers = providers;
        const current = providers.find(item => item.name === data.active_provider && item.active && item.models.includes(data.active_model));
        state.active = current ? {provider: current.name, model: data.active_model} : null;
        render(); status(providers.length ? 'Provider status loaded. Generation tests are not run automatically.' : 'No providers registered.');
        return true;
      });
    }
    function switchModel(providerName = provider.value, modelName = model.value) {
      return action('Applying model selection…', async () => {
        const item = state.providers.find(value => value.name === providerName);
        if (!item || !item.enabled || item.credential_configured === false || !item.models.includes(modelName)) throw new Error('Choose an enabled, configured provider and one of its listed models.');
        forgetProbe();
        let data;
        try {
          data = await api('/api/chat/model', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({provider: providerName, model: modelName})});
          if (data.success !== true || data.active_provider !== providerName || data.active_model !== modelName) throw new Error('Model selection was not confirmed. Refresh to check the active model.');
        } catch (error) { if (!state.destroyed) render(); throw error; }
        if (state.destroyed) return false;
        state.active = {provider: providerName, model: modelName}; item.model = modelName;
        render(); status(`Selected ${providerName} / ${modelName}. Generation has not been tested.`);
        if (typeof options.onSelectionChange === 'function') {
          try { await options.onSelectionChange({...state.active}); }
          catch (_) { if (!state.destroyed) status('Model selected. Refresh other model selectors to show the change.', true); }
        }
        return true;
      });
    }
    function testSelected() {
      return action('Authorizing provider test…', async () => {
        const item = selected();
        if (!item || !item.enabled || item.credential_configured === false || !cloud.has(item.name)) throw new Error('Select an enabled cloud provider with credentials configured.');
        if (typeof options.authorizeTest !== 'function') throw new Error('Administrator authorization is required to test a provider.');
        let headers;
        try { headers = await options.authorizeTest(item.name); } catch (_) { throw new Error('Provider test was not authorized.'); }
        if (!headers || typeof headers !== 'object' || Array.isArray(headers)) throw new Error('Provider test was not authorized.');
        if (state.destroyed) return false;
        forgetProbe();
        status(`Testing ${item.name} using its configured model…`);
        const data = await api('/api/chat/providers/test', {method: 'POST', headers: {...headers, 'Content-Type': 'application/json'}, body: JSON.stringify({provider: item.name})});
        headers = null;
        if (data.provider !== item.name || data.model !== item.model || !Object.prototype.hasOwnProperty.call(outcomes, data.status)) throw new Error('The test response did not match the configured provider and model. Refresh and retry.');
        if (state.destroyed) return false;
        state.probe = {provider: item.name, model: data.model, status: data.status};
        const chosenProvider = provider.value, chosenModel = model.value;
        render(); provider.value = chosenProvider; models(chosenModel);
        status(`${item.name} / ${data.model}: ${outcomes[data.status]}.`, data.status !== 'passed');
        return data.status === 'passed';
      });
    }
    function listen(el, event, handler) { el.addEventListener(event, handler); listeners.push([el, event, handler]); }
    listen(provider, 'change', () => models(selected()?.model));
    listen(model, 'change', controls);
    listen(apply, 'click', () => switchModel());
    listen(refreshButton, 'click', refresh);
    listen(testButton, 'click', testSelected);
    const controller = {refresh, switchModel, testSelected, destroy() {
      state.destroyed = true; pending?.abort();
      listeners.forEach(([el, event, handler]) => el.removeEventListener(event, handler));
      panel.remove(); state.providers = []; state.probe = null;
    }};
    controller.ready = refresh();
    return controller;
  }
  const exported = Object.freeze({mount});
  if (typeof module === 'object' && module.exports) module.exports = exported;
  else global.JarvisProviderSettings = exported;
})(typeof window === 'object' ? window : globalThis);
