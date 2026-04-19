# Kasm Workspaces 맞춤형 개발 환경 (VDI) Dockerfile
#
# 이 설정은 kasmweb/core-ubuntu-noble을 기반으로 최적화된 GUI 개발 환경을 구축합니다.
# 주요 특징:
# 1. 완벽한 한글 환경: 한국어 로케일 설정 및 fcitx-hangul 기반의 한글 입력 체계 구축
# 2. 강력한 개발 스택: uv, Node.js, Python, Git 및 고성능 터미널(Alacritty) 지원
# 3. GUI 생산성 도구: VS Code, Google Chrome, DBeaver, MongoDB Compass 사전 설치
# 4. 인프라 제어: Docker CLI 및 Docker-out-of-Docker(DooD)를 위한 권한 설정 포함
# 5. 사용자 최적화: kasm-user의 sudo 권한 부여 및 Zsh 기반의 현대적인 셸 환경 제공

FROM kasmweb/core-ubuntu-noble:1.18.0
USER root

# 1. 환경 변수 설정
ENV DEBIAN_FRONTEND=noninteractive \
    UV_INSTALL_DIR=/usr/local/bin \
    PASSWORD_STORE=basic

ENV XMODIFIERS=@im=fcitx \
    GTK_IM_MODULE=fcitx \
    QT_IM_MODULE=fcitx 

# 2. 기본 패키지 및 저장소 설정
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
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
    # uv
    && curl -LsSf https://astral.sh/uv/install.sh | bash - \
    # Node.js (20.x)
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get update && apt-get install -y --no-install-recommends nodejs \
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
    # Docker CLI
    && curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list \
    && apt-get update && apt-get install -y --no-install-recommends docker-ce-cli docker-compose-plugin \
    # Antigravity
    && curl -fsSL https://us-central1-apt.pkg.dev/doc/repo-signing-key.gpg | gpg --dearmor --yes -o /etc/apt/keyrings/antigravity-repo-key.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/antigravity-repo-key.gpg] https://us-central1-apt.pkg.dev/projects/antigravity-auto-updater-dev/ antigravity-debian main" > /etc/apt/sources.list.d/antigravity.list \
    && apt-get update && apt-get install -y --no-install-recommends antigravity \
    # Setup Locales (Korean & English)
    && locale-gen ko_KR.UTF-8 en_US.UTF-8 \
    && update-locale LANG=ko_KR.UTF-8 \
    # Cleanup
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 3. 기본 설정 및 스켈레톤 구성 (Root)
RUN mkdir -p /etc/skel/.config/autostart /etc/skel/.config/fcitx \
    && echo '[Desktop Entry]\nType=Application\nExec=fcitx -dr\nHidden=false\nNoDisplay=false\nX-GNOME-Autostart-enabled=true\nName[ko_KR]=fcitx\nName=fcitx' > /etc/skel/.config/autostart/fcitx.desktop \
    && echo "[Profile]\nIMName=fcitx-hangul" > /etc/skel/.config/fcitx/profile \
    && cp -r /etc/skel/. /home/kasm-user/ \
    && chown -R kasm-user:kasm-user /home/kasm-user

# 4. Chrome 샌드박스 및 키링 수정
# In containerized environments, Electron apps often need --no-sandbox and --password-store=basic
RUN echo '#!/usr/bin/env bash\n/usr/bin/google-chrome-stable --no-sandbox --password-store=basic "$@"' > /usr/local/bin/google-chrome \
    && chmod +x /usr/local/bin/google-chrome \
    && echo '#!/usr/bin/env bash\n/usr/bin/mongodb-compass --no-sandbox "$@"' > /usr/local/bin/mongodb-compass \
    && chmod +x /usr/local/bin/mongodb-compass

# 5. 시작 스크립트 설정
COPY startup/* /dockerstartup/
RUN chmod +x /dockerstartup/* \
    && chown -R kasm-user:kasm-user /home/kasm-user

# 6. 사용자 권한 설정 (DooD 지원 및 Sudo)
RUN for gid in 999 998 989; do \
        if getent group $gid; then \
            GROUP_NAME=$(getent group $gid | cut -d: -f1); \
        else \
            GROUP_NAME="docker_host_${gid}"; \
            groupadd -g $gid $GROUP_NAME; \
        fi; \
        usermod -aG $GROUP_NAME kasm-user; \
    done

# 7. Sudo 권한 부여
RUN echo "kasm-user ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

# 8. 최종 설정 및 셸 변경
RUN usermod -s /bin/zsh kasm-user

USER kasm-user

RUN im-config -n fcitx

WORKDIR /home/kasm-user
