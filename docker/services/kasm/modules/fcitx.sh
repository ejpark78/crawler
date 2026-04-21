#!/usr/bin/env bash
set -e

if [ "$EUID" -ne 0 ]; then
  echo "Error: Please run as root"
  exit 1
fi

echo "Installing Korean Language & IME Support..."
apt-get update && apt-get install -y --no-install-recommends \
    language-pack-ko \
    language-pack-en \
    fonts-nanum \
    fcitx \
    fcitx-hangul \
    fcitx-frontend-gtk2 \
    fcitx-frontend-gtk3 \
    fcitx-frontend-qt5 \
    fcitx-bin \
    im-config \
    dbus-x11

# Fcitx Autostart & Profile 설정 (Skel & User)
mkdir -p /etc/skel/.config/autostart /etc/skel/.config/fcitx
echo -e '[Desktop Entry]\nType=Application\nExec=fcitx -dr\nHidden=false\nNoDisplay=false\nX-GNOME-Autostart-enabled=true\nName[ko_KR]=fcitx\nName=fcitx' > /etc/skel/.config/autostart/fcitx.desktop
echo -e "[Profile]\nIMName=fcitx-hangul" > /etc/skel/.config/fcitx/profile

# 현재 사용자가 kasm-user인 경우를 대비해 복사 (Kasm 환경 특성)
if [ -d /home/kasm-user ]; then
    cp -r /etc/skel/. /home/kasm-user/
    chown -R kasm-user:kasm-user /home/kasm-user
fi

apt-get clean && rm -rf /var/lib/apt/lists/*
