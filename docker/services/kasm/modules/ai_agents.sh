#!/usr/bin/env bash
set -e
if [ "$EUID" -ne 0 ]; then
  echo "Error: Please run as root"
  exit 1
fi

echo "Installing AI Agents & Automation tools..."

# Claude Code
curl -fsSL https://claude.ai/install.sh | bash -
if [ -d ~/.local/share/claude ]; then
    rm -rf /usr/local/share/claude
    mv ~/.local/share/claude /usr/local/share/
    chmod -R 755 /usr/local/share/claude
    # Resolve the binary path (it's often a symlink to a versioned directory)
    # If it's a symlink, we want the target to point to /usr/local/share
    if [ -L ~/.local/bin/claude ]; then
        CLAUDE_TARGET=$(readlink -f ~/.local/bin/claude | sed "s|$HOME/.local/share|/usr/local/share|")
        ln -sf "$CLAUDE_TARGET" /usr/local/bin/claude
    else
        ln -sf /usr/local/share/claude/versions/$(ls /usr/local/share/claude/versions | head -n 1)/claude /usr/local/bin/claude
    fi
    chmod +x /usr/local/bin/claude
    rm -f ~/.local/bin/claude
fi

# OpenCode
curl -fsSL https://opencode.ai/install | bash -
if [ -d ~/.opencode ]; then
    rm -rf /usr/local/share/opencode
    mv ~/.opencode /usr/local/share/opencode
    chmod -R 755 /usr/local/share/opencode
    ln -sf /usr/local/share/opencode/bin/opencode /usr/local/bin/opencode
    chmod +x /usr/local/bin/opencode
fi

# Playwright (Set global path for browsers to be accessible by kasm-user)
export PLAYWRIGHT_BROWSERS_PATH=/usr/local/share/playwright
mkdir -p $PLAYWRIGHT_BROWSERS_PATH
npm install -g playwright
npx playwright install --with-deps chromium
chmod -R 755 $PLAYWRIGHT_BROWSERS_PATH

# Gemini CLI
npm install -g @google/gemini-cli
