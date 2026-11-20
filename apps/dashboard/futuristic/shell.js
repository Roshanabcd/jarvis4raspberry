/**
 * JARVIS OS Futuristic Shell Controller
 * Master Requirements: SPEC.md & PLAN.md Phase 2
 */

(function () {
  'use strict';

  // 18 Destinations per SPEC.md Section 3 & References
  const DESTINATIONS = [
    { id: 'dashboard', label: 'Dashboard', group: 'Core', icon: 'grid', phase: 3 },
    { id: 'chat', label: 'AI Chat', group: 'Core', icon: 'message-square', phase: 4 },
    { id: 'voice', label: 'Voice Assistant', group: 'Core', icon: 'mic', phase: 6 },
    { id: 'agents', label: 'AI Agents', group: 'Orchestration', icon: 'cpu', phase: 7 },
    { id: 'tasks', label: 'Tasks', group: 'Orchestration', icon: 'check-square', phase: 8 },
    { id: 'automation', label: 'Automation', group: 'Orchestration', icon: 'workflow', phase: 8 },
    { id: 'workspace', label: 'Developer Workspace', group: 'Engineering', icon: 'code', phase: 7 },
    { id: 'terminal', label: 'Terminal', group: 'Engineering', icon: 'terminal', phase: 7 },
    { id: 'calendar', label: 'Calendar', group: 'Productivity', icon: 'calendar', phase: 8 },
    { id: 'memory', label: 'Memory', group: 'Knowledge', icon: 'brain', phase: 8 },
    { id: 'knowledge', label: 'Knowledge', group: 'Knowledge', icon: 'book-open', phase: 8 },
    { id: 'documents', label: 'Document AI', group: 'Knowledge', icon: 'file-text', phase: 10 },
    { id: 'devices', label: 'Devices & Sensors', group: 'Hardware', icon: 'activity', phase: 9 },
    { id: 'robot', label: 'Robot Control', group: 'Hardware', icon: 'bot', phase: 9 },
    { id: 'integrations', label: 'Integrations', group: 'System', icon: 'plug', phase: 8 },
    { id: 'apps', label: 'Apps Center', group: 'System', icon: 'layers', phase: 8 },
    { id: 'youtube', label: 'YouTube AI', group: 'System', icon: 'video', phase: 8 },
    { id: 'research', label: 'Research Assistant', group: 'System', icon: 'search', phase: 8 },
    { id: 'settings', label: 'Settings', group: 'System', icon: 'settings', phase: 8 },
  ];

  // Shell State
  const state = {
    currentRoute: 'dashboard',
    theme: localStorage.getItem('jarvis_theme') || 'dark',
    accent: localStorage.getItem('jarvis_accent') || 'cyan',
    sidebarCollapsed: localStorage.getItem('jarvis_sidebar_collapsed') === 'true',
    avatar: localStorage.getItem('jarvis_avatar') || 'aria',
    lowPower: localStorage.getItem('jarvis_low_power_mode') === 'true',
    reducedMotion: localStorage.getItem('jarvis_reduced_motion') === 'true',
  };

  function init() {
    applyTheme(state.theme);
    applyAccent(state.accent);
    setupClock();
    setupSidebar();
    setupRouting();
    setupKeyboardNavigation();
    setupThemeControls();
    applyLowPower(state.lowPower, false);
    applyReducedMotion(state.reducedMotion, false);
    renderContent(getRouteFromHash());
  }

  // --- Clock & Telemetry Heartbeat ---
  function setupClock() {
    const clockEl = document.getElementById('shell-clock');
    const dateEl = document.getElementById('shell-date');
    function tick() {
      const now = new Date();
      if (clockEl) clockEl.textContent = now.toLocaleTimeString([], { hour12: false });
      if (dateEl) dateEl.textContent = now.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' });
    }
    tick();
    setInterval(tick, 1000);
  }

  // --- Theme & Accent ---
  function applyTheme(theme) {
    state.theme = theme;
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('jarvis_theme', theme);
  }

  function applyAccent(accent) {
    state.accent = accent;
    document.documentElement.setAttribute('data-accent', accent);
    localStorage.setItem('jarvis_accent', accent);
  }

  function applyLowPower(enabled, notify = false) {
    state.lowPower = enabled;
    localStorage.setItem('jarvis_low_power_mode', enabled ? 'true' : 'false');
    const lowPowerBtn = document.getElementById('low-power-toggle');
    if (enabled) {
      document.documentElement.setAttribute('data-power-mode', 'low');
      document.body.classList.add('low-power-mode');
      if (lowPowerBtn) {
        lowPowerBtn.classList.add('active');
        lowPowerBtn.setAttribute('aria-pressed', 'true');
      }
      window.jarvisAvatar?.setLowPowerMode(true);
      window.jarvisApi?.setPollInterval(10000);
      if (notify) window.showToast('Eco Low-Power Mode Enabled (animations & polling reduced)', 'info');
    } else {
      document.documentElement.removeAttribute('data-power-mode');
      document.body.classList.remove('low-power-mode');
      if (lowPowerBtn) {
        lowPowerBtn.classList.remove('active');
        lowPowerBtn.setAttribute('aria-pressed', 'false');
      }
      window.jarvisAvatar?.setLowPowerMode(false);
      window.jarvisApi?.setPollInterval(3000);
      if (notify) window.showToast('Normal Power Mode Restored', 'success');
    }
  }

  function applyReducedMotion(enabled, notify = false) {
    state.reducedMotion = enabled;
    localStorage.setItem('jarvis_reduced_motion', enabled ? 'true' : 'false');
    const motionBtn = document.getElementById('reduced-motion-toggle');
    if (enabled) {
      document.documentElement.setAttribute('data-reduced-motion', 'true');
      if (motionBtn) {
        motionBtn.classList.add('active');
        motionBtn.setAttribute('aria-pressed', 'true');
      }
      window.jarvisAvatar?.setReducedMotion(true);
      if (notify) window.showToast('Reduced Motion Mode Activated', 'info');
    } else {
      document.documentElement.removeAttribute('data-reduced-motion');
      if (motionBtn) {
        motionBtn.classList.remove('active');
        motionBtn.setAttribute('aria-pressed', 'false');
      }
      window.jarvisAvatar?.setReducedMotion(false);
      if (notify) window.showToast('Full Motion Animations Restored', 'info');
    }
  }

  function setupThemeControls() {
    const themeSelect = document.getElementById('theme-select');
    if (themeSelect) {
      themeSelect.value = state.theme;
      themeSelect.addEventListener('change', (e) => applyTheme(e.target.value));
    }
    const accentSelect = document.getElementById('accent-select');
    if (accentSelect) {
      accentSelect.value = state.accent;
      accentSelect.addEventListener('change', (e) => applyAccent(e.target.value));
    }
    const lowPowerBtn = document.getElementById('low-power-toggle');
    if (lowPowerBtn) {
      lowPowerBtn.addEventListener('click', () => {
        applyLowPower(!state.lowPower, true);
      });
    }
    const motionBtn = document.getElementById('reduced-motion-toggle');
    if (motionBtn) {
      motionBtn.addEventListener('click', () => {
        applyReducedMotion(!state.reducedMotion, true);
      });
    }
  }

  // --- Sidebar Collapse ---
  function setupSidebar() {
    const sidebar = document.getElementById('app-sidebar');
    const toggleBtn = document.getElementById('sidebar-toggle');
    if (sidebar && state.sidebarCollapsed) {
      sidebar.classList.add('collapsed');
    }
    if (toggleBtn && sidebar) {
      toggleBtn.addEventListener('click', () => {
        const isCollapsed = sidebar.classList.toggle('collapsed');
        state.sidebarCollapsed = isCollapsed;
        localStorage.setItem('jarvis_sidebar_collapsed', isCollapsed);
        toggleBtn.setAttribute('aria-expanded', !isCollapsed);
      });
    }
  }

  // --- Routing & Navigation ---
  function getRouteFromHash() {
    const hash = window.location.hash.replace('#', '').trim();
    if (hash === 'sensors') return 'sensors';
    const match = DESTINATIONS.find((d) => d.id === hash);
    return match ? match.id : 'dashboard';
  }

  function setupRouting() {
    window.addEventListener('hashchange', () => {
      navigateTo(getRouteFromHash(), false);
    });

    document.querySelectorAll('[data-route]').forEach((el) => {
      el.addEventListener('click', (e) => {
        e.preventDefault();
        const route = el.getAttribute('data-route');
        navigateTo(route, true);
      });
    });
  }

  function navigateTo(routeId, updateHash) {
    state.currentRoute = routeId;
    if (updateHash) {
      window.location.hash = '#' + routeId;
    }

    // Update active nav items
    document.querySelectorAll('.nav-item, .mobile-nav-item').forEach((item) => {
      const match = item.getAttribute('data-route') === routeId;
      item.classList.toggle('active', match);
      item.setAttribute('aria-selected', match ? 'true' : 'false');
    });

    renderContent(routeId);
  }

  // --- Keyboard Navigation (Roving Tabindex & Shortcuts) ---
  function setupKeyboardNavigation() {
    const navItems = Array.from(document.querySelectorAll('.app-sidebar .nav-item'));
    navItems.forEach((item, index) => {
      item.addEventListener('keydown', (e) => {
        let targetIndex = index;
        if (e.key === 'ArrowDown') {
          e.preventDefault();
          targetIndex = (index + 1) % navItems.length;
          navItems[targetIndex].focus();
        } else if (e.key === 'ArrowUp') {
          e.preventDefault();
          targetIndex = (index - 1 + navItems.length) % navItems.length;
          navItems[targetIndex].focus();
        } else if (e.key === 'Home') {
          e.preventDefault();
          navItems[0].focus();
        } else if (e.key === 'End') {
          e.preventDefault();
          navItems[navItems.length - 1].focus();
        }
      });
    });

    // Global Command Palette Shortcut (Ctrl+K or Cmd+K)
    window.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.getElementById('global-search');
        if (searchInput) searchInput.focus();
      }
    });
  }

  // --- Content Renderer & "Not Implemented Yet" States ---
  function renderContent(routeId) {
    const mainContainer = document.getElementById('main-content');
    if (!mainContainer) return;

    const dest = DESTINATIONS.find((d) => d.id === routeId) || DESTINATIONS[0];

    if (routeId === 'dashboard') {
      mainContainer.innerHTML = renderDashboardPlaceholder(window.jarvisApi?.lastTelemetry);
      bindDashboardTelemetry();
    } else if (routeId === 'chat') {
      if (window.jarvisChat) {
        window.jarvisChat.render(mainContainer);
      }
    } else if (routeId === 'voice') {
      if (window.jarvisVoice) {
        window.jarvisVoice.render(mainContainer);
      }
    } else if (routeId === 'agents') {
      if (window.jarvisDevHub) {
        window.jarvisDevHub.renderAgents(mainContainer);
      }
    } else if (routeId === 'workspace') {
      if (window.jarvisDevHub) {
        window.jarvisDevHub.renderWorkspace(mainContainer);
      }
    } else if (routeId === 'terminal') {
      if (window.jarvisDevHub) {
        window.jarvisDevHub.renderTerminal(mainContainer);
      }
    } else if (['tasks', 'automation', 'calendar', 'memory', 'knowledge', 'documents', 'integrations', 'apps'].includes(routeId)) {
      if (window.jarvisOperations) {
        mainContainer.innerHTML = '<div id="view-placeholder"></div>';
        window.jarvisOperations.renderDestination(routeId);
      }
    } else if (['devices', 'sensors', 'robot'].includes(routeId)) {
      if (window.jarvisRobotDevices) {
        mainContainer.innerHTML = '<div id="view-placeholder"></div>';
        window.jarvisRobotDevices.renderDestination(routeId);
      }
    } else {
      mainContainer.innerHTML = renderNotImplementedState(dest);
    }
  }

  function bindDashboardTelemetry() {
    if (!window.jarvisApi) return;

    window.jarvisApi.onTelemetry((telemetry) => {
      if (state.currentRoute !== 'dashboard') return;
      updateDashboardDom(telemetry);
    });

    window.jarvisApi.onStateChange((connState) => {
      const banner = document.getElementById('offline-alert-banner');
      if (banner) {
        banner.style.display = connState === 'offline' ? 'block' : 'none';
      }
      const connChip = document.getElementById('core-status-chip');
      if (connChip) {
        connChip.className = connState === 'online' ? 'status-chip success' : 'status-chip danger';
        connChip.innerHTML = `<span class="status-dot"></span> Core: ${connState.toUpperCase()}`;
      }
    });

    // Start background polling
    window.jarvisApi.startPolling();

    // Mount Digital Human Avatar (Phase 5)
    setupDashboardAvatar();
  }

  function setupDashboardAvatar() {
    const avatarContainer = document.getElementById('dashboard-avatar-container');
    if (!avatarContainer || !window.jarvisAvatar) return;

    window.jarvisAvatar.mount(avatarContainer);

    // Gender toggle buttons
    const ariaBtn = document.getElementById('btn-avatar-aria');
    const atlasBtn = document.getElementById('btn-avatar-atlas');
    const currentAvatar = window.jarvisAvatar.getAvatar();

    if (ariaBtn && atlasBtn) {
      ariaBtn.classList.toggle('active', currentAvatar === 'aria');
      atlasBtn.classList.toggle('active', currentAvatar === 'atlas');

      ariaBtn.addEventListener('click', () => {
        window.jarvisAvatar.setAvatar('aria');
        ariaBtn.classList.add('active');
        atlasBtn.classList.remove('active');
      });

      atlasBtn.addEventListener('click', () => {
        window.jarvisAvatar.setAvatar('atlas');
        atlasBtn.classList.add('active');
        ariaBtn.classList.remove('active');
      });
    }

    // State pills
    document.querySelectorAll('.avatar-state-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        const targetState = btn.getAttribute('data-state');
        if (targetState) {
          window.jarvisAvatar.setState(targetState);
          document.querySelectorAll('.avatar-state-btn').forEach((b) => b.classList.remove('active'));
          btn.classList.add('active');
        }
      });
    });

    // Update state chip & FPS meter
    const stateChip = document.getElementById('avatar-active-state-chip');
    const fpsDisplay = document.getElementById('avatar-fps-display');

    window.jarvisAvatar.subscribe(({ state: avatarState, fps }) => {
      if (stateChip) {
        stateChip.innerHTML = `<span class="status-dot"></span> State: ${avatarState.toUpperCase()}`;
      }
      if (fpsDisplay) {
        fpsDisplay.textContent = `${fps} FPS`;
      }
    });
  }

  function updateDashboardDom(t) {
    if (!t) return;

    // CPU
    const cpuEl = document.getElementById('metric-cpu');
    if (cpuEl) cpuEl.textContent = t.cpu.usage_pct !== 'Unavailable' ? `${t.cpu.usage_pct}%` : 'Unavailable';
    const cpuSubEl = document.getElementById('metric-cpu-sub');
    if (cpuSubEl) cpuSubEl.textContent = `${t.cpu.cores} cores · ${t.cpu.freq_mhz} MHz`;

    // RAM
    const ramEl = document.getElementById('metric-ram');
    if (ramEl) ramEl.textContent = t.ram.pct !== 'Unavailable' ? `${t.ram.pct}%` : 'Unavailable';
    const ramSubEl = document.getElementById('metric-ram-sub');
    if (ramSubEl) ramSubEl.textContent = `${t.ram.used_mb} / ${t.ram.total_mb} MB`;

    // Disk
    const diskEl = document.getElementById('metric-disk');
    if (diskEl) diskEl.textContent = t.disk.pct !== 'Unavailable' ? `${t.disk.pct}%` : 'Unavailable';
    const diskSubEl = document.getElementById('metric-disk-sub');
    if (diskSubEl) diskSubEl.textContent = `${t.disk.used_gb} / ${t.disk.total_gb} GB`;

    // Temperature
    const tempEl = document.getElementById('metric-temp');
    if (tempEl) tempEl.textContent = t.temperature.celsius !== 'Unavailable' ? `${t.temperature.celsius} °C` : 'Unavailable';

    // Network
    const netEl = document.getElementById('metric-net');
    if (netEl) netEl.textContent = t.network.recv_mb !== 'Unavailable' ? `↓ ${t.network.recv_mb} MB · ↑ ${t.network.sent_mb} MB` : 'Unavailable';

    // Battery & GPU
    const batteryEl = document.getElementById('metric-battery');
    if (batteryEl) batteryEl.textContent = t.battery;
    const gpuEl = document.getElementById('metric-gpu');
    if (gpuEl) gpuEl.textContent = t.gpu;

    // Host Architecture
    const hostEl = document.getElementById('host-kernel');
    if (hostEl) hostEl.textContent = t.host.kernel;
    const uptimeEl = document.getElementById('host-uptime');
    if (uptimeEl) uptimeEl.textContent = t.host.uptime;

    // AI Provider
    const aiProviderEl = document.getElementById('ai-active-provider');
    if (aiProviderEl) aiProviderEl.textContent = t.models.active_provider;

    // Multi-Agent Orchestrator
    const agentWorktreeEl = document.getElementById('orchestrator-worktrees');
    if (agentWorktreeEl) agentWorktreeEl.textContent = `${t.orchestrator.worktree_count} active worktrees`;
    const agentCountEl = document.getElementById('orchestrator-agents');
    if (agentCountEl) agentCountEl.textContent = `${t.orchestrator.registered_agents} registered agents`;

    // Robot Safety
    const robotStateEl = document.getElementById('robot-state');
    if (robotStateEl) robotStateEl.textContent = t.robot.state;
    const robotSafetyEl = document.getElementById('robot-safety');
    if (robotSafetyEl) robotSafetyEl.textContent = t.robot.safety;
  }

  function renderDashboardPlaceholder(telemetry) {
    const t = telemetry || {
      cpu: { usage_pct: 'Unavailable', freq_mhz: 'Unavailable', cores: 'Unavailable' },
      ram: { used_mb: 'Unavailable', total_mb: 'Unavailable', pct: 'Unavailable' },
      disk: { used_gb: 'Unavailable', total_gb: 'Unavailable', pct: 'Unavailable' },
      temperature: { celsius: 'Unavailable' },
      battery: 'Unavailable',
      gpu: 'Unavailable',
      network: { sent_mb: 'Unavailable', recv_mb: 'Unavailable' },
      host: { kernel: 'Unavailable', uptime: 'Unavailable', hostname: 'raspberrypi' },
      backend: { status: 'Healthy' },
      models: { active_provider: 'Unavailable' },
      orchestrator: { worktree_count: 'Unavailable', registered_agents: 'Unavailable' },
      robot: { state: 'IDLE', safety: 'Safety Latch Engaged' },
    };

    return `
      <!-- Live Offline Alert Banner -->
      <div id="offline-alert-banner" style="display:${window.jarvisApi?.state === 'offline' ? 'block' : 'none'}; margin-bottom:16px; padding:12px 18px; border-radius:var(--radius-md); background:rgba(255,59,48,0.18); border:1px solid var(--accent-danger); color:#FFA49E; font-size:0.88rem; font-weight:600;">
        ⚠️ Backend Connection Offline — Telemetry paused. Attempting automatic reconnection...
      </div>

      <div class="glass-panel" style="padding: 24px 28px; margin-bottom: 24px;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:16px;">
          <div>
            <div style="display:flex; gap:8px; margin-bottom:8px;">
              <span id="core-status-chip" class="status-chip success">
                <span class="status-dot"></span> Core: ONLINE
              </span>
              <span class="status-chip success">
                <span class="status-dot"></span> Real Data Layer Active
              </span>
            </div>
            <h1 style="margin:0 0 6px 0; font-size:1.75rem; letter-spacing:0.5px;">JARVIS Control Center</h1>
            <p style="margin:0; color:var(--text-secondary); font-size:0.9rem;">
              Futuristic AI Operating System &amp; Telemetry Hub
            </p>
          </div>
          <div style="display:flex; gap:10px; align-items:center;">
            <a href="/" class="btn-futuristic btn-secondary" title="View legacy 21-tab dashboard">
              ↩ Classic Dashboard
            </a>
            <button class="btn-futuristic" onclick="window.jarvisApi?.fetchAllTelemetry().then(()=>window.showToast('Telemetry refreshed from live backend', 'success')).catch(()=>window.showToast('Refresh failed: backend offline', 'danger'))">
              ↻ Refresh Telemetry
            </button>
          </div>
        </div>
      </div>

      <!-- Voice-First Assistant Action Banner (Mobile & Quick Interaction - SPEC Section 16 & PLAN Phase 10) -->
      <div class="mobile-voice-hero glass-panel" style="padding: 16px 20px; margin-bottom: 20px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; border-left: 3px solid var(--accent);">
        <div style="display:flex; align-items:center; gap:12px;">
          <div style="width:42px; height:42px; border-radius:50%; background:var(--accent-bg); border:1px solid var(--accent); display:flex; align-items:center; justify-content:center; color:var(--accent);" aria-hidden="true">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line></svg>
          </div>
          <div>
            <div style="font-size:0.75rem; font-weight:700; color:var(--accent); text-transform:uppercase; letter-spacing:1px;">Voice-First Interface</div>
            <div style="font-size:1.0rem; font-weight:700; color:var(--text-primary);">Natural Voice Dialogue Active</div>
          </div>
        </div>
        <a href="#voice" class="btn-futuristic" id="dashboard-voice-launch-btn" style="text-decoration:none; display:inline-flex; align-items:center; gap:6px;">
          🎙️ Open Voice Assistant
        </a>
      </div>

      <!-- Digital Human AI Avatar Showcase (SPEC Section 4 & PLAN Phase 5) -->
      <div class="avatar-showcase-panel glass-panel" style="margin-bottom: 24px;">
        <div style="display:flex; justify-content:space-between; align-items:center; width:100%; flex-wrap:wrap; gap:12px; margin-bottom:14px;">
          <div>
            <div style="font-size:0.75rem; font-weight:700; color:var(--accent); text-transform:uppercase; letter-spacing:1px; margin-bottom:4px;">Holographic Digital Human</div>
            <h2 style="margin:0; font-size:1.3rem; letter-spacing:0.5px;">JARVIS Neural Assistant</h2>
          </div>
          <div class="avatar-selector-toggle" role="group" aria-label="Avatar Character Selector">
            <button id="btn-avatar-aria" class="avatar-toggle-btn active" data-avatar="aria">ARIA (Female)</button>
            <button id="btn-avatar-atlas" class="avatar-toggle-btn" data-avatar="atlas">ATLAS (Male)</button>
          </div>
          <span id="avatar-active-state-chip" class="status-chip success">
            <span class="status-dot"></span> State: IDLE
          </span>
        </div>

        <div id="dashboard-avatar-container"></div>

        <!-- 9 State Verification Controls -->
        <div class="avatar-state-pills-row" role="group" aria-label="Avatar State Controls">
          <button class="avatar-state-btn active" data-state="idle">Idle</button>
          <button class="avatar-state-btn" data-state="listening">Listening</button>
          <button class="avatar-state-btn" data-state="thinking">Thinking</button>
          <button class="avatar-state-btn" data-state="speaking">Speaking</button>
          <button class="avatar-state-btn" data-state="happy">Happy</button>
          <button class="avatar-state-btn" data-state="concerned">Concerned</button>
          <button class="avatar-state-btn" data-state="error">Error</button>
          <button class="avatar-state-btn" data-state="offline">Offline</button>
          <button class="avatar-state-btn" data-state="muted">Muted</button>
        </div>

        <div class="avatar-meta-bar">
          <span>Renderer: <strong style="color:var(--text-primary)">Svg2D (Vector Digital Human)</strong></span>
          <span>·</span>
          <span>Performance: <span id="avatar-fps-display" class="avatar-fps-badge">60 FPS</span></span>
          <span>·</span>
          <span>Fallback: <span style="color:var(--accent)">Vrm3D ➔ Svg2D (Ready)</span></span>
        </div>
      </div>

      <!-- Real Telemetry Grid -->
      <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap:16px; margin-bottom: 24px;">
        <!-- CPU Card -->
        <div class="glass-card">
          <div style="font-size:0.75rem; font-weight:600; color:var(--text-secondary); text-transform:uppercase; margin-bottom:8px;">CPU Utilization</div>
          <div id="metric-cpu" style="font-size:1.6rem; font-weight:800; color:var(--accent); font-family:var(--font-mono);">${t.cpu.usage_pct !== 'Unavailable' ? t.cpu.usage_pct + '%' : 'Unavailable'}</div>
          <div id="metric-cpu-sub" style="font-size:0.75rem; color:var(--text-muted); margin-top:4px;">${t.cpu.cores} cores · ${t.cpu.freq_mhz} MHz</div>
        </div>

        <!-- RAM Card -->
        <div class="glass-card">
          <div style="font-size:0.75rem; font-weight:600; color:var(--text-secondary); text-transform:uppercase; margin-bottom:8px;">System Memory</div>
          <div id="metric-ram" style="font-size:1.6rem; font-weight:800; color:var(--text-primary); font-family:var(--font-mono);">${t.ram.pct !== 'Unavailable' ? t.ram.pct + '%' : 'Unavailable'}</div>
          <div id="metric-ram-sub" style="font-size:0.75rem; color:var(--text-muted); margin-top:4px;">${t.ram.used_mb} / ${t.ram.total_mb} MB</div>
        </div>

        <!-- Disk Card -->
        <div class="glass-card">
          <div style="font-size:0.75rem; font-weight:600; color:var(--text-secondary); text-transform:uppercase; margin-bottom:8px;">Storage (NVMe/Disk)</div>
          <div id="metric-disk" style="font-size:1.6rem; font-weight:800; color:var(--text-primary); font-family:var(--font-mono);">${t.disk.pct !== 'Unavailable' ? t.disk.pct + '%' : 'Unavailable'}</div>
          <div id="metric-disk-sub" style="font-size:0.75rem; color:var(--text-muted); margin-top:4px;">${t.disk.used_gb} / ${t.disk.total_gb} GB</div>
        </div>

        <!-- Thermal Card -->
        <div class="glass-card">
          <div style="font-size:0.75rem; font-weight:600; color:var(--text-secondary); text-transform:uppercase; margin-bottom:8px;">SoC Temperature</div>
          <div id="metric-temp" style="font-size:1.6rem; font-weight:800; color:var(--accent-green); font-family:var(--font-mono);">${t.temperature.celsius !== 'Unavailable' ? t.temperature.celsius + ' °C' : 'Unavailable'}</div>
          <div style="font-size:0.75rem; color:var(--text-muted); margin-top:4px;">Thermal Zone 0</div>
        </div>
      </div>

      <!-- Secondary Telemetry Grid -->
      <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap:18px; margin-bottom: 24px;">
        <!-- Network & Battery Card -->
        <div class="glass-card">
          <div style="font-size:0.8rem; font-weight:700; color:var(--accent); text-transform:uppercase; margin-bottom:12px;">Network &amp; Power</div>
          <div style="display:flex; justify-content:space-between; padding:6px 0; border-bottom:1px solid rgba(255,255,255,0.06);">
            <span style="color:var(--text-secondary); font-size:0.85rem;">Network I/O:</span>
            <span id="metric-net" style="font-family:var(--font-mono); font-weight:600; font-size:0.85rem;">${t.network.recv_mb !== 'Unavailable' ? '↓ ' + t.network.recv_mb + ' MB · ↑ ' + t.network.sent_mb + ' MB' : 'Unavailable'}</span>
          </div>
          <div style="display:flex; justify-content:space-between; padding:6px 0; border-bottom:1px solid rgba(255,255,255,0.06);">
            <span style="color:var(--text-secondary); font-size:0.85rem;">Battery:</span>
            <span id="metric-battery" style="color:var(--text-muted); font-size:0.85rem;">${t.battery}</span>
          </div>
          <div style="display:flex; justify-content:space-between; padding:6px 0;">
            <span style="color:var(--text-secondary); font-size:0.85rem;">GPU Acceleration:</span>
            <span id="metric-gpu" style="color:var(--text-muted); font-size:0.85rem;">${t.gpu}</span>
          </div>
        </div>

        <!-- Host Architecture Card -->
        <div class="glass-card">
          <div style="font-size:0.8rem; font-weight:700; color:var(--accent); text-transform:uppercase; margin-bottom:12px;">Host Architecture</div>
          <div style="display:flex; justify-content:space-between; padding:6px 0; border-bottom:1px solid rgba(255,255,255,0.06);">
            <span style="color:var(--text-secondary); font-size:0.85rem;">Kernel &amp; OS:</span>
            <span id="host-kernel" style="font-family:var(--font-mono); font-size:0.82rem; text-align:right; max-width:200px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${t.host.kernel}</span>
          </div>
          <div style="display:flex; justify-content:space-between; padding:6px 0;">
            <span style="color:var(--text-secondary); font-size:0.85rem;">System Uptime:</span>
            <span id="host-uptime" style="font-family:var(--font-mono); font-size:0.85rem;">${t.host.uptime}</span>
          </div>
        </div>

        <!-- AI Orchestrator & Model Card -->
        <div class="glass-card">
          <div style="font-size:0.8rem; font-weight:700; color:var(--accent); text-transform:uppercase; margin-bottom:12px;">AI Orchestrator &amp; Models</div>
          <div style="display:flex; justify-content:space-between; padding:6px 0; border-bottom:1px solid rgba(255,255,255,0.06);">
            <span style="color:var(--text-secondary); font-size:0.85rem;">Active AI Provider:</span>
            <span id="ai-active-provider" class="status-chip success" style="font-size:0.75rem;">${t.models.active_provider}</span>
          </div>
          <div style="display:flex; justify-content:space-between; padding:6px 0; border-bottom:1px solid rgba(255,255,255,0.06);">
            <span style="color:var(--text-secondary); font-size:0.85rem;">Agent Isolation:</span>
            <span id="orchestrator-worktrees" style="font-size:0.85rem; font-weight:600;">${t.orchestrator.worktree_count} active worktrees</span>
          </div>
          <div style="display:flex; justify-content:space-between; padding:6px 0;">
            <span style="color:var(--text-secondary); font-size:0.85rem;">Registered Agents:</span>
            <span id="orchestrator-agents" style="font-size:0.85rem; color:var(--text-secondary);">${t.orchestrator.registered_agents} registered agents</span>
          </div>
        </div>

        <!-- Robot Safety Card -->
        <div class="glass-card">
          <div style="font-size:0.8rem; font-weight:700; color:var(--accent); text-transform:uppercase; margin-bottom:12px;">Robot Hardware Safety</div>
          <div style="display:flex; justify-content:space-between; padding:6px 0; border-bottom:1px solid rgba(255,255,255,0.06);">
            <span style="color:var(--text-secondary); font-size:0.85rem;">Motion State:</span>
            <span id="robot-state" class="status-chip" style="font-size:0.75rem;">${t.robot.state}</span>
          </div>
          <div style="display:flex; justify-content:space-between; padding:6px 0;">
            <span style="color:var(--text-secondary); font-size:0.85rem;">Safety Interlock:</span>
            <span id="robot-safety" style="font-size:0.85rem; color:var(--accent-green); font-weight:600;">${t.robot.safety}</span>
          </div>
        </div>
      </div>
    `;
  }


  function renderNotImplementedState(dest) {
    return `
      <div class="glass-panel" style="padding: 40px; text-align: center; max-width: 680px; margin: 40px auto;">
        <div style="width:64px; height:64px; border-radius:50%; background:var(--accent-bg); border:1px solid var(--accent); margin:0 auto 20px auto; display:flex; align-items:center; justify-content:center; color:var(--accent); font-size:1.6rem; box-shadow:0 0 20px var(--accent-glow);">
          ⚡
        </div>
        <h2 style="font-size: 1.5rem; margin: 0 0 10px 0; color: var(--text-primary);">${dest.label}</h2>
        <div class="status-chip" style="margin-bottom: 16px;">
          Scheduled for Phase ${dest.phase}
        </div>
        <p style="color: var(--text-secondary); font-size: 0.92rem; line-height: 1.6; margin: 0 0 24px 0;">
          <strong>Not implemented yet.</strong> This destination is scheduled for delivery in <strong>Phase ${dest.phase}</strong> per <code>docs/jarvis-ui/PLAN.md</code>.
          <br>Existing services continue running in the classic dashboard.
        </p>
        <div style="display:flex; gap:12px; justify-content:center; flex-wrap:wrap;">
          <a href="/#tab-${dest.id}" class="btn-futuristic btn-secondary">
            View in Classic Dashboard
          </a>
          <button class="btn-futuristic" onclick="window.location.hash='#dashboard'">
            Back to Dashboard
          </button>
        </div>
      </div>
    `;
  }

  // --- Global Toast Notification Helper ---
  window.showToast = function (message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
      <span class="status-dot" style="background:var(--accent)"></span>
      <span style="flex:1">${message}</span>
    `;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transition = 'opacity 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 3200);
  };

  // Expose global controller
  const shellController = {
    state,
    navigateTo,
    applyTheme,
    applyAccent,
    applyLowPower,
    toggleLowPowerMode: () => applyLowPower(!state.lowPower, true),
    setLowPowerMode: (val) => applyLowPower(!!val, false),
    isLowPowerMode: () => state.lowPower,
    applyReducedMotion,
    toggleReducedMotion: () => applyReducedMotion(!state.reducedMotion, true),
    setReducedMotion: (val) => applyReducedMotion(!!val, false),
    isReducedMotion: () => state.reducedMotion,
    getCurrentRoute: () => state.currentRoute,
    showToast: (msg, type) => window.showToast(msg, type),
  };

  window.JARVIS_SHELL = shellController;
  window.jarvisShell = shellController;

  // Boot on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
