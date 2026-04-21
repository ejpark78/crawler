#!/usr/bin/env bash
set -e

echo "Initializing Joplin ..."

# Ensure Joplin exists in the user's home directory for persistence
if [ ! -d "$HOME/.joplin" ]; then
    echo "Syncing Joplin from /etc/skel..."
    if [ -d "/etc/skel/.joplin" ]; then
        cp -r /etc/skel/.joplin "$HOME/"
    else
        echo "Warning: /etc/skel/.joplin not found."
    fi
    
    # Sync desktop entry
    mkdir -p "$HOME/.local/share/applications"
    if [ -f "/etc/skel/.local/share/applications/joplin.desktop" ]; then
        cp -n /etc/skel/.local/share/applications/joplin.desktop "$HOME/.local/share/applications/" 2>/dev/null || true
    fi
fi

echo "Joplin initialization complete."
