#!/usr/bin/env bash
# ==============================================================================
# Kubernetes 운영 필수 도구 설치 스크립트
# ==============================================================================
# 이 스크립트는 Kubernetes 클러스터 관리 및 모니터링에 필요한 주요 CLI 도구들을
# 자동으로 감지하여 설치합니다. (대상: kubectl, helm, k9s, kubectx, stern 등)

set -e

# 루트 권한 확인
if [ "$EUID" -ne 0 ]; then
  echo "Error: Please run as root"
  exit 1
fi

echo "Installing Kubernetes tools..."

# 1. kubectl 설치 (Kubernetes 커맨드라인 도구)
echo "# 1. Installing kubectl..."
if ! command -v kubectl &> /dev/null; then
    KUBECTL_VERSION=$(curl -L -s https://dl.k8s.io/release/stable.txt)
    # 아키텍처 감지 (amd64, arm64)
    ARCH=$(uname -m)
    case $ARCH in
        x86_64)  K8S_ARCH="amd64" ;;
        aarch64) K8S_ARCH="arm64" ;;
        *)       echo "Unsupported architecture: $ARCH"; exit 1 ;;
    esac
    curl -LO "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/${K8S_ARCH}/kubectl"
    install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
    rm kubectl
else
    echo "kubectl already installed, skipping..."
fi

# 2. Helm 설치 (Kubernetes 패키지 매니저)
echo "# 2. Installing helm..."
if ! command -v helm &> /dev/null; then
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
else
    echo "helm already installed, skipping..."
fi

# 3. k9s 설치 (터미널 기반 클러스터 관리 UI)
echo "# 3. Installing k9s..."
if ! command -v k9s &> /dev/null; then
    K9S_JSON=$(curl -sL "https://api.github.com/repos/derailed/k9s/releases/latest")
    K9S_VERSION=$(echo "$K9S_JSON" | grep -Po '"tag_name": "v\K[^"]*' || true)
    if [ -z "$K9S_VERSION" ]; then
        echo "Error: Could not determine k9s version from GitHub API."
        echo "Response: $K9S_JSON"
        exit 1
    fi
    echo "k9s version: $K9S_VERSION"
    # 아키텍처에 맞는 바이너리 다운로드 (amd64 고정 사용 중이나 필요 시 변수화 가능)
    curl -Lo k9s.tar.gz "https://github.com/derailed/k9s/releases/download/v${K9S_VERSION}/k9s_Linux_amd64.tar.gz"
    tar -xzf k9s.tar.gz k9s
    mv k9s /usr/local/bin/k9s
    rm k9s.tar.gz
else
    echo "k9s already installed, skipping..."
fi

# 4. kubectx & kubens 설치 (컨텍스트 및 네임스페이스 빠른 전환 도구)
echo "# 4. Installing kubectx & kubens..."
if [ ! -d /opt/kubectx ]; then
    git clone https://github.com/ahmetb/kubectx /opt/kubectx
    ln -sf /opt/kubectx/kubectx /usr/local/bin/kubectx
    ln -sf /opt/kubectx/kubens /usr/local/bin/kubens
else
    echo "kubectx already installed, skipping..."
fi

# 5. stern 설치 (다중 파드 로그 실시간 스트리밍 도구)
echo "# 5. Installing stern..."
if ! command -v stern &> /dev/null; then
    STERN_JSON=$(curl -sL "https://api.github.com/repos/stern/stern/releases/latest")
    STERN_VERSION=$(echo "$STERN_JSON" | grep -Po '"tag_name": "v\K[^"]*' || true)
    if [ -z "$STERN_VERSION" ]; then
        echo "Error: Could not determine stern version from GitHub API."
        echo "Response: $STERN_JSON"
        exit 1
    fi
    echo "stern version: $STERN_VERSION"
    curl -Lo stern.tar.gz "https://github.com/stern/stern/releases/download/v${STERN_VERSION}/stern_${STERN_VERSION}_linux_amd64.tar.gz"
    tar -xzf stern.tar.gz stern
    mv stern /usr/local/bin/stern
    rm stern.tar.gz
else
    echo "stern already installed, skipping..."
fi

