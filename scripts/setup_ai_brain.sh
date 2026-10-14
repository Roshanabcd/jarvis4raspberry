#!/usr/bin/env bash
# JARVIS OS — AI Brain Setup Script
# Installs Ollama + pulls a capable model for aarch64/Raspberry Pi 5
# Also installs google-generativeai for Gemini fallback
set -euo pipefail

VENV="$(dirname "$0")/../venv"
JARVIS_DIR="$(dirname "$0")/.."

log()  { echo -e "\033[0;32m[AI-SETUP]\033[0m $*"; }
warn() { echo -e "\033[1;33m[WARN]\033[0m $*"; }

log "Installing Ollama..."
if ! command -v ollama &>/dev/null; then
  curl -fsSL https://ollama.com/install.sh | sh
  log "Ollama installed."
else
  log "Ollama already installed."
fi

log "Starting Ollama service..."
systemctl enable ollama 2>/dev/null || true
systemctl start ollama 2>/dev/null || (ollama serve &>/var/log/ollama.log &)
sleep 3

log "Pulling llama3.2:3b (3B model, fits in 8GB RAM)..."
ollama pull llama3.2:3b || ollama pull llama3.2 || warn "Could not pull llama3.2"

log "Pulling nomic-embed-text for vector memory..."
ollama pull nomic-embed-text || warn "Could not pull nomic-embed-text"

log "Installing Python AI packages..."
"${VENV}/bin/pip" install \
  google-generativeai \
  openai \
  anthropic \
  requests \
  httpx \
  numpy \
  --quiet

log "Installing chromadb for vector memory..."
"${VENV}/bin/pip" install chromadb --quiet || warn "chromadb install failed - vector memory uses SQLite fallback"

log "AI brain setup complete."
log "Test with: curl -s http://localhost:11434/api/generate -d '{\"model\":\"llama3.2:3b\",\"prompt\":\"Hello\",\"stream\":false}' | python3 -c 'import sys,json; print(json.load(sys.stdin)[\"response\"])'"
