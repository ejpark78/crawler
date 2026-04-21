# WSL2 (Ubuntu 24.04) 최적화 개발 환경 Dockerfile
# 이 설정은 호스트의 WSL 환경과 일관성을 유지하면서 프로젝트에 필요한 도구들을 사전 구성합니다.

FROM ubuntu:24.04

# 1. 환경 변수 설정
ENV DEBIAN_FRONTEND=noninteractive \
    LANG=ko_KR.UTF-8 \
    LANGUAGE=ko_KR:ko \
    LC_ALL=ko_KR.UTF-8 \
    UV_INSTALL_DIR=/usr/local/bin

# 2. 필수 시스템 패키지 및 한국어 로케일 설정
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
    python3 \
    python3-pip \
    sudo \
    locales \
    language-pack-ko \
    fonts-nanum \
    vim \
    jq \
    eza \
    fzf \
    zstd \
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
    && locale-gen ko_KR.UTF-8 en_US.UTF-8 \
    && update-locale LANG=ko_KR.UTF-8 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 3. 개발 도구 설치 (uv, Node.js)
RUN install -m 0755 -d /etc/apt/keyrings \
    && curl -LsSf https://astral.sh/uv/install.sh | bash - \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get update && apt-get install -y --no-install-recommends nodejs \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 4. 인프라 및 AI 도구 (Docker CLI, Antigravity, Claude Code)
RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list \
    && curl -fsSL https://us-central1-apt.pkg.dev/doc/repo-signing-key.gpg | gpg --dearmor --yes -o /etc/apt/keyrings/antigravity-repo-key.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/antigravity-repo-key.gpg] https://us-central1-apt.pkg.dev/projects/antigravity-auto-updater-dev/ antigravity-debian main" > /etc/apt/sources.list.d/antigravity.list \
    && curl -fsSL https://claude.ai/install.sh | bash - \
    && apt-get update && apt-get install -y --no-install-recommends \
        docker-ce-cli \
        docker-compose-plugin \
        antigravity \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 5. 크롤링 관련 의존성 (Playwright & Chrome Headless용)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgbm1 \
    libasound2t64 \
    libnss3 \
    libxshmfence1 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libgtk-3-0 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 6. 사용자 설정 (ejpark:1000)
# 호스트와 UID/GID를 맞추어 볼륨 마운트 시 권한 문제를 방지합니다.
RUN groupadd -g 1000 ejpark \
    && useradd -u 1000 -g ejpark -m -s /bin/zsh ejpark \
    && echo "ejpark ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

# 7. Oh My Zsh 설정 (User: ejpark)
USER ejpark
RUN sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended \
    && git clone https://github.com/zsh-users/zsh-autosuggestions ${HOME}/.oh-my-zsh/custom/plugins/zsh-autosuggestions \
    && git clone https://github.com/zsh-users/zsh-syntax-highlighting.git ${HOME}/.oh-my-zsh/custom/plugins/zsh-syntax-highlighting \
    && git clone https://github.com/Aloxaf/fzf-tab ${HOME}/.oh-my-zsh/custom/plugins/fzf-tab \
    && sed -i 's/plugins=(git)/plugins=(git git-prompt sudo docker web-search zsh-autosuggestions zsh-syntax-highlighting fzf-tab)/' ${HOME}/.zshrc

WORKDIR /home/ejpark

CMD ["/bin/zsh"]
