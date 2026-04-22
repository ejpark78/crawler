#!/usr/bin/env bash
set -e

if [ "$EUID" -ne 0 ]; then
  echo "Error: Please run as root"
  exit 1
fi

echo "Installing MongoDB Compass..."

# GUI Dependencies
apt-get update && apt-get install -y --no-install-recommends \
    libfuse2 libgbm1 libasound2t64 libnss3 libxshmfence1 libatk1.0-0 \
    libatk-bridge2.0-0 libcups2 libdrm2 libgtk-3-0 libsecret-1-0

wget -q https://compass.mongodb.com/api/v2/download/latest/compass/stable/linux_deb -O mongodb-compass.deb
apt-get install -y --no-install-recommends ./mongodb-compass.deb
rm mongodb-compass.deb

# Install wrapper to handle --no-sandbox
echo -e '#!/usr/bin/env bash\n/usr/bin/mongodb-compass --no-sandbox "$@"' > /usr/local/bin/mongodb-compass
chmod +x /usr/local/bin/mongodb-compass

apt-get autoremove -y --no-install-recommends 
apt-get clean && rm -rf /var/lib/apt/lists/*
