#!/usr/bin/env bash
set -e

echo "Installing AI Agents & Automation tools..."

# Claude Code
curl -fsSL https://claude.ai/install.sh | bash -

# OpenCode
curl -fsSL https://opencode.ai/install | bash -

# Playwright
npm install -g playwright
npx playwright install --with-deps chromium

# Gemini CLI
npm install -g @google/gemini-cli
