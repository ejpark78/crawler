#!/usr/bin/env bash
set -e
if [ "$EUID" -ne 0 ]; then
  echo "Error: Please run as root"
  exit 1
fi

echo "Installing Google Chrome..."

# GUI Dependencies
apt-get update && apt-get install -y --no-install-recommends \
    libfuse2 libgbm1 libasound2t64 libnss3 libxshmfence1 libatk1.0-0 \
    libatk-bridge2.0-0 libcups2 libdrm2 libgtk-3-0 libsecret-1-0

wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
apt-get install -y --no-install-recommends ./google-chrome-stable_current_amd64.deb
rm google-chrome-stable_current_amd64.deb

# Install wrapper to handle --no-sandbox
echo -e '#!/usr/bin/env bash\n/usr/bin/google-chrome-stable --no-sandbox --password-store=basic "$@"' > /usr/local/bin/google-chrome
chmod +x /usr/local/bin/google-chrome

apt-get clean && rm -rf /var/lib/apt/lists/*
