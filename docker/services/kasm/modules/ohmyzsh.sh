#!/usr/bin/env bash
set -e

echo "Installing Oh My Zsh & Plugins..."

# Dependencies
apt-get update && apt-get install -y --no-install-recommends \
    zsh git curl ca-certificates

ZSH=/etc/skel/.oh-my-zsh sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended

git clone https://github.com/zsh-users/zsh-autosuggestions /etc/skel/.oh-my-zsh/custom/plugins/zsh-autosuggestions
git clone https://github.com/zsh-users/zsh-syntax-highlighting.git /etc/skel/.oh-my-zsh/custom/plugins/zsh-syntax-highlighting
git clone https://github.com/Aloxaf/fzf-tab /etc/skel/.oh-my-zsh/custom/plugins/fzf-tab

# Initialize .zshrc in skel
cp /etc/skel/.oh-my-zsh/templates/zshrc.zsh-template /etc/skel/.zshrc
sed -i 's/export ZSH="\/etc\/skel\/.oh-my-zsh"/export ZSH="$HOME\/.oh-my-zsh"/' /etc/skel/.zshrc
sed -i 's/plugins=(git)/plugins=(git git-prompt sudo docker web-search zsh-autosuggestions zsh-syntax-highlighting fzf-tab)/' /etc/skel/.zshrc

echo -e '\n# Tilix VTE configuration\nif [ $TILIX_ID ] || [ $VTE_VERSION ]; then\n    source /etc/profile.d/vte-2.91.sh\nfi' >> /etc/skel/.zshrc
echo -e '\nalias docker="sudo docker"\n' >> /etc/skel/.zshrc

apt-get clean && rm -rf /var/lib/apt/lists/*
