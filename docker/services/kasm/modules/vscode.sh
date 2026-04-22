#!/usr/bin/env bash
set -e

if [ "$EUID" -ne 0 ]; then
  echo "Error: Please run as root"
  exit 1
fi

echo "Installing VS Code..."

# GUI Dependencies
apt-get update && apt-get install -y --no-install-recommends \
    libfuse2 libgbm1 libasound2t64 libnss3 libxshmfence1 libatk1.0-0 \
    libatk-bridge2.0-0 libcups2 libdrm2 libgtk-3-0 libsecret-1-0

curl -fSsL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /etc/apt/keyrings/packages.microsoft.gpg
echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" > /etc/apt/sources.list.d/vscode.list

apt-get update && apt-get install -y --no-install-recommends code

apt-get autoremove -y --no-install-recommends 
apt-get clean && rm -rf /var/lib/apt/lists/*
