#!/usr/bin/env bash
set -e

if [ "$EUID" -ne 0 ]; then
  echo "Error: Please run as root"
  exit 1
fi

echo "Installing Desktop Utilities & Terminals..."
apt-get update && apt-get install -y --no-install-recommends \
    tilix \
    alacritty \
    nautilus \
    flameshot \
    eza \
    fzf \
    git

apt-get clean && rm -rf /var/lib/apt/lists/*
