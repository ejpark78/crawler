FROM kasmweb/core-ubuntu-noble:1.18.0
USER root

# 1. Environment variables
ENV UV_INSTALL_DIR=/usr/local/bin \
    DEBIAN_FRONTEND=noninteractive \
    PASSWORD_STORE=basic \
    XMODIFIERS=@im=fcitx \
    GTK_IM_MODULE=fcitx \
    QT_IM_MODULE=fcitx 

# 2. Package & Repository Setup
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    gnupg \
    gnupg2 \
    software-properties-common \
    lsb-release \
    wget \
    git \
    zsh \
    locales \
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
    python3 \
    python3-pip \
    sudo \
    tilix \
    alacritty \
    nautilus \
    # GUI & Electron Dependencies for Chrome
    libgbm1 \
    libasound2t64 \
    libnss3 \
    libxshmfence1 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libgtk-3-0 \
    libsecret-1-0 \
    dbus-x11 \
    # External Repositories
    && install -m 0755 -d /etc/apt/keyrings \
    # Google Chrome (via .deb)
    && wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get install -y --no-install-recommends ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb \
    # VS Code
    && curl -fSsL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /etc/apt/keyrings/packages.microsoft.gpg \
    && echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" > /etc/apt/sources.list.d/vscode.list \
    && apt-get update && apt-get install -y --no-install-recommends code \
    # DBeaver
    && add-apt-repository ppa:serge-rider/dbeaver-ce -y \
    && apt-get update && apt-get install -y --no-install-recommends dbeaver-ce \
    # MongoDB Compass (via .deb)
    && wget -q https://compass.mongodb.com/api/v2/download/latest/compass/stable/linux_deb -O mongodb-compass.deb \
    && apt-get install -y --no-install-recommends ./mongodb-compass.deb \
    && rm mongodb-compass.deb \
    # Setup Locales (Korean & English)
    && locale-gen ko_KR.UTF-8 en_US.UTF-8 \
    && update-locale LANG=ko_KR.UTF-8 \
    # Cleanup
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 3. Korean Input configurations
USER kasm-user
WORKDIR /home/kasm-user

# 3.1 Install Oh My Zsh
RUN sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended \
    && git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions \
    && git clone https://github.com/zsh-users/zsh-syntax-highlighting.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting \
    && sed -i 's/plugins=(git)/plugins=(git zsh-autosuggestions zsh-syntax-highlighting)/' ~/.zshrc

# 3.2 Fcitx Setup (User)
RUN im-config -n fcitx

USER root
# 3.2 Skeleton Configuration (Root)
RUN mkdir -p /etc/skel/.config/autostart /etc/skel/.config/fcitx \
    && echo '[Desktop Entry]\nType=Application\nExec=fcitx -dr\nHidden=false\nNoDisplay=false\nX-GNOME-Autostart-enabled=true\nName[ko_KR]=fcitx\nName=fcitx' > /etc/skel/.config/autostart/fcitx.desktop \
    && echo "[Profile]\nIMName=fcitx-hangul" > /etc/skel/.config/fcitx/profile \
    && cp -r /etc/skel/. /home/kasm-user/ \
    && chown -R kasm-user:kasm-user /home/kasm-user

# 4. Chrome Sandbox/Keyring Fix
# In containerized environments, Electron apps often need --no-sandbox and --password-store=basic
RUN echo '#!/usr/bin/env bash\n/usr/bin/google-chrome-stable --no-sandbox --password-store=basic "$@"' > /usr/local/bin/google-chrome \
    && chmod +x /usr/local/bin/google-chrome \
    && echo '#!/usr/bin/env bash\n/usr/bin/mongodb-compass --no-sandbox "$@"' > /usr/local/bin/mongodb-compass \
    && chmod +x /usr/local/bin/mongodb-compass

# 4. Project Directory Structure & Startup Scripts
COPY custom_startup.sh /dockerstartup/custom_startup.sh
RUN chmod +x /dockerstartup/custom_startup.sh \
    && mkdir -p /home/kasm-user/project/docs/history /home/kasm-user/project/docs/plans \
    && chown -R kasm-user:kasm-user /home/kasm-user

# 5. User Permissions (Sudo)
RUN echo "kasm-user ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

# 6. Final Configuration
RUN usermod -s /bin/zsh kasm-user

USER kasm-user
WORKDIR /home/kasm-user

