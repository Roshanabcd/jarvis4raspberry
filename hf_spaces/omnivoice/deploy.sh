#!/usr/bin/env bash
# ==============================================================================
# One-Step Hugging Face Space Deployment Script for JARVIS OS OmniVoice
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================================================="
echo "   JARVIS OS • OmniVoice Hugging Face Space Deployer             "
echo "================================================================="

HF_USER="${1:-$HF_USERNAME}"
SPACE_NAME="${2:-omnivoice-jarvis}"

if [ -z "$HF_USER" ]; then
    read -rp "Enter your Hugging Face Username: " HF_USER
fi

if [ -z "$HF_USER" ]; then
    echo "Error: Hugging Face username is required."
    exit 1
fi

SPACE_REPO="https://huggingface.co/spaces/${HF_USER}/${SPACE_NAME}"
echo ""
echo "Target Space: $SPACE_REPO"
echo ""
echo "Steps:"
echo "1. If you haven't created the Space yet, create an empty Space at:"
echo "   https://huggingface.co/new-space"
echo "   - Name: ${SPACE_NAME}"
echo "   - SDK: Gradio"
echo "   - Hardware: Free CPU Basic or ZeroGPU"
echo ""

# Check if git is initialized in this folder
if [ ! -d ".git" ]; then
    git init -b main
    git add .
    git commit -m "initial commit: omnivoice for jarvis os"
fi

if git remote | grep -q "^hf$"; then
    git remote set-url hf "$SPACE_REPO"
else
    git remote add hf "$SPACE_REPO"
fi

echo "Deploying files to Hugging Face Space..."
git add app.py requirements.txt README.md
git commit -m "update omnivoice space files" || true
git push -u hf main

echo ""
echo "================================================================="
echo " Successfully pushed to: $SPACE_REPO"
echo " Live Endpoint will be: https://${HF_USER}-${SPACE_NAME}.hf.space"
echo "================================================================="
