#!/usr/bin/env bash
# Pull the smallest Ollama model for api_pusher
# Run: ./scripts/setup-ollama.sh

set -e

echo "Checking Ollama..."
if ! command -v ollama &> /dev/null; then
    echo "Ollama not found. Install from https://ollama.com"
    exit 1
fi

echo "Pulling tinyllama (smallest model, ~638MB)..."
ollama pull tinyllama

echo "Done. You can now use api_pusher with mode=ollama in tools/api_pusher/config.ini"
