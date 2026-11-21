/**
 * JARVIS AI OS — Operator Profile & Account Center (#tab-account)
 * Cyber-industrial, fully-decoupled operator management & RBAC subsystem.
 */

(function (root) {
  'use strict';

  const AccountCenter = {
    currentUser: null,
    preferences: {
      default_tab: 'home',
      voice_greeting: true,
      auto_speak_notifications: false,
      voice_actor: 'en_GB-alan-medium',
      default_model: 'llama3:latest'
    },
    users: [],
    activity: [],
    sessionRemaining: 300,
    sessionMax: 300,
    sessionTimerId: null,
    confirmActionCallback: null,

    init() {
      // Periodic identity badge sync
      this.refreshIdentityStatus();
      setInterval(() => this.refreshIdentityStatus(), 10000);

      // Start local countdown tick
      this.startSessionTimer();

      // Hook up any startup preferences if stored
      this.loadPreferences();
    },

    async loadAccountCenter() {
      try {
        await Promise.all([
          this.loadProfile(),
          this.loadPreferences(),
          this.loadUsers(),
          this.loadActivity()
        ]);
        this.renderAll();
      } catch (err) {
        console.error('[AccountCenter] load error:', err);
        if (root.jarvisNotify) {
          root.jarvisNotify.error('Failed to load Account Center data: ' + err.message);
        }
      }
    },

    async loadProfile() {
      try {
        const res = await fetch('/api/account/profile');
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        this.currentUser = data.user || data;
        this.sessionRemaining = data.session_remaining_s != null ? Math.round(data.session_remaining_s) : (data.session ? data.session.ttl_remaining : 300);
        this.sessionMax = data.session_ttl_s != null ? Math.round(data.session_ttl_s) : (data.session ? data.session.ttl_total : 300);
        return this.currentUser;
      } catch (e) {
        console.warn('[AccountCenter] profile fetch error:', e);
        return null;
      }
    },

    async loadPreferences() {
      try {
        const res = await fetch('/api/account/preferences');
        if (res.ok) {
          const data = await res.json();
          if (data.preferences) {
            this.preferences = Object.assign(this.preferences, data.preferences);
          }
        }
      } catch (e) {
        console.warn('[AccountCenter] preferences fetch error:', e);
      }
      return this.preferences;
    },

    async loadUsers() {
      try {
        const res = await fetch('/api/identity/users');
        if (res.ok) {
          const data = await res.json();
          this.users = data.users || [];
        }
      } catch (e) {
        console.warn('[AccountCenter] users fetch error:', e);
      }
      return this.users;
    },

    async loadActivity() {
      try {
        const res = await fetch('/api/account/activity');
        if (res.ok) {
          const data = await res.json();
          this.activity = data.activity || [];
        }
      } catch (e) {
        console.warn('[AccountCenter] activity fetch error:', e);
      }
      return this.activity;
    },

    async refreshIdentityStatus() {
      try {
        const res = await fetch('/api/identity/status');
        if (!res.ok) return;
        const data = await res.json();
        const active = data.active_user || {};
        const role = data.authorization_role || active.role || 'GUEST';
        const name = active.display_name || (data.is_admin_enrolled ? 'Roshan' : 'Guest');
        const avatarUrl = active.avatar_url || '';
        const avatarPreset = active.avatar_preset || 'jarvis';

        if (this.currentUser) {
          this.currentUser.role = role;
          this.currentUser.display_name = name;
        }

        this.updateHeaderPill(name, role, avatarUrl, avatarPreset);
        this.updateSidebarCard(name, role, avatarUrl, avatarPreset);
        this.updatePopoverStatus(name, role, data.is_admin_enrolled);
      } catch (e) {
        /* ignore network blip */
      }
    },

    updateHeaderPill(name, role, avatarUrl, avatarPreset) {
      const pill = document.getElementById('hdr-user-pill');
      if (!pill) return;

      const nameEl = document.getElementById('hdr-pill-name');
      const roleEl = document.getElementById('hdr-pill-role');
      const dotEl = document.getElementById('hdr-pill-dot');
      const avatarEl = document.getElementById('hdr-pill-avatar');

      if (nameEl) nameEl.textContent = name;
      if (roleEl) roleEl.textContent = role;

      if (dotEl) {
        dotEl.className = 'sidebar-op-role-dot ' + (role.toLowerCase());
      }

      if (avatarEl) {
        if (avatarUrl) {
          avatarEl.innerHTML = `<img src="${avatarUrl}" alt="${name}">`;
        } else {
          avatarEl.textContent = name.charAt(0).toUpperCase();
        }
      }

      // Legacy fallback
      if (!nameEl) {
        pill.textContent = `👤 ${name} (${role})`;
        pill.className = role === 'ADMIN' ? 'status-pill live' : 'status-pill';
      }
    },

    updateSidebarCard(name, role, avatarUrl, avatarPreset) {
      const nameEl = document.getElementById('sidebar-operator-name');
      const roleEl = document.getElementById('sidebar-role-text');
      const dotEl = document.getElementById('sidebar-role-dot');
      const avatarEl = document.getElementById('sidebar-avatar');

      if (nameEl) nameEl.textContent = name;
      if (roleEl) roleEl.textContent = role;
      if (dotEl) {
        dotEl.className = 'sidebar-op-role-dot ' + (role.toLowerCase());
      }
      if (avatarEl) {
        if (avatarUrl) {
          avatarEl.innerHTML = `<img src="${avatarUrl}" alt="${name}">`;
        } else {
          avatarEl.innerHTML = `<span>${name.charAt(0).toUpperCase()}</span>`;
        }
      }
    },

    updatePopoverStatus(name, role, isAdminEnrolled) {
      const badge = document.getElementById('popover-role-badge');
      if (badge) {
        badge.textContent = role;
        badge.className = 'jarvis-account-role-badge ' + (role.toLowerCase());
      }
      const banner = document.getElementById('admin-enroll-status-banner');
      if (banner) {
        if (isAdminEnrolled) {
          banner.innerHTML = `Operator: <strong>${name}</strong> • Level: <strong>${role}</strong>. Privileged actions require verified PIN.`;
        } else {
          banner.textContent = 'No administrator enrolled. Use First-Time Setup to initialize root credentials.';
        }
      }
    },

    renderAll() {
      this.renderHero();
      this.renderKpis();
      this.renderUsersTable();
      this.renderActivityFeed();
      this.renderPreferencesForm();
      this.updateSessionUi();
    },

    renderHero() {
      const user = this.currentUser || {};
      for (const [id, value] of [
        ['account-display-name-input', user.display_name],
        ['account-bio-input', user.bio],
        ['account-callsign-input', user.callsign]
      ]) {
        const input = document.getElementById(id);
        if (input) input.value = value || '';
      }
      const roleBadge = document.getElementById('account-role-badge');
      if (roleBadge) {
        roleBadge.textContent = user.role || 'Unavailable';
        roleBadge.className = 'account-badge-role ' + (user.role || '').toLowerCase();
      }

      // Avatar
      const avatarInner = document.getElementById('account-avatar-inner');
      if (avatarInner) {
        if (user.avatar_url) {
          avatarInner.innerHTML = `<img src="${user.avatar_url}?t=${Date.now()}" alt="${user.display_name}">`;
        } else {
          avatarInner.innerHTML = `<span>${(user.display_name || 'R').charAt(0).toUpperCase()}</span>`;
        }
      }

      // Presets highlight
      document.querySelectorAll('.avatar-preset-pill').forEach(pill => {
        const preset = pill.dataset.preset;
        if (preset === (user.avatar_preset || 'jarvis')) {
          pill.classList.add('active');
        } else {
          pill.classList.remove('active');
        }
      });
    },

    renderKpis() {
      const user = this.currentUser || {};
      const role = user.role || 'Unavailable';

      const kpiRole = document.getElementById('kpi-role-level');
      if (kpiRole) {
        kpiRole.textContent = role;
        kpiRole.style.color = role === 'ADMIN' ? '#00ff88' : role === 'USER' ? '#00d2ff' : '#ffb000';
      }

      const kpiSession = document.getElementById('kpi-session-status');
      if (kpiSession) {
        kpiSession.textContent = role === 'Unavailable' ? role : role === 'ADMIN' ? 'ELEVATED' : 'STANDARD';
        kpiSession.style.color = role === 'ADMIN' ? '#00ff88' : '#7aa5b9';
      }

      const kpiFace = document.getElementById('kpi-face-status');
      if (kpiFace) {
        kpiFace.textContent = user.has_face_enrolled ? 'ACTIVE' : 'NOT SET';
        kpiFace.style.color = user.has_face_enrolled ? '#00d2ff' : '#64748b';
      }

      const kpiUsers = document.getElementById('kpi-total-users');
      if (kpiUsers) {
        kpiUsers.textContent = String(this.users.length || 1);
      }
    },

    renderUsersTable() {
      const tbody = document.getElementById('account-users-table-body');
      if (!tbody) return;

      if (!this.users || this.users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--muted);padding:16px">No registered operators found.</td></tr>';
        return;
      }

      let html = '';
      this.users.forEach(u => {
        const initial = (u.display_name || 'U').charAt(0).toUpperCase();
        const roleClass = (u.role || 'guest').toLowerCase();
        const avatarImg = u.avatar_url ? `<img src="${u.avatar_url}" style="width:24px;height:24px;border-radius:50%;object-fit:cover">` : `<span style="width:24px;height:24px;border-radius:50%;background:#093245;color:#00d2ff;display:inline-flex;align-items:center;justify-content:center;font-size:0.75rem;font-weight:700">${initial}</span>`;
        const faceBadge = u.has_face_enrolled ? '<span style="color:#00ff88">● Enrolled</span>' : '<span style="color:var(--muted)">○ None</span>';
        const pinBadge = u.has_pin ? '<span style="color:#00d2ff">Configured</span>' : '<span style="color:var(--muted)">None</span>';
        const lastSeen = u.last_seen_at ? new Date(u.last_seen_at).toLocaleTimeString() : (u.created_at ? 'Registered' : 'Recent');

        html += `
          <tr data-user-id="${u.id}">
            <td style="display:flex;align-items:center;gap:8px">
              ${avatarImg}
              <div>
                <strong>${u.display_name}</strong>
                ${u.callsign ? `<div style="font-size:0.7rem;color:#7aa5b9">"${u.callsign}"</div>` : ''}
              </div>
            </td>
            <td><span class="account-badge-role ${roleClass}" style="font-size:0.68rem;padding:2px 8px">${u.role}</span></td>
            <td>${pinBadge}</td>
            <td>${faceBadge}</td>
            <td style="font-size:0.75rem;color:#91b6c9">${lastSeen}</td>
            <td>
              <div style="display:flex;gap:4px">
                <button class="btn dark" style="padding:2px 6px;font-size:0.7rem" onclick="AccountCenter.promptChangeUserRole('${u.id}', '${u.role}')" title="Change operator access role">Role</button>
                <button class="btn dark" style="padding:2px 6px;font-size:0.7rem" onclick="AccountCenter.promptResetUserPin('${u.id}', '${u.display_name}')" title="Reset operator PIN">PIN</button>
                <button class="btn dark" style="padding:2px 6px;font-size:0.7rem;color:#ff3366" onclick="AccountCenter.promptDeleteUser('${u.id}', '${u.display_name}', '${u.role}')" title="Remove operator">✕</button>
              </div>
            </td>
          </tr>
        `;
      });
      tbody.innerHTML = html;
    },

    renderActivityFeed() {
      const feed = document.getElementById('account-activity-feed');
      if (!feed) return;

      if (!this.activity || this.activity.length === 0) {
        feed.innerHTML = '<div style="color:var(--muted);font-size:0.78rem;text-align:center;padding:16px">No security events recorded yet.</div>';
        return;
      }

      let html = '';
      this.activity.slice(0, 25).forEach(item => {
        const time = item.timestamp ? new Date(item.timestamp).toLocaleTimeString() : 'Just now';
        const action = item.action || 'AUTH';
        let actionColor = '#00d2ff';
        if (action.includes('LOCK') || action.includes('DENIED')) actionColor = '#ff3366';
        else if (action.includes('ELEVATE') || action.includes('LOGIN') || action.includes('ENROLL')) actionColor = '#00ff88';

        html += `
          <div class="account-activity-item">
            <div class="account-activity-desc">
              <div style="display:flex;align-items:center;gap:6px">
                <span style="font-size:0.7rem;font-weight:700;color:${actionColor};border:1px solid ${actionColor}44;padding:1px 5px;border-radius:4px">${action}</span>
                <span style="font-size:0.8rem;color:#e2e8f0">${item.detail || item.action}</span>
              </div>
              <span class="account-activity-time">${time} • Client: ${item.client_ip || 'local'}</span>
            </div>
          </div>
        `;
      });
      feed.innerHTML = html;
    },

    renderPreferencesForm() {
      const tabSelect = document.getElementById('pref-default-tab');
      if (tabSelect && this.preferences.default_tab) {
        tabSelect.value = this.preferences.default_tab;
      }

      const voiceChk = document.getElementById('pref-voice-greeting');
      if (voiceChk) {
        voiceChk.checked = Boolean(this.preferences.voice_greeting);
      }

      const speechMode = document.getElementById('pref-speech-mode');
      if (speechMode && this.preferences.auto_speak_notifications) {
        speechMode.value = this.preferences.auto_speak_notifications;
      }

      const actorSel = document.getElementById('pref-voice-actor');
      if (actorSel && this.preferences.voice_actor) {
        actorSel.value = this.preferences.voice_actor;
      }
    },

    startSessionTimer() {
      if (this.sessionTimerId) clearInterval(this.sessionTimerId);
      this.sessionTimerId = setInterval(() => {
        if (this.sessionRemaining > 0) {
          this.sessionRemaining--;
          this.updateSessionUi();
        } else {
          // If session expired while role is admin, trigger lockdown warning
          if (this.currentUser && this.currentUser.role === 'ADMIN') {
            this.currentUser.role = 'GUEST';
            this.updateHeaderPill(this.currentUser.display_name, 'GUEST', this.currentUser.avatar_url);
            this.updateSidebarCard(this.currentUser.display_name, 'GUEST', this.currentUser.avatar_url);
            this.renderKpis();
            if (root.jarvisNotify) {
              root.jarvisNotify.warning('Admin elevation session timed out. Permissions locked to standard operator.');
            }
          }
        }
      }, 1000);
    },

    updateSessionUi() {
      const timerPill = document.getElementById('account-session-timer-text');
      const popoverPill = document.getElementById('popover-session-countdown');
      const progBar = document.getElementById('account-session-progress-bar');

      const isElevated = this.currentUser && this.currentUser.role === 'ADMIN';

      if (!isElevated || this.sessionRemaining <= 0) {
        if (timerPill) {
          timerPill.textContent = 'SESSION LOCKED (GUEST)';
          timerPill.className = 'account-timer-pill warning';
        }
        if (popoverPill) popoverPill.textContent = 'LOCKED';
        if (progBar) progBar.style.width = '0%';
        return;
      }

      const m = Math.floor(this.sessionRemaining / 60);
      const s = this.sessionRemaining % 60;
      const fmt = `${m}m ${s < 10 ? '0' : ''}${s}s`;

      if (timerPill) {
        timerPill.textContent = fmt;
        timerPill.className = this.sessionRemaining < 60 ? 'account-timer-pill warning' : 'account-timer-pill';
      }
      if (popoverPill) popoverPill.textContent = fmt;

      if (progBar && this.sessionMax > 0) {
        const pct = Math.max(0, Math.min(100, (this.sessionRemaining / this.sessionMax) * 100));
        progBar.style.width = `${pct}%`;
      }
    },

    // ─── Actions ─────────────────────────────────────────────────────────

    async saveOperatorProfile() {
      const name = document.getElementById('account-display-name-input')?.value.trim();
      const bio = document.getElementById('account-bio-input')?.value.trim();
      const callsign = document.getElementById('account-callsign-input')?.value.trim();

      if (!name) {
        if (root.jarvisNotify) root.jarvisNotify.error('Operator display name cannot be blank.');
        return;
      }

      try {
        const res = await fetch('/api/account/profile', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ display_name: name, bio, callsign })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Failed to update profile');

        if (root.jarvisNotify) root.jarvisNotify.success(`Profile saved. Callsign set to "${callsign}".`);
        await this.loadAccountCenter();
      } catch (e) {
        if (root.jarvisNotify) root.jarvisNotify.error('Save failed: ' + e.message);
      }
    },

    async uploadAvatarFile(input) {
      if (!input || !input.files || !input.files[0]) return;
      const file = input.files[0];
      const formData = new FormData();
      formData.append('file', file);

      try {
        if (root.jarvisNotify) root.jarvisNotify.info('Uploading operator avatar photo...');
        const res = await fetch('/api/account/avatar', {
          method: 'POST',
          body: formData
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Avatar upload failed');

        if (root.jarvisNotify) root.jarvisNotify.success('Custom avatar uploaded and synchronized.');
        await this.loadAccountCenter();
      } catch (e) {
        if (root.jarvisNotify) root.jarvisNotify.error('Avatar upload error: ' + e.message);
      } finally {
        input.value = '';
      }
    },

    async selectAvatarPreset(preset) {
      try {
        const res = await fetch('/api/account/avatar/preset', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ preset })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Failed to apply preset');

        if (root.jarvisNotify) root.jarvisNotify.success(`Avatar preset "${preset}" active.`);
        await this.loadAccountCenter();
      } catch (e) {
        if (root.jarvisNotify) root.jarvisNotify.error('Preset error: ' + e.message);
      }
    },

    openCameraAvatarModal() {
      const modal = document.getElementById('avatar-camera-modal');
      if (modal) modal.classList.add('open');
      const img = document.getElementById('avatar-camera-stream');
      if (img) img.src = '/api/vision/stream?t=' + Date.now();
    },

    closeCameraAvatarModal() {
      const modal = document.getElementById('avatar-camera-modal');
      if (modal) modal.classList.remove('open');
      const img = document.getElementById('avatar-camera-stream');
      if (img) img.src = '';
    },

    async captureCameraAvatar() {
      try {
        if (root.jarvisNotify) root.jarvisNotify.info('Capturing frame from Sony IMX708 camera...');
        const res = await fetch('/api/account/avatar/capture', { method: 'POST' });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Camera capture failed');

        if (root.jarvisNotify) root.jarvisNotify.success('Camera snapshot saved as operator avatar.');
        this.closeCameraAvatarModal();
        await this.loadAccountCenter();
      } catch (e) {
        if (root.jarvisNotify) root.jarvisNotify.error('Camera capture error: ' + e.message);
      }
    },

    async elevatePinSubmit() {
      const input = document.getElementById('account-pin-elevate-input');
      const pin = input ? input.value.trim() : '';
      if (!pin) {
        if (root.jarvisNotify) root.jarvisNotify.warning('Enter your administrator PIN to elevate.');
        return;
      }

      try {
        const res = await fetch('/api/identity/verify_pin', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-Jarvis-Client': 'account-center' },
          body: JSON.stringify({ pin })
        });
        const data = await res.json();
        if (!res.ok || data.authorization_role !== 'ADMIN') {
          throw new Error(data.detail || 'Invalid administrator PIN');
        }

        if (root.jarvisNotify) {
          root.jarvisNotify.success(`Identity elevated: ${data.active_user.display_name} (ADMIN)`);
        }

        // Voice Greeting
        if (this.preferences.voice_greeting) {
          const callsign = this.currentUser?.callsign || data.active_user.display_name || 'Commander';
          this.triggerVoiceGreeting(`Welcome back, ${callsign}. All security and actuation protocols elevated.`);
        }

        if (input) input.value = '';
        await this.loadAccountCenter();
      } catch (e) {
        if (root.jarvisNotify) root.jarvisNotify.error(e.message);
      }
    },

    async submitChangePinForm() {
      const curr = document.getElementById('change-pin-curr')?.value;
      const next = document.getElementById('change-pin-new')?.value;
      const conf = document.getElementById('change-pin-confirm')?.value;

      if (!next || next.length < 4) {
        if (root.jarvisNotify) root.jarvisNotify.warning('New PIN must be at least 4 digits.');
        return;
      }
      if (next !== conf) {
        if (root.jarvisNotify) root.jarvisNotify.error('New PINs do not match.');
        return;
      }

      try {
        const res = await fetch('/api/account/change_pin', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ current_pin: curr, new_pin: next, confirm_pin: conf })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'PIN change failed');

        if (root.jarvisNotify) root.jarvisNotify.success('Administrator PIN changed successfully.');
        document.getElementById('change-pin-curr').value = '';
        document.getElementById('change-pin-new').value = '';
        document.getElementById('change-pin-confirm').value = '';
        await this.loadAccountCenter();
      } catch (e) {
        if (root.jarvisNotify) root.jarvisNotify.error(e.message);
      }
    },

    async setSessionDurationPolicy(minutes) {
      try {
        const ttl_s = minutes * 60;
        const res = await fetch('/api/account/session/duration', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ttl_s })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Failed to update policy');

        const label = minutes >= 60 ? `${minutes / 60} hour(s)` : `${minutes} minutes`;
        if (root.jarvisNotify) root.jarvisNotify.info(`Session duration policy updated to ${label}.`);
        this.sessionMax = ttl_s;
        this.sessionRemaining = ttl_s;
        this.updateSessionUi();
      } catch (e) {
        if (root.jarvisNotify) root.jarvisNotify.error(e.message);
      }
    },

    async extendAdminSession(minutes) {
      try {
        const duration_s = (minutes || 15) * 60;
        const res = await fetch('/api/account/session/extend', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ duration_s })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Could not extend session');

        this.sessionRemaining += duration_s;
        this.sessionMax = Math.max(this.sessionMax, this.sessionRemaining);
        if (root.jarvisNotify) root.jarvisNotify.success(`Admin session extended by ${minutes || 15} minutes.`);
        this.updateSessionUi();
      } catch (e) {
        if (root.jarvisNotify) root.jarvisNotify.error(e.message);
      }
    },

    async lockAdminSession() {
      try {
        await fetch('/api/identity/logout', { method: 'POST', headers: { 'X-Jarvis-Client': 'account-center' } });
        if (root.jarvisNotify) root.jarvisNotify.warning('Operator session locked. Root privileges dropped.');

        if (this.preferences.voice_greeting) {
          this.triggerVoiceGreeting('Session secured. Terminal locked.');
        }

        this.sessionRemaining = 0;
        await this.loadAccountCenter();
      } catch (e) {
        if (root.jarvisNotify) root.jarvisNotify.error('Lock error: ' + e.message);
      }
    },

    openFaceEnrollModal() {
      const modal = document.getElementById('account-face-enroll-modal');
      if (modal) modal.classList.add('open');
      const img = document.getElementById('face-enroll-stream');
      if (img) img.src = '/api/vision/stream?t=' + Date.now();
    },

    closeFaceEnrollModal() {
      const modal = document.getElementById('account-face-enroll-modal');
      if (modal) modal.classList.remove('open');
      const img = document.getElementById('face-enroll-stream');
      if (img) img.src = '';
    },

    async submitFaceEnroll() {
      const pin = document.getElementById('face-enroll-pin')?.value;
      if (!pin) {
        if (root.jarvisNotify) root.jarvisNotify.warning('Enter your administrator PIN to confirm face enrollment.');
        return;
      }

      try {
        if (root.jarvisNotify) root.jarvisNotify.info('Detecting facial landmark vectors with YuNet model...');
        const res = await fetch('/api/account/face/enroll', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ pin, confirmed: true })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Face enrollment failed');

        if (root.jarvisNotify) root.jarvisNotify.success('YuNet biometric face template enrolled successfully.');
        this.closeFaceEnrollModal();
        await this.loadAccountCenter();
      } catch (e) {
        if (root.jarvisNotify) root.jarvisNotify.error('Biometric enrollment error: ' + e.message);
      }
    },

    openAddUserModal() {
      const modal = document.getElementById('account-add-user-modal');
      if (modal) modal.classList.add('open');
    },

    closeAddUserModal() {
      const modal = document.getElementById('account-add-user-modal');
      if (modal) modal.classList.remove('open');
    },

    async submitAddUser() {
      const name = document.getElementById('add-user-name')?.value.trim();
      const role = document.getElementById('add-user-role')?.value || 'USER';
      const pin = document.getElementById('add-user-pin')?.value.trim();
      const callsign = document.getElementById('add-user-callsign')?.value.trim();

      if (!name) {
        if (root.jarvisNotify) root.jarvisNotify.warning('Operator name is required.');
        return;
      }
      if (pin && pin.length < 4) {
        if (root.jarvisNotify) root.jarvisNotify.warning('PIN must be at least 4 digits.');
        return;
      }

      try {
        const res = await fetch('/api/identity/enroll_admin', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            display_name: name,
            pin: pin || '0000',
            role,
            callsign,
            confirmed: true,
            pin_only: true
          })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Failed to add operator');

        if (root.jarvisNotify) root.jarvisNotify.success(`Operator "${name}" (${role}) registered.`);
        this.closeAddUserModal();
        await this.loadAccountCenter();
      } catch (e) {
        if (root.jarvisNotify) root.jarvisNotify.error(e.message);
      }
    },

    promptChangeUserRole(userId, currentRole) {
      const newRole = currentRole === 'ADMIN' ? 'USER' : currentRole === 'USER' ? 'GUEST' : 'ADMIN';
      this.openConfirmModal({
        title: 'Change Operator Role',
        message: `Change role for operator from "${currentRole}" to "${newRole}"?`,
        confirmText: `Set to ${newRole}`,
        onConfirm: async () => {
          try {
            const res = await fetch('/api/account/users/role', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ user_id: userId, role: newRole })
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || 'Role update failed');
            if (root.jarvisNotify) root.jarvisNotify.success(`Role updated to ${newRole}.`);
            await this.loadAccountCenter();
          } catch (e) {
            if (root.jarvisNotify) root.jarvisNotify.error(e.message);
          }
        }
      });
    },

    promptResetUserPin(userId, userName) {
      const newPin = window.prompt ? window.prompt(`Enter new 4-digit PIN for ${userName}:`, '1234') : '1234';
      if (!newPin) return;

      this.executeResetPin(userId, newPin);
    },

    async executeResetPin(userId, newPin) {
      try {
        const res = await fetch('/api/account/users/reset_pin', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: userId, new_pin: newPin })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'PIN reset failed');
        if (root.jarvisNotify) root.jarvisNotify.success('Operator PIN reset successfully.');
      } catch (e) {
        if (root.jarvisNotify) root.jarvisNotify.error(e.message);
      }
    },

    promptDeleteUser(userId, userName, userRole) {
      // Check last admin
      const adminCount = this.users.filter(u => u.role === 'ADMIN').length;
      if (userRole === 'ADMIN' && adminCount <= 1) {
        if (root.jarvisNotify) {
          root.jarvisNotify.error('Action blocked: Cannot delete the primary / last remaining Administrator account.');
        }
        return;
      }

      this.openConfirmModal({
        title: 'Delete Operator',
        message: `Are you sure you want to permanently delete operator "${userName}"? This cannot be undone.`,
        confirmText: 'Delete Operator',
        danger: true,
        onConfirm: async () => {
          try {
            const res = await fetch(`/api/identity/users/${userId}`, { method: 'DELETE' });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || 'Deletion failed');
            if (root.jarvisNotify) root.jarvisNotify.warning(`Operator "${userName}" deleted.`);
            await this.loadAccountCenter();
          } catch (e) {
            if (root.jarvisNotify) root.jarvisNotify.error(e.message);
          }
        }
      });
    },

    async saveOperatorPreferences() {
      const default_tab = document.getElementById('pref-default-tab')?.value || 'home';
      const voice_greeting = document.getElementById('pref-voice-greeting')?.checked ?? true;
      const auto_speak_notifications = document.getElementById('pref-speech-mode')?.value || 'muted';
      const voice_actor = document.getElementById('pref-voice-actor')?.value || 'en_GB-alan-medium';

      const prefs = {
        default_tab,
        voice_greeting,
        auto_speak_notifications,
        voice_actor
      };

      try {
        const res = await fetch('/api/account/preferences', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(prefs)
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Failed to save preferences');

        this.preferences = Object.assign(this.preferences, prefs);
        if (root.jarvisNotify) root.jarvisNotify.success('Operator preferences saved.');
      } catch (e) {
        if (root.jarvisNotify) root.jarvisNotify.error(e.message);
      }
    },

    async clearSecurityActivity() {
      try {
        const res = await fetch('/api/account/activity/clear', { method: 'POST' });
        if (res.ok) {
          this.activity = [];
          this.renderActivityFeed();
          if (root.jarvisNotify) root.jarvisNotify.info('Security activity log cleared.');
        }
      } catch (e) {
        if (root.jarvisNotify) root.jarvisNotify.error('Clear log failed: ' + e.message);
      }
    },

    async triggerVoiceGreeting(text) {
      try {
        await fetch('/api/voice/speak', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text })
        });
      } catch (e) {
        console.warn('[AccountCenter] voice speak error:', e);
      }
    },

    openConfirmModal({ title, message, confirmText, danger, onConfirm }) {
      const modal = document.getElementById('account-confirm-modal');
      if (!modal) return;
      document.getElementById('confirm-modal-title').textContent = title || 'Confirm Action';
      document.getElementById('confirm-modal-message').textContent = message || 'Are you sure?';

      const btn = document.getElementById('confirm-modal-action-btn');
      btn.textContent = confirmText || 'Confirm';
      btn.className = danger ? 'btn danger' : 'btn ok';

      this.confirmActionCallback = onConfirm;
      modal.classList.add('open');
    },

    closeConfirmModal() {
      const modal = document.getElementById('account-confirm-modal');
      if (modal) modal.classList.remove('open');
      this.confirmActionCallback = null;
    },

    confirmModalAccept() {
      if (this.confirmActionCallback) {
        this.confirmActionCallback();
      }
      this.closeConfirmModal();
    }
  };

  // Expose to window
  root.AccountCenter = AccountCenter;

  // Auto-init on DOMContentLoaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => AccountCenter.init());
  } else {
    AccountCenter.init();
  }

})(window);
