#!/usr/bin/env bash
set -e
if [ "$EUID" -ne 0 ]; then
  echo "Error: Please run as root"
  exit 1
fi

echo "Installing Firefox (Non-Snap)..."

apt-get update && apt-get install -y --no-install-recommends wget gnupg

# Ensure keyrings directory exists
install -d -m 0755 /etc/apt/keyrings

# Import Mozilla APT repository key using a more resilient method
wget -qO- https://packages.mozilla.org/apt/repo-signing-key.gpg | gpg --dearmor | tee /etc/apt/keyrings/packages.mozilla.org.gpg > /dev/null

# Double check the permissions
chmod 644 /etc/apt/keyrings/packages.mozilla.org.gpg

# Install Firefox
apt-get update && apt-get install -y --no-install-recommends firefox

# Cleanup
apt-get autoremove -y --no-install-recommends 
apt-get clean && rm -rf /var/lib/apt/lists/*

echo "Firefox installation completed successfully."
