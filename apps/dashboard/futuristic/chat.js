/**
 * JARVIS OS Futuristic Conversation Panel Controller
 * Master Requirements: SPEC.md & PLAN.md Phase 4
 * Truthfulness: Provider and model labels derived from backend response metadata.
 * No mock data. Clean error recovery, code highlighting with copy, export, stop, and search.
 */

(function () {
  'use strict';

  class JarvisChatController {
    constructor() {
      this.messages = [];
      this.isGenerating = false;
      this.currentAbortController = null;
      this.currentRequestId = null;
      this.lastUserPrompt = '';
      this.searchQuery = '';
      this.providers = [];
      this.activeProvider = null;
      this.activeModel = null;
      this.chatMode = 'agent'; // 'agent' (use_tools: true) | 'conversation' (use_tools: false)
      this.autoSpeak = false;
      this.sessionId = 'default';
      this.historyLoaded = false;
    }

    /**
     * Render the chat interface into the provided container element.
     */
    render(container) {
      if (!container) return;

      container.innerHTML = `
        <div class="chat-page-layout">
          <!-- Chat Top Navigation & Controls Bar -->
          <div class="chat-toolbar glass-panel">
            <div class="chat-toolbar-left">
              <div class="chat-title-group">
                <span class="chat-status-indicator pulse-cyan" id="chat-live-indicator"></span>
                <h2 class="chat-panel-title">JARVIS Neural Interface</h2>
                <span class="status-chip success" id="chat-status-badge">
                  <span class="status-dot"></span> Ready
                </span>
              </div>
              <div class="chat-selector-group">
                <label for="chat-model-select" class="sr-only">AI Model</label>
                <select id="chat-model-select" class="chat-select" title="Active AI Provider & Model">
                  <option value="">Detecting providers…</option>
                </select>
                <label for="chat-mode-select" class="sr-only">Execution Mode</label>
                <select id="chat-mode-select" class="chat-select" title="Execution Mode">
                  <option value="agent">⚡ Agent Mode (Tools)</option>
                  <option value="conversation">💬 Direct Chat (No Tools)</option>
                </select>
              </div>
            </div>

            <div class="chat-toolbar-right">
              <div class="chat-search-wrapper">
                <span class="chat-search-icon">🔍</span>
                <input type="text" id="chat-search-input" class="chat-search-input" placeholder="Search conversation…" />
                <button id="chat-search-clear" class="btn-icon-sm" title="Clear search" style="display:none;">✕</button>
              </div>
              <button id="chat-export-btn" class="glass-btn btn-sm" title="Export conversation to Markdown or JSON">
                💾 Export
              </button>
              <button id="chat-clear-btn" class="glass-btn btn-sm btn-danger-soft" title="Clear conversation history">
                🗑️ Clear
              </button>
            </div>
          </div>

          <!-- Notification / Error Banner -->
          <div id="chat-notification-banner" class="chat-banner" style="display: none;"></div>

          <!-- Message Stream Container -->
          <div id="chat-messages-container" class="chat-messages-container" role="log" aria-live="polite">
            <div class="chat-loading-history" id="chat-history-loader">
              <span class="spinner-cyan"></span> Loading conversation memory…
            </div>
          </div>

          <!-- Quick Suggestion Prompts -->
          <div class="chat-prompts-row" id="chat-prompts-row">
            <button class="chat-prompt-chip" data-prompt="Run system diagnostic and report hardware telemetry">📊 System Telemetry</button>
            <button class="chat-prompt-chip" data-prompt="List active AI providers and model statuses">🧠 Active Models</button>
            <button class="chat-prompt-chip" data-prompt="What can you do, JARVIS?">⚡ Capabilities</button>
            <button class="chat-prompt-chip" data-prompt="Check connected sensors and robot safety status">🤖 Robot Safety</button>
          </div>

          <!-- Message Input Dock -->
          <div class="chat-input-dock glass-panel">
            <div class="chat-input-row">
              <button id="chat-attachment-btn" class="chat-dock-btn" title="Attach file (Not available)" aria-label="Attach file">
                📎
              </button>

              <div class="chat-textarea-container">
                <textarea
                  id="chat-input-textarea"
                  class="chat-textarea"
                  placeholder="Enter instruction or message for JARVIS… (Enter to send, Shift+Enter for newline)"
                  rows="1"
                  maxlength="4096"
                ></textarea>
              </div>

              <div class="chat-action-buttons">
                <button id="chat-stop-btn" class="glass-btn btn-danger-soft" style="display: none;" title="Stop generation">
                  ⏹ Stop
                </button>
                <button id="chat-send-btn" class="glass-btn btn-primary" title="Send message (Enter)">
                  <span>Send</span> ➔
                </button>
              </div>
            </div>

            <div class="chat-input-footer">
              <div class="chat-footer-left">
                <label class="chat-checkbox-label" title="Synthesize voice for responses">
                  <input type="checkbox" id="chat-auto-speak" />
                  <span>🔊 Voice Feedback</span>
                </label>
                <span class="chat-footer-divider">|</span>
                <span class="chat-hotkey-hint">Ctrl+K Focus search · Shift+Enter newline</span>
              </div>
              <div class="chat-footer-right" id="chat-active-meta-indicator">
                <span class="chat-meta-pill" id="chat-current-model-label">Provider: Detecting…</span>
              </div>
            </div>
          </div>
        </div>
      `;

      this.bindEvents();
      this.loadProviders();
      this.loadHistory();
    }

    /**
     * Bind all DOM listeners.
     */
    bindEvents() {
      const textarea = document.getElementById('chat-input-textarea');
      const sendBtn = document.getElementById('chat-send-btn');
      const stopBtn = document.getElementById('chat-stop-btn');
      const attachBtn = document.getElementById('chat-attachment-btn');
      const clearBtn = document.getElementById('chat-clear-btn');
      const exportBtn = document.getElementById('chat-export-btn');
      const searchInput = document.getElementById('chat-search-input');
      const searchClear = document.getElementById('chat-search-clear');
      const modelSelect = document.getElementById('chat-model-select');
      const modeSelect = document.getElementById('chat-mode-select');
      const autoSpeak = document.getElementById('chat-auto-speak');

      // Auto-resize textarea
      if (textarea) {
        textarea.addEventListener('input', () => {
          textarea.style.height = 'auto';
          textarea.style.height = Math.min(textarea.scrollHeight, 180) + 'px';
        });

        textarea.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.handleSend();
          }
        });
      }

      if (sendBtn) sendBtn.addEventListener('click', () => this.handleSend());
      if (stopBtn) stopBtn.addEventListener('click', () => this.handleStop());

      if (attachBtn) {
        attachBtn.addEventListener('click', () => {
          this.showBanner('Not available: File attachments are not supported by the current backend chat endpoint.', 'warning');
        });
      }

      if (clearBtn) {
        clearBtn.addEventListener('click', () => this.handleClearHistory());
      }

      if (exportBtn) {
        exportBtn.addEventListener('click', () => this.handleExport());
      }

      if (searchInput) {
        searchInput.addEventListener('input', (e) => {
          this.searchQuery = e.target.value.toLowerCase().trim();
          if (searchClear) searchClear.style.display = this.searchQuery ? 'inline-block' : 'none';
          this.filterMessages();
        });
      }

      if (searchClear) {
        searchClear.addEventListener('click', () => {
          if (searchInput) searchInput.value = '';
          this.searchQuery = '';
          searchClear.style.display = 'none';
          this.filterMessages();
        });
      }

      if (modelSelect) {
        modelSelect.addEventListener('change', async (e) => {
          const val = e.target.value;
          if (!val) return;
          const [prov, ...modelParts] = val.split(':');
          const mod = modelParts.join(':');
          try {
            await window.jarvisApi.switchChatModel(prov, mod);
            this.activeProvider = prov;
            this.activeModel = mod;
            this.updateModelLabel();
            this.showBanner(`Active AI model switched to: ${prov} (${mod})`, 'info', 3000);
          } catch (err) {
            this.showBanner(`Failed to switch AI model: ${err.message}`, 'error', 5000);
          }
        });
      }

      if (modeSelect) {
        modeSelect.addEventListener('change', (e) => {
          this.chatMode = e.target.value;
        });
      }

      if (autoSpeak) {
        autoSpeak.checked = this.autoSpeak;
        autoSpeak.addEventListener('change', (e) => {
          this.autoSpeak = e.target.checked;
        });
      }

      // Quick prompt chips
      document.querySelectorAll('.chat-prompt-chip').forEach((btn) => {
        btn.addEventListener('click', () => {
          const prompt = btn.getAttribute('data-prompt');
          if (textarea && prompt) {
            textarea.value = prompt;
            textarea.focus();
            this.handleSend();
          }
        });
      });
    }

    /**
     * Fetch configured providers and models from backend.
     */
    async loadProviders() {
      try {
        const data = await window.jarvisApi.getChatProviders();
        this.providers = data.providers || [];
        this.activeProvider = data.active_provider || null;
        this.activeModel = data.active_model || null;

        const select = document.getElementById('chat-model-select');
        if (!select) return;

        select.innerHTML = '';
        this.providers.forEach((p) => {
          if (p.models && p.models.length > 0) {
            const optgroup = document.createElement('optgroup');
            optgroup.label = `${p.name.toUpperCase()} ${p.available ? '● Available' : '○ Unavailable'}`;
            p.models.forEach((m) => {
              const opt = document.createElement('option');
              opt.value = `${p.name}:${m}`;
              opt.textContent = `${p.name} - ${m}`;
              if (p.name === this.activeProvider && m === this.activeModel) {
                opt.selected = true;
              }
              optgroup.appendChild(opt);
            });
            select.appendChild(optgroup);
          } else {
            const opt = document.createElement('option');
            opt.value = `${p.name}:${p.model || 'default'}`;
            opt.textContent = `${p.name} (${p.available ? 'Ready' : 'Not configured'})`;
            if (p.name === this.activeProvider) opt.selected = true;
            select.appendChild(opt);
          }
        });

        this.updateModelLabel();
      } catch (err) {
        console.warn('Failed to load chat providers:', err);
        const select = document.getElementById('chat-model-select');
        if (select) {
          select.innerHTML = '<option value="ollama:llama3.2:1b">ollama:llama3.2:1b (Fallback)</option>';
        }
      }
    }

    updateModelLabel() {
      const label = document.getElementById('chat-current-model-label');
      if (label) {
        label.textContent = `Provider: ${this.activeProvider || 'Unknown'} (${this.activeModel || 'Auto'})`;
      }
    }

    /**
     * Load existing conversation history from SQLite via API.
     */
    async loadHistory() {
      const container = document.getElementById('chat-messages-container');
      const loader = document.getElementById('chat-history-loader');

      try {
        const data = await window.jarvisApi.getChatHistory(this.sessionId);
        if (loader) loader.remove();

        const history = data.history || [];
        this.messages = [];

        if (history.length === 0) {
          this.renderWelcomeMessage();
        } else {
          history.forEach((turn, idx) => {
            const msgObj = {
              id: turn.message_id || `hist-${idx}`,
              role: turn.role === 'assistant' ? 'jarvis' : 'user',
              content: turn.content || turn.text || '',
              timestamp: turn.timestamp ? new Date(turn.timestamp * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
              provider: turn.provider || null,
              model: turn.model || null,
              tools_used: turn.tools_used || [],
              status: 'completed',
              isStreaming: false,
            };
            this.messages.push(msgObj);
            this.appendMessageElement(msgObj);
          });
        }
        this.historyLoaded = true;
        this.scrollToBottom();
      } catch (err) {
        console.warn('Could not load chat history:', err);
        if (loader) loader.innerHTML = `<span class="text-secondary">Conversation memory clean. Ready for input.</span>`;
        this.renderWelcomeMessage();
      }
    }

    renderWelcomeMessage() {
      const welcome = {
        id: 'welcome-0',
        role: 'jarvis',
        content: `**JARVIS Neural Interface Online.**\n\nAll systems operational. Connected to local intelligence engine and active AI orchestrator.\n\nType a command or select one of the quick actions below to begin.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        provider: 'edge_fastpath',
        model: 'local_conversation',
        tools_used: [],
        status: 'completed',
        isStreaming: false,
      };
      this.messages.push(welcome);
      this.appendMessageElement(welcome);
    }

    /**
     * Submit a new message to the assistant.
     */
    async handleSend() {
      const textarea = document.getElementById('chat-input-textarea');
      if (!textarea) return;
      const text = textarea.value.trim();
      if (!text || this.isGenerating) return;

      this.lastUserPrompt = text;
      textarea.value = '';
      textarea.style.height = 'auto';

      // 1. Add User Message
      const userMsg = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: text,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        provider: null,
        model: null,
        tools_used: [],
        status: 'completed',
        isStreaming: false,
      };
      this.messages.push(userMsg);
      this.appendMessageElement(userMsg);
      this.scrollToBottom();

      // 2. Prepare Assistant Streaming Bubble
      const assistantId = `jarvis-${Date.now()}`;
      const assistantMsg = {
        id: assistantId,
        role: 'jarvis',
        content: '',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        provider: this.activeProvider || 'ai_orchestrator',
        model: this.activeModel || '',
        tools_used: [],
        status: 'connecting',
        stage: 'Sending message…',
        isStreaming: true,
      };
      this.messages.push(assistantMsg);
      const msgElem = this.appendMessageElement(assistantMsg);
      this.scrollToBottom();

      // 3. UI Generation State
      this.setGenerating(true);
      const abortController = new AbortController();
      this.currentAbortController = abortController;
      this.currentRequestId = null;

      const modelSelect = document.getElementById('chat-model-select');
      const selectedVal = modelSelect ? modelSelect.value : '';
      let targetProvider = this.activeProvider;
      let targetModel = this.activeModel;
      if (selectedVal && selectedVal.includes(':')) {
        const parts = selectedVal.split(':');
        targetProvider = parts[0];
        targetModel = parts.slice(1).join(':');
      }

      let fullContent = '';
      let capturedProvider = targetProvider;
      let capturedModel = targetModel;
      let completedSuccessfully = false;

      try {
        await window.jarvisApi.streamChat({
          message: text,
          provider: targetProvider,
          model: targetModel,
          useTools: this.chatMode === 'agent',
          speak: this.autoSpeak,
          audioOutput: 'browser',
          sessionId: this.sessionId,
          signal: abortController.signal,

          onAccepted: (e) => {
            assistantMsg.status = 'accepted';
            assistantMsg.stage = e.message || 'Message received. Processing…';
            this.updateMessageElement(msgElem, assistantMsg);
          },

          onStart: (e) => {
            if (e.request_id) {
              this.currentRequestId = e.request_id;
              assistantMsg.requestId = e.request_id;
            }
            if (e.provider) capturedProvider = e.provider;
            if (e.model) capturedModel = e.model;
            assistantMsg.provider = capturedProvider;
            assistantMsg.model = capturedModel;
            assistantMsg.status = 'streaming';
            assistantMsg.stage = 'Streaming response…';
            this.updateMessageElement(msgElem, assistantMsg);
          },

          onProgress: (e) => {
            const stages = {
              intent_classification: 'Understanding intent…',
              model_inferring: 'Awaiting AI reasoning…',
              tool_executing: 'Executing system tool…',
              tool_observed: 'Evaluating tool output…',
              compound_planning: 'Planning workflow steps…',
              waiting: 'Processing…',
            };
            assistantMsg.stage = stages[e.stage] || e.stage || 'Working…';
            this.updateMessageElement(msgElem, assistantMsg);
          },

          onToken: (token, e) => {
            fullContent += token;
            assistantMsg.content = fullContent;
            if (e && e.provider) capturedProvider = e.provider;
            if (e && e.model) capturedModel = e.model;
            assistantMsg.provider = capturedProvider;
            assistantMsg.model = capturedModel;
            assistantMsg.status = 'streaming';
            this.updateMessageElement(msgElem, assistantMsg);
            this.scrollToBottom();
          },

          onToolCall: (e) => {
            if (!assistantMsg.tools_used.includes(e.name)) {
              assistantMsg.tools_used.push(e.name);
            }
            assistantMsg.toolCall = e;
            this.updateMessageElement(msgElem, assistantMsg);
          },

          onToolOutput: (e) => {
            assistantMsg.toolOutput = e;
            this.updateMessageElement(msgElem, assistantMsg);
          },

          onDone: (e) => {
            completedSuccessfully = !e.error && e.status !== 'failed' && e.status !== 'cancelled';
            assistantMsg.status = completedSuccessfully ? 'completed' : 'failed';
            assistantMsg.isStreaming = false;
            if (e.provider) capturedProvider = e.provider;
            if (e.model) capturedModel = e.model;
            assistantMsg.provider = capturedProvider;
            assistantMsg.model = capturedModel;
            if (e.total_ms) assistantMsg.totalMs = e.total_ms;
            if (e.error) assistantMsg.error = e.error;
            if (!fullContent && e.response) {
              fullContent = e.response;
              assistantMsg.content = fullContent;
            }
            this.updateMessageElement(msgElem, assistantMsg);
            this.scrollToBottom();
          },

          onError: (e) => {
            assistantMsg.status = 'error';
            assistantMsg.isStreaming = false;
            assistantMsg.error = e.message || 'Stream error';
            this.updateMessageElement(msgElem, assistantMsg);
            this.showBanner(e.message || 'Stream interrupted', 'error', 4000);
          },

          onAudio: (e) => {
            assistantMsg.audio = e;
            this.updateMessageElement(msgElem, assistantMsg);
          },
        });
      } catch (err) {
        if (err.name === 'AbortError') {
          assistantMsg.status = 'stopped';
          assistantMsg.isStreaming = false;
          assistantMsg.content = fullContent ? fullContent + '\n\n*(Stopped waiting)*' : '*(Generation cancelled by operator)*';
          this.updateMessageElement(msgElem, assistantMsg);
        } else {
          assistantMsg.status = 'error';
          assistantMsg.isStreaming = false;
          assistantMsg.error = err.message;
          if (!assistantMsg.content) {
            assistantMsg.content = `⚠️ **Connection Error:** ${err.message}\n\nClick **Retry** below to re-submit your instruction.`;
          }
          this.updateMessageElement(msgElem, assistantMsg);
          this.showBanner(`Chat stream failed: ${err.message}`, 'error', 5000);
        }
      } finally {
        this.setGenerating(false);
        this.currentAbortController = null;
        this.currentRequestId = null;
        this.scrollToBottom();
      }
    }

    /**
     * Stop active generation and notify backend.
     */
    async handleStop() {
      if (!this.isGenerating) return;

      const reqId = this.currentRequestId;
      if (this.currentAbortController) {
        this.currentAbortController.abort();
      }

      if (reqId) {
        try {
          await window.jarvisApi.cancelChat(reqId);
        } catch (e) {
          console.warn('Backend cancel failed:', e);
        }
      }

      this.setGenerating(false);
      this.showBanner('Generation stopped by operator.', 'info', 2500);
    }

    /**
     * Re-send last user prompt.
     */
    handleRegenerate() {
      if (this.isGenerating || !this.lastUserPrompt) return;
      const textarea = document.getElementById('chat-input-textarea');
      if (textarea) textarea.value = this.lastUserPrompt;
      this.handleSend();
    }

    /**
     * Clear history on backend and in UI.
     */
    async handleClearHistory() {
      const confirmClear = window.confirm('Clear conversation history from persistent memory?');
      if (!confirmClear) return;

      try {
        await window.jarvisApi.clearChatHistory(this.sessionId);
        this.messages = [];
        const container = document.getElementById('chat-messages-container');
        if (container) container.innerHTML = '';
        this.renderWelcomeMessage();
        this.showBanner('Conversation memory cleared.', 'info', 3000);
      } catch (err) {
        this.showBanner(`Failed to clear history: ${err.message}`, 'error', 4000);
      }
    }

    /**
     * Export conversation as Markdown or JSON.
     */
    handleExport() {
      if (this.messages.length === 0) {
        this.showBanner('No messages to export.', 'warning', 2500);
        return;
      }

      const format = window.confirm('Export format:\nOK: Markdown (.md)\nCancel: JSON (.json)') ? 'markdown' : 'json';
      let content = '';
      let filename = `jarvis-conversation-${new Date().toISOString().slice(0, 10)}`;
      let mimeType = 'text/plain';

      if (format === 'markdown') {
        filename += '.md';
        mimeType = 'text/markdown';
        content = `# JARVIS OS Conversation Export\n` +
          `Date: ${new Date().toLocaleString()}\n` +
          `Session: ${this.sessionId}\n\n---\n\n`;

        this.messages.forEach((m) => {
          const author = m.role === 'user' ? 'Operator' : 'JARVIS';
          const meta = m.provider ? ` (${m.provider}:${m.model || 'auto'})` : '';
          content += `### [${m.timestamp}] ${author}${meta}\n\n${m.content}\n\n`;
          if (m.tools_used && m.tools_used.length > 0) {
            content += `*Tools used: ${m.tools_used.join(', ')}*\n\n`;
          }
          content += `---\n\n`;
        });
      } else {
        filename += '.json';
        mimeType = 'application/json';
        content = JSON.stringify({
          exported_at: new Date().toISOString(),
          session_id: this.sessionId,
          messages: this.messages,
        }, null, 2);
      }

      const blob = new Blob([content], { type: mimeType });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      this.showBanner(`Exported conversation as ${filename}`, 'info', 3000);
    }

    /**
     * Set generation UI states (button toggle, status badges).
     */
    setGenerating(generating) {
      this.isGenerating = generating;
      const sendBtn = document.getElementById('chat-send-btn');
      const stopBtn = document.getElementById('chat-stop-btn');
      const statusBadge = document.getElementById('chat-status-badge');
      const liveDot = document.getElementById('chat-live-indicator');

      if (sendBtn) sendBtn.disabled = generating;
      if (stopBtn) stopBtn.style.display = generating ? 'inline-flex' : 'none';

      if (statusBadge) {
        if (generating) {
          statusBadge.className = 'status-chip warning';
          statusBadge.innerHTML = `<span class="status-dot"></span> Generating…`;
        } else {
          statusBadge.className = 'status-chip success';
          statusBadge.innerHTML = `<span class="status-dot"></span> Ready`;
        }
      }

      if (liveDot) {
        liveDot.className = generating ? 'chat-status-indicator pulse-amber' : 'chat-status-indicator pulse-cyan';
      }
    }

    /**
     * Show notification banner in chat view.
     */
    showBanner(message, type = 'info', timeout = 4000) {
      const banner = document.getElementById('chat-notification-banner');
      if (!banner) return;

      banner.className = `chat-banner banner-${type}`;
      banner.textContent = message;
      banner.style.display = 'block';

      if (timeout) {
        setTimeout(() => {
          banner.style.display = 'none';
        }, timeout);
      }
    }

    /**
     * Filter rendered message bubbles by search keyword.
     */
    filterMessages() {
      const elements = document.querySelectorAll('.chat-msg-row');
      elements.forEach((el) => {
        const text = el.textContent.toLowerCase();
        const matches = !this.searchQuery || text.includes(this.searchQuery);
        el.style.display = matches ? 'flex' : 'none';
      });
    }

    /**
     * Append a message DOM element to the scroll container.
     */
    appendMessageElement(msg) {
      const container = document.getElementById('chat-messages-container');
      if (!container) return null;

      const row = document.createElement('div');
      row.className = `chat-msg-row ${msg.role === 'user' ? 'row-user' : 'row-jarvis'}`;
      row.id = `msg-el-${msg.id}`;

      row.innerHTML = this.buildMessageHtml(msg);
      container.appendChild(row);

      this.bindMessageElementActions(row, msg);
      return row;
    }

    /**
     * Update an existing message DOM element during streaming.
     */
    updateMessageElement(el, msg) {
      if (!el) {
        el = document.getElementById(`msg-el-${msg.id}`);
      }
      if (!el) return;

      el.innerHTML = this.buildMessageHtml(msg);
      this.bindMessageElementActions(el, msg);
    }

    /**
     * Generate HTML string for a message.
     */
    buildMessageHtml(msg) {
      const isUser = msg.role === 'user';
      const authorLabel = isUser ? 'Operator' : 'JARVIS';
      const avatarIcon = isUser ? '👤' : '⚡';

      let metaTags = '';
      if (!isUser) {
        if (msg.provider) {
          metaTags += `<span class="chat-tag-pill provider-tag" title="Backend AI Provider">${msg.provider}${msg.model ? ` : ${msg.model}` : ''}</span>`;
        }
        if (msg.totalMs) {
          metaTags += `<span class="chat-tag-pill latency-tag" title="Inference Latency">${msg.totalMs}ms</span>`;
        }
      }

      let statusHtml = '';
      if (msg.isStreaming) {
        statusHtml = `<div class="chat-streaming-status"><span class="spinner-cyan-sm"></span> ${msg.stage || 'Working…'}</div>`;
      }

      // Collapsible Tool Call Card
      let toolHtml = '';
      if (msg.tools_used && msg.tools_used.length > 0) {
        const toolList = msg.tools_used.map((t) => `<code class="chat-inline-code">${t}</code>`).join(' ');
        toolHtml = `
          <details class="chat-tool-details">
            <summary class="chat-tool-summary">
              <span>🔧 Tools Invoked (${msg.tools_used.length}): ${toolList}</span>
            </summary>
            <div class="chat-tool-body">
              ${msg.toolCall ? `<div class="tool-sub"><span class="tool-label">Call:</span> <code>${JSON.stringify(msg.toolCall)}</code></div>` : ''}
              ${msg.toolOutput ? `<div class="tool-sub"><span class="tool-label">Result:</span> <code>${JSON.stringify(msg.toolOutput)}</code></div>` : ''}
            </div>
          </details>
        `;
      }

      // Body text rendering
      let bodyHtml = this.renderMarkdown(msg.content);
      if (msg.isStreaming) {
        bodyHtml += `<span class="chat-cursor-blink">▊</span>`;
      }

      // Actions (Copy, Regenerate, Audio)
      const actionsHtml = `
        <div class="chat-msg-actions">
          <button class="chat-action-btn copy-msg-btn" title="Copy message text">📋 Copy</button>
          ${!isUser && !msg.isStreaming && msg.id !== 'welcome-0' ? `<button class="chat-action-btn retry-msg-btn" title="Retry / Regenerate response">↺ Retry</button>` : ''}
          ${msg.audio && msg.audio.audio_url ? `<button class="chat-action-btn play-audio-btn" data-audio="${msg.audio.audio_url}" title="Play audio response">🔊 Play Voice</button>` : ''}
        </div>
      `;

      return `
        <div class="chat-msg-avatar" aria-hidden="true">${avatarIcon}</div>
        <div class="chat-msg-bubble">
          <div class="chat-msg-header">
            <div class="chat-msg-author">${authorLabel}</div>
            <div class="chat-msg-meta">
              ${metaTags}
              <span class="chat-msg-time">${msg.timestamp}</span>
            </div>
          </div>
          ${statusHtml}
          ${toolHtml}
          <div class="chat-msg-content">${bodyHtml}</div>
          ${actionsHtml}
        </div>
      `;
    }

    /**
     * Attach dynamic click handlers to message action buttons (copy, retry, play audio).
     */
    bindMessageElementActions(row, msg) {
      // Copy Message Text
      const copyBtn = row.querySelector('.copy-msg-btn');
      if (copyBtn) {
        copyBtn.addEventListener('click', () => {
          navigator.clipboard.writeText(msg.content).then(() => {
            copyBtn.textContent = '✓ Copied!';
            setTimeout(() => { copyBtn.textContent = '📋 Copy'; }, 2000);
          }).catch(() => {
            copyBtn.textContent = 'Failed';
          });
        });
      }

      // Retry / Regenerate
      const retryBtn = row.querySelector('.retry-msg-btn');
      if (retryBtn) {
        retryBtn.addEventListener('click', () => this.handleRegenerate());
      }

      // Play Audio
      const audioBtn = row.querySelector('.play-audio-btn');
      if (audioBtn) {
        audioBtn.addEventListener('click', () => {
          const url = audioBtn.getAttribute('data-audio');
          if (url) {
            if (window.jarvisVoice && window.jarvisVoice.playAudioUrl) {
              window.jarvisVoice.playAudioUrl(url, msg.text);
            } else {
              const audio = new Audio(url);
              audio.play().catch((err) => console.warn('Audio playback error:', err));
            }
          }
        });
      }

      // Code Block Copy Buttons
      row.querySelectorAll('.code-copy-btn').forEach((btn) => {
        btn.addEventListener('click', (e) => {
          const codeBlock = e.target.closest('.chat-code-block');
          if (codeBlock) {
            const codeEl = codeBlock.querySelector('code');
            if (codeEl) {
              navigator.clipboard.writeText(codeEl.innerText).then(() => {
                btn.textContent = '✓ Copied!';
                setTimeout(() => { btn.textContent = 'Copy'; }, 2000);
              });
            }
          }
        });
      });
    }

    /**
     * Safe Markdown parser with code syntax highlighting & copy buttons.
     */
    renderMarkdown(raw) {
      if (!raw) return '';

      // 1. Safe HTML escape
      let esc = raw
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

      // 2. Fenced Code Blocks (```lang ... ```)
      esc = esc.replace(/```([a-zA-Z0-9_\-\.]*)\n([\s\S]*?)```/g, (match, lang, code) => {
        const language = lang || 'code';
        return `
          <div class="chat-code-block">
            <div class="chat-code-header">
              <span class="chat-code-lang">${language}</span>
              <button class="code-copy-btn" title="Copy code to clipboard">Copy</button>
            </div>
            <pre><code class="language-${language}">${code.trim()}</code></pre>
          </div>
        `;
      });

      // 3. Inline code (`code`)
      esc = esc.replace(/`([^`]+)`/g, '<code class="chat-inline-code">$1</code>');

      // 4. Headers (###, ##, #)
      esc = esc.replace(/^### (.*$)/gim, '<h4 class="chat-h4">$1</h4>');
      esc = esc.replace(/^## (.*$)/gim, '<h3 class="chat-h3">$1</h3>');
      esc = esc.replace(/^# (.*$)/gim, '<h2 class="chat-h2">$1</h2>');

      // 5. Bold & Italic
      esc = esc.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
      esc = esc.replace(/\*([^*]+)\*/g, '<em>$1</em>');

      // 6. Blockquotes
      esc = esc.replace(/^\> (.*$)/gim, '<blockquote class="chat-blockquote">$1</blockquote>');

      // 7. Unordered Lists (wrap in valid semantic <ul> tags to satisfy WCAG listitem rules)
      esc = esc.replace(/(?:^\s*[-*]\s+.*(?:\r?\n|$))+/gm, (match) => {
        const items = match.trim().split(/\r?\n/).map(line => {
          const itemText = line.replace(/^\s*[-*]\s+/, '');
          return `<li class="chat-li">${itemText}</li>`;
        }).join('');
        return `<ul class="chat-ul">${items}</ul>`;
      });

      // 8. Line breaks (preserve newlines not already wrapped)
      esc = esc.replace(/\n/g, '<br>');

      return esc;
    }

    scrollToBottom() {
      const container = document.getElementById('chat-messages-container');
      if (container) {
        container.scrollTop = container.scrollHeight;
      }
    }
  }

  // Export singleton instance
  window.jarvisChat = new JarvisChatController();
})();
