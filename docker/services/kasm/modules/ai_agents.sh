#!/usr/bin/env bash
set -ex

if [ "$EUID" -ne 0 ]; then
  echo "Error: Please run as root"
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive
export HOME=/root
export PATH="/root/.local/bin:$PATH"

echo "Installing AI Agents & Automation tools..."

# --- Claude Code ---
echo ">>> Installing Claude Code..."
curl -fsSL https://claude.ai/install.sh | bash - || echo "Claude installer returned non-zero, checking if it still installed..."

if [ -d "$HOME/.local/share/claude" ] || [ -f "$HOME/.local/bin/claude" ]; then
    echo "Setting up Claude Code for global access..."
    
    # 1. Handle the share directory
    if [ -d "$HOME/.local/share/claude" ]; then
        echo "Moving Claude share directory to /usr/local/share/claude"
        rm -rf /usr/local/share/claude
        mv "$HOME/.local/share/claude" /usr/local/share/
        chmod -R 755 /usr/local/share/claude
    fi

    # 2. Handle the binary
    # If it's a regular file (not a symlink), move it
    if [ -f "$HOME/.local/bin/claude" ] && [ ! -L "$HOME/.local/bin/claude" ]; then
        echo "Moving Claude binary to /usr/local/bin/claude"
        mv "$HOME/.local/bin/claude" /usr/local/bin/claude
    fi
    
    # 3. Ensure global symlink exists (searching versions if necessary)
    if [ ! -f /usr/local/bin/claude ]; then
        echo "Searching for Claude binary in versions directory..."
        if [ -d /usr/local/share/claude/versions ]; then
            # Get the latest version (using version sort if possible)
            LATEST_VERSION=$(ls -1 /usr/local/share/claude/versions | sort -V 2>/dev/null | tail -n 1 || ls -1 /usr/local/share/claude/versions | tail -n 1)
            if [ -n "$LATEST_VERSION" ]; then
                CLAUDE_BIN_PATH="/usr/local/share/claude/versions/$LATEST_VERSION"
                echo "Found Claude version $LATEST_VERSION at $CLAUDE_BIN_PATH"
                ln -sf "$CLAUDE_BIN_PATH" /usr/local/bin/claude
            fi
        fi
    fi

    # 4. Final check and permissions
    if [ -f /usr/local/bin/claude ]; then
        chmod +x /usr/local/bin/claude
        echo "Claude Code global setup complete: $(which claude)"
    else
        echo "Warning: Could not set up Claude Code globally"
    fi

    # Cleanup the local symlink if it still exists
    rm -f "$HOME/.local/bin/claude"
fi

# --- OpenCode ---
echo ">>> Installing OpenCode..."
curl -fsSL https://opencode.ai/install | bash - || echo "OpenCode installer failed, but continuing..."

if [ -d "$HOME/.opencode" ]; then
    echo "Setting up OpenCode for global access..."
    rm -rf /usr/local/share/opencode
    mv "$HOME/.opencode" /usr/local/share/opencode
    chmod -R 755 /usr/local/share/opencode
    if [ -f /usr/local/share/opencode/bin/opencode ]; then
        ln -sf /usr/local/share/opencode/bin/opencode /usr/local/bin/opencode
        chmod +x /usr/local/bin/opencode
        echo "OpenCode global setup complete: $(which opencode)"
    fi
fi

# --- Playwright ---
echo ">>> Installing Playwright and Chromium..."
export PLAYWRIGHT_BROWSERS_PATH=/usr/local/share/playwright
mkdir -p $PLAYWRIGHT_BROWSERS_PATH
apt-get update
npm install -g playwright
# Install chromium and its system dependencies
npx playwright install --with-deps chromium
chmod -R 755 $PLAYWRIGHT_BROWSERS_PATH

# --- Gemini CLI ---
echo ">>> Installing Gemini CLI..."
npm install -g @google/gemini-cli

echo "AI Agents installation finished successfully!"
