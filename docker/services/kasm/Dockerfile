# Kasm Workspaces 맞춤형 개발 환경 (VDI) Dockerfile
#
# 이 설정은 kasmweb/core-ubuntu-noble을 기반으로 최적화된 GUI 개발 환경을 구축합니다.

FROM kasmweb/core-ubuntu-noble:1.18.0
USER root

# 0. 빌드 인자(Arguments) 설정 - 선택적 모듈 설치 제어
ARG MODULE_FCITX=true
ARG MODULE_OHMYZSH=true
ARG MODULE_DESKTOP_UTILS=false
ARG MODULE_UV=false
ARG MODULE_NODEJS=false
ARG MODULE_AI_AGENTS=false
ARG MODULE_VSCODE=false
ARG MODULE_DBEAVER=false
ARG MODULE_BRAVE=false
ARG MODULE_JOPLIN=false
ARG MODULE_DOCKER=false
ARG MODULE_ANTIGRAVITY=false
ARG MODULE_CHROME=true
ARG MODULE_FIREFOX=false
ARG MODULE_MONGO_COMPASS=false
ARG MODULE_K8S_TOOLS=true

# 1. 환경 변수 설정
ENV DEBIAN_FRONTEND=noninteractive \
    PASSWORD_STORE=basic \
    PLAYWRIGHT_BROWSERS_PATH=/usr/local/share/playwright \
    UV_INSTALL_DIR=/usr/local/bin

ENV XMODIFIERS=@im=fcitx \
    GTK_IM_MODULE=fcitx \
    QT_IM_MODULE=fcitx 

# 2. System Core & Base Packages (고정 레이어)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
    gnupg \
    gnupg2 \
    software-properties-common \
    lsb-release \
    wget \
    sudo \
    zstd \
    locales \
    python3 \
    python3-pip \
    eza \
    fzf \
    git \
    unzip \
    && locale-gen ko_KR.UTF-8 en_US.UTF-8 \
    && update-locale LANG=ko_KR.UTF-8 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 3. 선택적 모듈 설치 (모듈화된 스크립트 실행)
COPY modules/ /modules/
RUN chmod +x /modules/*.sh && /modules/install.sh

# 5. 시작 스크립트 설정
COPY startup/ /dockerstartup/custom_startup/
RUN chmod +x /dockerstartup/custom_startup/*.sh \
    && mv /dockerstartup/custom_startup/custom_startup.sh /dockerstartup/custom_startup.sh \
    && chown -R kasm-user:kasm-user /home/kasm-user

# 6. 사용자 권한 설정 (Sudo)
RUN echo "kasm-user ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers \
    && usermod -s /bin/zsh kasm-user

USER kasm-user
RUN im-config -n fcitx

WORKDIR /home/kasm-user
EXPOSE 6901
