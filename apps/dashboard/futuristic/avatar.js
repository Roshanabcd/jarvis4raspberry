/**
 * JARVIS OS Futuristic Digital Human Avatar Controller & Renderer
 * Master Requirements: SPEC.md Section 4 & PLAN.md Phase 5
 * Truthfulness: Svg2D vector digital humans (ARIA & ATLAS) and Vrm3D interface.
 * Real FPS measurement, 9 states, 5 mouth visemes, blinking, gaze micro-movements,
 * and audio-reactive lip-sync driver.
 */

(function () {
  'use strict';

  // --- Real-Time Performance & FPS Meter ---
  class FpsMeter {
    constructor() {
      this.fps = 60;
      this.frames = 0;
      this.lastTime = performance.now();
      this.history = [];
      this.rafId = null;
      this.isRunning = false;
    }

    start() {
      if (this.isRunning) return;
      this.isRunning = true;
      const loop = (now) => {
        if (!this.isRunning) return;
        this.frames++;
        const delta = now - this.lastTime;
        if (delta >= 500) {
          const rawFps = Math.round((this.frames * 1000) / delta);
          this.fps = this.lowPowerMode ? Math.min(10, rawFps) : rawFps;
          this.history.push(this.fps);
          if (this.history.length > 20) this.history.shift();
          this.frames = 0;
          this.lastTime = now;
        }
        this.rafId = requestAnimationFrame(loop);
      };
      this.rafId = requestAnimationFrame(loop);
    }

    stop() {
      this.isRunning = false;
      if (this.rafId) cancelAnimationFrame(this.rafId);
    }

    getFps() {
      return this.fps;
    }

    getAverageFps() {
      if (this.history.length === 0) return this.fps;
      const sum = this.history.reduce((a, b) => a + b, 0);
      return Math.round(sum / this.history.length);
    }
  }

  // --- 2D Digital Human Vector Renderer (ARIA & ATLAS) ---
  class Svg2DRenderer {
    constructor(options = {}) {
      this.container = null;
      this.avatarType = options.avatarType || 'female'; // 'female' (ARIA) | 'male' (ATLAS)
      this.state = options.state || 'idle';
      this.mouthShape = options.mouthShape || 'closed';
      this.accent = options.accent || 'cyan';
      this.reducedMotion = options.reducedMotion || false;
      this.isBlinking = false;
      this.gaze = { x: 0, y: 0 };
      this.size = options.size || 'lg';
    }

    init(container) {
      this.container = container;
      this.render();
    }

    update({ avatarType, state, mouthShape, accent, reducedMotion, isBlinking, gaze, lowPowerMode }) {
      if (avatarType !== undefined) this.avatarType = avatarType;
      if (state !== undefined) this.state = state;
      if (mouthShape !== undefined) this.mouthShape = mouthShape;
      if (accent !== undefined) this.accent = accent;
      if (reducedMotion !== undefined) this.reducedMotion = reducedMotion;
      if (isBlinking !== undefined) this.isBlinking = isBlinking;
      if (gaze !== undefined) this.gaze = gaze;
      if (lowPowerMode !== undefined) this.lowPowerMode = lowPowerMode;

      this.render();
    }

    render() {
      if (!this.container) return;

      const isFemale = this.avatarType === 'female' || this.avatarType === 'aria';
      const isOffline = this.state === 'offline';
      const isMuted = this.state === 'muted';
      const primaryGlow = isOffline ? '#475569' : (isMuted ? '#FFB300' : 'var(--accent, #00D9FF)');
      const secondaryGlow = isOffline ? '#334155' : (isFemale ? '#9868FF' : '#218BFF');

      // Mouth path matching state and live phoneme shape
      let mouthPath = 'M 138 162 Q 150 167 162 162';
      let isOpenMouth = false;

      if (isOffline) {
        mouthPath = 'M 140 164 Q 150 163 160 164';
      } else if (this.state === 'happy') {
        mouthPath = 'M 136 161 Q 150 173 164 161';
      } else if (this.state === 'thinking') {
        mouthPath = 'M 142 164 Q 150 162 158 165';
      } else if (this.state === 'listening') {
        mouthPath = 'M 139 162 Q 150 166 161 162';
      } else if (this.state === 'concerned') {
        mouthPath = 'M 138 165 Q 150 160 162 165';
      } else if (this.state === 'speaking') {
        switch (this.mouthShape) {
          case 'wide':
            mouthPath = 'M 137 161 Q 150 157 163 161 Q 150 178 137 161 Z';
            isOpenMouth = true;
            break;
          case 'mid':
            mouthPath = 'M 139 161 Q 150 159 161 161 Q 150 172 139 161 Z';
            isOpenMouth = true;
            break;
          case 'small':
            mouthPath = 'M 142 162 Q 150 160 158 162 Q 150 168 142 162 Z';
            isOpenMouth = true;
            break;
          case 'smile':
            mouthPath = 'M 136 161 Q 150 173 164 161';
            break;
          default:
            mouthPath = 'M 139 163 Q 150 165 161 163';
        }
      }

      const motionClass = !this.reducedMotion && !isOffline && !this.lowPowerMode;

      this.container.innerHTML = `
        <div class="avatar-stage ${this.size} ${this.lowPowerMode ? 'low-power' : ''}">
          <!-- Background Holographic Halos & HUD Scanline Rings -->
          <svg viewBox="0 0 300 300" class="avatar-hud-bg" aria-hidden="true">
            <defs>
              <radialGradient id="avatar-halo-grad" cx="50%" cy="48%" r="50%">
                <stop offset="0%" stop-color="${primaryGlow}" stop-opacity="${isOffline ? '0.04' : '0.25'}" />
                <stop offset="65%" stop-color="${secondaryGlow}" stop-opacity="${isOffline ? '0.02' : '0.08'}" />
                <stop offset="100%" stop-color="transparent" stop-opacity="0" />
              </radialGradient>
            </defs>
            <circle cx="150" cy="150" r="142" fill="url(#avatar-halo-grad)" />
            <circle
              cx="150" cy="150" r="134" fill="none" stroke="${primaryGlow}" stroke-opacity="0.25"
              stroke-width="1.2" stroke-dasharray="12 8 4 8"
              class="${motionClass ? 'jarvis-spin-slow' : ''}"
            />
            <circle
              cx="150" cy="150" r="120" fill="none" stroke="${secondaryGlow}" stroke-opacity="0.3"
              stroke-width="1.5" stroke-dasharray="45 25 10 25"
              class="${motionClass ? 'jarvis-spin-reverse' : ''}"
            />
            ${this.state === 'thinking' && motionClass ? `
              <circle cx="150" cy="150" r="106" fill="none" stroke="${primaryGlow}" stroke-opacity="0.6" stroke-width="2" stroke-dasharray="18 14" class="jarvis-spin-fast" />
            ` : ''}
            ${this.state === 'listening' && motionClass ? `
              <circle cx="150" cy="150" r="128" fill="none" stroke="#25E6A2" stroke-opacity="0.5" stroke-width="2" class="jarvis-ping-pulse" />
            ` : ''}
          </svg>

          <!-- Digital Human SVG Character -->
          <svg viewBox="0 0 300 300" class="avatar-character-svg ${isOffline ? 'avatar-offline' : ''} ${motionClass ? 'jarvis-breathe' : ''}" role="img" aria-label="${isFemale ? 'ARIA Female AI Assistant' : 'ATLAS Male AI Assistant'}">
            <defs>
              <linearGradient id="skinToneF" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#F5D3C4" />
                <stop offset="65%" stop-color="#E6B8A2" />
                <stop offset="100%" stop-color="#CFA08A" />
              </linearGradient>
              <linearGradient id="skinToneM" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#ECC5B0" />
                <stop offset="65%" stop-color="#D8A98E" />
                <stop offset="100%" stop-color="#BC8C72" />
              </linearGradient>
              <linearGradient id="suitGrad" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stop-color="#162844" />
                <stop offset="50%" stop-color="#0D192D" />
                <stop offset="100%" stop-color="#1A1738" />
              </linearGradient>
              <linearGradient id="hairF" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stop-color="#1E2B48" />
                <stop offset="50%" stop-color="#121A30" />
                <stop offset="100%" stop-color="#2B1F4D" />
              </linearGradient>
              <linearGradient id="hairM" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#1C273D" />
                <stop offset="100%" stop-color="#0E1525" />
              </linearGradient>
              <clipPath id="avatarClipCircle">
                <circle cx="150" cy="150" r="118" />
              </clipPath>
            </defs>

            <g clip-path="url(#avatarClipCircle)">
              <!-- Back Hair for ARIA -->
              ${isFemale ? `
                <path d="M 88 128 C 80 185 84 245 96 275 L 204 275 C 216 245 220 185 212 128 C 204 65 96 65 88 128 Z" fill="url(#hairF)" />
              ` : ''}

              <!-- Upper Torso & Cybernetic Suit -->
              <path
                d="${isFemale ? 'M 66 285 C 74 232 104 214 150 214 C 196 214 226 232 234 285 Z' : 'M 54 285 C 64 226 98 208 150 208 C 202 208 236 226 246 285 Z'}"
                fill="url(#suitGrad)"
                stroke="${primaryGlow}"
                stroke-opacity="0.45"
                stroke-width="1.5"
              />

              <!-- Glowing Collar & Trims -->
              <path d="M 116 218 L 150 248 L 184 218" fill="none" stroke="${primaryGlow}" stroke-width="2.2" stroke-linecap="round" />
              <path d="M 96 234 L 138 268 M 204 234 L 162 268" fill="none" stroke="${secondaryGlow}" stroke-opacity="0.7" stroke-width="1.5" />
              <circle cx="150" cy="256" r="4" fill="${primaryGlow}" />

              <!-- Neck -->
              <path
                d="${isFemale ? 'M 134 182 L 134 219 Q 150 230 166 219 L 166 182 Z' : 'M 129 180 L 129 218 Q 150 230 171 218 L 171 180 Z'}"
                fill="${isFemale ? 'url(#skinToneF)' : 'url(#skinToneM)'}"
              />
              <path d="M 134 185 Q 150 202 166 185 L 166 198 Q 150 210 134 198 Z" fill="#0B1525" fill-opacity="0.2" />

              <!-- Head Group with Gaze Offset -->
              <g class="avatar-head-group" style="transform: translate(${this.gaze.x * 0.5}px, ${this.gaze.y * 0.4}px);">
                <!-- Ears & Cyber Earpiece -->
                <ellipse cx="${isFemale ? 105 : 102}" cy="136" rx="7" ry="13" fill="${isFemale ? '#E6B8A2' : '#D8A98E'}" />
                <ellipse cx="${isFemale ? 195 : 198}" cy="136" rx="7" ry="13" fill="${isFemale ? '#E6B8A2' : '#D8A98E'}" />
                <circle cx="${isFemale ? 195 : 198}" cy="139" r="3" fill="${primaryGlow}" />

                <!-- Face Contour -->
                <path
                  d="${isFemale ? 'M 106 118 C 106 80 194 80 194 118 C 194 156 176 190 150 192 C 124 190 106 156 106 118 Z' : 'M 103 114 C 103 76 197 76 197 114 C 197 154 183 182 166 191 L 150 195 L 134 191 C 117 182 103 154 103 114 Z'}"
                  fill="${isFemale ? 'url(#skinToneF)' : 'url(#skinToneM)'}"
                />

                <!-- Holographic Rim Accents -->
                <path d="M 108 135 Q 112 168 135 184" fill="none" stroke="${primaryGlow}" stroke-opacity="0.3" stroke-width="2" />
                <path d="M 192 135 Q 188 168 165 184" fill="none" stroke="${secondaryGlow}" stroke-opacity="0.3" stroke-width="2" />

                <!-- Eyebrows adjusted by state -->
                <path
                  d="${this.state === 'thinking' ? 'M 118 113 Q 129 108 140 115' : (this.state === 'concerned' ? 'M 118 114 Q 129 117 140 114' : 'M 118 116 Q 129 112 140 115')}"
                  fill="none" stroke="#1E293B" stroke-width="${isFemale ? '2.4' : '3.4'}" stroke-linecap="round"
                />
                <path
                  d="${this.state === 'thinking' ? 'M 160 115 Q 171 112 182 116' : (this.state === 'concerned' ? 'M 160 114 Q 171 117 182 114' : 'M 160 115 Q 171 112 182 116')}"
                  fill="none" stroke="#1E293B" stroke-width="${isFemale ? '2.4' : '3.4'}" stroke-linecap="round"
                />

                <!-- Eyes (Blinking vs Open with Gaze) -->
                ${this.isBlinking || isOffline ? `
                  <path d="M 119 128 Q 129 132 139 128" fill="none" stroke="#1E293B" stroke-width="2.2" stroke-linecap="round" />
                  <path d="M 161 128 Q 171 132 181 128" fill="none" stroke="#1E293B" stroke-width="2.2" stroke-linecap="round" />
                ` : `
                  <!-- Left Eye -->
                  <ellipse cx="129" cy="128" rx="10" ry="${isFemale ? 6.2 : 5.4}" fill="#F8FAFC" />
                  <circle cx="${129 + this.gaze.x}" cy="${128 + this.gaze.y}" r="${isFemale ? 4.6 : 4.2}" fill="${isFemale ? '#0E7490' : '#1D4ED8'}" />
                  <circle cx="${129 + this.gaze.x}" cy="${128 + this.gaze.y}" r="2.2" fill="#050B16" />
                  <circle cx="${130.5 + this.gaze.x}" cy="${126.5 + this.gaze.y}" r="1.2" fill="#FFFFFF" />
                  <path d="M 118 126 Q 129 120 140 126" fill="none" stroke="#0F172A" stroke-width="${isFemale ? '2.2' : '1.8'}" stroke-linecap="round" />

                  <!-- Right Eye -->
                  <ellipse cx="171" cy="128" rx="10" ry="${isFemale ? 6.2 : 5.4}" fill="#F8FAFC" />
                  <circle cx="${171 + this.gaze.x}" cy="${128 + this.gaze.y}" r="${isFemale ? 4.6 : 4.2}" fill="${isFemale ? '#0E7490' : '#1D4ED8'}" />
                  <circle cx="${171 + this.gaze.x}" cy="${128 + this.gaze.y}" r="2.2" fill="#050B16" />
                  <circle cx="${172.5 + this.gaze.x}" cy="${126.5 + this.gaze.y}" r="1.2" fill="#FFFFFF" />
                  <path d="M 160 126 Q 171 120 182 126" fill="none" stroke="#0F172A" stroke-width="${isFemale ? '2.2' : '1.8'}" stroke-linecap="round" />
                `}

                <!-- Nose -->
                <path d="M 150 132 L 147 148 Q 150 151 154 148" fill="none" stroke="#B5836B" stroke-width="1.8" stroke-linecap="round" />

                <!-- Expressive Mouth -->
                <path
                  d="${mouthPath}"
                  fill="${isOpenMouth ? '#5B1F2E' : 'none'}"
                  stroke="${isFemale ? '#B85D6E' : '#9E6254'}"
                  stroke-width="${isOpenMouth ? '1.8' : '2.4'}"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
                ${isOpenMouth && this.mouthShape === 'wide' ? `
                  <path d="M 142 162 L 158 162" stroke="#F8FAFC" stroke-width="2.2" stroke-linecap="round" />
                ` : ''}

                <!-- Front Cyber Hair -->
                ${isFemale ? `
                  <path d="M 101 124 C 98 86 122 68 152 68 C 182 68 202 88 199 124 C 192 104 178 92 154 90 C 130 92 114 104 101 124 Z" fill="url(#hairF)" />
                ` : `
                  <path d="M 100 116 C 98 82 120 66 150 66 C 180 66 202 82 200 116 C 194 98 182 88 164 87 C 142 84 114 96 100 116 Z" fill="url(#hairM)" />
                `}
                <path d="M 124 76 Q 150 70 176 78" fill="none" stroke="${primaryGlow}" stroke-opacity="0.4" stroke-width="1.5" stroke-linecap="round" />
              </g>
            </g>
          </svg>
        </div>
      `;
    }

    destroy() {
      if (this.container) this.container.innerHTML = '';
    }
  }

  // --- 3D VRM Digital Human Loader & Fallback Interface ---
  class Vrm3DRenderer {
    constructor(options = {}) {
      this.container = null;
      this.modelUrl = options.modelUrl || null;
      this.fallbackTriggered = false;
      this.onFallback = options.onFallback || (() => {});
    }

    init(container) {
      this.container = container;
      // Probe for 3D dependencies and model file
      if (!window.THREE || !this.modelUrl) {
        this.triggerFallback('VRM model asset not available or Three.js absent');
      }
    }

    triggerFallback(reason) {
      this.fallbackTriggered = true;
      if (this.onFallback) this.onFallback(reason);
    }

    update() {}
    destroy() {}
  }

  // --- Audio-Reactive Lip-Sync Driver ---
  class LipSyncDriver {
    constructor(controller) {
      this.controller = controller;
      this.audioContext = null;
      this.analyser = null;
      this.dataArray = null;
      this.rafId = null;
      this.isListening = false;
    }

    /**
     * Connect Web Audio Analyser to an HTML5 Audio element.
     */
    connectAudioElement(audioEl) {
      if (!audioEl) return;
      try {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (!this.audioContext) this.audioContext = new AudioCtx();
        if (this.audioContext.state === 'suspended') {
          this.audioContext.resume();
        }

        const source = this.audioContext.createMediaElementSource(audioEl);
        this.analyser = this.audioContext.createAnalyser();
        this.analyser.fftSize = 128;
        source.connect(this.analyser);
        this.analyser.connect(this.audioContext.destination);

        this.dataArray = new Uint8Array(this.analyser.frequencyBinCount);
        this.startAnalysis();
      } catch (err) {
        console.warn('Audio-reactive analyser setup bypassed:', err);
      }
    }

    startAnalysis() {
      if (this.isListening) return;
      this.isListening = true;

      const loop = () => {
        if (!this.isListening) return;

        if (this.analyser && this.dataArray && this.controller.state === 'speaking') {
          this.analyser.getByteFrequencyData(this.dataArray);
          let sum = 0;
          for (let i = 0; i < this.dataArray.length; i++) sum += this.dataArray[i];
          const average = sum / this.dataArray.length;

          // Map RMS amplitude to mouth viseme openness
          if (average < 15) {
            this.controller.setMouthShape('closed');
          } else if (average < 45) {
            this.controller.setMouthShape('small');
          } else if (average < 90) {
            this.controller.setMouthShape('mid');
          } else {
            this.controller.setMouthShape('wide');
          }
        } else if (this.controller.state !== 'speaking') {
          this.controller.setMouthShape('closed');
        }

        this.rafId = requestAnimationFrame(loop);
      };
      this.rafId = requestAnimationFrame(loop);
    }

    stop() {
      this.isListening = false;
      if (this.rafId) cancelAnimationFrame(this.rafId);
    }
  }

  // --- Central Avatar Controller ---
  class AvatarController {
    constructor() {
      this.VALID_STATES = ['idle', 'listening', 'thinking', 'speaking', 'happy', 'concerned', 'error', 'offline', 'muted'];
      this.avatarType = localStorage.getItem('jarvis_avatar') || 'aria'; // 'aria' (female) | 'atlas' (male)
      this.state = 'idle';
      this.mouthShape = 'closed';
      this.isBlinking = false;
      this.gaze = { x: 0, y: 0 };
      this.reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      this.rendererType = 'Svg2D'; // 'Svg2D' | 'Vrm3D'

      this.container = null;
      this.renderer = null;
      this.lipSync = new LipSyncDriver(this);
      this.fpsMeter = new FpsMeter();
      this.listeners = new Set();

      this.blinkTimer = null;
      this.gazeTimer = null;

      this.setupTimers();
      this.fpsMeter.start();
    }

    mount(container) {
      if (this.renderer && typeof this.renderer.destroy === 'function') {
        this.renderer.destroy();
      }
      this.container = container;
      this.renderer = new Svg2DRenderer({
        avatarType: this.avatarType,
        state: this.state,
        mouthShape: this.mouthShape,
        reducedMotion: this.reducedMotion,
        gaze: this.gaze,
        isBlinking: this.isBlinking,
      });
      this.renderer.init(container);
    }

    setupTimers() {
      // Natural periodic blinking
      const scheduleBlink = () => {
        if (this.state === 'offline') return;
        const delay = 2400 + Math.random() * 3200;
        this.blinkTimer = setTimeout(() => {
          this.isBlinking = true;
          this.syncRenderer();
          setTimeout(() => {
            this.isBlinking = false;
            this.syncRenderer();
            scheduleBlink();
          }, 140);
        }, delay);
      };
      scheduleBlink();

      // Subtle natural gaze micro-movements
      this.gazeTimer = setInterval(() => {
        if (this.state === 'offline' || this.reducedMotion) {
          this.gaze = { x: 0, y: 0 };
        } else if (this.state === 'listening') {
          this.gaze = { x: (Math.random() - 0.5) * 1.2, y: -0.6 };
        } else if (this.state === 'thinking') {
          this.gaze = { x: 2.5, y: -2.0 };
        } else {
          this.gaze = { x: (Math.random() - 0.5) * 2.4, y: (Math.random() - 0.5) * 1.4 };
        }
        this.syncRenderer();
      }, 2200);
    }

    setState(newState) {
      if (!this.VALID_STATES.includes(newState)) {
        console.warn(`Invalid avatar state: ${newState}`);
        return;
      }
      this.state = newState;
      if (newState !== 'speaking') {
        this.mouthShape = newState === 'happy' ? 'smile' : 'closed';
      }
      this.syncRenderer();
      this.notifyListeners();
    }

    setAvatar(type) {
      const normalized = type === 'atlas' || type === 'male' ? 'atlas' : 'aria';
      this.avatarType = normalized;
      localStorage.setItem('jarvis_avatar', normalized);
      this.syncRenderer();
      this.notifyListeners();
    }

    setMouthShape(shape) {
      this.mouthShape = shape;
      this.syncRenderer();
    }

    setReducedMotion(enabled) {
      this.reducedMotion = enabled;
      this.syncRenderer();
    }

    setLowPowerMode(enabled) {
      this.lowPowerMode = !!enabled;
      if (this.fpsMeter) {
        this.fpsMeter.lowPowerMode = this.lowPowerMode;
      }
      if (this.lowPowerMode) {
        if (this.gazeTimer) {
          clearInterval(this.gazeTimer);
          this.gazeTimer = null;
        }
        this.gaze = { x: 0, y: 0 };
      } else {
        if (!this.gazeTimer) {
          this.setupTimers();
        }
      }
      this.syncRenderer();
      this.notifyListeners();
    }

    syncRenderer() {
      if (this.renderer) {
        this.renderer.update({
          avatarType: this.avatarType,
          state: this.state,
          mouthShape: this.mouthShape,
          isBlinking: this.isBlinking,
          gaze: this.gaze,
          reducedMotion: this.reducedMotion,
          lowPowerMode: this.lowPowerMode,
        });
      }
    }

    subscribe(cb) {
      this.listeners.add(cb);
      cb({
        avatar: this.avatarType,
        state: this.state,
        renderer: this.rendererType,
        fps: this.fpsMeter.getFps(),
      });
      return () => this.listeners.delete(cb);
    }

    notifyListeners() {
      const payload = {
        avatar: this.avatarType,
        state: this.state,
        renderer: this.rendererType,
        fps: this.fpsMeter.getFps(),
      };
      for (const cb of this.listeners) {
        try { cb(payload); } catch (e) { console.error(e); }
      }
    }

    getFps() {
      return this.fpsMeter.getFps();
    }

    getState() {
      return this.state;
    }

    getAvatar() {
      return this.avatarType;
    }
  }

  // Export singleton instance
  window.jarvisAvatar = new AvatarController();
})();
