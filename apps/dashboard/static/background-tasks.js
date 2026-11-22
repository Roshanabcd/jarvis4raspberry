(function (root) {
  'use strict';
  const active = new Set(['accepted', 'running']);
  const labels = {accepted:'Accepted — waiting to start', running:'Working…', succeeded:'Reply ready — review result', failed:'Failed', cancelled:'Cancelled', interrupted:'Interrupted by restart — not replayed'};

  function mount(doc, options = {}) {
    const form = doc.getElementById('background-task-form');
    if (!form) return null;
    const input = doc.getElementById('background-task-input');
    const submit = doc.getElementById('background-task-submit');
    const feedback = doc.getElementById('background-task-feedback');
    const list = doc.getElementById('background-task-list');
    const request = options.fetch || root.fetch.bind(root);
    const later = options.setTimeout || root.setTimeout.bind(root);
    const clear = options.clearTimeout || root.clearTimeout.bind(root);
    let pending = null, timer = null, loading = false, sending = false, disposed = false;

    async function api(path, init) {
      const response = await request('/api/task-jobs' + path, {...init, headers:{'X-Jarvis-Client':'dashboard', ...init?.headers}, signal: root.AbortSignal.timeout(10000)});
      if (!response.ok) throw new Error(String(response.status));
      return response.json();
    }
    function render(jobs) {
      list.replaceChildren();
      if (!jobs.length) { list.textContent = 'No background tasks yet.'; return; }
      for (const job of jobs) {
        if (!job || typeof job.job_id !== 'string' || !labels[job.status]) continue;
        const row = doc.createElement('article');
        row.style.cssText = 'padding:10px;margin:8px 0;border:1px solid var(--card-border);border-radius:6px;overflow-wrap:anywhere';
        const title = doc.createElement('strong');
        title.textContent = `${job.job_id} · ${labels[job.status]}`;
        row.appendChild(title);
        if (job.cancellation_requested && active.has(job.status)) {
          const note = doc.createElement('p');
          note.textContent = 'Stop requested. An action already in progress may finish.';
          row.appendChild(note);
        }
        if (job.status === 'failed') {
          const note = doc.createElement('p');
          note.textContent = job.error_detail || job.error_reason || 'This task did not finish successfully. Review the result before trying again.';
          row.appendChild(note);

          const actions = doc.createElement('div');
          actions.style.cssText = 'display:flex;gap:6px;margin-top:6px';
          const retryBtn = doc.createElement('button');
          retryBtn.type = 'button'; retryBtn.className = 'btn dark'; retryBtn.textContent = 'Retry task';
          retryBtn.addEventListener('click', async () => {
            retryBtn.disabled = true;
            try {
              await api('/' + encodeURIComponent(job.job_id) + '/retry', {method:'POST'});
              feedback.textContent = 'Task retry requested.';
              await refresh();
            } catch (_) {
              feedback.textContent = 'Retry could not be confirmed.';
              retryBtn.disabled = false;
            }
          });
          const dismissBtn = doc.createElement('button');
          dismissBtn.type = 'button'; dismissBtn.className = 'btn dark'; dismissBtn.textContent = 'Dismiss task';
          dismissBtn.addEventListener('click', async () => {
            dismissBtn.disabled = true;
            try {
              await api('/' + encodeURIComponent(job.job_id), {method:'DELETE'});
              feedback.textContent = 'Task dismissed.';
              await refresh();
            } catch (_) {
              feedback.textContent = 'Dismissal could not be confirmed.';
              dismissBtn.disabled = false;
            }
          });
          actions.appendChild(retryBtn);
          actions.appendChild(dismissBtn);
          row.appendChild(actions);
        }
        if (job.result_available && typeof job.response === 'string') {
          const reply = doc.createElement('p');
          reply.style.whiteSpace = 'pre-wrap';
          if (job.status === 'failed') {
            reply.style.cssText = 'white-space:pre-wrap;background:rgba(255,75,75,0.08);padding:8px 10px;border-radius:4px;border-left:3px solid #ff5555;margin-top:6px;font-family:monospace;font-size:0.9em;';
          }
          reply.textContent = job.response;
          row.appendChild(reply);
        } else if (job.status === 'succeeded') {
          const note = doc.createElement('p');
          note.textContent = 'Completion recorded. The reply text is no longer retained after restart.';
          row.appendChild(note);
        }
        if (active.has(job.status)) {
          const stop = doc.createElement('button');
          stop.type = 'button'; stop.className = 'btn dark'; stop.textContent = 'Stop task';
          stop.disabled = !!job.cancellation_requested;
          stop.addEventListener('click', async () => {
            stop.disabled = true;
            try {
              await api('/' + encodeURIComponent(job.job_id) + '/cancel', {method:'POST'});
              feedback.textContent = 'Stop requested. Refresh status to check the outcome; completed actions are not undone.';
              await refresh();
            } catch (_) {
              feedback.textContent = 'Stopping could not be confirmed. Refresh task status before trying again.';
              stop.disabled = false;
            }
          });
          row.appendChild(stop);
        }
        list.appendChild(row);
      }
    }
    async function refresh() {
      if (loading || disposed) return;
      loading = true;
      if (timer) clear(timer);
      timer = null;
      try {
        const data = await api('');
        if (!Array.isArray(data.jobs)) throw new Error('Invalid response');
        if (!disposed) render(data.jobs);
        if (!disposed && data.jobs.some(job => active.has(job?.status))) timer = later(refresh, 1500);
      } catch (_) {
        list.textContent = 'Task status is unavailable. Refresh to reconnect; this does not rerun tasks.';
        // Poll status only. Never resubmit a task after a lost response.
        if (!disposed) timer = later(refresh, 5000);
      } finally { loading = false; }
    }
    async function send(event) {
      event.preventDefault();
      const transcript = input.value.trim();
      if (!transcript || sending || disposed) return;
      // An uncertain submission keeps its token for an explicit retry.
      if (pending && pending.transcript !== transcript) {
        feedback.textContent = 'The previous submission is unconfirmed. Refresh task history, or retry the same text before starting a different task.';
        return;
      }
      if (!pending) pending = {transcript, key: root.crypto.randomUUID()};
      sending = true; submit.disabled = true;
      feedback.textContent = 'Sending task…';
      try {
        const job = await api('', {method:'POST', headers:{'Content-Type':'application/json', 'Idempotency-Key':pending.key}, body:JSON.stringify({transcript})});
        if (!job || typeof job.job_id !== 'string' || !labels[job.status]) throw new Error('Invalid response');
        pending = null;
        if (input.value.trim() === transcript) input.value = '';
        feedback.textContent = 'Task accepted. You can keep chatting while JARVIS works.';
        await refresh();
      } catch (error) {
        if (['400','403','422','429'].includes(error.message)) {
          pending = null;
          feedback.textContent = error.message === '429' ? 'The task queue is full. Wait for a task to finish, then try again.' : 'Task was not accepted. Check your session and task text.';
        } else {
          feedback.textContent = 'Acceptance could not be confirmed. Refresh task history or retry this same text; the retry uses the same task token.';
        }
      } finally { sending = false; submit.disabled = false; }
    }
    form.addEventListener('submit', send);
    doc.getElementById('background-task-refresh').addEventListener('click', refresh);
    refresh();
    return {refresh, send, dispose() {disposed = true; if (timer) clear(timer);}};
  }
  root.JarvisBackgroundTasks = {mount};
  if (typeof module !== 'undefined' && module.exports) module.exports = {mount};
  if (root.document) root.jarvisBackgroundTasks = mount(root.document);
})(typeof window !== 'undefined' ? window : globalThis);
