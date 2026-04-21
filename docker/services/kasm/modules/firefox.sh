#!/usr/bin/env bash
set -e
if [ "$EUID" -ne 0 ]; then
  echo "Error: Please run as root"
  exit 1
fi

echo "Installing Firefox (Non-Snap)..."

# Ensure keyrings directory exists
install -d -m 0755 /etc/apt/keyrings

# Import Mozilla APT repository key
wget -q https://packages.mozilla.org/apt/repo-signing-key.gpg -O- | tee /etc/apt/keyrings/packages.mozilla.org.gpg > /dev/null

# Add Mozilla APT repository
echo "deb [signed-by=/etc/apt/keyrings/packages.mozilla.org.gpg] https://packages.mozilla.org/apt mozilla main" | tee /etc/apt/sources.list.d/mozilla.list > /dev/null

# Configure APT pinning to prioritize Mozilla repository over Ubuntu's snap-redirected version
echo '
Package: *
Pin: origin packages.mozilla.org
Pin-Priority: 1000
' | tee /etc/apt/preferences.d/mozilla

# Install Firefox
apt-get update && apt-get install -y --no-install-recommends firefox

# Cleanup
apt-get clean && rm -rf /var/lib/apt/lists/*

echo "Firefox installation completed successfully."
