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

# --- Configuration ---
# List of modules to install (comma-separated)
# Available: claude, opencode, playwright, gemini, kimi, lmstudio, ollama
MODULES=${MODULES:-"claude,opencode,playwright,gemini,kimi,lmstudio,ollama"}

is_module_enabled() {
    local module="$1"
    [[ ",$MODULES," == *",$module,"* ]]
}

# --- Utility Functions ---
# Function to move tool data to /usr/local/share and setup symlink
# Usage: setup_global_tool <src_dir> <share_name> [bin_rel_path] [bin_name] [display_name] [local_bin_to_move]
setup_global_tool() {
    local src_dir="$1"
    local share_name="$2"
    local bin_rel_path="${3:-}"
    local bin_name="${4:-}"
    local display_name="${5:-$share_name}"
    local local_bin="${6:-}"

    # 1. Handle directory move
    if [ -d "$src_dir" ]; then
        echo ">>> Setting up $display_name for global access..."
        rm -rf "/usr/local/share/$share_name"
        mv "$src_dir" "/usr/local/share/$share_name"
        chmod -R 755 "/usr/local/share/$share_name"
    fi

    # 2. Handle binary (either in share or moved from external local path)
    if [ -n "$bin_name" ]; then
        local target_bin="/usr/local/bin/$bin_name"
        
        # Check if we should move an external local binary
        if [ -n "$local_bin" ] && [ -f "$local_bin" ] && [ ! -f "$target_bin" ]; then
             echo ">>> Moving $display_name binary to $target_bin..."
             mv "$local_bin" "$target_bin"
        fi

        # Check if we should link from share if it doesn't exist yet
        if [ -n "$bin_rel_path" ] && [ ! -f "$target_bin" ]; then
            local share_bin="/usr/local/share/$share_name/$bin_rel_path"
            if [ -f "$share_bin" ]; then
                ln -sf "$share_bin" "$target_bin"
            fi
        fi

        # Final setup and verification
        if [ -f "$target_bin" ]; then
            chmod +x "$target_bin"
            echo "$display_name global setup complete: $(which $bin_name)"
        fi
    fi
}

# Function to link the latest version from a versions directory
# Usage: link_latest_version <versions_dir> <target_bin_path> <display_name>
link_latest_version() {
    local versions_dir="$1"
    local target_bin="$2"
    local display_name="$3"

    if [ ! -f "$target_bin" ] && [ -d "$versions_dir" ]; then
        echo ">>> Searching for latest $display_name version in $versions_dir..."
        local latest_version
        latest_version=$(ls -1 "$versions_dir" | sort -V 2>/dev/null | tail -n 1 || ls -1 "$versions_dir" | tail -n 1)
        
        if [ -n "$latest_version" ]; then
            local bin_path="$versions_dir/$latest_version"
            echo "Found $display_name version $latest_version at $bin_path"
            ln -sf "$bin_path" "$target_bin"
            chmod +x "$target_bin"
        fi
    fi
}

# --- Claude Code ---
if is_module_enabled "claude"; then
    echo ">>> Installing Claude Code..."
    curl -fsSL https://claude.ai/install.sh | bash - || echo "Claude installer returned non-zero, checking if it still installed..."

    if [ -d "$HOME/.local/share/claude" ] || [ -f "$HOME/.local/bin/claude" ]; then
        echo "Setting up Claude Code for global access..."
        
        # Handle share directory and move local binary if it exists
        setup_global_tool "$HOME/.local/share/claude" "claude" "" "claude" "Claude Code" "$HOME/.local/bin/claude"

        # 3. Ensure global symlink exists (searching versions if necessary if it's still missing)
        link_latest_version "/usr/local/share/claude/versions" "/usr/local/bin/claude" "Claude Code"

        # Cleanup the local symlink if it still exists
        rm -f "$HOME/.local/bin/claude"
    fi
fi

# --- OpenCode ---
if is_module_enabled "opencode"; then
    echo ">>> Installing OpenCode..."
    curl -fsSL https://opencode.ai/install | bash - || echo "OpenCode installer failed, but continuing..."

    setup_global_tool "$HOME/.opencode" "opencode" "bin/opencode" "opencode" "OpenCode"
fi

# --- Gemini CLI ---
if is_module_enabled "gemini"; then
    echo ">>> Installing Gemini CLI..."
    npm install -g @google/gemini-cli
fi

# --- Kimi Code ---
if is_module_enabled "kimi"; then
    echo ">>> Installing Kimi Code..."
    curl -LsSf https://code.kimi.com/install.sh | bash - || echo "Kimi Code installer failed, but continuing..."

    # Handle Kimi Code binary and tool data
    setup_global_tool "$HOME/.local/share/uv/tools/kimi-cli" "kimi-cli" "" "kimi" "Kimi Code" "$HOME/.local/bin/kimi"
fi

# --- LM Studio ---
if is_module_enabled "lmstudio"; then
    echo ">>> Installing LM Studio..."
    curl -fsSL https://lmstudio.ai/install.sh | bash - || echo "LM Studio installer failed, but continuing..."

    # Bootstrap if possible before moving to global share
    [ -f "$HOME/.lmstudio/bin/lms" ] && "$HOME/.lmstudio/bin/lms" bootstrap -y || true

    setup_global_tool "$HOME/.lmstudio" "lmstudio" "bin/lms" "lms" "LM Studio"
fi

# --- Ollama ---
if is_module_enabled "ollama"; then
    echo ">>> Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | bash - || echo "Ollama installer failed, but continuing..."

    setup_global_tool "$HOME/.ollama" "ollama" "" "ollama" "Ollama" "$HOME/.local/bin/ollama"
fi

# --- Playwright ---
if is_module_enabled "playwright"; then
    echo ">>> Installing Playwright and Chromium..."
    export PLAYWRIGHT_BROWSERS_PATH=/usr/local/share/playwright
    mkdir -p $PLAYWRIGHT_BROWSERS_PATH
    apt-get update
    npm install -g playwright

    # Install chromium and its system dependencies
    npx playwright install --with-deps chromium
    chmod -R 755 $PLAYWRIGHT_BROWSERS_PATH
fi

# --- Finish AI Agents Installation ---
echo "AI Agents installation finished successfully!"
