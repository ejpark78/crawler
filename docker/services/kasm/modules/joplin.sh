#!/usr/bin/env bash
set -e

if [ "$EUID" -ne 0 ]; then
  echo "Error: Please run as root"
  exit 1
fi

echo "Installing Joplin..."

# Extracting AppImage because FUSE is often not available in Docker
wget -O - https://raw.githubusercontent.com/laurent22/joplin/dev/Joplin_install_and_update.sh | bash -s -- --allow-root --install-dir /etc/skel/.joplin

cd /etc/skel/.joplin
chmod +x Joplin.AppImage
./Joplin.AppImage --appimage-extract
mv squashfs-root app
rm Joplin.AppImage

mkdir -p /etc/skel/.local/share/applications
if [ -f /root/.local/share/applications/joplin.desktop ]; then
    cp /root/.local/share/applications/joplin.desktop /etc/skel/.local/share/applications/
    sed -i 's|Exec=.*|Exec=/home/kasm-user/.joplin/app/AppRun --no-sandbox|' /etc/skel/.local/share/applications/joplin.desktop
    sed -i 's|Icon=.*|Icon=/home/kasm-user/.joplin/app/joplin.png|' /etc/skel/.local/share/applications/joplin.desktop
fi
