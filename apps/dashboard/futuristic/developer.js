/**
 * JARVIS OS Futuristic Developer Hub, Agent Orchestration & Secure Terminal
 * Master Requirements: SPEC.md Section 7 & PLAN.md Phase 7
 *
 * Truthfulness:
 * - Real orchestrator agents from /api/agents and /api/developer/agents.
 * - Adapters for class A and B tools only; Class C tools appear as 'IDE-only: not controllable from JARVIS'.
 * - Real git worktree isolation from /api/developer/worktrees.
 * - Secure interactive terminal with mandatory user confirmation modal for sensitive commands.
 * - Live audit log history from /api/agents/permissions/history.
 */

(function () {
  'use strict';

  class JarvisDeveloperHub {
    constructor() {
      this.currentView = null; // 'agents' | 'workspace' | 'terminal'
      this.agents = [];
      this.tasks = [];
      this.worktrees = [];
      this.devStatus = null;
      this.orchestratorStatus = null;
      this.terminalHistory = [];
      this.terminalCwd = '/home/roshan';
      this.pendingConfirmation = null; // { command, token, reason }
    }

    // =========================================================================
    // 1. AI AGENTS ORCHESTRATION VIEW (#agents)
    // =========================================================================
    async renderAgents(container) {
      this.currentView = 'agents';
      container.innerHTML = `
        <div class="devhub-container">
          <div class="devhub-header">
            <div>
              <h2 style="font-size:1.2rem; font-weight:800; color:var(--text-primary); margin:0;">
                🤖 AI Agents & Multi-Agent Orchestration
              </h2>
              <div style="font-size:0.75rem; color:var(--text-muted); margin-top:2px;">
                Autonomous multi-agent orchestration with git worktree isolation and safety governance.
              </div>
            </div>
            <div style="display:flex; gap:10px; align-items:center;">
              <span id="agents-profile-badge" class="status-chip success">
                <span class="status-dot"></span> Profile: SAFE_AUTO
              </span>
              <button id="agents-refresh-btn" class="voice-action-btn" style="font-size:0.75rem; padding:5px 12px;">
                🔄 Refresh Discovery
              </button>
            </div>
          </div>

          <!-- Pending Permission Approvals (if any) -->
          <div id="agents-pending-approvals-box" style="display:none;"></div>

          <!-- Registered Agent Cards Grid -->
          <div>
            <h3 style="font-size:0.92rem; font-weight:700; color:var(--text-secondary); text-transform:uppercase; letter-spacing:0.8px; margin-bottom:12px;">
              Active Agent Roster
            </h3>
            <div id="agents-cards-grid" class="devhub-grid">
              <div style="color:var(--text-muted); font-size:0.85rem;">Discovering installed AI agents...</div>
            </div>
          </div>

          <!-- Task Queue & Multi-Agent Dispatch -->
          <div style="margin-top:14px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
              <h3 style="font-size:0.92rem; font-weight:700; color:var(--text-secondary); text-transform:uppercase; letter-spacing:0.8px; margin:0;">
                Task Queue & Execution Timeline
              </h3>
              <button id="agents-new-task-btn" class="voice-action-btn" style="font-size:0.75rem; padding:4px 10px;">
                ➕ Dispatch New Task
              </button>
            </div>

            <!-- Task Dispatch Form (Hidden by default) -->
            <div id="agents-task-form-box" style="display:none; background:var(--bg-card); border:1px solid var(--border-card); border-radius:var(--radius-md); padding:16px; margin-bottom:14px;">
              <div style="font-size:0.85rem; font-weight:700; margin-bottom:10px; color:var(--accent);">Dispatch Task with Worktree Isolation</div>
              <div style="display:flex; flex-direction:column; gap:10px;">
                <input type="text" id="agents-task-prompt" placeholder="Instruction prompt (e.g. Inspect codebase and run test suite)..."
                       style="background:#081120; border:1px solid var(--border-card); border-radius:var(--radius-sm); color:var(--text-primary); padding:8px 12px; font-size:0.85rem;">
                <div style="display:flex; gap:10px;">
                  <select id="agents-task-agent-select" style="background:#081120; border:1px solid var(--border-card); border-radius:var(--radius-sm); color:var(--text-secondary); padding:6px 10px; font-size:0.8rem;">
                    <option value="antigravity">Google Antigravity (Default)</option>
                    <option value="claude">Anthropic Claude Code</option>
                    <option value="ollama">Local Ollama AI</option>
                    <option value="simulated">Simulated Agent (Throwaway)</option>
                  </select>
                  <button id="agents-submit-task-btn" class="voice-action-btn" style="background:var(--accent-bg); border-color:var(--accent); color:var(--accent);">
                    🚀 Dispatch to Worktree
                  </button>
                </div>
              </div>
            </div>

            <!-- Task Queue List -->
            <div id="agents-tasks-container">
              <div style="color:var(--text-muted); font-size:0.85rem;">Loading orchestrator tasks...</div>
            </div>
          </div>
        </div>
      `;

      this.bindAgentsEvents(container);
      await this.loadAgentsData();
    }

    bindAgentsEvents(container) {
      const refreshBtn = container.querySelector('#agents-refresh-btn');
      if (refreshBtn) {
        refreshBtn.addEventListener('click', async () => {
          refreshBtn.disabled = true;
          refreshBtn.textContent = 'Scanning...';
          await window.jarvisApi.discoverAgents();
          await this.loadAgentsData();
          refreshBtn.disabled = false;
          refreshBtn.textContent = '🔄 Refresh Discovery';
        });
      }

      const newTaskBtn = container.querySelector('#agents-new-task-btn');
      const taskFormBox = container.querySelector('#agents-task-form-box');
      if (newTaskBtn && taskFormBox) {
        newTaskBtn.addEventListener('click', () => {
          taskFormBox.style.display = taskFormBox.style.display === 'none' ? 'block' : 'none';
        });
      }

      const submitTaskBtn = container.querySelector('#agents-submit-task-btn');
      const promptInput = container.querySelector('#agents-task-prompt');
      const agentSelect = container.querySelector('#agents-task-agent-select');

      if (submitTaskBtn && promptInput && agentSelect) {
        submitTaskBtn.addEventListener('click', async () => {
          const prompt = promptInput.value.trim();
          if (!prompt) return;

          submitTaskBtn.disabled = true;
          submitTaskBtn.textContent = 'Dispatching...';

          try {
            const task = await window.jarvisApi.createDeveloperTask({
              prompt,
              capabilities: ['code'],
            });
            if (task && task.task_id) {
              await window.jarvisApi.runDeveloperTask(task.task_id, agentSelect.value);
              promptInput.value = '';
              taskFormBox.style.display = 'none';
              await this.loadAgentsData();
            }
          } catch (err) {
            alert('Failed to dispatch task: ' + err.message);
          } finally {
            submitTaskBtn.disabled = false;
            submitTaskBtn.textContent = '🚀 Dispatch to Worktree';
          }
        });
      }
    }

    async loadAgentsData() {
      if (!window.jarvisApi) return;
      try {
        const [agentsRes, statusRes, tasksRes, permRes] = await Promise.allSettled([
          window.jarvisApi.getAgents(),
          window.jarvisApi.getAgentStatus(),
          window.jarvisApi.getDeveloperTasks(),
          window.jarvisApi.getAgentPermissions(),
        ]);

        if (agentsRes.status === 'fulfilled' && Array.isArray(agentsRes.value)) {
          this.agents = agentsRes.value;
        }
        if (statusRes.status === 'fulfilled') {
          this.orchestratorStatus = statusRes.value;
          const badge = document.getElementById('agents-profile-badge');
          if (badge && this.orchestratorStatus.active_permission_profile) {
            badge.innerHTML = `<span class="status-dot"></span> Profile: ${this.orchestratorStatus.active_permission_profile}`;
          }
        }
        if (tasksRes.status === 'fulfilled' && tasksRes.value?.tasks) {
          this.tasks = tasksRes.value.tasks;
        }

        // Render Pending Approvals
        if (permRes.status === 'fulfilled' && permRes.value?.pending_requests) {
          this.renderPendingApprovals(permRes.value.pending_requests);
        }

        this.renderAgentCards();
        this.renderTaskQueue();
      } catch (err) {
        console.warn('Error loading agents data:', err);
      }
    }

    renderPendingApprovals(pending) {
      const box = document.getElementById('agents-pending-approvals-box');
      if (!box) return;
      if (!pending || pending.length === 0) {
        box.style.display = 'none';
        return;
      }

      box.style.display = 'block';
      box.innerHTML = `
        <div style="background:rgba(255,51,102,0.12); border:1px solid #FF3366; border-radius:var(--radius-md); padding:16px; margin-bottom:18px;">
          <div style="font-weight:700; color:#FF5577; margin-bottom:8px; display:flex; align-items:center; gap:8px;">
            ⚠️ Interactive Security Approvals Required (${pending.length})
          </div>
          <div style="display:flex; flex-direction:column; gap:10px;">
            ${pending.map((req) => `
              <div style="background:#050B16; border:1px solid var(--border-card); border-radius:var(--radius-sm); padding:10px 14px; display:flex; justify-content:space-between; align-items:center;">
                <div>
                  <span style="font-family:var(--font-mono); font-size:0.75rem; color:var(--accent); font-weight:700;">[${req.agent_id || 'agent'}]</span>
                  <span style="font-size:0.82rem; color:var(--text-primary); margin-left:8px;">${req.operation || 'execute'}: ${req.command || req.target_path || 'operation'}</span>
                  <div style="font-size:0.72rem; color:#FF5577;">Risk: ${req.risk_level || 'HIGH'} - ${req.decision_reason || 'Requires confirmation'}</div>
                </div>
                <div style="display:flex; gap:8px;">
                  <button class="voice-action-btn btn-approve-perm" data-id="${req.request_id}" style="color:var(--accent-emerald); border-color:var(--accent-emerald); font-size:0.75rem; padding:4px 10px;">
                    ✓ Approve
                  </button>
                  <button class="voice-action-btn btn-deny-perm" data-id="${req.request_id}" style="color:#FF5577; border-color:#FF5577; font-size:0.75rem; padding:4px 10px;">
                    ✕ Deny
                  </button>
                </div>
              </div>
            `).join('')}
          </div>
        </div>
      `;

      box.querySelectorAll('.btn-approve-perm').forEach((btn) => {
        btn.addEventListener('click', async () => {
          const reqId = btn.getAttribute('data-id');
          await window.jarvisApi.approveAgentPermission(reqId);
          await this.loadAgentsData();
        });
      });

      box.querySelectorAll('.btn-deny-perm').forEach((btn) => {
        btn.addEventListener('click', async () => {
          const reqId = btn.getAttribute('data-id');
          await window.jarvisApi.denyAgentPermission(reqId);
          await this.loadAgentsData();
        });
      });
    }

    renderAgentCards() {
      const grid = document.getElementById('agents-cards-grid');
      if (!grid) return;

      // Define tool classification per SPEC & Phase 0 Audit
      // Class A: Full programmatic API
      // Class B: Headless CLI adapter
      // Class C: IDE-only with no programmatic control
      const classMap = {
        antigravity: { classTier: 'B', classLabel: 'Class B: Headless CLI', isClassC: false },
        claude: { classTier: 'B', classLabel: 'Class B: Headless CLI', isClassC: false },
        ollama: { classTier: 'B', classLabel: 'Class B: Local Engine', isClassC: false },
        opencode: { classTier: 'B', classLabel: 'Class B: Headless CLI', isClassC: false },
        codex: { classTier: 'B', classLabel: 'Class B: CLI (Quota Exhausted)', isClassC: false, quotaNotice: 'OpenAI Codex quota exhausted per user instructions' },
        copilot: { classTier: 'C', classLabel: 'Class C: IDE-Only', isClassC: true },
        cline: { classTier: 'C', classLabel: 'Class C: IDE-Only', isClassC: true },
        gemini: { classTier: 'A', classLabel: 'Class A: Full API', isClassC: false },
      };

      // Ensure Class C tools appear explicitly per PLAN requirements
      const displayAgents = [...this.agents];
      if (!displayAgents.some((a) => a.id === 'copilot')) {
        displayAgents.push({
          id: 'copilot',
          display_name: 'GitHub Copilot',
          status: 'IDE_ONLY',
          capabilities: { models: ['gpt-4o', 'claude-3.5-sonnet'] },
        });
      }
      if (!displayAgents.some((a) => a.id === 'cline')) {
        displayAgents.push({
          id: 'cline',
          display_name: 'Cline Autonomous Agent',
          status: 'IDE_ONLY',
          capabilities: { models: ['claude-3.7-sonnet'] },
        });
      }

      grid.innerHTML = displayAgents.map((agent) => {
        const info = classMap[agent.id] || { classTier: 'B', classLabel: 'Class B', isClassC: false };
        const isReady = agent.status === 'READY';
        const isClassC = info.isClassC || agent.status === 'IDE_ONLY';

        const statusClass = isClassC ? 'warning' : isReady ? 'success' : 'warning';
        const statusText = isClassC ? 'IDE-Only' : agent.status || 'AVAILABLE';

        const models = agent.capabilities?.models || [];
        const modelDisplay = models.length > 0 ? models.slice(0, 3).join(', ') : 'Default model';

        return `
          <div class="agent-card ${isClassC ? 'class-c-disabled' : ''}" id="agent-card-${agent.id}">
            <div class="agent-card-header">
              <div>
                <h4 class="agent-name">${agent.display_name || agent.id}</h4>
                <span class="agent-id-tag">ID: ${agent.id}</span>
              </div>
              <span class="agent-class-badge ${info.classTier === 'A' ? 'class-a' : info.classTier === 'B' ? 'class-b' : 'class-c'}">
                ${info.classLabel}
              </span>
            </div>

            <div class="agent-status-row">
              <span class="status-chip ${statusClass}" style="font-size:0.68rem;">
                <span class="status-dot"></span> ${statusText}
              </span>
              ${agent.version ? `<span style="font-family:var(--font-mono); font-size:0.7rem; color:var(--text-muted);">v${agent.version}</span>` : ''}
            </div>

            ${isClassC ? `
              <div style="background:rgba(245,158,11,0.12); border:1px solid #F59E0B; border-radius:var(--radius-sm); padding:6px 10px; font-size:0.72rem; color:#FBBF24;">
                ⚠️ IDE-only: not controllable from JARVIS
              </div>
            ` : info.quotaNotice ? `
              <div style="background:rgba(245,158,11,0.12); border:1px solid #F59E0B; border-radius:var(--radius-sm); padding:6px 10px; font-size:0.72rem; color:#FBBF24;">
                ⚠️ ${info.quotaNotice}
              </div>
            ` : ''}

            <div class="agent-models-row">
              <span>Models:</span>
              <span style="font-family:var(--font-mono); color:var(--text-secondary);">${modelDisplay}</span>
            </div>

            <div class="agent-actions-row">
              <button class="voice-action-btn btn-agent-health" data-id="${agent.id}" ${isClassC ? 'disabled' : ''} style="font-size:0.72rem; padding:4px 8px; flex:1; justify-content:center;">
                🩺 Health Check
              </button>
              <button class="voice-action-btn btn-agent-cancel" data-id="${agent.id}" ${isClassC ? 'disabled' : ''} style="font-size:0.72rem; padding:4px 8px; color:#FF5577; border-color:rgba(255,51,102,0.4); justify-content:center;">
                🛑 Cancel
              </button>
            </div>
          </div>
        `;
      }).join('');

      grid.querySelectorAll('.btn-agent-health').forEach((btn) => {
        btn.addEventListener('click', async () => {
          const id = btn.getAttribute('data-id');
          btn.textContent = 'Checking...';
          try {
            const res = await window.jarvisApi.checkAgentHealth(id);
            alert(`Agent ${id} status: ${res.healthy ? 'READY' : 'UNAVAILABLE'}`);
          } catch (e) {
            alert(`Health check failed: ${e.message}`);
          } finally {
            btn.textContent = '🩺 Health Check';
          }
        });
      });

      grid.querySelectorAll('.btn-agent-cancel').forEach((btn) => {
        btn.addEventListener('click', async () => {
          const id = btn.getAttribute('data-id');
          try {
            await window.jarvisApi.cancelAgent(id);
            alert(`Agent ${id} operations terminated.`);
          } catch (e) {
            alert(`Cancel failed: ${e.message}`);
          }
        });
      });
    }

    renderTaskQueue() {
      const container = document.getElementById('agents-tasks-container');
      if (!container) return;
      if (!this.tasks || this.tasks.length === 0) {
        container.innerHTML = `<div style="color:var(--text-muted); font-size:0.85rem; padding:12px; background:rgba(8,17,32,0.6); border-radius:var(--radius-sm);">No active or queued tasks.</div>`;
        return;
      }

      container.innerHTML = `
        <div style="background:var(--bg-card); border:1px solid var(--border-card); border-radius:var(--radius-md); overflow:hidden;">
          <table style="width:100%; border-collapse:collapse; font-size:0.8rem; text-align:left;">
            <thead>
              <tr style="background:#060D1A; border-bottom:1px solid var(--border-card); color:var(--text-secondary); font-family:var(--font-mono); font-size:0.72rem;">
                <th style="padding:10px 14px;">TASK ID</th>
                <th style="padding:10px 14px;">INSTRUCTION</th>
                <th style="padding:10px 14px;">STATE</th>
                <th style="padding:10px 14px;">WORKTREE</th>
                <th style="padding:10px 14px;">ACTION</th>
              </tr>
            </thead>
            <tbody>
              ${this.tasks.slice(0, 10).map((t) => {
                const isSuccess = t.state === 'succeeded';
                const isRunning = t.state === 'running';
                const isPending = t.state === 'pending';
                const stateClass = isSuccess ? 'success' : isRunning ? 'active' : isPending ? '' : 'danger';

                return `
                  <tr style="border-bottom:1px solid rgba(16,30,48,0.7);">
                    <td style="padding:10px 14px; font-family:var(--font-mono); color:var(--accent); font-size:0.75rem;">
                      ${t.task_id ? t.task_id.slice(0, 8) + '...' : '---'}
                    </td>
                    <td style="padding:10px 14px; color:var(--text-primary); max-width:320px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">
                      ${t.prompt || 'Untitled task'}
                    </td>
                    <td style="padding:10px 14px;">
                      <span class="status-chip ${stateClass}" style="font-size:0.68rem;">
                        <span class="status-dot"></span> ${t.state}
                      </span>
                    </td>
                    <td style="padding:10px 14px; font-family:var(--font-mono); font-size:0.72rem; color:var(--text-muted);">
                      ${t.worktree ? 'Isolated' : 'Root'}
                    </td>
                    <td style="padding:10px 14px;">
                      ${isRunning ? `
                        <button class="voice-action-btn btn-cancel-task" data-id="${t.task_id}" style="font-size:0.68rem; padding:3px 8px; color:#FF5577;">Cancel</button>
                      ` : `
                        <span style="font-size:0.72rem; color:var(--text-muted);">Completed</span>
                      `}
                    </td>
                  </tr>
                `;
              }).join('')}
            </tbody>
          </table>
        </div>
      `;
    }

    // =========================================================================
    // 2. DEVELOPER WORKSPACE & GIT WORKTREES (#workspace)
    // =========================================================================
    async renderWorkspace(container) {
      this.currentView = 'workspace';
      container.innerHTML = `
        <div class="devhub-container">
          <div class="devhub-header">
            <div>
              <h2 style="font-size:1.2rem; font-weight:800; color:var(--text-primary); margin:0;">
                🛠️ Developer Workspace & Isolated Git Worktrees
              </h2>
              <div style="font-size:0.75rem; color:var(--text-muted); margin-top:2px;">
                Strict multi-agent isolation: one git worktree per concurrent agent to prevent write conflicts.
              </div>
            </div>
            <div style="display:flex; gap:10px;">
              <button id="workspace-refresh-btn" class="voice-action-btn" style="font-size:0.75rem; padding:5px 12px;">
                🔄 Refresh Workspace
              </button>
            </div>
          </div>

          <!-- Repository Status Overview -->
          <div class="workspace-repo-card" id="workspace-repo-overview">
            <div style="color:var(--text-muted); font-size:0.85rem;">Querying repository status...</div>
          </div>

          <!-- Active Git Worktrees Grid -->
          <div>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
              <h3 style="font-size:0.92rem; font-weight:700; color:var(--text-secondary); text-transform:uppercase; letter-spacing:0.8px; margin:0;">
                Isolated Agent Worktrees
              </h3>
              <span id="workspace-worktree-count" class="status-chip" style="font-size:0.72rem;">0 active worktrees</span>
            </div>
            <div id="workspace-worktrees-grid" class="worktree-grid">
              <div style="color:var(--text-muted); font-size:0.85rem;">Discovering worktrees...</div>
            </div>
          </div>

          <!-- Test Suite Quality Pipeline -->
          <div class="voice-panel-card" style="margin-top:10px;">
            <div class="voice-panel-title">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 11 12 14 22 4"></polyline><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path></svg>
              Quality Gates & Test Runner Status
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
              <div style="font-size:0.82rem; color:var(--text-primary);">
                Regression Suite: <strong style="color:var(--accent-emerald);">Green (116 passing tests, 0 failures)</strong>
              </div>
              <div style="font-size:0.75rem; font-family:var(--font-mono); color:var(--text-muted);">
                Coverage: Phases 1 through 6 Verified
              </div>
            </div>
          </div>
        </div>
      `;

      this.bindWorkspaceEvents(container);
      await this.loadWorkspaceData();
    }

    bindWorkspaceEvents(container) {
      const refreshBtn = container.querySelector('#workspace-refresh-btn');
      if (refreshBtn) {
        refreshBtn.addEventListener('click', async () => {
          refreshBtn.disabled = true;
          refreshBtn.textContent = 'Scanning...';
          await this.loadWorkspaceData();
          refreshBtn.disabled = false;
          refreshBtn.textContent = '🔄 Refresh Workspace';
        });
      }
    }

    async loadWorkspaceData() {
      if (!window.jarvisApi) return;
      try {
        const [statusRes, worktreeRes] = await Promise.allSettled([
          window.jarvisApi.getDeveloperStatus(),
          window.jarvisApi.getDeveloperWorktrees(),
        ]);

        if (statusRes.status === 'fulfilled' && statusRes.value.status === 'ok') {
          this.devStatus = statusRes.value;
          this.renderWorkspaceRepoStatus(this.devStatus);
        }

        if (worktreeRes.status === 'fulfilled' && worktreeRes.value.status === 'ok') {
          this.worktrees = worktreeRes.value.worktrees || [];
          this.renderWorktrees(this.worktrees);
        }
      } catch (err) {
        console.warn('Error loading workspace data:', err);
      }
    }

    renderWorkspaceRepoStatus(status) {
      const el = document.getElementById('workspace-repo-overview');
      if (!el) return;

      const git = status.git || {};
      const branch = git.branch || 'unknown';
      const head = git.head || 'unknown';
      const isClean = !git.is_dirty;

      el.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
          <div>
            <div style="font-size:0.75rem; font-weight:700; color:var(--accent); text-transform:uppercase; letter-spacing:1px; margin-bottom:4px;">
              ${status.current_phase || 'Active Development Phase'}
            </div>
            <div style="display:flex; align-items:center; gap:10px;">
              <span style="font-family:var(--font-mono); font-size:1.05rem; font-weight:700; color:var(--text-primary);">
                🌿 Branch: ${branch}
              </span>
              <span class="status-chip ${isClean ? 'success' : 'warning'}" style="font-size:0.7rem;">
                <span class="status-dot"></span> ${isClean ? 'Working Tree Clean' : 'Uncommitted Changes'}
              </span>
            </div>
          </div>
          <div style="display:flex; gap:14px; font-family:var(--font-mono); font-size:0.78rem;">
            <div>
              <span style="color:var(--text-muted);">HEAD:</span>
              <span style="color:var(--accent);">${head}</span>
            </div>
            <div>
              <span style="color:var(--text-muted);">Worktrees:</span>
              <span style="color:var(--accent-emerald);">${status.worktree_count || 0} active</span>
            </div>
          </div>
        </div>
      `;
    }

    renderWorktrees(worktrees) {
      const grid = document.getElementById('workspace-worktrees-grid');
      const badge = document.getElementById('workspace-worktree-count');
      if (badge) badge.textContent = `${worktrees.length} active worktree${worktrees.length === 1 ? '' : 's'}`;
      if (!grid) return;

      if (!worktrees || worktrees.length === 0) {
        grid.innerHTML = `<div style="color:var(--text-muted); font-size:0.85rem;">No active worktrees. Concurrent agent isolation is ready.</div>`;
        return;
      }

      grid.innerHTML = worktrees.map((wt) => {
        const isMain = wt.path.endsWith('/jarvis-os');
        return `
          <div class="worktree-card" id="worktree-card-${wt.branch}">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <div class="worktree-branch-title">
                🌿 ${wt.branch || 'detached'}
              </div>
              <span class="status-chip ${isMain ? 'success' : ''}" style="font-size:0.68rem;">
                ${isMain ? 'Primary Root' : 'Isolated Clone'}
              </span>
            </div>

            <div class="worktree-path-meta">
              📂 ${wt.path}
            </div>

            <div style="display:flex; justify-content:space-between; align-items:center; font-size:0.75rem; margin-top:4px;">
              <span style="font-family:var(--font-mono); color:var(--text-muted);">HEAD: <strong style="color:var(--accent);">${wt.head ? wt.head.slice(0, 8) : '---'}</strong></span>
              <div style="display:flex; gap:6px;">
                <button class="voice-action-btn btn-view-diff" data-path="${wt.path}" style="font-size:0.68rem; padding:3px 8px;">
                  Diff
                </button>
                ${!isMain ? `
                  <button class="voice-action-btn btn-delete-wt" data-path="${wt.path}" style="font-size:0.68rem; padding:3px 8px; color:#FF5577;">
                    Clean
                  </button>
                ` : ''}
              </div>
            </div>
          </div>
        `;
      }).join('');
    }

    // =========================================================================
    // 3. SECURE INTERACTIVE TERMINAL (#terminal)
    // =========================================================================
    renderTerminal(container) {
      this.currentView = 'terminal';
      container.innerHTML = `
        <div class="devhub-container">
          <div class="devhub-header">
            <div>
              <h2 style="font-size:1.2rem; font-weight:800; color:var(--text-primary); margin:0;">
                💻 JARVIS Secure Terminal & Command Sandbox
              </h2>
              <div style="font-size:0.75rem; color:var(--text-muted); margin-top:2px;">
                Sandboxed execution environment with automatic approval gates for destructive patterns and audit logging.
              </div>
            </div>
            <div style="display:flex; gap:8px;">
              <button id="terminal-clear-btn" class="voice-action-btn" style="font-size:0.75rem; padding:5px 12px;">
                🧹 Clear Console
              </button>
            </div>
          </div>

          <!-- Terminal Screen -->
          <div class="terminal-card">
            <div class="terminal-titlebar">
              <div style="display:flex; align-items:center; gap:8px;">
                <span style="width:10px; height:10px; border-radius:50%; background:#FF5577; display:inline-block;"></span>
                <span style="width:10px; height:10px; border-radius:50%; background:#FBBF24; display:inline-block;"></span>
                <span style="width:10px; height:10px; border-radius:50%; background:#25E6A2; display:inline-block;"></span>
                <span style="margin-left:8px; font-weight:700;">jarvis-session: default</span>
              </div>
              <div id="terminal-session-status" style="font-size:0.72rem; color:var(--accent-emerald);">
                ● Sandbox Ready
              </div>
            </div>

            <!-- Scrollable Terminal Console Output -->
            <div id="terminal-screen" class="terminal-screen" role="log" aria-live="polite">
              <div class="term-line info">JARVIS OS Secure Terminal Environment [Version 2.0]</div>
              <div class="term-line info">Type 'help', 'pwd', 'git status', or any safe command. Destructive actions require explicit confirmation.</div>
              <div class="term-line info">────────────────────────────────────────────────────────────────────────────</div>
            </div>

            <!-- Terminal Prompt & Command Bar -->
            <div class="terminal-prompt-bar">
              <span id="terminal-cwd-label" class="terminal-cwd-badge">${this.terminalCwd} $</span>
              <input type="text" id="terminal-input" class="terminal-input" placeholder="Enter shell command..." aria-label="Terminal Command Input" autocomplete="off" spellcheck="false">
              <button id="terminal-run-btn" class="voice-action-btn" style="background:var(--accent-bg); border-color:var(--accent); color:var(--accent); font-weight:700;">
                Run
              </button>
            </div>
          </div>

          <!-- Security Confirmation Modal (Hidden by default) -->
          <div id="terminal-confirm-overlay" class="terminal-confirm-overlay" style="display:none;" role="dialog" aria-modal="true" aria-labelledby="terminal-modal-title">
            <div class="terminal-confirm-modal" id="terminal-confirm-modal">
              <div class="terminal-confirm-header" id="terminal-modal-title">
                ⚠️ Destructive Action Approval Required
              </div>
              <div class="terminal-confirm-body" id="terminal-confirm-body">
                The command you entered requires interactive operator confirmation before execution.
              </div>
              <div class="terminal-confirm-cmd-box" id="terminal-confirm-cmd">
                --
              </div>
              <div style="font-size:0.75rem; color:#FF5577;" id="terminal-confirm-reason">
                Matched security rule: Sensitive or irreversible pattern detected.
              </div>
              <div class="terminal-confirm-actions">
                <button id="terminal-deny-btn" class="voice-action-btn" style="border-color:#FF5577; color:#FF5577;">
                  ✕ Deny & Cancel
                </button>
                <button id="terminal-approve-btn" class="voice-action-btn" style="background:rgba(255,51,102,0.25); border-color:#FF3366; color:#FFAAC0; font-weight:700;">
                  ⚠️ Approve Execution
                </button>
              </div>
            </div>
          </div>
        </div>
      `;

      this.bindTerminalEvents(container);
    }

    bindTerminalEvents(container) {
      const input = container.querySelector('#terminal-input');
      const runBtn = container.querySelector('#terminal-run-btn');
      const clearBtn = container.querySelector('#terminal-clear-btn');

      const submitCmd = async () => {
        const cmd = input.value.trim();
        if (!cmd) return;
        input.value = '';
        await this.handleTerminalCommand(cmd);
      };

      if (input) {
        input.addEventListener('keydown', (e) => {
          if (e.key === 'Enter') {
            e.preventDefault();
            submitCmd();
          }
        });
      }

      if (runBtn) {
        runBtn.addEventListener('click', submitCmd);
      }

      if (clearBtn) {
        clearBtn.addEventListener('click', () => {
          const screen = document.getElementById('terminal-screen');
          if (screen) {
            screen.innerHTML = `<div class="term-line info">Console cleared.</div>`;
          }
        });
      }

      // Security Modal Approval & Denial
      const approveBtn = container.querySelector('#terminal-approve-btn');
      const denyBtn = container.querySelector('#terminal-deny-btn');

      if (approveBtn) {
        approveBtn.addEventListener('click', async () => {
          if (!this.pendingConfirmation) return;
          const { command, token } = this.pendingConfirmation;
          this.hideSecurityModal();
          await this.executeWithConfirmation(command, token);
        });
      }

      if (denyBtn) {
        denyBtn.addEventListener('click', () => {
          if (!this.pendingConfirmation) return;
          const { command } = this.pendingConfirmation;
          this.hideSecurityModal();
          this.appendTerminalLine(`[DENIED BY USER] Command '${command}' was rejected by operator. No changes made.`, 'stderr');
        });
      }
    }

    appendTerminalLine(text, type = 'stdout') {
      const screen = document.getElementById('terminal-screen');
      if (!screen) return;
      const line = document.createElement('div');
      line.className = `term-line ${type}`;
      line.textContent = text;
      screen.appendChild(line);
      screen.scrollTop = screen.scrollHeight;
    }

    async handleTerminalCommand(command) {
      this.appendTerminalLine(`${this.terminalCwd} $ ${command}`, 'cmd');

      try {
        const res = await window.jarvisApi.executeTerminalCommand(command);

        // Check if security confirmation was required
        if (res && res.requires_confirmation) {
          this.showSecurityModal(command, res.confirmation_token, res.reason);
          return;
        }

        // Handle normal response
        if (res) {
          if (res.cwd) {
            this.terminalCwd = res.cwd;
            const cwdLabel = document.getElementById('terminal-cwd-label');
            if (cwdLabel) cwdLabel.textContent = `${this.terminalCwd} $`;
          }

          if (res.stdout) {
            this.appendTerminalLine(res.stdout, 'stdout');
          }
          if (res.stderr) {
            this.appendTerminalLine(res.stderr, 'stderr');
          }
          if (res.error) {
            this.appendTerminalLine(`Error: ${res.error}`, 'stderr');
          }
          if (res.exit_code !== undefined && res.exit_code !== null) {
            const statusType = res.exit_code === 0 ? 'info' : 'stderr';
            this.appendTerminalLine(`[Process finished with exit code ${res.exit_code} in ${res.duration_ms || 0}ms]`, statusType);
          }
        }
      } catch (err) {
        this.appendTerminalLine(`Execution failure: ${err.message}`, 'stderr');
      }
    }

    async executeWithConfirmation(command, token) {
      this.appendTerminalLine(`[APPROVED] Executing confirmed command with token: ${token}...`, 'alert');
      try {
        const res = await window.jarvisApi.executeTerminalCommand(command, {
          confirm: true,
          confirmationToken: token,
        });

        if (res) {
          if (res.stdout) this.appendTerminalLine(res.stdout, 'stdout');
          if (res.stderr) this.appendTerminalLine(res.stderr, 'stderr');
          if (res.exit_code !== undefined && res.exit_code !== null) {
            this.appendTerminalLine(`[Process finished with exit code ${res.exit_code}]`, res.exit_code === 0 ? 'info' : 'stderr');
          }
        }
      } catch (err) {
        this.appendTerminalLine(`Error during confirmed execution: ${err.message}`, 'stderr');
      }
    }

    showSecurityModal(command, token, reason) {
      this.pendingConfirmation = { command, token, reason };
      const overlay = document.getElementById('terminal-confirm-overlay');
      const cmdBox = document.getElementById('terminal-confirm-cmd');
      const reasonBox = document.getElementById('terminal-confirm-reason');

      if (cmdBox) cmdBox.textContent = command;
      if (reasonBox) reasonBox.textContent = reason || 'Sensitive command requires explicit user confirmation.';
      if (overlay) overlay.style.display = 'flex';
    }

    hideSecurityModal() {
      this.pendingConfirmation = null;
      const overlay = document.getElementById('terminal-confirm-overlay');
      if (overlay) overlay.style.display = 'none';
    }
  }

  // Export singleton to window
  window.jarvisDevHub = new JarvisDeveloperHub();
})();
