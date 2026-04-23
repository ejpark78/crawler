# Kubernetes Control Plane 및 Worker 노드용 커스텀 이미지
#
# 이 Dockerfile은 kindest/node 이미지를 기반으로 하며,
# 클러스터 운영 및 노드 간 통신에 필요한 추가 도구들을 설치합니다.

ARG K8S_VERSION=v1.35.1
FROM kindest/node:${K8S_VERSION}

# 1. containerd 설정 최적화
# snapshotter를 native로 변경하고 SystemdCgroup을 활성화하여 성능과 안정성을 높입니다.
RUN sed -i 's/snapshotter = "overlayfs"/snapshotter = "native"/g' /etc/containerd/config.toml \
    && sed -i 's/SystemdCgroup = false/SystemdCgroup = true/g' /etc/containerd/config.toml

# 2. SSH 서버 및 필수 유틸리티 설치
# 노드 간 자동 접속 및 디버깅을 위해 openssh-server와 기본 도구들을 설치합니다.
RUN apt-get update && apt-get install -y openssh-server openssh-client git curl \
    && mkdir -p /var/run/sshd \
    && sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config \
    && sed -i 's/^#\?PasswordAuthentication .*/PasswordAuthentication no/' /etc/ssh/sshd_config \
    && sed -i 's/^#\?StrictHostKeyChecking .*/StrictHostKeyChecking no/' /etc/ssh/ssh_config \
    && echo "    StrictHostKeyChecking no" >> /etc/ssh/ssh_config \
    && echo "    UserKnownHostsFile /dev/null" >> /etc/ssh/ssh_config \
    && apt-get autoremove -y --no-install-recommends \
    && apt-get clean && rm -rf /var/lib/apt/lists/*    

# 3. 표준 CNI 플러그인 설치
# bridge, portmap, loopback 등 기본 네트워크 구성을 위한 CNI 바이너리를 설치합니다.
RUN CNI_PLUGINS_VERSION="v1.6.0" \
    && ARCH=$(uname -m | sed 's/x86_64/amd64/' | sed 's/aarch64/arm64/') \
    && mkdir -p /opt/cni/bin \
    && curl -L "https://github.com/containernetworking/plugins/releases/download/${CNI_PLUGINS_VERSION}/cni-plugins-linux-${ARCH}-${CNI_PLUGINS_VERSION}.tgz" | tar -xz -C /opt/cni/bin

# 4. K8s 운영 도구 설치
# kubectl, kubeadm, kubelet 등 핵심 도구들을 구성합니다.
COPY modules /modules
RUN chmod +x /modules/* && /modules/k8s_tools.sh

WORKDIR /root

# 5. 시작 및 초기화 스크립트 복사
COPY startup /startup
RUN chmod -R +x /startup

# SSH 서비스 포트
EXPOSE 22

# SSH 서버를 엔트리포인트로 실행
CMD ["/startup/sshd.sh"]
