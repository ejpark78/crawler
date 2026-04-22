#!/usr/bin/env bash
set -e
if [ "$EUID" -ne 0 ]; then
  echo "Error: Please run as root"
  exit 1
fi

echo "Installing Brave Browser..."
curl -fsS https://dl.brave.com/install.sh | bash -
apt-get update && apt-get install -y --no-install-recommends brave-browser

apt-get autoremove -y --no-install-recommends 
apt-get clean && rm -rf /var/lib/apt/lists/*
