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
  };

  function init() {
    applyTheme(state.theme);
    applyAccent(state.accent);
    setupClock();
    setupSidebar();
    setupRouting();
    setupKeyboardNavigation();
    setupThemeControls();
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

    // Check if destination has custom implementation or placeholder
    if (routeId === 'dashboard') {
      mainContainer.innerHTML = renderDashboardPlaceholder();
    } else {
      mainContainer.innerHTML = renderNotImplementedState(dest);
    }
  }

  function renderDashboardPlaceholder() {
    return `
      <div class="glass-panel" style="padding: 28px; margin-bottom: 24px;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:16px;">
          <div>
            <div class="status-chip success" style="margin-bottom:8px;">
              <span class="status-dot"></span> System Operational · Phase 2 Shell Active
            </div>
            <h1 style="margin:0 0 8px 0; font-size:1.8rem; letter-spacing:0.5px;">JARVIS Control Center</h1>
            <p style="margin:0; color:var(--text-secondary); font-size:0.92rem;">
              Futuristic AI Operating System &amp; Humanoid Digital Avatar
            </p>
          </div>
          <div style="display:flex; gap:10px; align-items:center;">
            <a href="/" class="btn-futuristic btn-secondary" title="View legacy 21-tab dashboard">
              ↩ Return to Classic UI
            </a>
            <button class="btn-futuristic" onclick="window.showToast('Connecting AI subsystems…', 'info')">
              ⚡ Quick Sync
            </button>
          </div>
        </div>
      </div>

      <!-- Overview Cards Grid -->
      <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:18px; margin-bottom: 24px;">
        <div class="glass-card">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
            <span style="font-size:0.8rem; font-weight:600; color:var(--text-secondary); text-transform:uppercase;">Digital Avatar</span>
            <span class="status-chip success">Ready</span>
          </div>
          <div style="display:flex; align-items:center; gap:14px;">
            <div style="width:48px; height:48px; border-radius:50%; background:var(--accent-bg); border:1px solid var(--accent); display:flex; align-items:center; justify-content:center; color:var(--accent); font-size:1.2rem;">
              ARIA
            </div>
            <div>
              <div style="font-weight:700; font-size:1rem;">Female Assistant (ARIA)</div>
              <div style="font-size:0.8rem; color:var(--text-muted);">Idle · Awaiting Phase 5 Avatar Renderer</div>
            </div>
          </div>
        </div>

        <div class="glass-card">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
            <span style="font-size:0.8rem; font-weight:600; color:var(--text-secondary); text-transform:uppercase;">Voice Pipeline</span>
            <span class="status-chip success">Armed</span>
          </div>
          <div style="font-weight:700; font-size:1rem; margin-bottom:4px;">Audio-Reactive Subsystem</div>
          <div style="font-size:0.8rem; color:var(--text-muted);">Single mic owner · Phase 6 Integration</div>
        </div>

        <div class="glass-card">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
            <span style="font-size:0.8rem; font-weight:600; color:var(--text-secondary); text-transform:uppercase;">Agent Hub</span>
            <span class="status-chip">Worktree Safe</span>
          </div>
          <div style="font-weight:700; font-size:1rem; margin-bottom:4px;">Multi-Agent Orchestrator</div>
          <div style="font-size:0.8rem; color:var(--text-muted);">Antigravity + Copilot active · Codex paused</div>
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
  window.JARVIS_SHELL = {
    state,
    navigateTo,
    applyTheme,
    applyAccent,
  };

  // Boot on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
