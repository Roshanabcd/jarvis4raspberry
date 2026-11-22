/**
 * JARVIS OS — Unified Notification, Alert Center & Speech Bus
 * Provides stacked glassmorphic toasts, slide-out history drawer,
 * sequential speech queue, and non-blocking replacement for window.alert().
 */

(function (root) {
  'use strict';

  const STORAGE_KEY_HISTORY = 'jarvis_notification_history_v1';
  const STORAGE_KEY_AUTOSPEAK = 'jarvis_auto_speak_notifications';

  let toastContainer = null;
  let historyDrawer = null;
  let drawerOverlay = null;
  let drawerList = null;
  let notifBadge = null;
  let autoSpeakToggle = null;

  let notifications = [];
  let speechQueue = [];
  let isSpeaking = false;
  let currentAudio = null;
  let activeFilter = 'all';

  // Load saved state
  try {
    const saved = localStorage.getItem(STORAGE_KEY_HISTORY);
    if (saved) notifications = JSON.parse(saved).slice(0, 50);
  } catch (_) { notifications = []; }

  function saveHistory() {
    try {
      localStorage.setItem(STORAGE_KEY_HISTORY, JSON.stringify(notifications.slice(0, 50)));
    } catch (_) {}
  }

  function isAutoSpeakEnabled() {
    return localStorage.getItem(STORAGE_KEY_AUTOSPEAK) === 'true';
  }

  function setAutoSpeakEnabled(val) {
    localStorage.setItem(STORAGE_KEY_AUTOSPEAK, val ? 'true' : 'false');
    if (autoSpeakToggle) autoSpeakToggle.checked = !!val;
  }

  // --- Speech Queue ---
  async function speakText(text, onEnd) {
    if (!text || typeof text !== 'string') {
      if (onEnd) onEnd();
      return;
    }
    const cleanText = text
      .replace(/[\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]/gu, '')
      .replace(/`{1,3}[^`]*`{1,3}/g, '')
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
      .replace(/[#*_~]/g, '')
      .trim();

    if (!cleanText) {
      if (onEnd) onEnd();
      return;
    }

    try {
      const res = await fetch('/api/voice/speak', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: cleanText })
      });
      const data = await res.json();
      if (data && data.audio_url) {
        if (currentAudio) {
          try { currentAudio.pause(); currentAudio = null; } catch (_) {}
        }
        const audio = new Audio(data.audio_url);
        currentAudio = audio;
        audio.onended = () => { currentAudio = null; if (onEnd) onEnd(); };
        audio.onerror = () => { currentAudio = null; if (onEnd) onEnd(); };
        await audio.play().catch(() => { if (onEnd) onEnd(); });
        return;
      }
    } catch (e) {
      if (root.speechSynthesis) {
        const u = new SpeechSynthesisUtterance(cleanText);
        u.onend = () => { if (onEnd) onEnd(); };
        u.onerror = () => { if (onEnd) onEnd(); };
        root.speechSynthesis.speak(u);
        return;
      }
    }
    if (onEnd) onEnd();
  }

  function processSpeechQueue() {
    if (isSpeaking || speechQueue.length === 0) return;
    isSpeaking = true;
    const nextItem = speechQueue.shift();
    speakText(nextItem.text, () => {
      isSpeaking = false;
      setTimeout(processSpeechQueue, 250);
    });
  }

  function queueSpeech(text) {
    speechQueue.push({ text, timestamp: Date.now() });
    processSpeechQueue();
  }

  function stopSpeech() {
    speechQueue = [];
    isSpeaking = false;
    if (currentAudio) {
      try { currentAudio.pause(); currentAudio = null; } catch (_) {}
    }
    if (root.speechSynthesis) {
      try { root.speechSynthesis.cancel(); } catch (_) {}
    }
  }

  // --- UI Elements Initialization ---
  function initDOM() {
    if (toastContainer) return;

    // Toast Container
    toastContainer = document.getElementById('jarvis-toast-container');
    if (!toastContainer) {
      toastContainer = document.createElement('div');
      toastContainer.id = 'jarvis-toast-container';
      toastContainer.setAttribute('role', 'region');
      toastContainer.setAttribute('aria-label', 'Notifications');
      document.body.appendChild(toastContainer);
    }

    // Drawer Overlay
    drawerOverlay = document.createElement('div');
    drawerOverlay.className = 'jarvis-drawer-overlay';
    drawerOverlay.onclick = closeDrawer;
    document.body.appendChild(drawerOverlay);

    // Slide-out Drawer
    historyDrawer = document.createElement('div');
    historyDrawer.id = 'jarvis-notif-drawer';
    historyDrawer.innerHTML = `
      <div class="jarvis-drawer-header">
        <div class="jarvis-drawer-title">
          <span>🔔</span>
          <span>Notification Center</span>
          <span class="jarvis-drawer-badge" id="jarvis-drawer-unread-badge">0</span>
        </div>
        <div style="display:flex;gap:8px;align-items:center">
          <button class="btn dark" style="padding:4px 8px;font-size:0.75rem" onclick="jarvisNotify.clearAll()">Clear All</button>
          <button class="jarvis-toast-btn-icon" style="font-size:1.1rem;padding:4px 8px" onclick="jarvisNotify.closeDrawer()">✕</button>
        </div>
      </div>
      <div class="jarvis-drawer-toolbar">
        <div style="display:flex;gap:6px">
          <button class="jarvis-drawer-filter-btn active" data-filter="all" onclick="jarvisNotify.setFilter('all')">All</button>
          <button class="jarvis-drawer-filter-btn" data-filter="unread" onclick="jarvisNotify.setFilter('unread')">Unread</button>
          <button class="jarvis-drawer-filter-btn" data-filter="error" onclick="jarvisNotify.setFilter('error')">Alerts</button>
        </div>
        <label style="display:inline-flex;align-items:center;gap:6px;font-size:0.72rem;color:var(--text);cursor:pointer">
          <input type="checkbox" id="jarvis-drawer-autospeak" ${isAutoSpeakEnabled() ? 'checked' : ''} onchange="jarvisNotify.toggleAutoSpeak(this.checked)">
          <span>Auto-Speak</span>
        </label>
      </div>
      <div class="jarvis-drawer-list" id="jarvis-drawer-list"></div>
    `;
    document.body.appendChild(historyDrawer);
    drawerList = document.getElementById('jarvis-drawer-list');

    notifBadge = document.getElementById('hdr-notif-count');
    autoSpeakToggle = document.getElementById('hdr-auto-speak-notif');
    if (autoSpeakToggle) {
      autoSpeakToggle.checked = isAutoSpeakEnabled();
      autoSpeakToggle.onchange = (e) => setAutoSpeakEnabled(e.target.checked);
    }

    renderDrawerList();
    updateUnreadCount();
  }

  function updateUnreadCount() {
    const unread = notifications.filter(n => !n.read).length;
    if (notifBadge) {
      notifBadge.textContent = unread > 0 ? (unread > 99 ? '99+' : unread) : '';
      notifBadge.style.display = unread > 0 ? 'inline-block' : 'none';
    }
    const drawerBadge = document.getElementById('jarvis-drawer-unread-badge');
    if (drawerBadge) {
      drawerBadge.textContent = unread;
      drawerBadge.style.display = unread > 0 ? 'inline-block' : 'none';
    }
  }

  function renderDrawerList() {
    if (!drawerList) return;
    drawerList.replaceChildren();

    let items = notifications;
    if (activeFilter === 'unread') items = items.filter(n => !n.read);
    else if (activeFilter === 'error') items = items.filter(n => n.severity === 'error' || n.severity === 'warning');

    if (items.length === 0) {
      const empty = document.createElement('div');
      empty.style.cssText = 'color:#64748b;text-align:center;padding:40px 10px;font-size:0.85rem';
      empty.textContent = activeFilter === 'unread' ? 'No unread notifications' : 'No notifications in history';
      drawerList.appendChild(empty);
      return;
    }

    items.forEach(n => {
      const card = document.createElement('div');
      card.className = `jarvis-drawer-item ${!n.read ? 'unread' : ''}`;
      const icons = { info: 'ℹ️', success: '✅', warning: '⚠️', error: '🚨' };
      const timeStr = new Date(n.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

      card.innerHTML = `
        <div style="display:flex;align-items:center;justify-content:space-between;gap:6px">
          <span style="display:flex;align-items:center;gap:6px;font-size:0.8rem;font-weight:600">
            <span>${icons[n.severity] || 'ℹ️'}</span>
            <span style="color:${n.severity === 'error' ? '#ff3366' : n.severity === 'warning' ? '#ffb000' : n.severity === 'success' ? '#00ff88' : '#00d2ff'}">${n.title}</span>
          </span>
          <span style="font-size:0.7rem;color:#64748b">${timeStr}</span>
        </div>
        <div style="font-size:0.82rem;color:#cbd5e1;line-height:1.4">${n.message}</div>
        <div style="display:flex;align-items:center;gap:6px;margin-top:6px">
          <button class="btn dark" style="padding:2px 8px;font-size:0.7rem" onclick="jarvisNotify.speakOne('${n.id}')">🔊 Speak</button>
          ${!n.read ? `<button class="btn dark" style="padding:2px 8px;font-size:0.7rem" onclick="jarvisNotify.markRead('${n.id}')">Mark Read</button>` : ''}
          ${n.action ? `<button class="jarvis-toast-action-btn" style="font-size:0.7rem;padding:2px 8px" id="action-${n.id}">${n.action.text}</button>` : ''}
        </div>
      `;
      if (n.action && n.action.onClick) {
        setTimeout(() => {
          const actBtn = document.getElementById(`action-${n.id}`);
          if (actBtn) actBtn.onclick = () => { n.action.onClick(); closeDrawer(); };
        }, 0);
      }
      drawerList.appendChild(card);
    });
  }

  // --- Dispatch Notification ---
  function notify(severity, message, options = {}) {
    initDOM();
    if (!message) return null;

    const id = 'notif_' + Date.now() + '_' + Math.random().toString(36).substr(2, 6);
    const title = options.title || (severity === 'error' ? 'Critical Alert' : severity === 'warning' ? 'System Warning' : severity === 'success' ? 'Task Completed' : 'JARVIS Notice');
    const autoDismissMs = options.durationMs !== undefined ? options.durationMs : (severity === 'error' ? 10000 : 6500);

    const record = {
      id,
      severity,
      title,
      message,
      timestamp: Date.now(),
      read: false,
      action: options.action
    };

    notifications.unshift(record);
    if (notifications.length > 80) notifications.pop();
    saveHistory();
    updateUnreadCount();
    renderDrawerList();

    // Create Toast Element
    const toast = document.createElement('div');
    toast.className = 'jarvis-toast';
    toast.dataset.severity = severity;
    toast.dataset.id = id;

    const icons = { info: 'ℹ️', success: '✅', warning: '⚠️', error: '🚨' };
    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

    let actionsHtml = '';
    if (options.action && options.action.text) {
      actionsHtml = `<button class="jarvis-toast-action-btn" id="toast-action-${id}">${options.action.text}</button>`;
    }

    toast.innerHTML = `
      <div class="jarvis-toast-header">
        <div class="jarvis-toast-title-row">
          <span class="jarvis-toast-icon">${icons[severity] || 'ℹ️'}</span>
          <span class="jarvis-toast-title">${title}</span>
        </div>
        <span class="jarvis-toast-time">${timeStr}</span>
        <div class="jarvis-toast-controls">
          <button class="jarvis-toast-btn-icon" title="Speak this notification aloud" id="toast-speak-${id}">🔊</button>
          <button class="jarvis-toast-btn-icon" title="Dismiss" id="toast-close-${id}">✕</button>
        </div>
      </div>
      <div class="jarvis-toast-body">${message}</div>
      ${actionsHtml ? `<div class="jarvis-toast-actions">${actionsHtml}</div>` : ''}
      ${autoDismissMs > 0 ? `<div class="jarvis-toast-progress" style="animation-duration:${autoDismissMs}ms"></div>` : ''}
    `;

    toastContainer.prepend(toast);

    const closeBtn = toast.querySelector(`#toast-close-${id}`);
    if (closeBtn) closeBtn.onclick = () => dismissToast(toast, id);

    const speakBtn = toast.querySelector(`#toast-speak-${id}`);
    if (speakBtn) speakBtn.onclick = () => queueSpeech(`${title}. ${message}`);

    const actBtn = toast.querySelector(`#toast-action-${id}`);
    if (actBtn && options.action && options.action.onClick) {
      actBtn.onclick = () => {
        options.action.onClick();
        dismissToast(toast, id);
      };
    }

    if (isAutoSpeakEnabled() || options.speak) {
      queueSpeech(`${title}. ${message}`);
    }

    if (autoDismissMs > 0) {
      setTimeout(() => {
        dismissToast(toast, id);
      }, autoDismissMs);
    }

    return id;
  }

  function dismissToast(toast, id) {
    if (!toast || toast.classList.contains('jarvis-toast-out')) return;
    toast.classList.add('jarvis-toast-out');
    const rec = notifications.find(n => n.id === id);
    if (rec) rec.read = true;
    saveHistory();
    updateUnreadCount();
    setTimeout(() => {
      if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, 320);
  }

  function openDrawer() {
    initDOM();
    notifications.forEach(n => n.read = true);
    saveHistory();
    updateUnreadCount();
    renderDrawerList();
    historyDrawer.classList.add('open');
    drawerOverlay.classList.add('open');
  }

  function closeDrawer() {
    if (historyDrawer) historyDrawer.classList.remove('open');
    if (drawerOverlay) drawerOverlay.classList.remove('open');
  }

  function toggleDrawer() {
    if (historyDrawer && historyDrawer.classList.contains('open')) closeDrawer();
    else openDrawer();
  }

  function clearAll() {
    notifications = [];
    saveHistory();
    updateUnreadCount();
    renderDrawerList();
  }

  function markRead(id) {
    const item = notifications.find(n => n.id === id);
    if (item) { item.read = true; saveHistory(); updateUnreadCount(); renderDrawerList(); }
  }

  function speakOne(id) {
    const item = notifications.find(n => n.id === id);
    if (item) queueSpeech(`${item.title}. ${item.message}`);
  }

  function setFilter(filter) {
    activeFilter = filter;
    document.querySelectorAll('.jarvis-drawer-filter-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.filter === filter);
    });
    renderDrawerList();
  }

  // --- Native Dialog Replacement ---
  root.alert = function (message) {
    const msgStr = typeof message === 'object' ? JSON.stringify(message, null, 2) : String(message);
    const isError = /error|failed|cannot|denied|forbidden|403|500|exception/i.test(msgStr);
    const isRbac = /requires (USER|ADMIN)|403|GUEST/i.test(msgStr);

    if (isRbac) {
      notify('error', msgStr, {
        title: 'Access Restricted (RBAC)',
        action: {
          text: '🔑 Sign In with PIN',
          onClick: () => {
            if (typeof root.toggleAccountPopover === 'function') root.toggleAccountPopover();
          }
        }
      });
    } else {
      notify(isError ? 'error' : 'info', msgStr, {
        title: isError ? 'System Notice' : 'Information'
      });
    }
  };

  root.jarvisConfirm = function (message, onConfirm, onCancel, options = {}) {
    const modalId = 'jarvis-confirm-modal';
    let modal = document.getElementById(modalId);
    if (modal) modal.remove();

    modal = document.createElement('div');
    modal.id = modalId;
    modal.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.65);backdrop-filter:blur(8px);z-index:10010;display:flex;align-items:center;justify-content:center;padding:20px';
    modal.innerHTML = `
      <div style="background:rgba(8,20,32,0.96);border:1px solid #1e4b66;border-radius:14px;box-shadow:0 15px 40px rgba(0,0,0,0.8),0 0 20px rgba(0,210,255,0.15);width:420px;max-width:100%;padding:22px">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">
          <span style="font-size:1.4rem">⚠️</span>
          <h3 style="margin:0;font-size:1.1rem;color:#ffb000;font-weight:700">${options.title || 'Confirmation Required'}</h3>
        </div>
        <p style="font-size:0.9rem;line-height:1.5;color:#e2e8f0;margin-bottom:20px;word-break:break-word">${message}</p>
        <div style="display:flex;justify-content:flex-end;gap:10px">
          <button id="jarvis-confirm-cancel" class="btn dark" style="padding:6px 14px">Cancel</button>
          <button id="jarvis-confirm-ok" class="btn" style="padding:6px 16px;background:#00d2ff;color:#050d18;font-weight:700">Confirm</button>
        </div>
      </div>
    `;
    document.body.appendChild(modal);

    const closeModal = () => { modal.remove(); };
    document.getElementById('jarvis-confirm-cancel').onclick = () => { closeModal(); if (onCancel) onCancel(); };
    document.getElementById('jarvis-confirm-ok').onclick = () => { closeModal(); if (onConfirm) onConfirm(); };
  };

  root.confirm = function (message) {
    console.warn('[JARVIS] Intercepted native window.confirm:', message);
    notify('warning', `Action confirmed: ${message}`, { title: 'Security Confirmation' });
    return true;
  };

  // Export public API
  root.jarvisNotify = {
    info: (msg, opts) => notify('info', msg, opts),
    success: (msg, opts) => notify('success', msg, opts),
    warning: (msg, opts) => notify('warning', msg, opts),
    error: (msg, opts) => notify('error', msg, opts),
    alert: (msg, opts) => root.alert(msg),
    confirm: (msg, onConfirm, onCancel, opts) => root.jarvisConfirm(msg, onConfirm, onCancel, opts),
    openDrawer,
    closeDrawer,
    toggleDrawer,
    clearAll,
    markRead,
    speakOne,
    setFilter,
    toggleAutoSpeak: (val) => setAutoSpeakEnabled(val),
    isAutoSpeakEnabled,
    speakText,
    stopSpeech,
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDOM);
  } else {
    initDOM();
  }
})(window);
