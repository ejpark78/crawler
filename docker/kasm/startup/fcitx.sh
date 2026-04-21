#!/usr/bin/env bash
# This script runs at container start as the kasm-user.

echo "Initializing Korean Input (Fcitx)..."

# 1. Ensure configuration exists in the persistent home directory
if [ ! -f "$HOME/.config/fcitx/profile" ]; then
    echo "Copying fcitx configuration templates from /etc/skel..."
    mkdir -p "$HOME/.config/fcitx" "$HOME/.config/autostart"
    cp -rn /etc/skel/.config/fcitx/* "$HOME/.config/fcitx/" 2>/dev/null || true
    cp -rn /etc/skel/.config/autostart/* "$HOME/.config/autostart/" 2>/dev/null || true
fi

# 2. Ensure .xinputrc is set to fcitx
if [ ! -f "$HOME/.xinputrc" ]; then
    echo "run_im fcitx" > "$HOME/.xinputrc"
fi

# 4. Start fcitx if it's not already running
# Kasm's window manager startup might not always trigger autostart correctly.
if ! pgrep -x "fcitx" > /dev/null; then
    echo "Starting fcitx-daemon..."
    fcitx -dr
fi

echo "Korean Input and Zsh initialization complete."
