/**
 * JARVIS OS Futuristic Voice Assistant & Audio Waveform Engine
 * Master Requirements: SPEC.md Section 6 & PLAN.md Phase 6
 *
 * Truthfulness:
 * - Real hardware device names from /api/voice/status.
 * - Real audio waveforms via Web Audio AnalyserNode (or ambient resting baseline).
 * - Real voice synthesis via backend /api/voice/speak and staged audio playback.
 * - Audio-reactive mouth modulation (never called "phoneme lip-sync").
 * - Instant barge-in speech interruption (< 300ms cancel gate).
 */

(function () {
  'use strict';

  class JarvisVoiceAssistant {
    constructor() {
      this.container = null;
      this.state = 'idle'; // idle | listening | processing | speaking | muted | offline | error
      this.voiceStatus = null;
      this.wakeStatus = null;
      this.tuning = { speed: 0.85, num_steps: 32, reference_text: '' };
      this.volume = 1.0;
      this.isMuted = false;
      this.pollTimer = null;
      this.lastCancelTimeMs = 0;

      // Web Audio & Visualizer State
      this.audioContext = null;
      this.analyser = null;
      this.dataArray = null;
      this.micStream = null;
      this.micSourceNode = null;
      this.audioElement = null;
      this.audioSourceNode = null;
      this.canvas = null;
      this.canvasCtx = null;
      this.rafId = null;

      // Web Speech Fallback Recognition
      this.speechRecognition = null;
      this.isBrowserListening = false;

      // Subtitles History
      this.currentSubtitles = {
        speaker: 'jarvis',
        text: 'Voice engine online and ready. Say "jarvis" or click the microphone to speak.',
        status: 'Standby',
      };
    }

    init() {
      this.setupAudioElement();
      this.setupWebSpeechFallback();
      this.fetchInitialStatus();
      this.startPolling();
    }

    setupAudioElement() {
      let audio = document.getElementById('jarvis-voice-audio');
      if (!audio) {
        audio = document.createElement('audio');
        audio.id = 'jarvis-voice-audio';
        audio.crossOrigin = 'anonymous';
        audio.style.display = 'none';
        document.body.appendChild(audio);
      }
      this.audioElement = audio;

      audio.addEventListener('play', () => {
        this.setState('speaking');
        this.updateSubtitles('jarvis', this.currentSubtitles.text, 'Speaking');
        if (window.jarvisAvatar) {
          window.jarvisAvatar.setState('speaking');
          if (window.jarvisAvatar.lipSync) {
            window.jarvisAvatar.lipSync.connectAudioElement(this.audioElement);
          }
        }
      });

      audio.addEventListener('ended', () => {
        this.setState(this.isMuted ? 'muted' : 'idle');
        this.updateSubtitles('jarvis', this.currentSubtitles.text, 'Speech completed');
        if (window.jarvisAvatar && window.jarvisAvatar.state === 'speaking') {
          window.jarvisAvatar.setState('idle');
          window.jarvisAvatar.setMouthShape('closed');
        }
      });

      audio.addEventListener('pause', () => {
        if (this.state === 'speaking') {
          this.setState(this.isMuted ? 'muted' : 'idle');
          if (window.jarvisAvatar && window.jarvisAvatar.state === 'speaking') {
            window.jarvisAvatar.setState('idle');
            window.jarvisAvatar.setMouthShape('closed');
          }
        }
      });

      audio.addEventListener('error', (e) => {
        console.warn('Audio playback error:', e);
        this.setState(this.isMuted ? 'muted' : 'idle');
        this.updateSubtitles('jarvis', 'Audio playback failed or format unsupported', 'Playback Error');
        if (window.jarvisAvatar) {
          window.jarvisAvatar.setState('concerned');
        }
      });
    }

    ensureAudioContext() {
      try {
        if (!this.audioContext) {
          const AudioContextClass = window.AudioContext || window.webkitAudioContext;
          if (AudioContextClass) {
            this.audioContext = new AudioContextClass();
          }
        }
        if (this.audioContext && this.audioContext.state === 'suspended') {
          this.audioContext.resume();
        }
        if (this.audioContext && !this.analyser) {
          this.analyser = this.audioContext.createAnalyser();
          this.analyser.fftSize = 256;
          this.analyser.smoothingTimeConstant = 0.8;
          this.dataArray = new Uint8Array(this.analyser.frequencyBinCount);
        }
      } catch (err) {
        console.warn('Web Audio initialization bypassed:', err);
      }
    }

    setupWebSpeechFallback() {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechRecognition) {
        try {
          this.speechRecognition = new SpeechRecognition();
          this.speechRecognition.continuous = false;
          this.speechRecognition.interimResults = true;
          this.speechRecognition.lang = 'en-US';

          this.speechRecognition.onresult = (event) => {
            let interimTranscript = '';
            let finalTranscript = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) {
              if (event.results[i].isFinal) {
                finalTranscript += event.results[i][0].transcript;
              } else {
                interimTranscript += event.results[i][0].transcript;
              }
            }
            const display = finalTranscript || interimTranscript;
            if (display) {
              this.updateSubtitles('user', display, finalTranscript ? 'Transcribed' : 'Listening...');
            }
            if (finalTranscript) {
              this.handleUserVoiceInput(finalTranscript);
            }
          };

          this.speechRecognition.onerror = (event) => {
            console.warn('Speech recognition error:', event.error);
            if (event.error === 'not-allowed') {
              this.handlePermissionDenied();
            } else if (event.error !== 'no-speech') {
              this.updateSubtitles('user', `Speech recognition error: ${event.error}`, 'Recognition Failed');
            }
            this.stopBrowserListening();
          };

          this.speechRecognition.onend = () => {
            this.isBrowserListening = false;
            if (this.state === 'listening') {
              this.setState(this.isMuted ? 'muted' : 'idle');
            }
          };
        } catch (err) {
          console.warn('SpeechRecognition initialization error:', err);
        }
      }
    }

    async fetchInitialStatus() {
      if (!window.jarvisApi) return;
      try {
        const [voiceRes, wakeRes, tuningRes] = await Promise.allSettled([
          window.jarvisApi.getVoiceStatus(),
          window.jarvisApi.getWakeStatus(),
          window.jarvisApi.getVoiceTuning(),
        ]);

        if (voiceRes.status === 'fulfilled') {
          this.voiceStatus = voiceRes.value;
          this.isMuted = Boolean(this.voiceStatus?.muted);
          if (this.isMuted && this.state !== 'speaking') {
            this.state = 'muted';
          }
        }
        if (wakeRes.status === 'fulfilled') {
          this.wakeStatus = wakeRes.value;
        }
        if (tuningRes.status === 'fulfilled' && tuningRes.value.status === 'ok') {
          this.tuning = {
            speed: tuningRes.value.speed ?? 0.85,
            num_steps: tuningRes.value.num_steps ?? 32,
            reference_text: tuningRes.value.reference_text || '',
          };
        }
      } catch (err) {
        console.warn('Error fetching initial voice status:', err);
      }
      this.updateView();
    }

    startPolling() {
      if (this.pollTimer) clearInterval(this.pollTimer);
      this.pollTimer = setInterval(async () => {
        if (!window.jarvisApi) return;
        try {
          const status = await window.jarvisApi.getVoiceStatus();
          this.voiceStatus = status;
          this.isMuted = Boolean(status.muted);
          if (this.isMuted && this.state !== 'speaking' && this.state !== 'listening') {
            this.state = 'muted';
          } else if (!this.isMuted && this.state === 'muted') {
            this.state = 'idle';
          }
          this.updateView();
        } catch (err) {
          if (this.state !== 'offline') {
            this.state = 'offline';
            this.updateView();
          }
        }
      }, 3500);
    }

    setState(newState) {
      this.state = newState;
      this.updateView();
    }

    updateSubtitles(speaker, text, status) {
      this.currentSubtitles = {
        speaker: speaker || 'jarvis',
        text: text || '',
        status: status || '',
      };
      const speakerEl = document.getElementById('voice-subtitles-speaker');
      const textEl = document.getElementById('voice-subtitles-text');
      const statusEl = document.getElementById('voice-subtitles-status');
      const boxEl = document.getElementById('voice-subtitles-box');

      if (speakerEl) {
        speakerEl.textContent = speaker === 'user' ? '👤 YOU' : '🤖 JARVIS';
        speakerEl.className = `voice-subtitles-speaker speaker-${speaker === 'user' ? 'user' : 'jarvis'}`;
      }
      if (textEl) {
        textEl.textContent = text;
      }
      if (statusEl) {
        statusEl.textContent = status ? `[${status}]` : '';
      }
      if (boxEl) {
        boxEl.classList.toggle('active', this.state === 'listening' || this.state === 'speaking');
      }
    }

    // --- Audio-Reactive Waveform Engine ---
    startWaveformLoop() {
      if (this.rafId) cancelAnimationFrame(this.rafId);

      const render = () => {
        if (!this.canvas || !this.canvasCtx) return;
        const width = this.canvas.width;
        const height = this.canvas.height;
        const ctx = this.canvasCtx;

        ctx.clearRect(0, 0, width, height);

        // Background subtle grid/lines
        ctx.strokeStyle = 'rgba(0, 217, 255, 0.08)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(0, height / 2);
        ctx.lineTo(width, height);
        ctx.moveTo(0, height / 2);
        ctx.lineTo(width, 0);
        ctx.stroke();

        let hasLiveAudio = false;

        if (this.analyser && this.dataArray && (this.state === 'speaking' || this.state === 'listening')) {
          this.analyser.getByteFrequencyData(this.dataArray);
          let sum = 0;
          for (let i = 0; i < this.dataArray.length; i++) sum += this.dataArray[i];
          if (sum > 0) hasLiveAudio = true;
        }

        if (hasLiveAudio) {
          // Render Live Frequency Wave Spectrum
          const barCount = 48;
          const barWidth = (width / barCount) - 3;
          const slice = Math.floor(this.dataArray.length / barCount) || 1;

          for (let i = 0; i < barCount; i++) {
            const val = this.dataArray[i * slice] || 0;
            const percent = val / 255;
            const barHeight = Math.max(4, percent * (height - 24));
            const x = i * (barWidth + 3) + 2;
            const y = (height - barHeight) / 2;

            // Gradient: cyan to purple
            const grad = ctx.createLinearGradient(0, y, 0, y + barHeight);
            if (this.state === 'listening') {
              grad.addColorStop(0, '#FF3366');
              grad.addColorStop(1, '#9868FF');
            } else {
              grad.addColorStop(0, '#00D9FF');
              grad.addColorStop(0.6, '#218BFF');
              grad.addColorStop(1, '#9868FF');
            }

            ctx.fillStyle = grad;
            ctx.shadowBlur = 8;
            ctx.shadowColor = this.state === 'listening' ? 'rgba(255,51,102,0.4)' : 'rgba(0,217,255,0.4)';
            ctx.beginPath();
            ctx.roundRect ? ctx.roundRect(x, y, barWidth, barHeight, 2) : ctx.rect(x, y, barWidth, barHeight);
            ctx.fill();
          }
          ctx.shadowBlur = 0;
        } else {
          // Render Ambient Holographic Sine Waves (Resting Baseline)
          const now = performance.now() * 0.002;
          const waveCount = 3;

          for (let w = 0; w < waveCount; w++) {
            ctx.beginPath();
            const phase = now + w * 1.5;
            const amplitude = 12 + w * 6;
            const speed = 0.02 + w * 0.01;

            ctx.strokeStyle = w === 0 ? 'rgba(0, 217, 255, 0.7)' : w === 1 ? 'rgba(152, 104, 255, 0.5)' : 'rgba(33, 139, 255, 0.3)';
            ctx.lineWidth = w === 0 ? 2 : 1.2;

            for (let x = 0; x < width; x += 4) {
              const y = (height / 2) + Math.sin(x * speed + phase) * amplitude * Math.sin((x / width) * Math.PI);
              if (x === 0) ctx.moveTo(x, y);
              else ctx.lineTo(x, y);
            }
            ctx.stroke();
          }
        }

        this.rafId = requestAnimationFrame(render);
      };

      this.rafId = requestAnimationFrame(render);
    }

    // --- Push-to-Talk / Listening Controls ---
    async toggleListening() {
      if (this.state === 'listening') {
        this.stopListening();
      } else {
        await this.startListening();
      }
    }

    async startListening() {
      this.ensureAudioContext();

      // If muted, prompt unmute
      if (this.isMuted) {
        await this.unmute();
      }

      // If currently speaking, barge-in first
      if (this.state === 'speaking') {
        await this.interrupt();
      }

      this.hideErrorBanner();
      this.setState('listening');
      this.updateSubtitles('user', 'Listening... Speak now', 'Listening');

      if (window.jarvisAvatar) {
        window.jarvisAvatar.setState('listening');
      }

      // Request browser microphone stream for live waveform
      try {
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          this.micStream = stream;
          if (this.audioContext && this.analyser) {
            this.micSourceNode = this.audioContext.createMediaStreamSource(stream);
            this.micSourceNode.connect(this.analyser);
          }
        }
      } catch (err) {
        if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
          this.handlePermissionDenied();
          return;
        }
        console.warn('Microphone stream access warning:', err);
      }

      // Trigger Web Speech recognition or push-to-talk backend
      if (this.speechRecognition) {
        try {
          this.isBrowserListening = true;
          this.speechRecognition.start();
        } catch (err) {
          console.warn('Could not start browser speech recognition:', err);
        }
      } else if (window.jarvisApi) {
        // Fallback to backend push-to-talk /api/voice/listen_once
        this.runBackendListenOnce();
      }
    }

    async runBackendListenOnce() {
      try {
        this.updateSubtitles('user', 'Capturing voice audio from microphone...', 'Listening');
        const res = await window.jarvisApi.listenOnce(4);
        this.stopMicStream();
        if (res && res.text) {
          this.updateSubtitles('user', res.text, 'Transcribed');
          await this.handleUserVoiceInput(res.text);
        } else {
          this.updateSubtitles('user', 'No speech detected or transcription idle', 'Idle');
          this.setState(this.isMuted ? 'muted' : 'idle');
          if (window.jarvisAvatar) window.jarvisAvatar.setState('idle');
        }
      } catch (err) {
        console.warn('Backend listen_once error:', err);
        this.stopMicStream();
        this.updateSubtitles('user', 'Voice transcription unavailable: ' + (err.message || 'error'), 'STT Unavailable');
        this.setState(this.isMuted ? 'muted' : 'idle');
        if (window.jarvisAvatar) window.jarvisAvatar.setState('concerned');
      }
    }

    stopListening() {
      this.stopBrowserListening();
      this.stopMicStream();
      this.setState(this.isMuted ? 'muted' : 'idle');
      if (window.jarvisAvatar && window.jarvisAvatar.state === 'listening') {
        window.jarvisAvatar.setState('idle');
      }
    }

    stopBrowserListening() {
      if (this.speechRecognition && this.isBrowserListening) {
        try {
          this.speechRecognition.stop();
        } catch (e) {}
        this.isBrowserListening = false;
      }
    }

    stopMicStream() {
      if (this.micSourceNode) {
        try { this.micSourceNode.disconnect(); } catch (e) {}
        this.micSourceNode = null;
      }
      if (this.micStream) {
        this.micStream.getTracks().forEach((track) => track.stop());
        this.micStream = null;
      }
    }

    handlePermissionDenied() {
      this.stopListening();
      this.setState('error');
      this.showErrorBanner(
        'Microphone Permission Denied',
        'Browser microphone access was blocked or denied. Please grant microphone permission in your browser address bar to use voice commands.',
        () => this.startListening()
      );
      if (window.jarvisAvatar) {
        window.jarvisAvatar.setState('error');
      }
    }

    // --- Command Handling & AI Speech Synthesis ---
    async handleUserVoiceInput(text) {
      if (!text || !text.trim()) return;
      this.setState('processing');
      this.updateSubtitles('jarvis', 'Thinking...', 'Processing');
      if (window.jarvisAvatar) {
        window.jarvisAvatar.setState('thinking');
      }

      try {
        if (!window.jarvisApi) throw new Error('API client not available');

        // Execute inference and synthesize speech via backend
        const synthRes = await window.jarvisApi.synthesizeSpeech(text, {
          speed: this.tuning.speed,
          numSteps: this.tuning.num_steps,
        });

        if (synthRes && synthRes.success && synthRes.audio_url) {
          const replyText = synthRes.text || text;
          this.updateSubtitles('jarvis', replyText, 'Playing');
          this.playAudioUrl(synthRes.audio_url, replyText);
        } else {
          // If backend TTS fails or reports error
          const errDetail = synthRes?.error || 'Speech synthesis failed';
          this.handleTtsFailure(errDetail, text);
        }
      } catch (err) {
        console.warn('Voice command processing error:', err);
        this.handleTtsFailure(err.message, text);
      }
    }

    handleTtsFailure(errorMessage, fallbackText) {
      console.warn('Handling TTS failure:', errorMessage);
      this.setState('error');
      this.updateSubtitles('jarvis', fallbackText ? `[Text Reply]: ${fallbackText}` : 'Speech synthesis unavailable', 'TTS Error');
      this.showErrorBanner('TTS Synthesis Error', `Text-to-speech could not stage audio: ${errorMessage}`, () => {
        this.hideErrorBanner();
        this.setState(this.isMuted ? 'muted' : 'idle');
      });

      // Browser speech synthesis fallback if present
      if (window.speechSynthesis && fallbackText) {
        try {
          const utterance = new SpeechSynthesisUtterance(fallbackText);
          utterance.rate = this.tuning.speed || 1.0;
          utterance.onstart = () => {
            this.setState('speaking');
            if (window.jarvisAvatar) window.jarvisAvatar.setState('speaking');
          };
          utterance.onend = () => {
            this.setState(this.isMuted ? 'muted' : 'idle');
            if (window.jarvisAvatar) window.jarvisAvatar.setState('idle');
          };
          window.speechSynthesis.speak(utterance);
        } catch (e) {
          console.warn('Browser speechSynthesis fallback failed:', e);
        }
      } else {
        if (window.jarvisAvatar) window.jarvisAvatar.setState('concerned');
      }
    }

    playAudioUrl(url, speechText) {
      this.ensureAudioContext();
      if (!this.audioElement) this.setupAudioElement();

      if (speechText) {
        this.updateSubtitles('jarvis', speechText, 'Speaking');
      }

      this.setState('speaking');
      if (window.jarvisAvatar) {
        window.jarvisAvatar.setState('speaking');
      }

      // Connect HTML5 Audio to Web Audio Analyser if not already connected
      if (this.audioContext && this.analyser && !this.audioSourceNode) {
        try {
          this.audioSourceNode = this.audioContext.createMediaElementSource(this.audioElement);
          this.audioSourceNode.connect(this.analyser);
          this.analyser.connect(this.audioContext.destination);
        } catch (err) {
          console.warn('Audio element source connection warning:', err);
        }
      }

      this.audioElement.volume = this.volume;
      this.audioElement.src = url;
      this.audioElement.play().catch((err) => {
        console.warn('Audio play error:', err);
        this.handleTtsFailure(err.message, speechText);
      });
    }

    // --- Barge-In / Speech Interruption ---
    async interrupt() {
      const t0 = performance.now();

      // 1. Halt HTML5 Audio playback immediately
      if (this.audioElement) {
        this.audioElement.pause();
        this.audioElement.currentTime = 0;
      }

      // 2. Halt browser speech synthesis if active
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }

      // 3. Reset avatar state to idle and mouth viseme to closed immediately
      if (window.jarvisAvatar) {
        window.jarvisAvatar.setState('idle');
        window.jarvisAvatar.setMouthShape('closed');
      }

      // 4. Update local state
      this.setState(this.isMuted ? 'muted' : 'idle');
      this.updateSubtitles('jarvis', this.currentSubtitles.text, 'Interrupted');

      // 5. Notify backend to halt hardware/PipeWire playback
      if (window.jarvisApi) {
        try {
          await window.jarvisApi.interruptVoice();
        } catch (err) {
          console.warn('Backend interrupt error:', err);
        }
      }

      const elapsed = performance.now() - t0;
      this.lastCancelTimeMs = elapsed;
      console.log(`[JARVIS Voice] Interruption cancelled speech in ${elapsed.toFixed(1)}ms`);
      return elapsed;
    }

    // --- Mute / Unmute Controls ---
    async toggleMute() {
      if (this.isMuted) {
        await this.unmute();
      } else {
        await this.mute();
      }
    }

    async mute() {
      this.isMuted = true;
      if (this.state === 'listening') {
        this.stopListening();
      }
      this.setState('muted');
      if (window.jarvisApi) {
        try {
          await window.jarvisApi.muteVoice();
        } catch (err) {
          console.warn('Backend mute error:', err);
        }
      }
      this.updateView();
    }

    async unmute() {
      this.isMuted = false;
      this.setState('idle');
      if (window.jarvisApi) {
        try {
          await window.jarvisApi.unmuteVoice();
        } catch (err) {
          console.warn('Backend unmute error:', err);
        }
      }
      this.updateView();
    }

    // --- Diagnostics & Hardware Device Tests ---
    async runMicrophoneTest() {
      if (!window.jarvisApi) return;
      const testBtn = document.getElementById('voice-test-mic-btn');
      if (testBtn) {
        testBtn.disabled = true;
        testBtn.textContent = '⏳ Recording (3s)...';
      }
      this.updateSubtitles('user', 'Recording 3-second hardware microphone sample...', 'Mic Test');

      try {
        const res = await window.jarvisApi.testMicrophone(3);
        if (res && res.success) {
          this.updateSubtitles('user', `Test Result: "${res.transcript || 'Audio signal captured'}" (RMS: ${res.rms_level || 'OK'})`, 'Mic Verified');
        } else {
          this.updateSubtitles('user', `Mic test result: ${res?.error || 'No speech captured'}`, 'Mic Test Result');
        }
      } catch (err) {
        this.updateSubtitles('user', `Microphone hardware test failed: ${err.message}`, 'Test Failed');
      } finally {
        if (testBtn) {
          testBtn.disabled = false;
          testBtn.textContent = '🎙️ Test Mic (3s)';
        }
      }
    }

    async runSpeakerTest() {
      if (!window.jarvisApi) return;
      const testBtn = document.getElementById('voice-test-spk-btn');
      if (testBtn) {
        testBtn.disabled = true;
        testBtn.textContent = '⏳ Testing...';
      }
      this.updateSubtitles('jarvis', 'Playing diagnostic sine tone through hardware speaker...', 'Speaker Test');

      try {
        const res = await window.jarvisApi.testSpeaker();
        if (res && res.success) {
          this.updateSubtitles('jarvis', 'Speaker diagnostic tone played. Confirm aloud if heard.', 'Tone Played');
        } else {
          this.updateSubtitles('jarvis', `Speaker test output: ${res?.error || 'Unavailable'}`, 'Speaker Error');
        }
      } catch (err) {
        this.updateSubtitles('jarvis', `Speaker hardware test failed: ${err.message}`, 'Test Failed');
      } finally {
        if (testBtn) {
          testBtn.disabled = false;
          testBtn.textContent = '🔊 Test Speaker Tone';
        }
      }
    }

    async applyTuning() {
      if (!window.jarvisApi) return;
      const speedInput = document.getElementById('voice-tuning-speed');
      const stepsInput = document.getElementById('voice-tuning-steps');
      const saveBtn = document.getElementById('voice-save-tuning-btn');

      const speed = speedInput ? parseFloat(speedInput.value) : this.tuning.speed;
      const num_steps = stepsInput ? parseInt(stepsInput.value, 10) : this.tuning.num_steps;

      if (saveBtn) {
        saveBtn.disabled = true;
        saveBtn.textContent = 'Saving...';
      }

      try {
        const res = await window.jarvisApi.updateVoiceTuning({ speed, num_steps });
        if (res && res.status === 'ok') {
          this.tuning.speed = speed;
          this.tuning.num_steps = num_steps;
          this.showBanner('Voice tuning parameters updated successfully.', 'success', 3000);
        } else {
          this.showBanner('Failed to update tuning parameters.', 'error', 4000);
        }
      } catch (err) {
        this.showBanner(`Tuning error: ${err.message}`, 'error', 4000);
      } finally {
        if (saveBtn) {
          saveBtn.disabled = false;
          saveBtn.textContent = '💾 Apply Tuning';
        }
      }
    }

    showErrorBanner(title, message, onRetry) {
      let banner = document.getElementById('voice-error-banner');
      if (!banner && this.container) {
        banner = document.createElement('div');
        banner.id = 'voice-error-banner';
        banner.className = 'voice-error-banner';
        this.container.prepend(banner);
      }
      if (banner) {
        banner.style.display = 'flex';
        banner.innerHTML = `
          <div>
            <strong style="color:#FF3366;">⚠️ ${title}:</strong>
            <span> ${message}</span>
          </div>
          ${onRetry ? `<button id="voice-banner-retry-btn" class="voice-action-btn" style="font-size:0.75rem; padding:4px 10px;">Retry</button>` : ''}
        `;
        const retryBtn = document.getElementById('voice-banner-retry-btn');
        if (retryBtn && onRetry) {
          retryBtn.addEventListener('click', onRetry);
        }
      }
    }

    hideErrorBanner() {
      const banner = document.getElementById('voice-error-banner');
      if (banner) banner.style.display = 'none';
    }

    showBanner(msg, type = 'info', timeout = 3000) {
      if (window.jarvisChat && window.jarvisChat.showBanner) {
        window.jarvisChat.showBanner(msg, type, timeout);
      } else {
        console.log(`[JARVIS Voice] [${type}] ${msg}`);
      }
    }

    // --- Render Full Voice Assistant View ---
    render(container) {
      this.container = container;
      this.container.innerHTML = this.getTemplate();
      this.bindElements();
      this.setupCanvas();
      this.startWaveformLoop();

      // Mount avatar into voice interface if available
      if (window.jarvisAvatar) {
        const avatarBox = document.getElementById('voice-avatar-container');
        if (avatarBox) {
          window.jarvisAvatar.mount(avatarBox);
        }
      }

      this.updateView();
    }

    getTemplate() {
      const diag = this.voiceStatus?.diagnostics || {};
      const micInfo = diag.microphone || this.voiceStatus?.device || {};
      const spkInfo = diag.speaker || this.voiceStatus?.speaker || {};
      const ttsInfo = diag.tts || this.voiceStatus?.tts || {};

      const micName = micInfo.device || micInfo.name || 'Unavailable';
      const spkName = spkInfo.device || spkInfo.name || 'Default System Speaker';
      const ttsProvider = ttsInfo.provider || this.voiceStatus?.tts?.provider || 'Local TTS Fallback';
      const wakeWord = this.voiceStatus?.wake_word || 'jarvis';
      const captureOwner = this.voiceStatus?.capture_owner || 'backend';

      return `
        <div class="voice-view-container" id="voice-view-container">
          <!-- Voice Top Status Bar -->
          <div class="voice-header-bar">
            <div style="display:flex; align-items:center; gap:12px;">
              <h2 style="font-size:1.15rem; font-weight:800; color:var(--text-primary); margin:0; letter-spacing:0.5px;">
                🎙️ JARVIS Voice Assistant & Pipeline
              </h2>
              <span class="status-chip" style="font-size:0.7rem;" title="Capture daemon owner">
                Owner: ${captureOwner}
              </span>
            </div>

            <div style="display:flex; align-items:center; gap:10px;">
              <!-- Microphone Privacy Indicator -->
              <div id="voice-privacy-indicator" class="voice-privacy-badge privacy-standby" role="status" aria-live="polite">
                <span class="voice-privacy-dot"></span>
                <span id="voice-privacy-text">Standby (Wake Word: "${wakeWord}")</span>
              </div>
            </div>
          </div>

          <!-- Main Grid -->
          <div class="voice-grid">
            <!-- Left Hero Card: Avatar, Waveforms, Subtitles, Controls -->
            <div class="voice-hero-card">
              <!-- Digital Human Avatar Mount Point -->
              <div id="voice-avatar-container" style="display:flex; justify-content:center; align-items:center; min-height:160px; margin-bottom:8px;"></div>

              <!-- Real Audio Waveform Canvas -->
              <canvas id="voice-waveform-canvas" class="voice-waveform-canvas" width="680" height="150" aria-label="Real-time audio waveform visualizer"></canvas>

              <!-- Live Subtitles Box -->
              <div id="voice-subtitles-box" class="voice-subtitles-box" aria-live="polite">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                  <span id="voice-subtitles-speaker" class="voice-subtitles-speaker speaker-jarvis">🤖 JARVIS</span>
                  <span id="voice-subtitles-status" class="voice-subtitles-status">[Standby]</span>
                </div>
                <div id="voice-subtitles-text" class="voice-subtitles-text">
                  ${this.currentSubtitles.text}
                </div>
              </div>

              <!-- Central Push-To-Talk Button -->
              <div class="voice-mic-center">
                <button id="voice-mic-main-btn" class="voice-mic-main-btn" aria-label="Microphone Voice Activation">
                  <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                    <line x1="12" y1="19" x2="12" y2="23"></line>
                    <line x1="8" y1="23" x2="16" y2="23"></line>
                  </svg>
                </button>
                <span id="voice-mic-label" class="voice-mic-label">Click or Hold to Speak</span>
              </div>

              <!-- Primary Action Controls -->
              <div class="voice-controls-row">
                <button id="voice-bargein-btn" class="voice-action-btn bargein" title="Interrupt active speech immediately (< 300ms)">
                  🛑 Interrupt (Barge-In)
                </button>
                <button id="voice-mute-btn" class="voice-action-btn" title="Toggle microphone capture mute">
                  ${this.isMuted ? '🔊 Unmute Mic' : '🔇 Mute Mic'}
                </button>
                <button id="voice-test-phrase-btn" class="voice-action-btn" title="Synthesize test greeting">
                  🗣️ Test Voice
                </button>
              </div>
            </div>

            <!-- Right Column: Diagnostics & Tuning -->
            <div class="voice-side-col">
              <!-- Diagnostics & Hardware Devices -->
              <div class="voice-panel-card">
                <div class="voice-panel-title">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
                  Hardware & Audio Pipeline
                </div>

                <div class="voice-stat-row">
                  <span class="voice-stat-label">Microphone:</span>
                  <span class="voice-stat-val" id="voice-diag-mic" title="${micName}">${micName.length > 22 ? micName.slice(0, 20) + '...' : micName}</span>
                </div>

                <div class="voice-stat-row">
                  <span class="voice-stat-label">Speaker:</span>
                  <span class="voice-stat-val" id="voice-diag-spk" title="${spkName}">${spkName.length > 22 ? spkName.slice(0, 20) + '...' : spkName}</span>
                </div>

                <div class="voice-stat-row">
                  <span class="voice-stat-label">TTS Engine:</span>
                  <span class="voice-stat-val" id="voice-diag-tts">${ttsProvider}</span>
                </div>

                <div class="voice-stat-row">
                  <span class="voice-stat-label">Wake Word:</span>
                  <span class="voice-stat-val" style="color:var(--accent);">"${wakeWord}" (Active)</span>
                </div>

                <div class="voice-stat-row">
                  <span class="voice-stat-label">Lip-Sync Mode:</span>
                  <span class="voice-stat-val" style="color:var(--accent-purple);">Audio-Reactive RMS</span>
                </div>

                <div style="display:flex; gap:8px; margin-top:8px;">
                  <button id="voice-test-mic-btn" class="voice-action-btn" style="flex:1; justify-content:center; font-size:0.75rem;">
                    🎙️ Test Mic (3s)
                  </button>
                  <button id="voice-test-spk-btn" class="voice-action-btn" style="flex:1; justify-content:center; font-size:0.75rem;">
                    🔊 Test Speaker Tone
                  </button>
                </div>
              </div>

              <!-- Voice Synthesis & Audio Tuning -->
              <div class="voice-panel-card">
                <div class="voice-panel-title">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="4" y1="21" x2="4" y2="14"></line><line x1="4" y1="10" x2="4" y2="3"></line><line x1="12" y1="21" x2="12" y2="12"></line><line x1="12" y1="8" x2="12" y2="3"></line><line x1="20" y1="21" x2="20" y2="16"></line><line x1="20" y1="12" x2="20" y2="3"></line><line x1="1" y1="14" x2="7" y2="14"></line><line x1="9" y1="8" x2="15" y2="8"></line><line x1="17" y1="16" x2="23" y2="16"></line></svg>
                  Voice Parameters & Tuning
                </div>

                <!-- Speech Speed Slider -->
                <div class="voice-tuning-group">
                  <div class="voice-tuning-header">
                    <span class="voice-stat-label">Speech Speed</span>
                    <span class="voice-stat-val" id="voice-speed-val">${this.tuning.speed.toFixed(2)}x</span>
                  </div>
                  <input type="range" id="voice-tuning-speed" class="voice-tuning-slider" min="0.5" max="2.0" step="0.05" value="${this.tuning.speed}">
                </div>

                <!-- Diffusion Steps Slider -->
                <div class="voice-tuning-group">
                  <div class="voice-tuning-header">
                    <span class="voice-stat-label">Diffusion Steps</span>
                    <span class="voice-stat-val" id="voice-steps-val">${this.tuning.num_steps}</span>
                  </div>
                  <input type="range" id="voice-tuning-steps" class="voice-tuning-slider" min="8" max="64" step="4" value="${this.tuning.num_steps}">
                </div>

                <!-- Playback Volume Slider -->
                <div class="voice-tuning-group">
                  <div class="voice-tuning-header">
                    <span class="voice-stat-label">Output Volume</span>
                    <span class="voice-stat-val" id="voice-volume-val">${Math.round(this.volume * 100)}%</span>
                  </div>
                  <input type="range" id="voice-tuning-volume" class="voice-tuning-slider" min="0" max="1" step="0.05" value="${this.volume}">
                </div>

                <button id="voice-save-tuning-btn" class="voice-action-btn" style="justify-content:center; margin-top:6px;">
                  💾 Apply Tuning
                </button>
              </div>
            </div>
          </div>
        </div>
      `;
    }

    bindElements() {
      // Main Mic Button
      const micBtn = document.getElementById('voice-mic-main-btn');
      if (micBtn) {
        micBtn.addEventListener('click', () => this.toggleListening());
      }

      // Barge-in Button
      const bargeinBtn = document.getElementById('voice-bargein-btn');
      if (bargeinBtn) {
        bargeinBtn.addEventListener('click', () => this.interrupt());
      }

      // Mute Toggle Button
      const muteBtn = document.getElementById('voice-mute-btn');
      if (muteBtn) {
        muteBtn.addEventListener('click', () => this.toggleMute());
      }

      // Test Phrase Button
      const testPhraseBtn = document.getElementById('voice-test-phrase-btn');
      if (testPhraseBtn) {
        testPhraseBtn.addEventListener('click', () => {
          this.handleUserVoiceInput('Hello, I am JARVIS. Voice pipeline and audio-reactive mouth modulation are fully operational.');
        });
      }

      // Hardware Diagnostic Test Buttons
      const testMicBtn = document.getElementById('voice-test-mic-btn');
      if (testMicBtn) {
        testMicBtn.addEventListener('click', () => this.runMicrophoneTest());
      }

      const testSpkBtn = document.getElementById('voice-test-spk-btn');
      if (testSpkBtn) {
        testSpkBtn.addEventListener('click', () => this.runSpeakerTest());
      }

      // Tuning Controls
      const speedInput = document.getElementById('voice-tuning-speed');
      const speedVal = document.getElementById('voice-speed-val');
      if (speedInput && speedVal) {
        speedInput.addEventListener('input', () => {
          speedVal.textContent = parseFloat(speedInput.value).toFixed(2) + 'x';
        });
      }

      const stepsInput = document.getElementById('voice-tuning-steps');
      const stepsVal = document.getElementById('voice-steps-val');
      if (stepsInput && stepsVal) {
        stepsInput.addEventListener('input', () => {
          stepsVal.textContent = stepsInput.value;
        });
      }

      const volInput = document.getElementById('voice-tuning-volume');
      const volVal = document.getElementById('voice-volume-val');
      if (volInput && volVal) {
        volInput.addEventListener('input', () => {
          this.volume = parseFloat(volInput.value);
          volVal.textContent = Math.round(this.volume * 100) + '%';
          if (this.audioElement) this.audioElement.volume = this.volume;
        });
      }

      const saveTuningBtn = document.getElementById('voice-save-tuning-btn');
      if (saveTuningBtn) {
        saveTuningBtn.addEventListener('click', () => this.applyTuning());
      }
    }

    setupCanvas() {
      const canvas = document.getElementById('voice-waveform-canvas');
      if (!canvas) return;
      this.canvas = canvas;
      this.canvasCtx = canvas.getContext('2d');

      // Adjust resolution for device pixel ratio
      const dpr = window.devicePixelRatio || 1;
      const rect = canvas.getBoundingClientRect();
      canvas.width = (rect.width || 680) * dpr;
      canvas.height = (rect.height || 180) * dpr;
      this.canvasCtx.scale(dpr, dpr);
    }

    updateView() {
      // Update Privacy Badge
      const privacyBadge = document.getElementById('voice-privacy-indicator');
      const privacyText = document.getElementById('voice-privacy-text');
      const micBtn = document.getElementById('voice-mic-main-btn');
      const micLabel = document.getElementById('voice-mic-label');
      const muteBtn = document.getElementById('voice-mute-btn');

      if (!privacyBadge || !privacyText) return;

      const wakeWord = this.voiceStatus?.wake_word || 'jarvis';

      if (this.state === 'listening') {
        privacyBadge.className = 'voice-privacy-badge privacy-recording';
        privacyText.textContent = 'Recording / Mic Active';
        if (micBtn) {
          micBtn.className = 'voice-mic-main-btn listening';
        }
        if (micLabel) micLabel.textContent = 'Listening... Click to stop';
      } else if (this.state === 'speaking') {
        privacyBadge.className = 'voice-privacy-badge privacy-standby';
        privacyText.textContent = 'Speaking Response';
        if (micBtn) micBtn.className = 'voice-mic-main-btn';
        if (micLabel) micLabel.textContent = 'Speaking... Click to barge-in';
      } else if (this.isMuted || this.state === 'muted') {
        privacyBadge.className = 'voice-privacy-badge privacy-muted';
        privacyText.textContent = 'Microphone Muted';
        if (micBtn) micBtn.className = 'voice-mic-main-btn muted';
        if (micLabel) micLabel.textContent = 'Muted — Click to unmute';
      } else if (this.state === 'offline') {
        privacyBadge.className = 'voice-privacy-badge privacy-offline';
        privacyText.textContent = 'Voice Engine Offline';
        if (micBtn) micBtn.className = 'voice-mic-main-btn';
        if (micLabel) micLabel.textContent = 'Engine Offline';
      } else {
        privacyBadge.className = 'voice-privacy-badge privacy-standby';
        privacyText.textContent = `Standby (Wake Word: "${wakeWord}")`;
        if (micBtn) micBtn.className = 'voice-mic-main-btn';
        if (micLabel) micLabel.textContent = 'Click or Hold to Speak';
      }

      if (muteBtn) {
        muteBtn.textContent = this.isMuted ? '🔊 Unmute Mic' : '🔇 Mute Mic';
      }
    }

    destroy() {
      if (this.pollTimer) clearInterval(this.pollTimer);
      if (this.rafId) cancelAnimationFrame(this.rafId);
      this.stopListening();
      if (this.audioElement) {
        this.audioElement.pause();
        this.audioElement.src = '';
      }
    }
  }

  // Export singleton to window
  window.jarvisVoice = new JarvisVoiceAssistant();
  window.addEventListener('DOMContentLoaded', () => {
    window.jarvisVoice.init();
  });
})();
