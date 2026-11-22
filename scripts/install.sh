#!/usr/bin/env bash
# JARVIS OS Production Installer
# Target: Raspberry Pi 5 8GB running Debian 13 (trixie) / Raspberry Pi OS
# Run as: sudo bash scripts/install.sh
# Idempotent — safe to re-run.

set -euo pipefail
IFS=$'\n\t'

ACTUAL_USER="${SUDO_USER:-$(id -un)}"
JARVIS_USER="${JARVIS_USER:-$ACTUAL_USER}"
SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
JARVIS_HOME="${JARVIS_HOME:-$SCRIPT_ROOT}"
VENV_DIR="${JARVIS_HOME}/venv"
SERVICE_DIR="/etc/systemd/system"
LOG_DIR="/var/log/jarvis"
PYTHON_BIN="${VENV_DIR}/bin/python3"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
log()   { echo -e "${GREEN}[JARVIS]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

[[ $EUID -eq 0 ]] || error "Run this script as root: sudo bash $0"

log "Starting JARVIS OS installation..."
log "Install dir: ${JARVIS_HOME}"
log "User:        ${JARVIS_USER}"

# ─── 1. System packages ─────────────────────────────────────
log "Installing system dependencies..."
apt-get update -qq
apt-get install -y --no-install-recommends \
  python3 python3-pip python3-venv python3-dev \
  libatlas-base-dev libopenblas-dev \
  espeak espeak-ng \
  i2c-tools libi2c-dev \
  git curl wget build-essential \
  alsa-utils libsndfile1 portaudio19-dev \
  sqlite3 libsqlite3-dev \
  libgpiod2 gpiod python3-libgpiod \
  networkd-dispatcher \
  2>/dev/null || warn "Some packages may not be available on this platform."

# ─── 2. Enable hardware interfaces ──────────────────────────
log "Enabling I2C, SPI, UART via raspi-config (non-interactive)..."
raspi-config nonint do_i2c 0   2>/dev/null || warn "raspi-config: I2C enable skipped"
raspi-config nonint do_spi 0   2>/dev/null || warn "raspi-config: SPI enable skipped"
raspi-config nonint do_serial_hw 0 2>/dev/null || warn "raspi-config: UART enable skipped"

# ─── 3. User & groups ───────────────────────────────────────
log "Adding ${JARVIS_USER} to hardware groups..."
for GRP in i2c spi gpio audio dialout video; do
  usermod -aG "$GRP" "$JARVIS_USER" 2>/dev/null || warn "Group $GRP not found."
done

# ─── 4. Log directory ───────────────────────────────────────
mkdir -p "$LOG_DIR"
chown -R "$JARVIS_USER":"$JARVIS_USER" "$LOG_DIR"

# ─── 5. Python venv ─────────────────────────────────────────
log "Setting up Python virtual environment..."
if [[ ! -d "$VENV_DIR" ]]; then
  python3 -m venv "$VENV_DIR"
fi

sudo -u "$JARVIS_USER" "$VENV_DIR/bin/pip" install --upgrade pip -q
sudo -u "$JARVIS_USER" "$VENV_DIR/bin/pip" install \
  fastapi uvicorn pydantic pyyaml requests \
  psutil smbus2 pyserial python-dotenv \
  httpx pytest 2>/dev/null

# Optional packages (non-fatal)
sudo -u "$JARVIS_USER" "$VENV_DIR/bin/pip" install picamera2 2>/dev/null || warn "picamera2 not installed (Camera Module 3 optional)"
sudo -u "$JARVIS_USER" "$VENV_DIR/bin/pip" install openai-whisper 2>/dev/null || warn "openai-whisper not installed (STT optional)"
sudo -u "$JARVIS_USER" "$VENV_DIR/bin/pip" install pyttsx3 2>/dev/null || warn "pyttsx3 not installed (TTS uses espeak fallback)"

# ─── 6. .env file ───────────────────────────────────────────
if [[ ! -f "${JARVIS_HOME}/.env" ]]; then
  log "Creating .env from template..."
  cp "${JARVIS_HOME}/.env.example" "${JARVIS_HOME}/.env"
  chown "$JARVIS_USER":"$JARVIS_USER" "${JARVIS_HOME}/.env"
  chmod 600 "${JARVIS_HOME}/.env"
  warn "Edit ${JARVIS_HOME}/.env to add your API keys before starting."
fi

# ─── 7. Systemd services ────────────────────────────────────
log "Installing systemd services..."

# Main JARVIS service
cat > "${SERVICE_DIR}/jarvis-core.service" << EOF
[Unit]
Description=JARVIS OS Core Service
After=network-online.target
Wants=network-online.target

[Service]
User=${JARVIS_USER}
WorkingDirectory=${JARVIS_HOME}
ExecStart=${VENV_DIR}/bin/python3 -m uvicorn apps.core.main:app --host 127.0.0.1 --port 8000 --log-level info
EnvironmentFile=${JARVIS_HOME}/.env
Environment=JARVIS_HOME=${JARVIS_HOME}
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=jarvis-core

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable jarvis-core.service
log "Service jarvis-core.service enabled."

# ─── 8. Verify ─────────────────────────────────────────────
log "Running tests..."
cd "$JARVIS_HOME"
sudo -u "$JARVIS_USER" "$VENV_DIR/bin/pytest" tests/ -q --tb=short 2>&1 | tail -5

log ""
log "╔══════════════════════════════════════════════════╗"
log "║  JARVIS OS installation complete!                ║"
log "║  Start:   sudo systemctl start jarvis-core       ║"
log "║  Status:  sudo systemctl status jarvis-core      ║"
log "║  Logs:    sudo journalctl -u jarvis-core -f      ║"
log "║  URL:     http://$(hostname -I | awk '{print $1}'):8000/ ║"
log "╚══════════════════════════════════════════════════╝"
