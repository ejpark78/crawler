#!/usr/bin/env bash
set -e

if [ "$EUID" -ne 0 ]; then
  echo "Error: Please run as root"
  exit 1
fi

MODULES_DIR="/modules"

echo "Starting modular installation..."

# 모듈 설치 함수
install_module() {
    local name=$1
    local script=$2
    local enabled=$3

    if [ "$enabled" = "true" ]; then
        echo "Installing module: $name..."
        if [ -f "$MODULES_DIR/$script" ]; then
            bash "$MODULES_DIR/$script"
        else
            echo "Warning: Script $script not found in $MODULES_DIR"
        fi
    else
        echo "Skipping module: $name"
    fi
}

# 개별 모듈 실행
install_module "Fcitx" "fcitx.sh" "$MODULE_FCITX"
install_module "Desktop Utils" "desktop_utils.sh" "$MODULE_DESKTOP_UTILS"
install_module "uv" "uv.sh" "$MODULE_UV"
install_module "Node.js" "nodejs.sh" "$MODULE_NODEJS"
install_module "AI Agents" "ai_agents.sh" "$MODULE_AI_AGENTS"
install_module "VS Code" "vscode.sh" "$MODULE_VSCODE"
install_module "DBeaver" "dbeaver.sh" "$MODULE_DBEAVER"
install_module "Brave" "brave.sh" "$MODULE_BRAVE"
install_module "Oh My Zsh" "ohmyzsh.sh" "$MODULE_OHMYZSH"
install_module "Joplin" "joplin.sh" "$MODULE_JOPLIN"
install_module "Docker" "docker.sh" "$MODULE_DOCKER"
install_module "Antigravity" "antigravity.sh" "$MODULE_ANTIGRAVITY"
install_module "Chrome" "chrome.sh" "$MODULE_CHROME"
install_module "Firefox" "firefox.sh" "$MODULE_FIREFOX"
install_module "Mongo Compass" "mongo_compass.sh" "$MODULE_MONGO_COMPASS"

echo "Modular installation completed."
