#!/usr/bin/env bash
# This script runs at container start as the kasm-user.

echo "Initializing Oh My Zsh ..."

# 3. Ensure Zsh configuration exists for Oh My Zsh persistence
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    echo "Syncing Oh My Zsh configuration from /etc/skel..."
    cp -rn /etc/skel/.oh-my-zsh "$HOME/" 2>/dev/null || true
    cp -n /etc/skel/.zshrc "$HOME/" 2>/dev/null || true

    cp /modules/.zshrc "$HOME/.zshrc"
fi

echo "Oh My Zsh initialization complete."
