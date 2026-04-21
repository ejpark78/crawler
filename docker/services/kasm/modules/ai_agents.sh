#!/usr/bin/env bash
set -e
if [ "$EUID" -ne 0 ]; then
  echo "Error: Please run as root"
  exit 1
fi

echo "Installing AI Agents & Automation tools..."

# Claude Code
curl -fsSL https://claude.ai/install.sh | bash -
# Move binary to global path if found in root's local bin
if [ -f /root/.local/bin/claude ]; then
    mv /root/.local/bin/claude /usr/local/bin/claude
    chmod +x /usr/local/bin/claude
fi

# OpenCode
curl -fsSL https://opencode.ai/install | bash -
# OpenCode installs to $HOME/.opencode/bin
if [ -f /root/.opencode/bin/opencode ]; then
    mv /root/.opencode/bin/opencode /usr/local/bin/opencode
    chmod +x /usr/local/bin/opencode
    # Cleanup empty dir
    rm -rf /root/.opencode
fi

# Playwright (Set global path for browsers to be accessible by kasm-user)
export PLAYWRIGHT_BROWSERS_PATH=/usr/local/share/playwright
mkdir -p $PLAYWRIGHT_BROWSERS_PATH
npm install -g playwright
npx playwright install --with-deps chromium
chmod -R 755 $PLAYWRIGHT_BROWSERS_PATH

# Gemini CLI
npm install -g @google/gemini-cli
