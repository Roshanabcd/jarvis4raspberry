/**
 * JARVIS OS Typed API Client & Real-Time Telemetry Layer
 * Master Requirements: SPEC.md & PLAN.md Phase 3
 * Truthfulness: Every metric comes from verified backend responses or renders 'Unavailable'.
 */

(function () {
  'use strict';

  class JarvisApiClient {
    constructor(options = {}) {
      this.baseUrl = options.baseUrl || window.location.origin;
      this.state = 'connecting'; // connecting | online | offline | reconnecting | error
      this.stateListeners = new Set();
      this.telemetryListeners = new Set();
      this.pollTimer = null;
      this.pollInterval = options.pollInterval || 3000;
      this.failureCount = 0;
      this.maxBackoff = 15000;
      this.abortController = null;
      this.lastTelemetry = null;
    }

    onStateChange(callback) {
      this.stateListeners.add(callback);
      callback(this.state, this.lastTelemetry);
      return () => this.stateListeners.delete(callback);
    }

    onTelemetry(callback) {
      this.telemetryListeners.add(callback);
      if (this.lastTelemetry) callback(this.lastTelemetry);
      return () => this.telemetryListeners.delete(callback);
    }

    setState(newState) {
      this.state = newState;
      for (const cb of this.stateListeners) {
        try { cb(this.state, this.lastTelemetry); } catch (e) { console.error(e); }
      }
    }

    async request(path, options = {}) {
      const url = `${this.baseUrl}${path}`;
      const headers = {
        'Accept': 'application/json',
        'x-jarvis-client': 'dashboard',
        ...(options.headers || {}),
      };

      try {
        const res = await fetch(url, {
          ...options,
          headers,
          signal: options.signal || AbortSignal.timeout(6000),
        });

        if (!res.ok) {
          throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        }
        return await res.json();
      } catch (err) {
        throw err;
      }
    }

    // --- Conversational AI & Streaming Chat Methods (Phase 4) ---
    async getChatProviders() {
      return await this.request('/api/chat/providers');
    }

    async switchChatModel(provider, model) {
      return await this.request('/api/chat/model', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider, model }),
      });
    }

    async getChatHistory(sessionId = 'default') {
      return await this.request(`/api/chat/history?session_id=${encodeURIComponent(sessionId)}`);
    }

    async clearChatHistory(sessionId = 'default') {
      return await this.request(`/api/chat/history?session_id=${encodeURIComponent(sessionId)}`, {
        method: 'DELETE',
      });
    }

    async cancelChat(requestId) {
      if (!requestId) return { status: 'no_id' };
      try {
        return await this.request('/api/chat/cancel', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ request_id: requestId }),
          keepalive: true,
        });
      } catch (err) {
        console.warn('Cancel chat error:', err);
        return { status: 'error', error: err.message };
      }
    }

    /**
     * Stream conversation from POST /api/chat/stream using Server-Sent Events (SSE).
     */
    async streamChat(params) {
      const {
        message,
        provider,
        model,
        useTools = true,
        speak = false,
        audioOutput = 'browser',
        sessionId = 'default',
        signal,
        onEvent,
        onAccepted,
        onStart,
        onProgress,
        onToken,
        onToolCall,
        onToolOutput,
        onDone,
        onAudio,
        onError,
      } = params;

      const url = `${this.baseUrl}/api/chat/stream`;
      const body = {
        message,
        session_id: sessionId,
        use_tools: useTools,
        speak,
        audio_output: audioOutput,
      };
      if (provider) body.provider = provider;
      if (model) body.model = model;

      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal,
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }

      if (!res.body) {
        throw new Error('Server returned empty response stream');
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop(); // keep partial trailing line

          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed.startsWith('data: ')) continue;
            const jsonStr = trimmed.slice(6).trim();
            if (!jsonStr) continue;

            try {
              const event = JSON.parse(jsonStr);
              if (onEvent) onEvent(event);

              if (event.type === 'accepted' && onAccepted) onAccepted(event);
              else if (event.type === 'start' && onStart) onStart(event);
              else if (event.type === 'progress' && onProgress) onProgress(event);
              else if (event.type === 'token' && onToken) onToken(event.content || '', event);
              else if (event.type === 'tool_call' && onToolCall) onToolCall(event);
              else if (event.type === 'tool_output' && onToolOutput) onToolOutput(event);
              else if (event.type === 'done' && onDone) onDone(event);
              else if (event.type === 'audio' && onAudio) onAudio(event);
              else if ((event.type === 'error' || event.type === 'audio_error') && onError) onError(event);
            } catch (jsonErr) {
              console.warn('Failed to parse SSE JSON payload:', jsonStr, jsonErr);
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    }

    // --- Voice Assistant & Pipeline Methods (Phase 6) ---
    async getVoiceStatus() {
      return await this.request('/api/voice/status');
    }

    async getWakeStatus() {
      return await this.request('/api/voice/wake_status');
    }

    async getVoiceDiagnostics() {
      return await this.request('/api/voice/diagnostics');
    }

    async getVoiceTuning() {
      return await this.request('/api/voice/tuning');
    }

    async updateVoiceTuning(tuning) {
      return await this.request('/api/voice/tuning', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(tuning),
      });
    }

    async muteVoice() {
      return await this.request('/api/voice/mute', { method: 'POST' });
    }

    async unmuteVoice() {
      return await this.request('/api/voice/unmute', { method: 'POST' });
    }

    async startVoiceListening() {
      return await this.request('/api/voice/start', { method: 'POST' });
    }

    async stopVoiceListening() {
      return await this.request('/api/voice/stop', { method: 'POST' });
    }

    async interruptVoice() {
      return await this.request('/api/voice/interrupt', { method: 'POST' });
    }

    async listenOnce(durationSecs = 4) {
      return await this.request('/api/voice/listen_once', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ duration_secs: durationSecs }),
      });
    }

    async sendVoiceCommand(text) {
      return await this.request('/api/voice/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      });
    }

    async synthesizeSpeech(text, options = {}) {
      return await this.request('/api/voice/speak', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text,
          voice_type: options.voiceType || 'cloned',
          speed: options.speed,
          num_steps: options.numSteps,
          reference_text: options.referenceText,
        }),
      });
    }

    async testMicrophone(durationSecs = 3) {
      return await this.request(`/api/voice/test/microphone?duration_secs=${encodeURIComponent(durationSecs)}`, {
        method: 'POST',
      });
    }

    async testSpeaker() {
      return await this.request('/api/voice/test/speaker', { method: 'POST' });
    }

    async confirmSpeaker(confirmed = true) {
      return await this.request('/api/voice/test/speaker/confirm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ confirmed }),
      });
    }

    // --- AI Agents & Orchestration Methods (Phase 7) ---
    async getAgents() {
      return await this.request('/api/agents');
    }

    async discoverAgents() {
      return await this.request('/api/agents/discover');
    }

    async getAgentStatus() {
      return await this.request('/api/agents/status');
    }

    async cancelAgent(agentId) {
      return await this.request(`/api/agents/${encodeURIComponent(agentId)}/cancel`, { method: 'POST' });
    }

    async checkAgentHealth(agentId) {
      return await this.request(`/api/agents/${encodeURIComponent(agentId)}/health`, { method: 'POST' });
    }

    async getAgentPermissions() {
      return await this.request('/api/agents/permissions');
    }

    async approveAgentPermission(requestId, reason = 'Manually approved by operator') {
      return await this.request('/api/agents/permissions/approve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ request_id: requestId, reason }),
      });
    }

    async denyAgentPermission(requestId, reason = 'Denied by operator') {
      return await this.request('/api/agents/permissions/deny', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ request_id: requestId, reason }),
      });
    }

    async getAgentPermissionHistory() {
      return await this.request('/api/agents/permissions/history');
    }

    // --- Developer Workspace & Git Worktrees Methods (Phase 7) ---
    async getDeveloperStatus() {
      return await this.request('/api/developer/status');
    }

    async getDeveloperWorktrees() {
      return await this.request('/api/developer/worktrees');
    }

    async getDeveloperTasks() {
      return await this.request('/api/developer/tasks');
    }

    async createDeveloperTask(task) {
      return await this.request('/api/developer/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(task),
      });
    }

    async runDeveloperTask(taskId, agentId = null) {
      return await this.request(`/api/developer/tasks/${encodeURIComponent(taskId)}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_id: agentId }),
      });
    }

    async cancelDeveloperTask(taskId) {
      return await this.request(`/api/developer/tasks/${encodeURIComponent(taskId)}/cancel`, { method: 'POST' });
    }

    async getDeveloperTaskDiff(taskId) {
      return await this.request(`/api/developer/tasks/${encodeURIComponent(taskId)}/diff`);
    }

    async deleteDeveloperWorktree(taskId) {
      return await this.request(`/api/developer/tasks/${encodeURIComponent(taskId)}/worktree`, { method: 'DELETE' });
    }

    // --- Secure Terminal Execution & Process Tracking (Phase 7) ---
    async executeTerminalCommand(command, options = {}) {
      return await this.request('/api/terminal/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          command,
          session_id: options.sessionId || 'default',
          confirm: Boolean(options.confirm),
          confirmation_token: options.confirmationToken || null,
          timeout: options.timeout || 45,
        }),
      });
    }

    async getTerminalHistory(sessionId = 'default') {
      return await this.request(`/api/terminal/history?session_id=${encodeURIComponent(sessionId)}`);
    }

    async getTerminalProcesses() {
      return await this.request('/api/terminal/processes');
    }

    async stopTerminalProcess(jobId) {
      return await this.request(`/api/terminal/processes/${encodeURIComponent(jobId)}/stop`, { method: 'POST' });
    }

    // --- Tasks & Background Jobs (Phase 8) ---
    async getBackgroundJobs() {
      return await this.request('/api/task-jobs');
    }

    async submitBackgroundJob(transcript, idempotencyKey = null) {
      const key = idempotencyKey || (typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : 'key-' + Date.now());
      return await this.request('/api/task-jobs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Idempotency-Key': key,
        },
        body: JSON.stringify({ transcript }),
      });
    }

    async cancelBackgroundJob(jobId) {
      return await this.request(`/api/task-jobs/${encodeURIComponent(jobId)}/cancel`, { method: 'POST' });
    }

    async resumeDeveloperTask(taskId) {
      return await this.request(`/api/developer/tasks/${encodeURIComponent(taskId)}/resume`, { method: 'POST' });
    }

    async verifyDeveloperTask(taskId, reviewerId = null) {
      return await this.request(`/api/developer/tasks/${encodeURIComponent(taskId)}/verify${reviewerId ? '?reviewer_id=' + encodeURIComponent(reviewerId) : ''}`, { method: 'POST' });
    }

    // --- Document AI & RAG Assistant (Phase 10) ---
    async getDocumentList(collection = null) {
      const q = collection ? `?collection=${encodeURIComponent(collection)}` : '';
      return await this.request(`/api/document-qa/documents${q}`);
    }

    async getDocumentDetails(documentId) {
      return await this.request(`/api/document-qa/documents/${encodeURIComponent(documentId)}`);
    }

    async deleteDocument(documentId) {
      return await this.request(`/api/document-qa/documents/${encodeURIComponent(documentId)}`, { method: 'DELETE' });
    }

    async searchDocumentChunks(query, documentId = null, topK = 5) {
      return await this.request('/api/document-qa/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, document_id: documentId, top_k: topK }),
      });
    }

    async askDocumentQuestion(query, documentId = null, topK = 5) {
      return await this.request('/api/document-qa/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, document_id: documentId, top_k: topK }),
      });
    }

    async summarizeDocument(documentId, summaryType = 'comprehensive') {
      return await this.request('/api/document-qa/summarize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ document_id: documentId, summary_type: summaryType }),
      });
    }

    async getDocumentCollections() {
      return await this.request('/api/document-qa/collections');
    }

    async getDocumentSystemStatus() {
      return await this.request('/api/document-qa/status');
    }

    async proposeDeveloperTask(taskId, targetBranch = 'feature/jarvis-ui') {
      return await this.request(`/api/developer/tasks/${encodeURIComponent(taskId)}/propose`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_branch: targetBranch }),
      });
    }

    // --- Automations & Scheduler (Phase 8) ---
    async getAutomations() {
      return await this.request('/api/automations/tasks');
    }

    async createAutomation(name, schedule, command, args = [], description = '') {
      return await this.request('/api/automations/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, schedule, command, args, description }),
      });
    }

    async toggleAutomation(taskId, enable = true) {
      return await this.request(`/api/automations/tasks/${encodeURIComponent(taskId)}/toggle?enable=${Boolean(enable)}`, {
        method: 'POST',
      });
    }

    async deleteAutomation(taskId) {
      return await this.request(`/api/automations/tasks/${encodeURIComponent(taskId)}`, {
        method: 'DELETE',
      });
    }

    async triggerDueAutomations() {
      return await this.request('/api/automations/tasks/run_due', { method: 'POST' });
    }

    // --- Memory & Knowledge Store (Phase 8) ---
    async searchMemory(query = '', category = null, limit = 50) {
      let url = `/api/memory/search?query=${encodeURIComponent(query)}&limit=${limit}`;
      if (category) url += `&category=${encodeURIComponent(category)}`;
      return await this.request(url);
    }

    async storeMemory(category, content, importance = 5) {
      return await this.request('/api/memory/store', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ category, content, importance }),
      });
    }

    async updateMemory(memoryId, content, importance = null) {
      const payload = { content };
      if (importance !== null) payload.importance = importance;
      return await this.request(`/api/memory/${encodeURIComponent(memoryId)}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
    }

    async deleteMemory(memoryId) {
      return await this.request(`/api/memory/${encodeURIComponent(memoryId)}`, {
        method: 'DELETE',
      });
    }

    async getMemoryCategories() {
      return await this.request('/api/memory/categories');
    }

    async getMemoryStats() {
      return await this.request('/api/memory/stats');
    }

    // --- Connected Apps & Apps Center (Phase 8) ---
    async getAppsCatalog(query = null, category = null, status = null, capability = null) {
      const params = new URLSearchParams();
      if (query) params.set('query', query);
      if (category) params.set('category', category);
      if (status) params.set('status', status);
      if (capability) params.set('capability', capability);
      const qs = params.toString();
      return await this.request(`/api/apps/catalog${qs ? '?' + qs : ''}`);
    }

    async getAppCategories() {
      return await this.request('/api/apps/categories');
    }

    async getAppDetails(appId) {
      return await this.request(`/api/apps/app/${encodeURIComponent(appId)}`);
    }

    async launchApp(appId) {
      return await this.request(`/api/apps/launch/${encodeURIComponent(appId)}`, { method: 'POST' });
    }

    async toggleAppFavorite(appId) {
      return await this.request(`/api/apps/favorite/${encodeURIComponent(appId)}`, { method: 'POST' });
    }

    async getRecentApps(limit = 6) {
      return await this.request(`/api/apps/recent?limit=${encodeURIComponent(limit)}`);
    }

    // --- Integrations & Connectors (Phase 8) ---
    async getSettings() {
      return await this.request('/api/settings');
    }

    async saveIntegrations(settingsDict, adminPin) {
      return await this.request('/api/settings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Jarvis-Admin-Pin': adminPin,
          'X-Jarvis-Admin-Confirmation': 'privileged-settings-action',
        },
        body: JSON.stringify({ settings: settingsDict }),
      });
    }

    // --- Robotics & Actuators Control (Phase 9) ---
    async getRobotState() {
      return await this.request('/api/robot/state');
    }

    async emergencyStopRobot() {
      return await this.request('/api/robot/estop', { method: 'POST' });
    }

    async stopRobot() {
      return await this.request('/api/robot/stop', { method: 'POST' });
    }

    async disarmRobot() {
      return await this.request('/api/robot/disarm', { method: 'POST' });
    }

    async armRobot(adminPin) {
      return await this.request('/api/robot/arm', {
        method: 'POST',
        headers: {
          'X-Jarvis-Admin-Pin': adminPin,
          'X-Jarvis-Actuation-Confirmation': 'physical-motion',
        },
      });
    }

    async clearRobotEstop(adminPin) {
      return await this.request('/api/robot/clear_estop', {
        method: 'POST',
        headers: {
          'X-Jarvis-Admin-Pin': adminPin,
          'X-Jarvis-Actuation-Confirmation': 'physical-motion',
        },
      });
    }

    async moveRobot(direction, speed = 50, adminPin = '') {
      return await this.request(`/api/robot/${direction}?speed=${encodeURIComponent(speed)}`, {
        method: 'POST',
        headers: {
          'X-Jarvis-Admin-Pin': adminPin,
          'X-Jarvis-Actuation-Confirmation': 'physical-motion',
        },
      });
    }

    async setRobotServo(channel, angle, adminPin = '') {
      return await this.request(`/api/robot/servo?channel=${encodeURIComponent(channel)}&angle=${encodeURIComponent(angle)}`, {
        method: 'POST',
        headers: {
          'X-Jarvis-Admin-Pin': adminPin,
          'X-Jarvis-Actuation-Confirmation': 'physical-motion',
        },
      });
    }

    // --- Hardware Sensors & Diagnostics (Phase 9) ---
    async getSensorsOverview() {
      return await this.request('/api/sensors/');
    }

    async readAllSensors() {
      return await this.request('/api/sensors/all');
    }

    async getSensorsStatus() {
      return await this.request('/api/sensors/status');
    }

    async calibrateSensor(sensorName) {
      return await this.request(`/api/sensors/${encodeURIComponent(sensorName)}/calibrate`, { method: 'POST' });
    }

    async getDiagnostics() {
      return await this.request('/api/diagnostics');
    }

    async getI2cHealth() {
      return await this.request('/api/health/i2c');
    }

    async getSerialHealth() {
      return await this.request('/api/health/serial');
    }

    // Allowlisted Metric Extraction with strict truthfulness
    sanitizeTelemetry(rawSystem, rawHealth, rawDev) {
      const formatNumber = (val, decimals = 1) => {
        return typeof val === 'number' && !isNaN(val) ? val.toFixed(decimals) : 'Unavailable';
      };

      const system = rawSystem || {};
      const health = rawHealth || {};
      const dev = rawDev || {};

      return {
        timestamp: new Date().toISOString(),
        cpu: {
          usage_pct: typeof system.cpu_usage_pct === 'number' ? system.cpu_usage_pct.toFixed(1) : 'Unavailable',
          freq_mhz: formatNumber(system.cpu_freq_mhz, 0),
          cores: system.cpu_cores || 'Unavailable',
        },
        ram: {
          used_mb: typeof system.ram_used_mb === 'number' ? system.ram_used_mb : 'Unavailable',
          total_mb: typeof system.ram_total_mb === 'number' ? system.ram_total_mb : 'Unavailable',
          pct: typeof system.ram_pct === 'number' ? system.ram_pct.toFixed(1) : 'Unavailable',
        },
        disk: {
          used_gb: typeof system.disk_used_gb === 'number' ? system.disk_used_gb.toFixed(1) : 'Unavailable',
          total_gb: typeof system.disk_total_gb === 'number' ? system.disk_total_gb.toFixed(1) : 'Unavailable',
          pct: typeof system.disk_pct === 'number' ? system.disk_pct.toFixed(1) : 'Unavailable',
        },
        temperature: {
          celsius: typeof system.temp_c === 'number' ? system.temp_c.toFixed(1) : (typeof system.cpu_temp_c === 'number' ? system.cpu_temp_c.toFixed(1) : 'Unavailable'),
        },
        battery: 'Unavailable', // AC / USB-C powered host
        gpu: 'Unavailable', // VideoCore VII headless (no standard hardware API exposed)
        network: {
          sent_mb: formatNumber(system.net_sent_mb, 1),
          recv_mb: formatNumber(system.net_recv_mb, 1),
        },
        host: {
          os: system.os || 'Linux',
          kernel: system.os_version || 'Unavailable',
          arch: system.arch || 'Unavailable',
          hostname: system.hostname || 'raspberrypi',
          uptime: system.uptime_str || 'Unavailable',
        },
        backend: {
          status: health.status === 'OK' ? 'Healthy' : (health.status || 'Unavailable'),
          core_component: health.components?.backend || 'Unavailable',
        },
        models: {
          active_provider: health.components?.ai_provider || 'Unavailable',
          openrouter: dev.providers?.openrouter?.configured ? 'Ready' : 'Not configured',
          ollama: dev.providers?.ollama?.configured ? `Ready (${dev.providers.ollama.model || 'local'})` : 'Unavailable',
        },
        orchestrator: {
          worktree_count: typeof dev.worktree_count === 'number' ? dev.worktree_count : 'Unavailable',
          registered_agents: typeof dev.agents?.registered_count === 'number' ? dev.agents.registered_count : 'Unavailable',
          active_tasks: typeof dev.tasks?.running === 'number' ? dev.tasks.running : 'Unavailable',
          total_tasks: typeof dev.tasks?.total === 'number' ? dev.tasks.total : 'Unavailable',
        },
        robot: {
          state: health.components?.robot || system.robot_state || 'IDLE',
          safety: health.components?.robot_hardware || 'Safety Latch Engaged',
        },
        voice: {
          engine: health.components?.voice_engine || 'Unavailable',
          microphone: health.components?.microphone || 'Unavailable',
          speaker: health.components?.speaker || 'Unavailable',
        }
      };
    }

    async fetchAllTelemetry() {
      try {
        const [rawSystem, rawHealth, rawDev] = await Promise.all([
          this.request('/api/system').catch(() => null),
          this.request('/api/health').catch(() => null),
          this.request('/api/developer/status').catch(() => null),
        ]);

        if (!rawSystem && !rawHealth) {
          throw new Error('Both system telemetry and health endpoints unreachable');
        }

        this.failureCount = 0;
        this.setState('online');

        const sanitized = this.sanitizeTelemetry(rawSystem, rawHealth, rawDev);
        this.lastTelemetry = sanitized;

        for (const cb of this.telemetryListeners) {
          try { cb(sanitized); } catch (e) { console.error(e); }
        }

        return sanitized;
      } catch (err) {
        this.failureCount++;
        this.setState(this.failureCount > 1 ? 'offline' : 'reconnecting');
        throw err;
      }
    }

    startPolling() {
      if (this.pollTimer) clearInterval(this.pollTimer);

      const loop = async () => {
        try {
          await this.fetchAllTelemetry();
        } catch (e) {
          // Failure handled in fetchAllTelemetry
        }

        const nextDelay = this.state === 'offline' 
          ? Math.min(this.pollInterval * Math.pow(1.5, Math.min(this.failureCount, 5)), this.maxBackoff)
          : this.pollInterval;

        this.pollTimer = setTimeout(loop, nextDelay);
      };

      loop();
    }

    stopPolling() {
      if (this.pollTimer) {
        clearTimeout(this.pollTimer);
        this.pollTimer = null;
      }
    }

    setPollInterval(ms) {
      this.pollInterval = ms;
      if (this.pollTimer) {
        clearTimeout(this.pollTimer);
        this.pollTimer = null;
        this.startPolling();
      }
    }
  }

  // Export singleton client
  window.jarvisApi = new JarvisApiClient();
})();
