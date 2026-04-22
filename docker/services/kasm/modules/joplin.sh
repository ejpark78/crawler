#!/usr/bin/env bash
set -ex

if [ "$EUID" -ne 0 ]; then
  echo "Error: Please run as root"
  exit 1
fi

echo "Installing Joplin..."

# Create the target directory first
INSTALL_DIR="/etc/skel/.joplin"
mkdir -p "$INSTALL_DIR"

# Extracting AppImage because FUSE is often not available in Docker
# Note: Using = for long options because the installer script's getopts logic requires it
wget -O - https://raw.githubusercontent.com/laurent22/joplin/dev/Joplin_install_and_update.sh | bash -s -- --allow-root --install-dir="$INSTALL_DIR"

if [ ! -d "$INSTALL_DIR" ] || [ ! -f "$INSTALL_DIR/Joplin.AppImage" ]; then
    echo "Searching for Joplin.AppImage in case it installed elsewhere..."
    FOUND_APPIMAGE=$(find /root -name "Joplin.AppImage" | head -n 1)
    if [ -n "$FOUND_APPIMAGE" ]; then
        echo "Found AppImage at $FOUND_APPIMAGE, moving to $INSTALL_DIR"
        mv "$FOUND_APPIMAGE" "$INSTALL_DIR/Joplin.AppImage"
    else
        echo "Error: Joplin.AppImage not found!"
        exit 1
    fi
fi

cd "$INSTALL_DIR"
chmod +x Joplin.AppImage
./Joplin.AppImage --appimage-extract
mv squashfs-root app
rm Joplin.AppImage

mkdir -p /etc/skel/.local/share/applications
# The installer might have created a desktop file for root
if [ -f /root/.local/share/applications/joplin.desktop ]; then
    cp /root/.local/share/applications/joplin.desktop /etc/skel/.local/share/applications/
    sed -i 's|Exec=.*|Exec=/home/kasm-user/.joplin/app/AppRun --no-sandbox|' /etc/skel/.local/share/applications/joplin.desktop
    sed -i 's|Icon=.*|Icon=/home/kasm-user/.joplin/app/joplin.png|' /etc/skel/.local/share/applications/joplin.desktop
fi

echo "Joplin installation completed successfully."
