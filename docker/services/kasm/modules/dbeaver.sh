#!/usr/bin/env bash
set -e
if [ "$EUID" -ne 0 ]; then
  echo "Error: Please run as root"
  exit 1
fi

echo "Installing DBeaver..."

# GUI Dependencies
apt-get update && apt-get install -y --no-install-recommends \
    libfuse2 libgbm1 libasound2t64 libnss3 libxshmfence1 libatk1.0-0 \
    libatk-bridge2.0-0 libcups2 libdrm2 libgtk-3-0 libsecret-1-0

add-apt-repository ppa:serge-rider/dbeaver-ce -y
apt-get update && apt-get install -y --no-install-recommends dbeaver-ce
apt-get clean && rm -rf /var/lib/apt/lists/*
