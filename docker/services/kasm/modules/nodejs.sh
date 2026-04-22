#!/usr/bin/env bash
set -e

if [ "$EUID" -ne 0 ]; then
  echo "Error: Please run as root"
  exit 1
fi

echo "Installing Node.js 20..."
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get update && apt-get install -y --no-install-recommends nodejs
apt-get clean && rm -rf /var/lib/apt/lists/*

echo "Installing Bun..."
curl -fsSL https://bun.sh/install | BUN_INSTALL=/usr/local/bun bash
ln -sf /usr/local/bun/bin/bun /usr/local/bin/bun

echo "Installing pnpm..."
npm install -g pnpm
