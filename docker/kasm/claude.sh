#!/usr/bin/env bash

cd

# Node.js (20.x)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash -
sudo apt-get update && apt-get install -y --no-install-recommends nodejs

# Claude
curl -fsSL https://claude.ai/install.sh | bash -

# Ollama
curl -fsSL https://ollama.com/install.sh | bash -

# OpenCode
curl -fsSL https://opencode.ai/install | bash -

# uv
curl -LsSf https://astral.sh/uv/install.sh | bash -

# Google Gemini CLI
npm install -g @google/gemini-cli

# Playwright
npm install -g playwright
npx playwright install --with-deps chromium
