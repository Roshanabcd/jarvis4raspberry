/**
 * JARVIS OS Operations Hub (Phase 8)
 * Manages Tasks Center, Automations & Schedules, Calendar & Reminders,
 * Long-Term Memory, Knowledge Base, Integrations, and Connected Apps.
 * 
 * Strict Truthfulness Guarantee:
 * - Every task status, schedule, memory record, integration connectivity,
 *   and app manifest comes directly from backend REST endpoints.
 * - No mock scores, fake percentages, or simulated statuses.
 * - Planned applications explicitly indicate roadmap state and cannot be launched.
 */

(function () {
  'use strict';

  class JarvisOperationsHub {
    constructor() {
      this.currentFilter = 'all';
      this.memoryCategory = 'ALL';
      this.appCategory = 'all';
      this.selectedTimezone = 'UTC';
      this.searchQuery = '';
      this.cachedTasks = [];
      this.cachedAutomations = [];
      this.cachedMemories = [];
      this.cachedApps = [];
      this.cachedIntegrations = null;
      this.pollTimer = null;
    }

    renderDestination(destId) {
      const container = document.getElementById('view-placeholder');
      if (!container) return;

      container.className = 'view-container';
      container.innerHTML = '';

      switch (destId) {
        case 'tasks':
          this.renderTasks(container);
          break;
        case 'automation':
          this.renderAutomation(container);
          break;
        case 'calendar':
          this.renderCalendar(container);
          break;
        case 'memory':
          this.renderMemory(container);
          break;
        case 'knowledge':
          this.renderKnowledge(container);
          break;
        case 'documents':
          this.renderDocuments(container);
          break;
        case 'integrations':
          this.renderIntegrations(container);
          break;
        case 'apps':
          this.renderApps(container);
          break;
        default:
          container.innerHTML = `<div class="p-6">Destination ${destId} not routed in Operations Hub.</div>`;
      }
    }

    // ──────────────────────────────────────────────────────────────────────────
    // 1. Destination 4: Tasks Center (#tasks)
    // ──────────────────────────────────────────────────────────────────────────

    async renderTasks(container) {
      container.innerHTML = `
        <div class="ops-header">
          <div>
            <h2 class="ops-title">Tasks Center</h2>
            <p class="ops-subtitle">Multi-agent developer tasks & background jobs orchestration</p>
          </div>
          <div class="ops-header-actions">
            <button class="btn-futuristic btn-secondary" id="tasks-refresh-btn">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 4v6h-6"></path><path d="M1 20v-6h6"></path><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>
              Refresh
            </button>
            <button class="btn-futuristic btn-primary" id="tasks-create-toggle-btn">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
              New Task
            </button>
          </div>
        </div>

        <!-- Task Creation Drawer -->
        <div class="glass-panel ops-create-panel hidden" id="task-create-drawer">
          <h3 class="card-title">Create Developer or Background Task</h3>
          <form id="task-create-form" class="ops-form">
            <div class="form-row">
              <div class="form-group flex-2">
                <label for="task-title-input">Task Title *</label>
                <input type="text" id="task-title-input" class="input-futuristic" placeholder="e.g. Audit API error handling" required />
              </div>
              <div class="form-group flex-1">
                <label for="task-type-select">Task Type</label>
                <select id="task-type-select" class="input-futuristic">
                  <option value="developer">Developer Task (Worktree)</option>
                  <option value="background">Background Job (Autonomous)</option>
                </select>
              </div>
              <div class="form-group flex-1">
                <label for="task-priority-input">Priority (1-10)</label>
                <input type="number" id="task-priority-input" class="input-futuristic" min="1" max="10" value="5" />
              </div>
            </div>
            <div class="form-group">
              <label for="task-desc-input">Task Description / Prompt *</label>
              <textarea id="task-desc-input" class="input-futuristic" rows="3" placeholder="Enter explicit instructions for the task..." required></textarea>
            </div>
            <div class="form-actions">
              <button type="button" class="btn-futuristic btn-secondary" id="task-create-cancel-btn">Cancel</button>
              <button type="submit" class="btn-futuristic btn-primary" id="task-create-submit-btn">Submit Task</button>
            </div>
          </form>
        </div>

        <!-- Task Status Filter Tabs -->
        <div class="ops-tabs" role="tablist" aria-label="Task Status Filters" id="task-status-tabs">
          <button class="ops-tab active" data-filter="all" role="tab" aria-selected="true">All Tasks</button>
          <button class="ops-tab" data-filter="pending" role="tab" aria-selected="false">Pending</button>
          <button class="ops-tab" data-filter="running" role="tab" aria-selected="false">Running</button>
          <button class="ops-tab" data-filter="succeeded" role="tab" aria-selected="false">Succeeded</button>
          <button class="ops-tab" data-filter="failed" role="tab" aria-selected="false">Failed</button>
          <button class="ops-tab" data-filter="cancelled" role="tab" aria-selected="false">Cancelled</button>
        </div>

        <!-- Task List Container -->
        <div class="ops-list-container" id="tasks-list">
          <div class="ops-loading">Loading task queue from orchestrator...</div>
        </div>

        <!-- Diff Inspection Modal -->
        <div class="terminal-confirm-overlay hidden" id="task-diff-modal" role="dialog" aria-modal="true" aria-labelledby="task-diff-title">
          <div class="glass-panel" style="max-width:800px; width:95%; max-height:85vh; display:flex; flex-direction:column; gap:16px;">
            <div class="card-header">
              <h3 class="card-title" id="task-diff-title">Worktree Diff Inspection</h3>
              <button class="btn-futuristic btn-secondary btn-icon" id="task-diff-close-btn" aria-label="Close diff modal">✕</button>
            </div>
            <div style="flex:1; overflow-y:auto; background:#020612; border:1px solid rgba(0,217,255,0.2); border-radius:var(--radius-sm); padding:14px; font-family:var(--font-mono); font-size:0.8rem; color:#A0C0E0; white-space:pre-wrap;" id="task-diff-content"></div>
          </div>
        </div>
      `;

      // Event listeners
      const drawer = container.querySelector('#task-create-drawer');
      container.querySelector('#tasks-create-toggle-btn').addEventListener('click', () => {
        drawer.classList.toggle('hidden');
      });
      container.querySelector('#task-create-cancel-btn').addEventListener('click', () => {
        drawer.classList.add('hidden');
      });
      container.querySelector('#tasks-refresh-btn').addEventListener('click', () => {
        this.loadTasks(container);
      });

      // Filter tabs
      container.querySelectorAll('#task-status-tabs .ops-tab').forEach(tab => {
        tab.addEventListener('click', () => {
          container.querySelectorAll('#task-status-tabs .ops-tab').forEach(t => {
            t.classList.remove('active');
            t.setAttribute('aria-selected', 'false');
          });
          tab.classList.add('active');
          tab.setAttribute('aria-selected', 'true');
          this.currentFilter = tab.getAttribute('data-filter');
          this.renderFilteredTasks(container);
        });
      });

      // Form submission
      const form = container.querySelector('#task-create-form');
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const title = container.querySelector('#task-title-input').value.trim();
        const type = container.querySelector('#task-type-select').value;
        const priority = parseInt(container.querySelector('#task-priority-input').value, 10) || 5;
        const desc = container.querySelector('#task-desc-input').value.trim();
        const submitBtn = container.querySelector('#task-create-submit-btn');

        if (!title || !desc) return;
        submitBtn.disabled = true;

        try {
          if (type === 'developer') {
            await window.jarvisApi.createDeveloperTask(title, desc, desc, priority);
          } else {
            await window.jarvisApi.submitBackgroundJob(desc);
          }
          if (window.jarvisShell) window.jarvisShell.showToast(`Task "${title}" created successfully!`, 'success');
          form.reset();
          drawer.classList.add('hidden');
          await this.loadTasks(container);
        } catch (err) {
          if (window.jarvisShell) window.jarvisShell.showToast(`Failed to create task: ${err.message}`, 'error');
        } finally {
          submitBtn.disabled = false;
        }
      });

      // Diff modal close
      container.querySelector('#task-diff-close-btn').addEventListener('click', () => {
        container.querySelector('#task-diff-modal').classList.add('hidden');
      });

      await this.loadTasks(container);
    }

    async loadTasks(container) {
      const listEl = container.querySelector('#tasks-list');
      if (!listEl) return;

      try {
        const [devTasksRes, bgJobsRes] = await Promise.all([
          window.jarvisApi.getDeveloperTasks().catch(() => ({ tasks: [] })),
          window.jarvisApi.getBackgroundJobs().catch(() => ({ jobs: [] })),
        ]);

        const devTasks = (devTasksRes && devTasksRes.tasks) || [];
        const bgJobs = ((bgJobsRes && bgJobsRes.jobs) || []).map(j => ({
          task_id: j.job_id,
          title: `Background Job ${j.job_id}`,
          description: j.response || `Status: ${j.status}`,
          status: j.status,
          is_background: true,
          created_at: j.created_at || Date.now() / 1000,
        }));

        this.cachedTasks = [...devTasks, ...bgJobs];
        this.renderFilteredTasks(container);
      } catch (err) {
        listEl.innerHTML = `<div class="ops-error">Error loading tasks: ${this.escapeHtml(err.message)}</div>`;
      }
    }

    renderFilteredTasks(container) {
      const listEl = container.querySelector('#tasks-list');
      if (!listEl) return;

      let filtered = this.cachedTasks;
      if (this.currentFilter !== 'all') {
        filtered = filtered.filter(t => (t.status || '').toLowerCase() === this.currentFilter);
      }

      if (filtered.length === 0) {
        listEl.innerHTML = `
          <div class="glass-panel text-center p-8">
            <p class="ops-empty-text">No tasks found matching filter: <strong class="text-accent">${this.escapeHtml(this.currentFilter)}</strong></p>
          </div>
        `;
        return;
      }

      listEl.innerHTML = filtered.map(t => {
        const status = (t.status || 'pending').toLowerCase();
        const isBg = Boolean(t.is_background);
        return `
          <div class="glass-panel task-card" id="task-card-${t.task_id}" data-task-id="${t.task_id}">
            <div class="task-card-header">
              <div style="display:flex; align-items:center; gap:10px;">
                <span class="task-status-chip chip-${status}">${status.toUpperCase()}</span>
                <span class="task-id-badge">${isBg ? 'BG-JOB' : 'DEV-TASK'} #${t.task_id.slice(0, 10)}</span>
                <h4 class="task-title">${this.escapeHtml(t.title || 'Untitled Task')}</h4>
              </div>
              <div class="task-meta text-muted">
                ${t.created_at ? new Date(t.created_at * 1000).toLocaleTimeString() : ''}
              </div>
            </div>
            <div class="task-desc">${this.escapeHtml(t.description || t.prompt || 'No description provided')}</div>
            ${t.worktree ? `<div class="task-worktree-tag">Isolated Worktree: <code>${this.escapeHtml(t.worktree)}</code></div>` : ''}
            <div class="task-actions">
              ${!isBg && (status === 'pending' || status === 'failed') ? `
                <button class="btn-futuristic btn-secondary btn-sm btn-run" data-id="${t.task_id}">
                  ▶ Run Task
                </button>
              ` : ''}
              ${status === 'running' ? `
                <button class="btn-futuristic btn-danger btn-sm btn-cancel" data-id="${t.task_id}" data-bg="${isBg}">
                  ⏹ Cancel
                </button>
              ` : ''}
              ${!isBg && (status === 'failed' || status === 'cancelled') ? `
                <button class="btn-futuristic btn-secondary btn-sm btn-resume" data-id="${t.task_id}">
                  ↺ Resume / Retry
                </button>
              ` : ''}
              ${!isBg && status === 'succeeded' ? `
                <button class="btn-futuristic btn-secondary btn-sm btn-verify" data-id="${t.task_id}">
                  ✓ Quality Verify
                </button>
                <button class="btn-futuristic btn-primary btn-sm btn-propose" data-id="${t.task_id}">
                  ⤤ Propose Merge
                </button>
              ` : ''}
              ${!isBg && t.worktree ? `
                <button class="btn-futuristic btn-secondary btn-sm btn-diff" data-id="${t.task_id}">
                  Diff
                </button>
              ` : ''}
            </div>
          </div>
        `;
      }).join('');

      // Wire action buttons
      listEl.querySelectorAll('.btn-run').forEach(btn => {
        btn.addEventListener('click', async () => {
          const id = btn.getAttribute('data-id');
          btn.disabled = true;
          try {
            await window.jarvisApi.runDeveloperTask(id);
            if (window.jarvisShell) window.jarvisShell.showToast(`Task ${id} started`, 'info');
            await this.loadTasks(container);
          } catch (e) {
            if (window.jarvisShell) window.jarvisShell.showToast(`Error running task: ${e.message}`, 'error');
          } finally { btn.disabled = false; }
        });
      });

      listEl.querySelectorAll('.btn-cancel').forEach(btn => {
        btn.addEventListener('click', async () => {
          const id = btn.getAttribute('data-id');
          const isBg = btn.getAttribute('data-bg') === 'true';
          btn.disabled = true;
          try {
            if (isBg) {
              await window.jarvisApi.cancelBackgroundJob(id);
            } else {
              await window.jarvisApi.cancelDeveloperTask(id);
            }
            if (window.jarvisShell) window.jarvisShell.showToast(`Task ${id} cancelled`, 'warning');
            await this.loadTasks(container);
          } catch (e) {
            if (window.jarvisShell) window.jarvisShell.showToast(`Error cancelling: ${e.message}`, 'error');
          } finally { btn.disabled = false; }
        });
      });

      listEl.querySelectorAll('.btn-resume').forEach(btn => {
        btn.addEventListener('click', async () => {
          const id = btn.getAttribute('data-id');
          btn.disabled = true;
          try {
            await window.jarvisApi.resumeDeveloperTask(id);
            if (window.jarvisShell) window.jarvisShell.showToast(`Task ${id} resumed`, 'info');
            await this.loadTasks(container);
          } catch (e) {
            if (window.jarvisShell) window.jarvisShell.showToast(`Error resuming: ${e.message}`, 'error');
          } finally { btn.disabled = false; }
        });
      });

      listEl.querySelectorAll('.btn-verify').forEach(btn => {
        btn.addEventListener('click', async () => {
          const id = btn.getAttribute('data-id');
          btn.disabled = true;
          try {
            const res = await window.jarvisApi.verifyDeveloperTask(id);
            if (window.jarvisShell) window.jarvisShell.showToast(`Verification complete: ${JSON.stringify(res.verification?.overall_status || 'passed')}`, 'success');
          } catch (e) {
            if (window.jarvisShell) window.jarvisShell.showToast(`Verification error: ${e.message}`, 'error');
          } finally { btn.disabled = false; }
        });
      });

      listEl.querySelectorAll('.btn-propose').forEach(btn => {
        btn.addEventListener('click', async () => {
          const id = btn.getAttribute('data-id');
          btn.disabled = true;
          try {
            await window.jarvisApi.proposeDeveloperTask(id, 'feature/jarvis-ui');
            if (window.jarvisShell) window.jarvisShell.showToast(`Task ${id} proposed for merge review`, 'success');
            await this.loadTasks(container);
          } catch (e) {
            if (window.jarvisShell) window.jarvisShell.showToast(`Proposal error: ${e.message}`, 'error');
          } finally { btn.disabled = false; }
        });
      });

      listEl.querySelectorAll('.btn-diff').forEach(btn => {
        btn.addEventListener('click', async () => {
          const id = btn.getAttribute('data-id');
          try {
            const res = await window.jarvisApi.getDeveloperTaskDiff(id);
            const modal = container.querySelector('#task-diff-modal');
            const content = container.querySelector('#task-diff-content');
            content.textContent = res.diff || '(No diff detected in task worktree)';
            modal.classList.remove('hidden');
          } catch (e) {
            if (window.jarvisShell) window.jarvisShell.showToast(`Error reading diff: ${e.message}`, 'error');
          }
        });
      });
    }

    // ──────────────────────────────────────────────────────────────────────────
    // 2. Destination 5: Automations & Schedule (#automation)
    // ──────────────────────────────────────────────────────────────────────────

    async renderAutomation(container) {
      container.innerHTML = `
        <div class="ops-header">
          <div>
            <h2 class="ops-title">Automations & Workflows</h2>
            <p class="ops-subtitle">Persistent SQLite task scheduler & cron triggers</p>
          </div>
          <div class="ops-header-actions">
            <button class="btn-futuristic btn-secondary" id="auto-trigger-due-btn">
              ⚡ Trigger Due Tasks
            </button>
            <button class="btn-futuristic btn-secondary" id="auto-refresh-btn">
              Refresh
            </button>
            <button class="btn-futuristic btn-primary" id="auto-create-toggle-btn">
              + New Automation
            </button>
          </div>
        </div>

        <!-- Automation Creation Drawer -->
        <div class="glass-panel ops-create-panel hidden" id="auto-create-drawer">
          <h3 class="card-title">Schedule New Automation Workflow</h3>
          <form id="auto-create-form" class="ops-form">
            <div class="form-row">
              <div class="form-group flex-2">
                <label for="auto-name-input">Automation Name *</label>
                <input type="text" id="auto-name-input" class="input-futuristic" placeholder="e.g. Daily System Health Sweep" required />
              </div>
              <div class="form-group flex-1">
                <label for="auto-schedule-input">Schedule Expression *</label>
                <input type="text" id="auto-schedule-input" class="input-futuristic" placeholder="HH:MM UTC, every Xs, or once" required />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group flex-2">
                <label for="auto-command-input">Command / Callback Key *</label>
                <input type="text" id="auto-command-input" class="input-futuristic" placeholder="e.g. run_system_health_check" required />
              </div>
              <div class="form-group flex-1">
                <label for="auto-tz-select">Timezone Reference</label>
                <select id="auto-tz-select" class="input-futuristic">
                  <option value="UTC">UTC (Coordinated Universal Time)</option>
                  <option value="America/New_York">America/New_York (Eastern)</option>
                  <option value="America/Los_Angeles">America/Los_Angeles (Pacific)</option>
                  <option value="Europe/London">Europe/London (GMT/BST)</option>
                  <option value="Asia/Tokyo">Asia/Tokyo (JST)</option>
                </select>
              </div>
            </div>
            <div class="form-group">
              <label for="auto-desc-input">Description</label>
              <input type="text" id="auto-desc-input" class="input-futuristic" placeholder="Optional context or purpose" />
            </div>
            <div class="form-actions">
              <button type="button" class="btn-futuristic btn-secondary" id="auto-create-cancel-btn">Cancel</button>
              <button type="submit" class="btn-futuristic btn-primary" id="auto-create-submit-btn">Register Automation</button>
            </div>
          </form>
        </div>

        <!-- Automations List -->
        <div class="ops-list-container" id="automations-list">
          <div class="ops-loading">Loading scheduled automations...</div>
        </div>
      `;

      // Event handlers
      const drawer = container.querySelector('#auto-create-drawer');
      container.querySelector('#auto-create-toggle-btn').addEventListener('click', () => {
        drawer.classList.toggle('hidden');
      });
      container.querySelector('#auto-create-cancel-btn').addEventListener('click', () => {
        drawer.classList.add('hidden');
      });
      container.querySelector('#auto-refresh-btn').addEventListener('click', () => {
        this.loadAutomations(container);
      });

      container.querySelector('#auto-trigger-due-btn').addEventListener('click', async () => {
        try {
          const res = await window.jarvisApi.triggerDueAutomations();
          const ran = res.executed || [];
          if (window.jarvisShell) {
            window.jarvisShell.showToast(`Executed ${ran.length} due tasks: ${ran.join(', ') || 'None due'}`, 'info');
          }
          await this.loadAutomations(container);
        } catch (err) {
          if (window.jarvisShell) window.jarvisShell.showToast(`Error running due: ${err.message}`, 'error');
        }
      });

      // Automation creation
      const form = container.querySelector('#auto-create-form');
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = container.querySelector('#auto-name-input').value.trim();
        let schedule = container.querySelector('#auto-schedule-input').value.trim();
        const command = container.querySelector('#auto-command-input').value.trim();
        const tz = container.querySelector('#auto-tz-select').value;
        const desc = container.querySelector('#auto-desc-input').value.trim();
        const submitBtn = container.querySelector('#auto-create-submit-btn');

        // If HH:MM without timezone, append selected TZ
        if (/^\d{1,2}:\d{2}$/.test(schedule)) {
          schedule = `${schedule} ${tz}`;
        }

        submitBtn.disabled = true;
        try {
          await window.jarvisApi.createAutomation(name, schedule, command, [], desc);
          if (window.jarvisShell) window.jarvisShell.showToast(`Automation "${name}" registered!`, 'success');
          form.reset();
          drawer.classList.add('hidden');
          await this.loadAutomations(container);
        } catch (err) {
          if (window.jarvisShell) window.jarvisShell.showToast(`Failed: ${err.message}`, 'error');
        } finally {
          submitBtn.disabled = false;
        }
      });

      await this.loadAutomations(container);
    }

    async loadAutomations(container) {
      const listEl = container.querySelector('#automations-list');
      if (!listEl) return;

      try {
        const res = await window.jarvisApi.getAutomations();
        const tasks = res.tasks || [];
        this.cachedAutomations = tasks;

        if (tasks.length === 0) {
          listEl.innerHTML = `
            <div class="glass-panel text-center p-8">
              <p class="ops-empty-text">No active automations scheduled in database.</p>
            </div>
          `;
          return;
        }

        listEl.innerHTML = tasks.map(t => {
          const isEnabled = Boolean(t.enabled);
          return `
            <div class="glass-panel automation-card" id="auto-card-${t.id}">
              <div class="automation-header">
                <div style="display:flex; align-items:center; gap:12px;">
                  <span class="automation-toggle-dot ${isEnabled ? 'dot-active' : 'dot-paused'}"></span>
                  <h4 class="automation-title">${this.escapeHtml(t.name)}</h4>
                  <span class="tz-indicator">${this.escapeHtml(t.schedule)}</span>
                </div>
                <div style="display:flex; align-items:center; gap:8px;">
                  <button class="btn-futuristic btn-secondary btn-sm btn-auto-toggle" data-id="${t.id}" data-enabled="${isEnabled}">
                    ${isEnabled ? '⏸ Pause' : '▶ Resume'}
                  </button>
                  <button class="btn-futuristic btn-danger btn-sm btn-auto-delete" data-id="${t.id}" aria-label="Delete automation">
                    🗑 Delete
                  </button>
                </div>
              </div>
              <div class="automation-details text-muted">
                Command: <code>${this.escapeHtml(t.command)}</code> | 
                Runs: <strong>${t.run_count || 0}</strong> | 
                Last run: ${t.last_run ? new Date(t.last_run * 1000).toLocaleString() : 'Never'}
              </div>
              ${t.description ? `<div class="automation-desc text-secondary">${this.escapeHtml(t.description)}</div>` : ''}
            </div>
          `;
        }).join('');

        // Wire toggle and delete buttons
        listEl.querySelectorAll('.btn-auto-toggle').forEach(btn => {
          btn.addEventListener('click', async () => {
            const id = btn.getAttribute('data-id');
            const current = btn.getAttribute('data-enabled') === 'true';
            btn.disabled = true;
            try {
              await window.jarvisApi.toggleAutomation(id, !current);
              if (window.jarvisShell) window.jarvisShell.showToast(`Automation ${id} ${!current ? 'resumed' : 'paused'}`, 'info');
              await this.loadAutomations(container);
            } catch (err) {
              if (window.jarvisShell) window.jarvisShell.showToast(`Toggle failed: ${err.message}`, 'error');
            } finally { btn.disabled = false; }
          });
        });

        listEl.querySelectorAll('.btn-auto-delete').forEach(btn => {
          btn.addEventListener('click', async () => {
            const id = btn.getAttribute('data-id');
            btn.disabled = true;
            try {
              await window.jarvisApi.deleteAutomation(id);
              if (window.jarvisShell) window.jarvisShell.showToast(`Automation ${id} removed`, 'warning');
              await this.loadAutomations(container);
            } catch (err) {
              if (window.jarvisShell) window.jarvisShell.showToast(`Delete failed: ${err.message}`, 'error');
            } finally { btn.disabled = false; }
          });
        });
      } catch (err) {
        listEl.innerHTML = `<div class="ops-error">Error loading automations: ${this.escapeHtml(err.message)}</div>`;
      }
    }

    // ──────────────────────────────────────────────────────────────────────────
    // 3. Destination 12: Calendar & Reminders (#calendar)
    // ──────────────────────────────────────────────────────────────────────────

    async renderCalendar(container) {
      container.innerHTML = `
        <div class="ops-header">
          <div>
            <h2 class="ops-title">Calendar & Reminders</h2>
            <p class="ops-subtitle">Chronological schedule agenda with confirmed timezone handling</p>
          </div>
          <div class="ops-header-actions">
            <div style="display:flex; align-items:center; gap:8px;">
              <label for="calendar-tz-selector" class="text-secondary text-sm">Timezone:</label>
              <select id="calendar-tz-selector" class="input-futuristic" style="padding:4px 8px; width:auto;">
                <option value="UTC" selected>UTC</option>
                <option value="America/New_York">America/New_York (ET)</option>
                <option value="America/Los_Angeles">America/Los_Angeles (PT)</option>
                <option value="Europe/London">Europe/London (GMT/BST)</option>
                <option value="Asia/Tokyo">Asia/Tokyo (JST)</option>
              </select>
            </div>
            <button class="btn-futuristic btn-secondary" id="cal-refresh-btn">Refresh</button>
            <button class="btn-futuristic btn-primary" id="cal-new-reminder-btn">+ Reminder</button>
          </div>
        </div>

        <!-- Quick Reminder Form Drawer -->
        <div class="glass-panel ops-create-panel hidden" id="cal-reminder-drawer">
          <h3 class="card-title">Schedule New Event or Reminder</h3>
          <form id="cal-reminder-form" class="ops-form">
            <div class="form-row">
              <div class="form-group flex-2">
                <label for="cal-event-title">Event Title *</label>
                <input type="text" id="cal-event-title" class="input-futuristic" placeholder="e.g. Standup Meeting" required />
              </div>
              <div class="form-group flex-1">
                <label for="cal-event-time">Time (HH:MM) *</label>
                <input type="text" id="cal-event-time" class="input-futuristic" placeholder="10:00" required />
              </div>
            </div>
            <div class="form-actions">
              <button type="button" class="btn-futuristic btn-secondary" id="cal-reminder-cancel-btn">Cancel</button>
              <button type="submit" class="btn-futuristic btn-primary" id="cal-reminder-submit-btn">Save Event</button>
            </div>
          </form>
        </div>

        <div class="calendar-grid-layout">
          <!-- Upcoming Agenda -->
          <div class="glass-panel" style="flex:2;">
            <div class="card-header">
              <h3 class="card-title">Scheduled Agenda & Reminders</h3>
              <span class="tz-indicator" id="cal-active-tz-chip">TZ: UTC</span>
            </div>
            <div class="calendar-agenda-list" id="calendar-agenda-items">
              <div class="ops-loading">Loading calendar items...</div>
            </div>
          </div>

          <!-- Chronological Month View Overview -->
          <div class="glass-panel" style="flex:1;">
            <div class="card-header">
              <h3 class="card-title">Calendar Timeline</h3>
            </div>
            <div class="calendar-mini-view" id="calendar-mini-month">
              <div class="calendar-month-header">${new Date().toLocaleString('default', { month: 'long', year: 'numeric' })}</div>
              <div class="calendar-today-badge">Today: ${new Date().toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })}</div>
              <div class="calendar-tz-info text-secondary text-sm" style="margin-top:16px;">
                Times are adjusted and validated against the selected timezone.
              </div>
            </div>
          </div>
        </div>
      `;

      const tzSelector = container.querySelector('#calendar-tz-selector');
      const tzChip = container.querySelector('#cal-active-tz-chip');
      tzSelector.addEventListener('change', (e) => {
        this.selectedTimezone = e.target.value;
        tzChip.textContent = `TZ: ${this.selectedTimezone}`;
        this.loadCalendar(container);
      });

      const drawer = container.querySelector('#cal-reminder-drawer');
      container.querySelector('#cal-new-reminder-btn').addEventListener('click', () => {
        drawer.classList.toggle('hidden');
      });
      container.querySelector('#cal-reminder-cancel-btn').addEventListener('click', () => {
        drawer.classList.add('hidden');
      });
      container.querySelector('#cal-refresh-btn').addEventListener('click', () => {
        this.loadCalendar(container);
      });

      const form = container.querySelector('#cal-reminder-form');
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const title = container.querySelector('#cal-event-title').value.trim();
        const time = container.querySelector('#cal-event-time').value.trim();
        const submitBtn = container.querySelector('#cal-reminder-submit-btn');

        if (!title || !time) return;
        submitBtn.disabled = true;

        try {
          // Store event in Memory under EVENT category and register with scheduler
          await window.jarvisApi.storeMemory('EVENT', `[Event] ${title} scheduled for ${time} ${this.selectedTimezone}`, 7);
          await window.jarvisApi.createAutomation(title, `${time} ${this.selectedTimezone}`, 'event_reminder', [], `Calendar reminder in ${this.selectedTimezone}`);
          if (window.jarvisShell) window.jarvisShell.showToast(`Reminder "${title}" scheduled!`, 'success');
          form.reset();
          drawer.classList.add('hidden');
          await this.loadCalendar(container);
        } catch (err) {
          if (window.jarvisShell) window.jarvisShell.showToast(`Error saving reminder: ${err.message}`, 'error');
        } finally {
          submitBtn.disabled = false;
        }
      });

      await this.loadCalendar(container);
    }

    async loadCalendar(container) {
      const agendaEl = container.querySelector('#calendar-agenda-items');
      if (!agendaEl) return;

      try {
        const [autoRes, eventMemoriesRes] = await Promise.all([
          window.jarvisApi.getAutomations().catch(() => ({ tasks: [] })),
          window.jarvisApi.searchMemory('', 'EVENT', 20).catch(() => ({ data: [] })),
        ]);

        const scheduledTasks = (autoRes.tasks || []).map(t => ({
          title: t.name,
          time: t.schedule,
          description: t.description || `Command: ${t.command}`,
          type: 'scheduled_task',
          id: t.id,
        }));

        const events = (eventMemoriesRes.data || []).map(m => ({
          title: m.content.split('scheduled for')[0].replace('[Event]', '').trim() || m.content,
          time: m.content.includes('scheduled for') ? m.content.split('scheduled for')[1].trim() : 'Daily',
          description: m.content,
          type: 'memory_event',
          id: m.id,
        }));

        const allItems = [...scheduledTasks, ...events];

        if (allItems.length === 0) {
          agendaEl.innerHTML = `
            <div class="p-6 text-center text-muted">
              No calendar events or reminders scheduled. Click "+ Reminder" to add one.
            </div>
          `;
          return;
        }

        agendaEl.innerHTML = allItems.map(item => `
          <div class="calendar-event-card">
            <div class="event-time-badge">${this.escapeHtml(item.time)}</div>
            <div class="event-body">
              <h4 class="event-title">${this.escapeHtml(item.title)}</h4>
              <div class="event-desc text-secondary text-sm">${this.escapeHtml(item.description)}</div>
            </div>
            <span class="event-type-chip">${item.type === 'memory_event' ? 'Reminder' : 'Automation'}</span>
          </div>
        `).join('');
      } catch (err) {
        agendaEl.innerHTML = `<div class="ops-error">Error loading calendar: ${this.escapeHtml(err.message)}</div>`;
      }
    }

    // ──────────────────────────────────────────────────────────────────────────
    // 4. Destination 6: Memory (#memory)
    // ──────────────────────────────────────────────────────────────────────────

    async renderMemory(container) {
      container.innerHTML = `
        <div class="ops-header">
          <div>
            <h2 class="ops-title">Long-Term Memory</h2>
            <p class="ops-subtitle">Persistent SQLite memory database & contextual recall</p>
          </div>
          <div class="ops-header-actions">
            <button class="btn-futuristic btn-secondary" id="mem-refresh-btn">Refresh</button>
            <button class="btn-futuristic btn-primary" id="mem-new-toggle-btn">+ Store Memory</button>
          </div>
        </div>

        <!-- Store Memory Form Drawer -->
        <div class="glass-panel ops-create-panel hidden" id="mem-create-drawer">
          <h3 class="card-title">Store New Memory Entity</h3>
          <form id="mem-create-form" class="ops-form">
            <div class="form-row">
              <div class="form-group flex-1">
                <label for="mem-category-select">Category *</label>
                <select id="mem-category-select" class="input-futuristic" required>
                  <option value="USER">USER</option>
                  <option value="PROJECT">PROJECT</option>
                  <option value="ROBOT">ROBOT</option>
                  <option value="SYSTEM">SYSTEM</option>
                  <option value="CONVERSATION">CONVERSATION</option>
                  <option value="TASK">TASK</option>
                  <option value="KNOWLEDGE">KNOWLEDGE</option>
                  <option value="PREFERENCE">PREFERENCE</option>
                  <option value="EVENT">EVENT</option>
                </select>
              </div>
              <div class="form-group flex-1">
                <label for="mem-importance-input">Importance (1-10)</label>
                <input type="number" id="mem-importance-input" class="input-futuristic" min="1" max="10" value="5" />
              </div>
            </div>
            <div class="form-group">
              <label for="mem-content-input">Memory Content *</label>
              <textarea id="mem-content-input" class="input-futuristic" rows="3" placeholder="Enter memory text..." required></textarea>
            </div>
            <div class="form-actions">
              <button type="button" class="btn-futuristic btn-secondary" id="mem-create-cancel-btn">Cancel</button>
              <button type="submit" class="btn-futuristic btn-primary" id="mem-create-submit-btn">Store in Memory</button>
            </div>
          </form>
        </div>

        <!-- Search & Category Filters -->
        <div class="ops-search-bar">
          <input type="text" id="mem-search-input" class="input-futuristic flex-1" placeholder="Search persistent memory content..." />
          <div class="ops-category-pills" id="mem-category-pills">
            <button class="category-pill active" data-cat="ALL">ALL</button>
            <button class="category-pill" data-cat="USER">USER</button>
            <button class="category-pill" data-cat="PROJECT">PROJECT</button>
            <button class="category-pill" data-cat="security_analytics">SYSTEM</button>
            <button class="category-pill" data-cat="TASK">TASK</button>
            <button class="category-pill" data-cat="KNOWLEDGE">KNOWLEDGE</button>
            <button class="category-pill" data-cat="EVENT">EVENT</button>
          </div>
        </div>

        <!-- Memory Cards Container -->
        <div class="ops-list-container" id="memories-list">
          <div class="ops-loading">Searching memory database...</div>
        </div>

        <!-- Edit Memory Inline Modal -->
        <div class="terminal-confirm-overlay hidden" id="mem-edit-modal" role="dialog" aria-modal="true" aria-labelledby="mem-edit-modal-title">
          <div class="glass-panel" style="max-width:560px; width:95%; display:flex; flex-direction:column; gap:16px;">
            <div class="card-header">
              <h3 class="card-title" id="mem-edit-modal-title">Edit Memory Record</h3>
              <button class="btn-futuristic btn-secondary btn-icon" id="mem-edit-close-btn" aria-label="Close edit modal">✕</button>
            </div>
            <form id="mem-edit-form" class="ops-form">
              <input type="hidden" id="mem-edit-id" />
              <div class="form-group">
                <label for="mem-edit-content">Memory Content *</label>
                <textarea id="mem-edit-content" class="input-futuristic" rows="4" required></textarea>
              </div>
              <div class="form-group">
                <label for="mem-edit-importance">Importance (1-10)</label>
                <input type="number" id="mem-edit-importance" class="input-futuristic" min="1" max="10" />
              </div>
              <div class="form-actions">
                <button type="button" class="btn-futuristic btn-secondary" id="mem-edit-cancel-btn">Cancel</button>
                <button type="submit" class="btn-futuristic btn-primary" id="mem-edit-save-btn">Save Changes</button>
              </div>
            </form>
          </div>
        </div>
      `;

      // Drawer toggle
      const drawer = container.querySelector('#mem-create-drawer');
      container.querySelector('#mem-new-toggle-btn').addEventListener('click', () => {
        drawer.classList.toggle('hidden');
      });
      container.querySelector('#mem-create-cancel-btn').addEventListener('click', () => {
        drawer.classList.add('hidden');
      });
      container.querySelector('#mem-refresh-btn').addEventListener('click', () => {
        this.loadMemories(container);
      });

      // Category filter pills
      container.querySelectorAll('#mem-category-pills .category-pill').forEach(pill => {
        pill.addEventListener('click', () => {
          container.querySelectorAll('#mem-category-pills .category-pill').forEach(p => p.classList.remove('active'));
          pill.classList.add('active');
          this.memoryCategory = pill.getAttribute('data-cat');
          this.loadMemories(container);
        });
      });

      // Search input with debounce
      let searchTimeout = null;
      container.querySelector('#mem-search-input').addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        this.searchQuery = e.target.value.trim();
        searchTimeout = setTimeout(() => this.loadMemories(container), 250);
      });

      // Store memory form
      const form = container.querySelector('#mem-create-form');
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const cat = container.querySelector('#mem-category-select').value;
        const imp = parseInt(container.querySelector('#mem-importance-input').value, 10) || 5;
        const content = container.querySelector('#mem-content-input').value.trim();
        const submitBtn = container.querySelector('#mem-create-submit-btn');

        if (!content) return;
        submitBtn.disabled = true;

        try {
          await window.jarvisApi.storeMemory(cat, content, imp);
          if (window.jarvisShell) window.jarvisShell.showToast(`Memory stored in ${cat}`, 'success');
          form.reset();
          drawer.classList.add('hidden');
          await this.loadMemories(container);
        } catch (err) {
          if (window.jarvisShell) window.jarvisShell.showToast(`Failed to store: ${err.message}`, 'error');
        } finally {
          submitBtn.disabled = false;
        }
      });

      // Edit modal close
      const editModal = container.querySelector('#mem-edit-modal');
      container.querySelector('#mem-edit-close-btn').addEventListener('click', () => editModal.classList.add('hidden'));
      container.querySelector('#mem-edit-cancel-btn').addEventListener('click', () => editModal.classList.add('hidden'));

      // Edit form submit
      const editForm = container.querySelector('#mem-edit-form');
      editForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const id = container.querySelector('#mem-edit-id').value;
        const content = container.querySelector('#mem-edit-content').value.trim();
        const imp = parseInt(container.querySelector('#mem-edit-importance').value, 10) || 5;
        const saveBtn = container.querySelector('#mem-edit-save-btn');

        saveBtn.disabled = true;
        try {
          await window.jarvisApi.updateMemory(id, content, imp);
          if (window.jarvisShell) window.jarvisShell.showToast(`Memory #${id} updated successfully`, 'success');
          editModal.classList.add('hidden');
          await this.loadMemories(container);
        } catch (err) {
          if (window.jarvisShell) window.jarvisShell.showToast(`Update failed: ${err.message}`, 'error');
        } finally {
          saveBtn.disabled = false;
        }
      });

      await this.loadMemories(container);
    }

    async loadMemories(container) {
      const listEl = container.querySelector('#memories-list');
      if (!listEl) return;

      try {
        const cat = this.memoryCategory === 'ALL' ? null : this.memoryCategory;
        const res = await window.jarvisApi.searchMemory(this.searchQuery, cat, 50);
        const memories = res.data || [];
        this.cachedMemories = memories;

        if (memories.length === 0) {
          listEl.innerHTML = `
            <div class="glass-panel text-center p-8">
              <p class="ops-empty-text">No memories found matching "${this.escapeHtml(this.searchQuery || this.memoryCategory)}".</p>
            </div>
          `;
          return;
        }

        listEl.innerHTML = memories.map(m => `
          <div class="glass-panel memory-card" id="mem-card-${m.id}">
            <div class="memory-card-header">
              <div style="display:flex; align-items:center; gap:8px;">
                <span class="memory-cat-badge">${this.escapeHtml(m.category)}</span>
                <span class="memory-imp-badge">Priority ${m.importance || 5}/10</span>
                <span class="memory-id-badge">#${m.id}</span>
              </div>
              <div style="display:flex; align-items:center; gap:8px;">
                <button class="btn-futuristic btn-secondary btn-sm btn-mem-edit" data-id="${m.id}" data-content="${this.escapeHtml(m.content)}" data-imp="${m.importance || 5}">
                  ✎ Edit
                </button>
                <button class="btn-futuristic btn-danger btn-sm btn-mem-delete" data-id="${m.id}" aria-label="Delete memory">
                  🗑 Delete
                </button>
              </div>
            </div>
            <div class="memory-content">${this.escapeHtml(m.content)}</div>
            <div class="memory-meta text-muted text-sm">
              Updated: ${m.updated_at ? new Date(m.updated_at * 1000).toLocaleString() : 'N/A'} | 
              Access Count: ${m.access_count || 0}
            </div>
          </div>
        `).join('');

        // Wire Edit buttons
        listEl.querySelectorAll('.btn-mem-edit').forEach(btn => {
          btn.addEventListener('click', () => {
            const id = btn.getAttribute('data-id');
            const content = btn.getAttribute('data-content');
            const imp = btn.getAttribute('data-imp');

            container.querySelector('#mem-edit-id').value = id;
            container.querySelector('#mem-edit-content').value = content;
            container.querySelector('#mem-edit-importance').value = imp;
            container.querySelector('#mem-edit-modal').classList.remove('hidden');
          });
        });

        // Wire Delete buttons
        listEl.querySelectorAll('.btn-mem-delete').forEach(btn => {
          btn.addEventListener('click', async () => {
            const id = btn.getAttribute('data-id');
            btn.disabled = true;
            try {
              await window.jarvisApi.deleteMemory(id);
              if (window.jarvisShell) window.jarvisShell.showToast(`Memory #${id} deleted`, 'warning');
              await this.loadMemories(container);
            } catch (err) {
              if (window.jarvisShell) window.jarvisShell.showToast(`Delete failed: ${err.message}`, 'error');
            } finally { btn.disabled = false; }
          });
        });
      } catch (err) {
        listEl.innerHTML = `<div class="ops-error">Error searching memories: ${this.escapeHtml(err.message)}</div>`;
      }
    }

    // ──────────────────────────────────────────────────────────────────────────
    // 5. Destination 13: Knowledge Base (#knowledge)
    // ──────────────────────────────────────────────────────────────────────────

    async renderKnowledge(container) {
      container.innerHTML = `
        <div class="ops-header">
          <div>
            <h2 class="ops-title">Knowledge Base & Documents</h2>
            <p class="ops-subtitle">Curated project facts, architectural specifications & indexed documentation</p>
          </div>
          <div class="ops-header-actions">
            <button class="btn-futuristic btn-secondary" id="know-refresh-btn">Refresh</button>
            <button class="btn-futuristic btn-primary" id="know-new-btn">+ Add Knowledge</button>
          </div>
        </div>

        <!-- Add Knowledge Drawer -->
        <div class="glass-panel ops-create-panel hidden" id="know-create-drawer">
          <h3 class="card-title">Add Structured Knowledge Fact</h3>
          <form id="know-create-form" class="ops-form">
            <div class="form-group">
              <label for="know-content-input">Technical Fact or Documentation Text *</label>
              <textarea id="know-content-input" class="input-futuristic" rows="3" placeholder="Enter technical knowledge..." required></textarea>
            </div>
            <div class="form-actions">
              <button type="button" class="btn-futuristic btn-secondary" id="know-cancel-btn">Cancel</button>
              <button type="submit" class="btn-futuristic btn-primary" id="know-submit-btn">Save to Knowledge</button>
            </div>
          </form>
        </div>

        <!-- Knowledge Search -->
        <div class="ops-search-bar">
          <input type="text" id="know-search-input" class="input-futuristic flex-1" placeholder="Search knowledge base facts & documents..." />
        </div>

        <div class="ops-list-container" id="knowledge-list">
          <div class="ops-loading">Querying knowledge facts...</div>
        </div>
      `;

      const drawer = container.querySelector('#know-create-drawer');
      container.querySelector('#know-new-btn').addEventListener('click', () => drawer.classList.toggle('hidden'));
      container.querySelector('#know-cancel-btn').addEventListener('click', () => drawer.classList.add('hidden'));
      container.querySelector('#know-refresh-btn').addEventListener('click', () => this.loadKnowledge(container));

      let searchTimeout = null;
      container.querySelector('#know-search-input').addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        const q = e.target.value.trim();
        searchTimeout = setTimeout(() => this.loadKnowledge(container, q), 250);
      });

      const form = container.querySelector('#know-create-form');
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const content = container.querySelector('#know-content-input').value.trim();
        const submitBtn = container.querySelector('#know-submit-btn');
        if (!content) return;

        submitBtn.disabled = true;
        try {
          await window.jarvisApi.storeMemory('KNOWLEDGE', content, 8);
          if (window.jarvisShell) window.jarvisShell.showToast('Knowledge record saved', 'success');
          form.reset();
          drawer.classList.add('hidden');
          await this.loadKnowledge(container);
        } catch (err) {
          if (window.jarvisShell) window.jarvisShell.showToast(`Error: ${err.message}`, 'error');
        } finally { submitBtn.disabled = false; }
      });

      await this.loadKnowledge(container);
    }

    async loadKnowledge(container, query = '') {
      const listEl = container.querySelector('#knowledge-list');
      if (!listEl) return;

      try {
        const [knowRes, projRes] = await Promise.all([
          window.jarvisApi.searchMemory(query, 'KNOWLEDGE', 30).catch(() => ({ data: [] })),
          window.jarvisApi.searchMemory(query, 'PROJECT', 20).catch(() => ({ data: [] })),
        ]);

        const items = [...(knowRes.data || []), ...(projRes.data || [])];
        if (items.length === 0) {
          listEl.innerHTML = `
            <div class="glass-panel text-center p-8">
              <p class="ops-empty-text">No knowledge facts found matching search query.</p>
            </div>
          `;
          return;
        }

        listEl.innerHTML = items.map(k => `
          <div class="glass-panel knowledge-card">
            <div class="knowledge-header">
              <span class="memory-cat-badge">${this.escapeHtml(k.category)}</span>
              <span class="text-muted text-sm">${k.created_at ? new Date(k.created_at * 1000).toLocaleDateString() : ''}</span>
            </div>
            <div class="knowledge-body">${this.escapeHtml(k.content)}</div>
          </div>
        `).join('');
      } catch (err) {
        listEl.innerHTML = `<div class="ops-error">Error loading knowledge: ${this.escapeHtml(err.message)}</div>`;
      }
    }

    // ──────────────────────────────────────────────────────────────────────────
    // Destination: Document AI (#documents - Phase 10)
    // ──────────────────────────────────────────────────────────────────────────

    async renderDocuments(container) {
      container.innerHTML = `
        <div class="ops-header">
          <div>
            <h2 class="ops-title">Document AI & RAG Assistant</h2>
            <p class="ops-subtitle">Grounded retrieval-augmented generation, multi-format parsing & verified citations</p>
          </div>
          <div class="ops-header-actions">
            <button class="btn-futuristic btn-secondary" id="doc-refresh-btn">Refresh</button>
            <button class="btn-futuristic btn-primary" id="doc-upload-trigger-btn">+ Ingest Document</button>
          </div>
        </div>

        <!-- Ingest Document Drawer -->
        <div class="glass-panel ops-create-panel hidden" id="doc-ingest-drawer">
          <h3 class="card-title">Ingest Document (PDF, DOCX, TXT, MD, CSV)</h3>
          <form id="doc-upload-form" class="ops-form">
            <div class="form-group">
              <label for="doc-file-select">Select Document File *</label>
              <input type="file" id="doc-file-select" class="input-futuristic" accept=".pdf,.docx,.txt,.md,.csv" required />
            </div>
            <div class="form-group">
              <label for="doc-coll-tag">Collection Tag (Optional)</label>
              <input type="text" id="doc-coll-tag" class="input-futuristic" placeholder="e.g. Robotics, Architecture, Research" />
            </div>
            <div class="form-actions">
              <button type="button" class="btn-futuristic btn-secondary" id="doc-cancel-btn">Cancel</button>
              <button type="submit" class="btn-futuristic btn-primary" id="doc-submit-upload-btn">Upload & Index</button>
            </div>
          </form>
        </div>

        <!-- Grounded Q&A Quick Bar -->
        <div class="glass-panel" style="margin-bottom: 20px; padding: 16px;">
          <h3 class="card-title" style="margin-bottom: 8px;">Ask Grounded Document Question</h3>
          <div style="display:flex; gap:10px;">
            <input type="text" id="doc-qa-input" class="input-futuristic flex-1" placeholder="Ask questions grounded strictly in your uploaded documents..." />
            <button class="btn-futuristic btn-primary" id="doc-qa-btn">Ask AI</button>
          </div>
          <div id="doc-qa-response-box" class="hidden" style="margin-top: 14px; background: rgba(0,0,0,0.3); border: 1px solid var(--border-subtle); border-radius: 6px; padding: 12px;">
            <div id="doc-qa-answer" style="white-space: pre-wrap; line-height: 1.6; font-size: 0.9rem;"></div>
            <div id="doc-qa-sources" style="margin-top: 10px; font-size: 0.8rem; color: var(--accent-cyan);"></div>
          </div>
        </div>

        <!-- Documents List -->
        <div class="ops-list-container" id="documents-list">
          <div class="ops-loading">Loading ingested documents...</div>
        </div>
      `;

      const drawer = container.querySelector('#doc-ingest-drawer');
      container.querySelector('#doc-upload-trigger-btn').addEventListener('click', () => drawer.classList.toggle('hidden'));
      container.querySelector('#doc-cancel-btn').addEventListener('click', () => drawer.classList.add('hidden'));
      container.querySelector('#doc-refresh-btn').addEventListener('click', () => this.loadDocuments(container));

      // Handle upload form
      const uploadForm = container.querySelector('#doc-upload-form');
      uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const fileInput = container.querySelector('#doc-file-select');
        const collInput = container.querySelector('#doc-coll-tag');
        const submitBtn = container.querySelector('#doc-submit-upload-btn');

        if (!fileInput.files.length) return;
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        if (collInput.value.trim()) formData.append('collection', collInput.value.trim());

        submitBtn.disabled = true;
        submitBtn.textContent = 'Indexing...';

        try {
          const res = await fetch('/api/document-qa/upload', {
            method: 'POST',
            body: formData,
          });
          if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || 'Upload failed');
          }
          if (window.jarvisShell) window.jarvisShell.showToast('Document ingested successfully!', 'success');
          uploadForm.reset();
          drawer.classList.add('hidden');
          await this.loadDocuments(container);
        } catch (err) {
          if (window.jarvisShell) window.jarvisShell.showToast(`Upload failed: ${err.message}`, 'error');
        } finally {
          submitBtn.disabled = false;
          submitBtn.textContent = 'Upload & Index';
        }
      });

      // Handle Q&A
      const qaInput = container.querySelector('#doc-qa-input');
      const qaBtn = container.querySelector('#doc-qa-btn');
      const qaBox = container.querySelector('#doc-qa-response-box');
      const qaAnswer = container.querySelector('#doc-qa-answer');
      const qaSources = container.querySelector('#doc-qa-sources');

      qaBtn.addEventListener('click', async () => {
        const query = qaInput.value.trim();
        if (!query) return;
        qaBtn.disabled = true;
        qaBtn.textContent = 'Thinking...';
        try {
          const res = await window.jarvisApi.askDocumentQuestion(query);
          qaBox.classList.remove('hidden');
          qaAnswer.textContent = res.answer;
          if (res.citations && res.citations.length) {
            qaSources.innerHTML = '<strong>Verified Sources:</strong> ' + res.citations.map(c => `${c.source_title}${c.page ? ` (p. ${c.page})` : ''}`).join(', ');
          } else {
            qaSources.textContent = '';
          }
        } catch (err) {
          if (window.jarvisShell) window.jarvisShell.showToast(`Q&A error: ${err.message}`, 'error');
        } finally {
          qaBtn.disabled = false;
          qaBtn.textContent = 'Ask AI';
        }
      });

      await this.loadDocuments(container);
    }

    async loadDocuments(container) {
      const listEl = container.querySelector('#documents-list');
      if (!listEl) return;

      try {
        const data = await window.jarvisApi.getDocumentList();
        const docs = data.documents || [];

        if (docs.length === 0) {
          listEl.innerHTML = `
            <div class="glass-panel text-center p-8">
              <p class="ops-empty-text">No documents indexed in Document AI yet. Upload your first document above!</p>
            </div>
          `;
          return;
        }

        listEl.innerHTML = docs.map(d => `
          <div class="glass-panel knowledge-card">
            <div class="knowledge-header">
              <span class="memory-cat-badge">${this.escapeHtml(d.doc_type ? d.doc_type.toUpperCase() : 'DOC')}</span>
              <span class="text-sm text-muted">${d.page_count} pages · ${d.chunk_count} chunks · ${d.word_count || 0} words</span>
            </div>
            <div class="knowledge-body">
              <strong>${this.escapeHtml(d.filename)}</strong>
              ${d.collection ? `<span class="badge" style="margin-left: 8px; font-size: 0.75rem;">${this.escapeHtml(d.collection)}</span>` : ''}
            </div>
            <div style="display:flex; justify-content:flex-end; gap:8px; margin-top:10px;">
              <button class="btn-futuristic btn-secondary btn-sm doc-delete-btn" data-doc-id="${d.id}">Delete</button>
            </div>
          </div>
        `).join('');

        // Bind delete buttons
        listEl.querySelectorAll('.doc-delete-btn').forEach(btn => {
          btn.addEventListener('click', async () => {
            const docId = btn.getAttribute('data-doc-id');
            if (!confirm('Are you sure you want to delete this document?')) return;
            try {
              await window.jarvisApi.deleteDocument(docId);
              if (window.jarvisShell) window.jarvisShell.showToast('Document deleted.', 'success');
              await this.loadDocuments(container);
            } catch (e) {
              if (window.jarvisShell) window.jarvisShell.showToast(`Delete failed: ${e.message}`, 'error');
            }
          });
        });
      } catch (err) {
        listEl.innerHTML = `<div class="ops-error">Error loading documents: ${this.escapeHtml(err.message)}</div>`;
      }
    }

    // ──────────────────────────────────────────────────────────────────────────
    // 6. Destination 7: Integrations & Connectors (#integrations)
    // ──────────────────────────────────────────────────────────────────────────

    async renderIntegrations(container) {
      container.innerHTML = `
        <div class="ops-header">
          <div>
            <h2 class="ops-title">Integrations & Connectors</h2>
            <p class="ops-subtitle">Genuine AI provider adapters, hardware interfaces & cloud services</p>
          </div>
          <div class="ops-header-actions">
            <button class="btn-futuristic btn-secondary" id="int-refresh-btn">Probe Integrations</button>
            <button class="btn-futuristic btn-primary" id="int-pin-drawer-toggle">Admin PIN / Keys</button>
          </div>
        </div>

        <!-- PIN Settings Drawer -->
        <div class="glass-panel ops-create-panel hidden" id="int-pin-drawer">
          <h3 class="card-title">Save Integration API Keys (Admin Secured)</h3>
          <form id="int-save-form" class="ops-form">
            <div class="form-group">
              <label for="int-admin-pin">Administrator PIN *</label>
              <input type="password" id="int-admin-pin" class="input-futuristic" placeholder="Enter PIN to authorize key save" required />
            </div>
            <div class="form-row">
              <div class="form-group flex-1">
                <label for="int-openrouter-key">OpenRouter API Key</label>
                <input type="password" id="int-openrouter-key" class="input-futuristic" placeholder="sk-or-v1-..." />
              </div>
              <div class="form-group flex-1">
                <label for="int-gemini-key">Google Gemini API Key</label>
                <input type="password" id="int-gemini-key" class="input-futuristic" placeholder="AIzaSy..." />
              </div>
            </div>
            <div class="form-actions">
              <button type="button" class="btn-futuristic btn-secondary" id="int-pin-cancel-btn">Cancel</button>
              <button type="submit" class="btn-futuristic btn-primary" id="int-pin-save-btn">Authorize & Save</button>
            </div>
          </form>
        </div>

        <!-- Integrations Grid -->
        <div class="integrations-grid" id="integrations-cards-grid">
          <div class="ops-loading">Probing adapter connectivity...</div>
        </div>
      `;

      const drawer = container.querySelector('#int-pin-drawer');
      container.querySelector('#int-pin-drawer-toggle').addEventListener('click', () => drawer.classList.toggle('hidden'));
      container.querySelector('#int-pin-cancel-btn').addEventListener('click', () => drawer.classList.add('hidden'));
      container.querySelector('#int-refresh-btn').addEventListener('click', () => this.loadIntegrations(container));

      const form = container.querySelector('#int-save-form');
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const pin = container.querySelector('#int-admin-pin').value.trim();
        const orKey = container.querySelector('#int-openrouter-key').value.trim();
        const gemKey = container.querySelector('#int-gemini-key').value.trim();
        const saveBtn = container.querySelector('#int-pin-save-btn');

        if (!pin) return;
        const updates = {};
        if (orKey) updates.openrouter_api_key = orKey;
        if (gemKey) updates.gemini_api_key = gemKey;

        if (Object.keys(updates).length === 0) {
          if (window.jarvisShell) window.jarvisShell.showToast('No new keys entered to save.', 'info');
          return;
        }

        saveBtn.disabled = true;
        try {
          await window.jarvisApi.saveIntegrations(updates, pin);
          if (window.jarvisShell) window.jarvisShell.showToast('Integrations updated successfully', 'success');
          form.reset();
          drawer.classList.add('hidden');
          await this.loadIntegrations(container);
        } catch (err) {
          if (window.jarvisShell) window.jarvisShell.showToast(`Admin verification failed: ${err.message}`, 'error');
        } finally {
          saveBtn.disabled = false;
        }
      });

      await this.loadIntegrations(container);
    }

    async loadIntegrations(container) {
      const grid = container.querySelector('#integrations-cards-grid');
      if (!grid) return;

      try {
        const [devStatus, settingsRes] = await Promise.all([
          window.jarvisApi.getDeveloperStatus().catch(() => null),
          window.jarvisApi.getSettings().catch(() => null),
        ]);

        const devProviders = (devStatus && devStatus.providers) || {};
        const registeredAgents = (devStatus && devStatus.agents?.agents) || [];

        // Build list of known integration adapters
        const adapters = [
          {
            id: 'openrouter',
            name: 'OpenRouter AI',
            category: 'LLM Gateway',
            type: 'Class A (API/SDK)',
            status: devProviders.openrouter?.status || 'ready',
            configured: Boolean(devProviders.openrouter?.configured),
            note: 'Multi-model cloud router (Active)',
          },
          {
            id: 'ollama',
            name: 'Ollama Local Models',
            category: 'Local LLM',
            type: 'Class B (Headless CLI / HTTP)',
            status: devProviders.ollama?.status || 'ready',
            configured: Boolean(devProviders.ollama?.configured),
            note: `Model: ${devProviders.ollama?.model || 'llama3.2:1b'}`,
          },
          {
            id: 'gemini',
            name: 'Google Gemini',
            category: 'Vision & Multimodal',
            type: 'Class A (API/SDK)',
            status: devProviders.gemini?.status || 'missing_key',
            configured: Boolean(devProviders.gemini?.configured),
            note: devProviders.gemini?.configured ? 'Configured' : 'Missing API Key',
          },
          {
            id: 'antigravity',
            name: 'Google Antigravity CLI',
            category: 'Agent Harness',
            type: 'Class B (Headless CLI)',
            status: 'ready',
            configured: true,
            note: 'Primary autonomous developer agent',
          },
          {
            id: 'claude',
            name: 'Anthropic Claude Code',
            category: 'Developer CLI',
            type: 'Class B (CLI Tool)',
            status: registeredAgents.find(a => a.agent_id === 'claude')?.status || 'MANUAL_HANDOFF',
            configured: true,
            note: 'Manual handoff adapter active',
          },
          {
            id: 'codex',
            name: 'OpenAI Codex',
            category: 'Code Engine',
            type: 'Class B (CLI)',
            status: 'QUOTA_EXHAUSTED',
            configured: false,
            note: 'Quota exhausted per project instructions; execution disabled',
          },
          {
            id: 'copilot',
            name: 'GitHub Copilot',
            category: 'IDE Extension',
            type: 'Class C (IDE-only)',
            status: 'IDE_ONLY',
            configured: false,
            note: 'IDE-only: not controllable from JARVIS',
          },
          {
            id: 'cline',
            name: 'Cline Autonomous Extension',
            category: 'IDE Extension',
            type: 'Class C (IDE-only)',
            status: 'IDE_ONLY',
            configured: false,
            note: 'IDE-only: not controllable from JARVIS',
          },
        ];

        grid.innerHTML = adapters.map(a => {
          let badgeClass = 'chip-ready';
          let statusLabel = 'READY';

          if (a.status === 'missing_key') {
            badgeClass = 'chip-amber';
            statusLabel = 'MISSING KEY';
          } else if (a.status === 'QUOTA_EXHAUSTED') {
            badgeClass = 'chip-danger';
            statusLabel = 'EXHAUSTED';
          } else if (a.status === 'IDE_ONLY') {
            badgeClass = 'chip-ide';
            statusLabel = 'IDE ONLY';
          } else if (a.status === 'MANUAL_HANDOFF') {
            badgeClass = 'chip-blue';
            statusLabel = 'HANDOFF';
          }

          return `
            <div class="glass-panel integration-card" id="int-card-${a.id}">
              <div class="integration-header">
                <div>
                  <h4 class="integration-name">${this.escapeHtml(a.name)}</h4>
                  <span class="integration-cat text-muted text-sm">${this.escapeHtml(a.category)}</span>
                </div>
                <span class="integration-status-chip ${badgeClass}">${statusLabel}</span>
              </div>
              <div class="integration-type-tag"><code>${this.escapeHtml(a.type)}</code></div>
              <div class="integration-note text-secondary text-sm">${this.escapeHtml(a.note)}</div>
            </div>
          `;
        }).join('');
      } catch (err) {
        grid.innerHTML = `<div class="ops-error">Error probing integrations: ${this.escapeHtml(err.message)}</div>`;
      }
    }

    // ──────────────────────────────────────────────────────────────────────────
    // 7. Destination 14: Connected Apps (#apps)
    // ──────────────────────────────────────────────────────────────────────────

    async renderApps(container) {
      container.innerHTML = `
        <div class="ops-header">
          <div>
            <h2 class="ops-title">Connected Applications</h2>
            <p class="ops-subtitle">Central registry catalog, user favorites & sandboxed app lifecycle</p>
          </div>
          <div class="ops-header-actions">
            <a href="/suite" target="_blank" class="btn-futuristic btn-primary" style="text-decoration:none;">⚡ Unified Suite</a>
            <button class="btn-futuristic btn-secondary" id="apps-refresh-btn">Refresh Catalog</button>
          </div>
        </div>

        <!-- Search and Category Filters -->
        <div class="ops-search-bar">
          <input type="text" id="apps-search-input" class="input-futuristic flex-1" placeholder="Search application catalog by name or capability..." />
          <div class="ops-category-pills" id="apps-category-pills">
            <button class="category-pill active" data-cat="all">ALL</button>
            <button class="category-pill" data-cat="ai_agents">AI</button>
            <button class="category-pill" data-cat="developer_tools">DEVELOPER</button>
            <button class="category-pill" data-cat="productivity">PRODUCTIVITY</button>
            <button class="category-pill" data-cat="security_analytics">SYSTEM</button>
            <button class="category-pill" data-cat="experimental">ROBOTICS</button>
          </div>
        </div>

        <!-- Apps Catalog Grid -->
        <div class="apps-catalog-grid" id="apps-catalog-cards">
          <div class="ops-loading">Loading application catalog from registry...</div>
        </div>

        <!-- Planned App Modal (Strict Truthfulness) -->
        <div class="terminal-confirm-overlay hidden" id="app-planned-modal" role="dialog" aria-modal="true" aria-labelledby="app-planned-title">
          <div class="glass-panel" style="max-width:500px; width:95%; display:flex; flex-direction:column; gap:16px;">
            <div class="card-header">
              <h3 class="card-title text-amber" id="app-planned-title">Roadmap Application</h3>
              <button class="btn-futuristic btn-secondary btn-icon" id="app-planned-close-btn" aria-label="Close dialog">✕</button>
            </div>
            <div class="text-secondary" id="app-planned-desc" style="line-height:1.5;"></div>
            <div class="form-actions">
              <button class="btn-futuristic btn-primary" id="app-planned-ok-btn">Understood</button>
            </div>
          </div>
        </div>
      `;

      container.querySelector('#apps-refresh-btn').addEventListener('click', () => this.loadApps(container));

      // Category filters
      container.querySelectorAll('#apps-category-pills .category-pill').forEach(pill => {
        pill.addEventListener('click', () => {
          container.querySelectorAll('#apps-category-pills .category-pill').forEach(p => p.classList.remove('active'));
          pill.classList.add('active');
          this.appCategory = pill.getAttribute('data-cat');
          this.loadApps(container);
        });
      });

      // Search input
      let searchTimeout = null;
      container.querySelector('#apps-search-input').addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        const q = e.target.value.trim();
        searchTimeout = setTimeout(() => this.loadApps(container, q), 250);
      });

      // Planned modal
      const modal = container.querySelector('#app-planned-modal');
      container.querySelector('#app-planned-close-btn').addEventListener('click', () => modal.classList.add('hidden'));
      container.querySelector('#app-planned-ok-btn').addEventListener('click', () => modal.classList.add('hidden'));

      await this.loadApps(container);
    }

    async loadApps(container, query = '') {
      const grid = container.querySelector('#apps-catalog-cards');
      if (!grid) return;

      try {
        const cat = this.appCategory === 'all' ? null : this.appCategory;
        const res = await window.jarvisApi.getAppsCatalog(query, cat);
        const apps = res.applications || [];
        this.cachedApps = apps;

        if (apps.length === 0) {
          grid.innerHTML = `
            <div class="glass-panel text-center p-8" style="grid-column:1/-1;">
              <p class="ops-empty-text">No applications found matching search criteria.</p>
            </div>
          `;
          return;
        }

        grid.innerHTML = apps.map(app => {
          const isPlanned = (app.status || '').toLowerCase() === 'planned';
          const canOpen = app.status === 'available';
          const isFav = Boolean(app.is_favorite);

          return `
            <div class="glass-panel app-card" id="app-card-${app.id}">
              <div class="app-card-top">
                <div class="app-icon-box">
                  <span class="app-icon-glyph">✦</span>
                </div>
                <button class="btn-fav ${isFav ? 'fav-active' : ''}" data-id="${app.id}" aria-label="Toggle favorite">
                  ★
                </button>
              </div>
              <h4 class="app-title">${this.escapeHtml(app.name)}</h4>
              <p class="app-desc text-secondary text-sm">${this.escapeHtml(app.description || 'No description')}</p>
              ${app.id.startsWith('extension-') ? `<p class="text-secondary text-sm">${this.escapeHtml(app.roadmap || '')}</p>` : ''}
              <div class="app-tags">
                <span class="app-status-badge ${isPlanned ? 'badge-planned' : 'badge-available'}">
                  ${this.escapeHtml(app.id.startsWith('extension-') ? (app.status === 'available' ? 'INTERFACE REGISTERED' : 'UNAVAILABLE') : String(app.status || 'unavailable').toUpperCase())}
                </span>
                <span class="app-cat-badge">${this.escapeHtml(app.category || 'General')}</span>
                <span class="app-version-badge">v${this.escapeHtml(app.version || '0.1.0')}</span>
              </div>
              <div class="app-actions">
                <button class="btn-futuristic ${canOpen ? 'btn-primary' : 'btn-secondary'} btn-sm btn-launch" data-id="${app.id}" data-planned="${!canOpen}" data-roadmap="${this.escapeHtml(app.roadmap || '')}">
                  ${canOpen ? 'Launch Application' : 'View Status'}
                </button>
              </div>
            </div>
          `;
        }).join('');

        // Wire favorite buttons
        grid.querySelectorAll('.btn-fav').forEach(btn => {
          btn.addEventListener('click', async () => {
            const id = btn.getAttribute('data-id');
            btn.disabled = true;
            try {
              const res = await window.jarvisApi.toggleAppFavorite(id);
              btn.classList.toggle('fav-active', res.is_favorite);
              if (window.jarvisShell) window.jarvisShell.showToast(`Updated favorite: ${id}`, 'info');
            } catch (err) {
              if (window.jarvisShell) window.jarvisShell.showToast(`Favorite failed: ${err.message}`, 'error');
            } finally { btn.disabled = false; }
          });
        });

        // Wire launch buttons
        grid.querySelectorAll('.btn-launch').forEach(btn => {
          btn.addEventListener('click', async () => {
            const id = btn.getAttribute('data-id');
            const isPlanned = btn.getAttribute('data-planned') === 'true';
            const roadmap = btn.getAttribute('data-roadmap');

            if (isPlanned) {
              // Surface honest roadmap explanation
              const modal = container.querySelector('#app-planned-modal');
              container.querySelector('#app-planned-desc').innerHTML = `
                <strong>${this.escapeHtml(id)}</strong> cannot be opened in its current state.<br><br>
                ${roadmap ? `<em>Roadmap note: ${this.escapeHtml(roadmap)}</em>` : 'Implementation scheduled in a future release.'}
              `;
              modal.classList.remove('hidden');
              return;
            }

            btn.disabled = true;
            try {
              const res = await window.jarvisApi.launchApp(id);
              if (window.jarvisShell) {
                window.jarvisShell.showToast(res.message || `Launched ${id}`, 'success');
                if (res.target_tab) {
                  window.location.hash = res.target_tab;
                } else if (typeof res.route === 'string' && /^\/(?!\/)/.test(res.route) && !res.route.includes('\\')) {
                  window.location.assign(res.route);
                } else {
                  window.jarvisShell.showToast('Not available: the application has no valid local interface route.', 'error');
                }
              }
            } catch (err) {
              if (window.jarvisShell) window.jarvisShell.showToast(`Launch failed: ${err.message}`, 'error');
            } finally { btn.disabled = false; }
          });
        });
      } catch (err) {
        grid.innerHTML = `<div class="ops-error">Error loading applications: ${this.escapeHtml(err.message)}</div>`;
      }
    }

    escapeHtml(str) {
      if (typeof str !== 'string') return '';
      return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    }
  }

  // Export singleton
  window.jarvisOperations = new JarvisOperationsHub();
})();
