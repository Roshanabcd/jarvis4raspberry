#!/usr/bin/env bash
# JARVIS OS — Start Ollama Local AI Brain
# Run once at boot or before starting JARVIS
# Usage: bash scripts/start_ollama.sh [model_name]

set -euo pipefail

OLLAMA_BIN="${HOME}/.local/bin/ollama"
OLLAMA_MODEL="${1:-llama3.2:1b}"
OLLAMA_HOST="127.0.0.1:11434"
OLLAMA_URL="http://${OLLAMA_HOST}"
LOG="/tmp/ollama_jarvis.log"

export PATH="${HOME}/.local/bin:${PATH}"
export LD_LIBRARY_PATH="${HOME}/.local/lib/ollama:${LD_LIBRARY_PATH:-}"
export OLLAMA_HOST="${OLLAMA_HOST}"
export OLLAMA_MODELS="${HOME}/.ollama/models"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

if [ ! -f "$OLLAMA_BIN" ]; then
  echo -e "${YELLOW}Ollama not found at $OLLAMA_BIN${NC}"
  echo "Run: curl -L https://github.com/ollama/ollama/releases/download/v0.35.1/ollama-linux-arm64.tar.zst | tar --zstd -xf - -C /tmp && cp /tmp/bin/ollama ~/.local/bin/"
  exit 1
fi

# Check if already running
if curl -sf "${OLLAMA_URL}/" > /dev/null 2>&1 || curl -sf "${OLLAMA_URL}/api/tags" > /dev/null 2>&1; then
  echo -e "${GREEN}Ollama already running${NC}"
else
  echo "Starting Ollama..."
  nohup "$OLLAMA_BIN" serve > "$LOG" 2>&1 &
  sleep 5
  if curl -sf "${OLLAMA_URL}/" > /dev/null 2>&1 || curl -sf "${OLLAMA_URL}/api/tags" > /dev/null 2>&1; then
    echo -e "${GREEN}Ollama started successfully${NC}"
  else
    echo "Failed to start Ollama. See $LOG"
    exit 1
  fi
fi

# Check model
MODELS=$(curl -s "${OLLAMA_URL}/api/tags" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(' '.join(m['name'] for m in d.get('models', [])))
" 2>/dev/null)

if echo "$MODELS" | grep -q "${OLLAMA_MODEL}"; then
  echo -e "${GREEN}Model ${OLLAMA_MODEL} ready${NC}"
else
  echo "Pulling model ${OLLAMA_MODEL}..."
  curl -s "${OLLAMA_URL}/api/pull" \
    -d "{\"model\":\"${OLLAMA_MODEL}\",\"stream\":false}" \
    --max-time 600 | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print('Status:', d.get('status', 'unknown'))
except: print('Pull completed')
"
fi

echo ""
echo -e "${GREEN}✓ Ollama ready. Test with:${NC}"
echo "  curl http://127.0.0.1:11434/api/generate -d '{\"model\":\"${OLLAMA_MODEL}\",\"prompt\":\"Say hello as JARVIS\",\"stream\":false}'"
