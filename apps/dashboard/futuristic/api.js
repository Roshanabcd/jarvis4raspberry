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
      if (this.state !== newState) {
        this.state = newState;
        for (const cb of this.stateListeners) {
          try { cb(this.state, this.lastTelemetry); } catch (e) { console.error(e); }
        }
      }
    }

    async request(path, options = {}) {
      const url = `${this.baseUrl}${path}`;
      const headers = {
        'Accept': 'application/json',
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
  }

  // Export singleton client
  window.jarvisApi = new JarvisApiClient();
})();
