/**
 * JARVIS OS Robotics, Devices & Sensor Suite (Phase 9)
 * Manages Hardware Devices, Sensor Telemetry, and Robot Actuation.
 * 
 * Safety & Truthfulness Directives:
 * - Hardware remains DISARMED by default.
 * - Emergency stop is latched and prominently accessible at all times.
 * - Real hardware verification checklist is documented in HARDWARE_CHECKLIST.md.
 * - Simulation mode is explicitly labeled; never presented as physical verification.
 * - Distinct styling for DISCONNECTED, SIMULATED, DEGRADED, and READY states.
 */

(function () {
  'use strict';

  class JarvisRobotDevicesHub {
    constructor() {
      this.robotState = {
        state: 'IDLE',
        armed: false,
        emergency_stopped: false,
        simulated: true,
        http_actuation_enabled: false,
      };
      this.sensorsData = {};
      this.sensorStatuses = {};
      this.devicesHealth = null;
      this.activityLog = [];
      this.pollTimer = null;
    }

    renderDestination(destId) {
      const container = document.getElementById('view-placeholder');
      if (!container) return;

      container.className = 'view-container';
      container.innerHTML = '';

      switch (destId) {
        case 'devices':
          this.renderDevices(container);
          break;
        case 'sensors':
          this.renderSensors(container);
          break;
        case 'robot':
          this.renderRobot(container);
          break;
        default:
          container.innerHTML = `<div class="p-6">Destination ${destId} not routed in Robot/Devices Hub.</div>`;
      }
    }

    // ──────────────────────────────────────────────────────────────────────────
    // 1. Destination 10: Hardware Devices (#devices)
    // ──────────────────────────────────────────────────────────────────────────

    async renderDevices(container) {
      container.innerHTML = `
        <div class="ops-header">
          <div>
            <h2 class="ops-title">Connected Devices & Architecture</h2>
            <p class="ops-subtitle">Host controllers, serial discovery, I2C bus interfaces & camera telemetry</p>
          </div>
          <div class="ops-header-actions">
            <button class="btn-futuristic btn-secondary" id="dev-refresh-btn">Scan Hardware</button>
          </div>
        </div>

        <div class="ops-tabs" role="tablist" aria-label="Hardware Destination Tabs" style="margin-bottom:18px;">
          <button class="ops-tab active" id="tab-sub-devices" role="tab" aria-selected="true">Connected Devices</button>
          <button class="ops-tab" id="tab-sub-sensors" role="tab" aria-selected="false">Sensors Telemetry</button>
        </div>

        <div class="devices-grid">
          <!-- Raspberry Pi 5 Host Controller -->
          <div class="glass-panel device-card" id="card-device-rpi">
            <div class="device-card-header">
              <div class="device-icon-box">π5</div>
              <div>
                <h4 class="device-title">Raspberry Pi 5 Host Controller</h4>
                <span class="device-arch text-muted text-sm" id="dev-rpi-arch">Linux aarch64 · BCM2712</span>
              </div>
              <span class="device-status-chip chip-ready" id="dev-rpi-status">HOST OK</span>
            </div>
            <div class="device-metrics-grid" id="dev-rpi-metrics">
              <div class="metric-mini"><span class="lbl">CPU Temp:</span> <strong id="dev-temp">-- °C</strong></div>
              <div class="metric-mini"><span class="lbl">Memory:</span> <strong id="dev-ram">-- MB</strong></div>
              <div class="metric-mini"><span class="lbl">Disk:</span> <strong id="dev-disk">-- GB</strong></div>
              <div class="metric-mini"><span class="lbl">State:</span> <strong id="dev-power">Normal</strong></div>
            </div>
          </div>

          <!-- ESP32-S3 Microcontroller / Serial Bus -->
          <div class="glass-panel device-card" id="card-device-esp32">
            <div class="device-card-header">
              <div class="device-icon-box">ESP</div>
              <div>
                <h4 class="device-title">ESP32-S3 Microcontroller Bus</h4>
                <span class="device-arch text-muted text-sm">UART /dev/ttyUSB0 · 115200 baud</span>
              </div>
              <span class="device-status-chip chip-blue" id="dev-esp32-status">SIMULATED</span>
            </div>
            <div class="device-desc text-secondary text-sm">
              Handles low-level PWM servo control, motor encoder counting, and hardware heartbeat protocol.
            </div>
            <div class="device-ports-box" id="dev-serial-ports">
              <span class="text-muted text-sm">Scanning serial ports...</span>
            </div>
          </div>

          <!-- Camera Subsystem -->
          <div class="glass-panel device-card" id="card-device-cam">
            <div class="device-card-header">
              <div class="device-icon-box">CAM</div>
              <div>
                <h4 class="device-title">Sony IMX708 Camera Subsystem</h4>
                <span class="device-arch text-muted text-sm">CSI-2 Bus · 12MP Wide AF</span>
              </div>
              <span class="device-status-chip chip-blue" id="dev-cam-status">SIMULATED</span>
            </div>
            <div class="device-desc text-secondary text-sm">
              High-resolution visual telemetry pipeline with computer-use OCR and spatial recognition.
            </div>
          </div>

          <!-- Audio Hardware Subsystem -->
          <div class="glass-panel device-card" id="card-device-audio">
            <div class="device-card-header">
              <div class="device-icon-box">MIC</div>
              <div>
                <h4 class="device-title">ReSpeaker Lite USB Audio</h4>
                <span class="device-arch text-muted text-sm">Dual Mic Array · ALSA Playback/Capture</span>
              </div>
              <span class="device-status-chip chip-ready" id="dev-audio-status">READY</span>
            </div>
            <div class="device-desc text-secondary text-sm">
              Single-owner hardware microphone capture daemon with low-latency barge-in interruption.
            </div>
          </div>

          <!-- I2C Bus 1 Discovery -->
          <div class="glass-panel device-card" id="card-device-i2c" style="grid-column: 1 / -1;">
            <div class="device-card-header">
              <div class="device-icon-box">I²C</div>
              <div>
                <h4 class="device-title">I2C Bus 1 Devices Scan (/dev/i2c-1)</h4>
                <span class="device-arch text-muted text-sm">Fast-Mode 400 kHz · PCA9685, BME280, BH1750, VL53L0X</span>
              </div>
              <span class="device-status-chip chip-amber" id="dev-i2c-status">SCAN COMPLETED</span>
            </div>
            <div class="i2c-address-map" id="dev-i2c-map">
              <div class="ops-loading">Scanning I2C bus addresses...</div>
            </div>
          </div>
        </div>
      `;

      container.querySelector('#dev-refresh-btn').addEventListener('click', () => this.loadDevices(container));
      container.querySelector('#tab-sub-sensors').addEventListener('click', () => {
        window.location.hash = '#sensors';
        this.renderSensors(container);
      });
      await this.loadDevices(container);
    }

    async loadDevices(container) {
      try {
        const [health, diag, i2cRes, serialRes] = await Promise.all([
          window.jarvisApi.request('/api/health').catch(() => null),
          window.jarvisApi.getDiagnostics().catch(() => null),
          window.jarvisApi.getI2cHealth().catch(() => null),
          window.jarvisApi.getSerialHealth().catch(() => null),
        ]);

        // Host Pi 5
        const sys = (health && health.system) || {};
        if (container.querySelector('#dev-temp')) container.querySelector('#dev-temp').textContent = sys.temperature ? `${sys.temperature} °C` : 'Unavailable';
        if (container.querySelector('#dev-ram')) container.querySelector('#dev-ram').textContent = sys.ram ? `${sys.ram.used_mb}/${sys.ram.total_mb} MB` : 'Unavailable';
        if (container.querySelector('#dev-disk')) container.querySelector('#dev-disk').textContent = sys.disk ? `${sys.disk.used_gb}/${sys.disk.total_gb} GB` : 'Unavailable';

        // Serial Ports
        const portsBox = container.querySelector('#dev-serial-ports');
        if (portsBox) {
          const ports = (serialRes && serialRes.ports) || [];
          if (ports.length === 0) {
            portsBox.innerHTML = '<span class="text-secondary text-sm">No physical serial devices attached. Degrading gracefully to in-memory simulation protocol.</span>';
          } else {
            portsBox.innerHTML = ports.map(p => `<span class="port-tag"><code>${this.escapeHtml(p)}</code></span>`).join(' ');
          }
        }

        // I2C Map
        const i2cBox = container.querySelector('#dev-i2c-map');
        if (i2cBox) {
          const devices = (i2cRes && i2cRes.devices) || [];
          const knownMap = {
            '0x40': 'PCA9685 16-Channel PWM Servo Controller',
            '0x76': 'BME280 Temperature/Humidity/Pressure Sensor',
            '0x77': 'BME280 Alternate Address',
            '0x23': 'BH1750 Ambient Light Intensity Sensor',
            '0x29': 'VL53L0X Time-of-Flight Laser Distance Sensor',
          };

          if (devices.length === 0) {
            i2cBox.innerHTML = `
              <div class="i2c-empty-box">
                <span class="text-amber">No responding physical I2C addresses detected on bus 1.</span>
                <span class="text-secondary text-sm" style="margin-left:8px;">Sensors running in simulated fallback mode per standing safety rules.</span>
              </div>
            `;
          } else {
            i2cBox.innerHTML = devices.map(addr => `
              <div class="i2c-device-chip">
                <code>${this.escapeHtml(addr)}</code>
                <span>${this.escapeHtml(knownMap[addr] || 'Unknown I2C Peripheral')}</span>
              </div>
            `).join('');
          }
        }
      } catch (err) {
        console.error('Error loading devices telemetry:', err);
      }
    }

    // ──────────────────────────────────────────────────────────────────────────
    // 2. Destination 10: Environmental & Spatial Sensors (#sensors)
    // ──────────────────────────────────────────────────────────────────────────

    async renderSensors(container) {
      container.innerHTML = `
        <div class="ops-header">
          <div>
            <h2 class="ops-title">Sensors Telemetry Suite</h2>
            <p class="ops-subtitle">Environmental, optical, laser time-of-flight, ultrasonic, and passive infrared telemetry</p>
          </div>
          <div class="ops-header-actions">
            <span class="simulation-banner" id="sensors-mode-banner">SIMULATION MODE ACTIVE</span>
            <button class="btn-futuristic btn-secondary" id="sensors-read-btn">Read All Sensors</button>
          </div>
        </div>

        <div class="ops-tabs" role="tablist" aria-label="Sensors Destination Tabs" style="margin-bottom:18px;">
          <button class="ops-tab" id="tab-sub-devices-from-sensors" role="tab" aria-selected="false">Connected Devices</button>
          <button class="ops-tab active" id="tab-sub-sensors-active" role="tab" aria-selected="true">Sensors Telemetry</button>
        </div>

        <div class="sensors-grid" id="sensors-cards-container">
          <div class="ops-loading">Reading sensor bus telemetry...</div>
        </div>
      `;

      container.querySelector('#sensors-read-btn').addEventListener('click', () => this.loadSensors(container));
      container.querySelector('#tab-sub-devices-from-sensors').addEventListener('click', () => {
        window.location.hash = '#devices';
        this.renderDevices(container);
      });
      await this.loadSensors(container);
    }

    async loadSensors(container) {
      const grid = container.querySelector('#sensors-cards-container');
      if (!grid) return;

      try {
        const [overviewRes, readRes] = await Promise.all([
          window.jarvisApi.getSensorsOverview().catch(() => null),
          window.jarvisApi.readAllSensors().catch(() => null),
        ]);

        const statuses = (overviewRes && overviewRes.status) || {};
        const readings = readRes || {};

        const sensorList = [
          {
            id: 'bme280',
            name: 'BME280 Environmental Sensor',
            type: 'I2C (0x76)',
            status: statuses.bme280 || 'uninitialized',
            data: readings.bme280 || {},
            format: (d) => `Temp: ${d.temperature !== undefined ? d.temperature + ' °C' : 'N/A'} | Humidity: ${d.humidity !== undefined ? d.humidity + ' %' : 'N/A'} | Pressure: ${d.pressure !== undefined ? d.pressure + ' hPa' : 'N/A'}`,
          },
          {
            id: 'bh1750',
            name: 'BH1750 Ambient Light Lux',
            type: 'I2C (0x23)',
            status: statuses.bh1750 || 'uninitialized',
            data: readings.bh1750 || {},
            format: (d) => `Illuminance: ${d.lux !== undefined ? d.lux + ' Lux' : 'N/A'} (${d.lux > 200 ? 'Bright' : 'Ambient'})`,
          },
          {
            id: 'vl53l0x',
            name: 'VL53L0X Laser Distance',
            type: 'I2C (0x29)',
            status: statuses.vl53l0x || 'degraded',
            data: readings.vl53l0x || {},
            format: (d) => `Range: ${d.distance_mm !== undefined ? d.distance_mm + ' mm' : 'N/A'} (Time-of-Flight Laser)`,
          },
          {
            id: 'hcsr04',
            name: 'HC-SR04 Ultrasonic Distance',
            type: 'GPIO Echo/Trigger',
            status: statuses.hcsr04 || 'simulated',
            data: readings.hcsr04 || {},
            format: (d) => `Obstacle Distance: ${d.distance_cm !== undefined ? d.distance_cm + ' cm' : 'N/A'}`,
          },
          {
            id: 'hcsr501',
            name: 'HC-SR501 PIR Motion Detector',
            type: 'GPIO Digital Input',
            status: statuses.hcsr501 || 'simulated',
            data: readings.hcsr501 || {},
            format: (d) => `Motion Detected: ${d.motion_detected ? 'YES — ACTIVITY ALERT' : 'NO — AREA SECURE'}`,
          },
        ];

        grid.innerHTML = sensorList.map(s => {
          let badgeClass = 'chip-blue';
          const st = (s.status || '').toLowerCase();
          if (st === 'ready' || st === 'ok') badgeClass = 'chip-ready';
          else if (st === 'degraded' || st === 'uninitialized') badgeClass = 'chip-amber';
          else if (st === 'disconnected') badgeClass = 'chip-danger';

          return `
            <div class="glass-panel sensor-card" id="sensor-card-${s.id}">
              <div class="sensor-header">
                <div>
                  <h4 class="sensor-title">${this.escapeHtml(s.name)}</h4>
                  <span class="sensor-bus text-muted text-sm">${this.escapeHtml(s.type)}</span>
                </div>
                <span class="sensor-status-chip ${badgeClass}">${s.status.toUpperCase()}</span>
              </div>
              <div class="sensor-readout">
                ${this.escapeHtml(s.format(s.data))}
              </div>
              <div class="sensor-actions">
                <button class="btn-futuristic btn-secondary btn-sm btn-sensor-calibrate" data-id="${s.id}">
                  Calibrate Sensor
                </button>
              </div>
            </div>
          `;
        }).join('');

        // Wire calibration buttons
        grid.querySelectorAll('.btn-sensor-calibrate').forEach(btn => {
          btn.addEventListener('click', async () => {
            const id = btn.getAttribute('data-id');
            btn.disabled = true;
            try {
              const res = await window.jarvisApi.calibrateSensor(id);
              if (window.jarvisShell) window.jarvisShell.showToast(`Calibrated ${id}: ${res.calibrated ? 'Success' : 'Failed'}`, 'info');
              await this.loadSensors(container);
            } catch (err) {
              if (window.jarvisShell) window.jarvisShell.showToast(`Calibration error: ${err.message}`, 'error');
            } finally { btn.disabled = false; }
          });
        });
      } catch (err) {
        grid.innerHTML = `<div class="ops-error">Error reading sensors: ${this.escapeHtml(err.message)}</div>`;
      }
    }

    // ──────────────────────────────────────────────────────────────────────────
    // 3. Destination 11: Robotics Control & Actuators (#robot)
    // ──────────────────────────────────────────────────────────────────────────

    async renderRobot(container) {
      container.innerHTML = `
        <div class="ops-header">
          <div>
            <h2 class="ops-title">Robotics & Physical Actuators</h2>
            <p class="ops-subtitle">Chassis kinematics, 16-channel servo controller & safety interlocks</p>
          </div>
          <div class="ops-header-actions">
            <span class="simulation-banner" id="robot-mode-indicator">SIMULATION MODE ACTIVE</span>
            <button class="btn-futuristic btn-secondary" id="robot-refresh-btn">Sync State</button>
          </div>
        </div>

        <!-- Latched Emergency Stop Banner (Highest Safety Priority) -->
        <div class="robot-estop-banner" id="robot-estop-banner">
          <div class="estop-banner-content">
            <div class="estop-status-icon">⚠</div>
            <div>
              <h3 class="estop-title" id="robot-estop-title">SAFETY LATCH DISARMED</h3>
              <p class="estop-desc" id="robot-estop-desc">Motion actuators are disarmed by default. Explicit authorization required to arm.</p>
            </div>
          </div>
          <div class="estop-banner-actions">
            <button class="btn-estop" id="robot-estop-btn" aria-label="Engage Emergency Stop">
              EMERGENCY STOP
            </button>
            <button class="btn-futuristic btn-secondary hidden" id="robot-clear-estop-btn">
              Clear E-Stop
            </button>
          </div>
        </div>

        <!-- Robot Control Grid -->
        <div class="robot-grid">
          <!-- Actuator Safety & Arming Controls -->
          <div class="glass-panel robot-card" style="flex:1;">
            <div class="card-header">
              <h3 class="card-title">Arming & Gating Status</h3>
              <span class="robot-state-chip" id="robot-state-chip">STATE: IDLE</span>
            </div>
            <div class="robot-status-metrics">
              <div class="metric-row"><span class="lbl">Actuators:</span> <strong id="robot-armed-status" class="text-amber">DISARMED</strong></div>
              <div class="metric-row"><span class="lbl">Emergency Stop:</span> <strong id="robot-estop-status" class="text-green">INACTIVE</strong></div>
              <div class="metric-row"><span class="lbl">HTTP Actuation:</span> <strong id="robot-http-status">DISABLED</strong></div>
              <div class="metric-row"><span class="lbl">Target Mode:</span> <strong class="text-accent">SIMULATED CONTROLLER</strong></div>
            </div>
            <div class="robot-arming-actions">
              <button class="btn-futuristic btn-primary" id="robot-arm-btn">
                🔒 Arm Actuators
              </button>
              <button class="btn-futuristic btn-secondary" id="robot-disarm-btn">
                Disarm Actuators
              </button>
            </div>
          </div>

          <!-- Directional Motion D-Pad -->
          <div class="glass-panel robot-card" style="flex:1;">
            <div class="card-header">
              <h3 class="card-title">Directional Kinematics</h3>
              <span class="text-secondary text-sm">Differential Drive</span>
            </div>
            <div class="robot-dpad-container">
              <button class="btn-dpad btn-dpad-up" id="btn-move-fwd" disabled aria-label="Move Forward">▲</button>
              <div class="dpad-row">
                <button class="btn-dpad btn-dpad-left" id="btn-move-left" disabled aria-label="Turn Left">◀</button>
                <button class="btn-dpad btn-dpad-stop" id="btn-move-stop" aria-label="Stop Motion">■</button>
                <button class="btn-dpad btn-dpad-right" id="btn-move-right" disabled aria-label="Turn Right">▶</button>
              </div>
              <button class="btn-dpad btn-dpad-down" id="btn-move-bwd" disabled aria-label="Move Backward">▼</button>
            </div>
            <div class="speed-slider-box">
              <label for="robot-speed-slider" class="text-sm">Velocity Limit: <strong id="speed-val">50%</strong></label>
              <input type="range" id="robot-speed-slider" min="10" max="100" value="50" class="slider-futuristic" />
            </div>
          </div>

          <!-- Servo Pan / Tilt Controls -->
          <div class="glass-panel robot-card" style="flex:1;">
            <div class="card-header">
              <h3 class="card-title">PCA9685 Servos (16-Ch)</h3>
            </div>
            <div class="servo-control-box">
              <label for="servo-ch0-slider" class="text-sm">Channel 0 (Pan): <strong id="servo-ch0-val">90°</strong></label>
              <input type="range" id="servo-ch0-slider" min="0" max="180" value="90" class="slider-futuristic" disabled />
            </div>
            <div class="servo-control-box" style="margin-top:14px;">
              <label for="servo-ch1-slider" class="text-sm">Channel 1 (Tilt): <strong id="servo-ch1-val">90°</strong></label>
              <input type="range" id="servo-ch1-slider" min="0" max="180" value="90" class="slider-futuristic" disabled />
            </div>
            <div class="text-secondary text-sm" style="margin-top:16px;">
              Servos are automatically held at 90° resting angle when disarmed.
            </div>
          </div>
        </div>

        <!-- Robot Safety Audit Log -->
        <div class="glass-panel" style="margin-top:20px;">
          <div class="card-header">
            <h3 class="card-title">Robotics Safety Audit Log</h3>
            <span class="text-muted text-sm">Real-time local event ledger</span>
          </div>
          <div class="robot-log-container" id="robot-log-entries">
            <div class="log-entry text-muted">[INIT] Robotics safety interlock initialized. Simulation mode enforced.</div>
          </div>
        </div>

        <!-- Admin PIN Modal for Arming / E-Stop Clear -->
        <div class="terminal-confirm-overlay hidden" id="robot-pin-modal" role="dialog" aria-modal="true" aria-labelledby="robot-pin-title">
          <div class="glass-panel" style="max-width:440px; width:95%; display:flex; flex-direction:column; gap:16px;">
            <div class="card-header">
              <h3 class="card-title text-amber" id="robot-pin-title">Authorize Physical Actuation</h3>
              <button class="btn-futuristic btn-secondary btn-icon" id="robot-pin-close-btn" aria-label="Close dialog">✕</button>
            </div>
            <p class="text-secondary text-sm" id="robot-pin-desc">
              Arming actuators or clearing emergency stop requires explicit authorization with Administrator PIN.
            </p>
            <div class="form-group">
              <label for="robot-auth-pin">Administrator PIN *</label>
              <input type="password" id="robot-auth-pin" class="input-futuristic" placeholder="Enter PIN..." required />
            </div>
            <div class="form-actions">
              <button type="button" class="btn-futuristic btn-secondary" id="robot-pin-cancel-btn">Cancel</button>
              <button type="button" class="btn-futuristic btn-primary" id="robot-pin-confirm-btn">Confirm Authorization</button>
            </div>
          </div>
        </div>
      `;

      // Event handlers
      container.querySelector('#robot-refresh-btn').addEventListener('click', () => this.syncRobotState(container));

      // Emergency Stop (Always Immediate, Never Prompts)
      container.querySelector('#robot-estop-btn').addEventListener('click', async () => {
        try {
          await window.jarvisApi.emergencyStopRobot();
          this.logAction('EMERGENCY STOP ENGAGED BY OPERATOR');
          if (window.jarvisShell) window.jarvisShell.showToast('EMERGENCY STOP ENGAGED!', 'danger');
          await this.syncRobotState(container);
        } catch (err) {
          if (window.jarvisShell) window.jarvisShell.showToast(`E-Stop failed: ${err.message}`, 'error');
        }
      });

      // Immediate Stop
      container.querySelector('#btn-move-stop').addEventListener('click', async () => {
        try {
          await window.jarvisApi.stopRobot();
          this.logAction('Motion Stopped (Stop Command)');
          await this.syncRobotState(container);
        } catch (err) {
          if (window.jarvisShell) window.jarvisShell.showToast(`Stop failed: ${err.message}`, 'error');
        }
      });

      // Disarm (Immediate, Always Available)
      container.querySelector('#robot-disarm-btn').addEventListener('click', async () => {
        try {
          await window.jarvisApi.disarmRobot();
          this.logAction('Actuators Disarmed');
          if (window.jarvisShell) window.jarvisShell.showToast('Actuators disarmed safely', 'info');
          await this.syncRobotState(container);
        } catch (err) {
          if (window.jarvisShell) window.jarvisShell.showToast(`Disarm failed: ${err.message}`, 'error');
        }
      });

      // Speed Slider
      const speedSlider = container.querySelector('#robot-speed-slider');
      const speedVal = container.querySelector('#speed-val');
      speedSlider.addEventListener('input', (e) => {
        speedVal.textContent = `${e.target.value}%`;
      });

      // Arm Button (Requires PIN)
      const pinModal = container.querySelector('#robot-pin-modal');
      let pendingAction = null;

      container.querySelector('#robot-arm-btn').addEventListener('click', () => {
        pendingAction = 'arm';
        container.querySelector('#robot-pin-title').textContent = 'Arm Robotics Actuators';
        container.querySelector('#robot-auth-pin').value = '';
        pinModal.classList.remove('hidden');
      });

      container.querySelector('#robot-clear-estop-btn').addEventListener('click', () => {
        pendingAction = 'clear_estop';
        container.querySelector('#robot-pin-title').textContent = 'Clear Emergency Stop';
        container.querySelector('#robot-auth-pin').value = '';
        pinModal.classList.remove('hidden');
      });

      container.querySelector('#robot-pin-close-btn').addEventListener('click', () => pinModal.classList.add('hidden'));
      container.querySelector('#robot-pin-cancel-btn').addEventListener('click', () => pinModal.classList.add('hidden'));

      container.querySelector('#robot-pin-confirm-btn').addEventListener('click', async () => {
        const pin = container.querySelector('#robot-auth-pin').value.trim();
        if (!pin) return;

        pinModal.classList.add('hidden');
        try {
          if (pendingAction === 'arm') {
            await window.jarvisApi.armRobot(pin);
            this.logAction('Actuators Armed with Admin PIN');
            if (window.jarvisShell) window.jarvisShell.showToast('Actuators armed successfully', 'warning');
          } else if (pendingAction === 'clear_estop') {
            await window.jarvisApi.clearRobotEstop(pin);
            this.logAction('Emergency Stop Cleared with Admin PIN');
            if (window.jarvisShell) window.jarvisShell.showToast('Emergency stop cleared', 'success');
          }
          await this.syncRobotState(container);
        } catch (err) {
          if (window.jarvisShell) window.jarvisShell.showToast(`Action failed: ${err.message}`, 'error');
        }
      });

      // Directional buttons (Disabled unless armed)
      const directions = [
        { id: '#btn-move-fwd', dir: 'forward' },
        { id: '#btn-move-bwd', dir: 'backward' },
        { id: '#btn-move-left', dir: 'left' },
        { id: '#btn-move-right', dir: 'right' },
      ];

      directions.forEach(({ id, dir }) => {
        container.querySelector(id).addEventListener('click', async () => {
          const spd = parseInt(speedSlider.value, 10) || 50;
          try {
            await window.jarvisApi.moveRobot(dir, spd);
            this.logAction(`Motion command: ${dir.toUpperCase()} @ ${spd}%`);
            await this.syncRobotState(container);
          } catch (err) {
            if (window.jarvisShell) window.jarvisShell.showToast(`Move failed: ${err.message}`, 'error');
          }
        });
      });

      // Servo Sliders
      const ch0 = container.querySelector('#servo-ch0-slider');
      const ch1 = container.querySelector('#servo-ch1-slider');
      const ch0Val = container.querySelector('#servo-ch0-val');
      const ch1Val = container.querySelector('#servo-ch1-val');

      ch0.addEventListener('change', async (e) => {
        ch0Val.textContent = `${e.target.value}°`;
        try {
          await window.jarvisApi.setRobotServo(0, parseInt(e.target.value, 10));
          this.logAction(`Servo CH0 Pan -> ${e.target.value}°`);
        } catch (err) {
          if (window.jarvisShell) window.jarvisShell.showToast(`Servo failed: ${err.message}`, 'error');
        }
      });

      ch1.addEventListener('change', async (e) => {
        ch1Val.textContent = `${e.target.value}°`;
        try {
          await window.jarvisApi.setRobotServo(1, parseInt(e.target.value, 10));
          this.logAction(`Servo CH1 Tilt -> ${e.target.value}°`);
        } catch (err) {
          if (window.jarvisShell) window.jarvisShell.showToast(`Servo failed: ${err.message}`, 'error');
        }
      });

      await this.syncRobotState(container);
    }

    async syncRobotState(container) {
      try {
        const res = await window.jarvisApi.getRobotState();
        this.robotState = res || this.robotState;

        const isArmed = Boolean(this.robotState.armed);
        const isEstop = Boolean(this.robotState.emergency_stopped);
        const stateName = this.robotState.state || (isEstop ? 'ESTOP' : (isArmed ? 'ARMED' : 'IDLE'));

        // Update E-Stop Banner
        const estopBanner = container.querySelector('#robot-estop-banner');
        const estopTitle = container.querySelector('#robot-estop-title');
        const estopDesc = container.querySelector('#robot-estop-desc');
        const clearEstopBtn = container.querySelector('#robot-clear-estop-btn');

        if (isEstop) {
          estopBanner.classList.add('banner-estop-active');
          estopTitle.textContent = 'EMERGENCY STOP LATCHED';
          estopDesc.textContent = 'Hardware interlock active. All motor PWM and servo channels frozen.';
          clearEstopBtn.classList.remove('hidden');
        } else {
          estopBanner.classList.remove('banner-estop-active');
          estopTitle.textContent = isArmed ? 'ACTUATORS ARMED & READY' : 'SAFETY LATCH DISARMED';
          estopDesc.textContent = isArmed 
            ? 'Actuators are live in simulation mode. Keep emergency stop within reach.'
            : 'Motion actuators are disarmed by default. Explicit authorization required to arm.';
          clearEstopBtn.classList.add('hidden');
        }

        // Metrics card
        container.querySelector('#robot-state-chip').textContent = `STATE: ${stateName}`;
        const armedEl = container.querySelector('#robot-armed-status');
        armedEl.textContent = isArmed ? 'ARMED (LIVE)' : 'DISARMED (SAFE)';
        armedEl.className = isArmed ? 'text-green' : 'text-amber';

        const estopEl = container.querySelector('#robot-estop-status');
        estopEl.textContent = isEstop ? 'ACTIVE (LATCHED)' : 'INACTIVE';
        estopEl.className = isEstop ? 'text-danger' : 'text-green';

        const httpEl = container.querySelector('#robot-http-status');
        httpEl.textContent = this.robotState.http_actuation_enabled ? 'ENABLED' : 'DISABLED';

        // Enable/Disable motion buttons
        const canMove = isArmed && !isEstop;
        ['#btn-move-fwd', '#btn-move-bwd', '#btn-move-left', '#btn-move-right'].forEach(sel => {
          const btn = container.querySelector(sel);
          if (btn) btn.disabled = !canMove;
        });

        ['#servo-ch0-slider', '#servo-ch1-slider'].forEach(sel => {
          const slider = container.querySelector(sel);
          if (slider) slider.disabled = !canMove;
        });
      } catch (err) {
        console.error('Error syncing robot state:', err);
      }
    }

    logAction(msg) {
      const entry = `[${new Date().toLocaleTimeString()}] ${msg}`;
      this.activityLog.unshift(entry);
      const container = document.getElementById('robot-log-entries');
      if (container) {
        container.innerHTML = this.activityLog.slice(0, 30).map(e => `
          <div class="log-entry">${this.escapeHtml(e)}</div>
        `).join('');
      }
    }

    escapeHtml(str) {
      if (typeof str !== 'string') return '';
      return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    }
  }

  // Export singleton
  window.jarvisRobotDevices = new JarvisRobotDevicesHub();
})();