# 6. Cilium CLI 설치 (Cilium CNI 관리 도구)
echo "# 6. Installing cilium cli..."
if ! command -v cilium &> /dev/null; then
    CILIUM_CLI_VERSION=$(curl -sL https://raw.githubusercontent.com/cilium/cilium-cli/main/stable.txt)
    curl -L --fail --remote-name-all "https://github.com/cilium/cilium-cli/releases/download/${CILIUM_CLI_VERSION}/cilium-linux-amd64.tar.gz"
    tar xzf cilium-linux-amd64.tar.gz
    mv cilium /usr/local/bin
    rm cilium-linux-amd64.tar.gz
else
    echo "cilium already installed, skipping..."
fi

# 7. calicoctl 설치 (Calico CNI 관리 도구)
echo "# 7. Installing calicoctl..."
if ! command -v calicoctl &> /dev/null; then
    CALICO_JSON=$(curl -sL "https://api.github.com/repos/projectcalico/calico/releases/latest")
    CALICO_VERSION=$(echo "$CALICO_JSON" | grep -Po '"tag_name": "\K[^"]*' || true)
    if [ -z "$CALICO_VERSION" ]; then
        echo "Error: Could not determine calico version from GitHub API."
        echo "Response: $CALICO_JSON"
        exit 1
    fi
    echo "calico version: $CALICO_VERSION"
    curl -L "https://github.com/projectcalico/calico/releases/download/${CALICO_VERSION}/calicoctl-linux-amd64" -o calicoctl
    chmod +x calicoctl
    mv calicoctl /usr/local/bin/
else
    echo "calicoctl already installed, skipping..."
fi

# 8. Headlamp 설치 (Kubernetes 웹 대시보드 UI)
echo "# 8. Installing headlamp..."
if ! command -v headlamp &> /dev/null && [ ! -f /usr/bin/headlamp ]; then
    # Electron 앱 실행을 위한 GUI 의존성 라이브러리 설치
    apt-get update && apt-get install -y --no-install-recommends \
        libfuse2 libgbm1 libasound2t64 libnss3 libxshmfence1 libatk1.0-0 \
        libatk-bridge2.0-0 libcups2 libdrm2 libgtk-3-0 libsecret-1-0

    set -x
    curl -Lfo headlamp.deb "https://github.com/kubernetes-sigs/headlamp/releases/download/v0.41.0/headlamp_0.41.0-1_amd64.deb"
    if ! apt-get install -y --no-install-recommends ./headlamp.deb; then
        echo "Warning: apt-get install ./headlamp.deb failed, trying with --fix-broken"
        apt-get install -y --fix-broken
        apt-get install -y --no-install-recommends ./headlamp.deb
    fi
    rm headlamp.deb
    set +x
else
    echo "headlamp already installed, skipping..."
fi

# Headlamp 샌드박스 패치 (컨테이너 환경에서 실행 가능하도록 --no-sandbox 옵션 강제 적용)
if [ -f /usr/bin/headlamp ]; then
    echo "Patching Headlamp for Electron sandbox..."
    echo -e '#!/usr/bin/env bash\n/usr/bin/headlamp --no-sandbox "$@"' > /usr/local/bin/headlamp-wrapped
    chmod +x /usr/local/bin/headlamp-wrapped
    # 데스크탑 엔트리 파일 업데이트
    if [ -f /usr/share/applications/headlamp.desktop ]; then
        sed -i 's/Exec=\/usr\/bin\/headlamp %U/Exec=\/usr\/local\/bin\/headlamp-wrapped %U/g' /usr/share/applications/headlamp.desktop
    fi
else
    echo "Warning: /usr/bin/headlamp not found, skip patching"
fi

# 9. istioctl 설치 (Istio 서비스 메시 관리 도구)
echo "# 9. Installing istioctl..."
if ! command -v istioctl &> /dev/null; then
    ISTIO_JSON=$(curl -sL https://api.github.com/repos/istio/istio/releases/latest)
    ISTIO_VERSION=$(echo "$ISTIO_JSON" | grep -Po '"tag_name": "\K[^"]*' || true)

    if [ -z "$ISTIO_VERSION" ]; then
        echo "Error: Could not determine Istio version from GitHub API."
        echo "Response: $ISTIO_JSON"
        exit 1
    fi
    echo "Istio version: $ISTIO_VERSION"

    curl -L https://istio.io/downloadIstio | ISTIO_VERSION=$ISTIO_VERSION sh -
    if [ -d istio-$ISTIO_VERSION ]; then
        mv istio-$ISTIO_VERSION/bin/istioctl /usr/local/bin/
        rm -rf istio-$ISTIO_VERSION
    else
        # 디렉토리명이 다른 경우 처리
        ISTIO_DIR=$(ls -d istio-* | head -n 1)
        if [ -n "$ISTIO_DIR" ]; then
            mv $ISTIO_DIR/bin/istioctl /usr/local/bin/
            rm -rf $ISTIO_DIR
        fi
    fi
else
    echo "istioctl already installed, skipping..."
fi

# 정리 (패키지 리스트 및 불필요한 파일 삭제)
apt-get autoremove -y --no-install-recommends 
apt-get clean && rm -rf /var/lib/apt/lists/*

echo "Kubernetes tools installation completed."
