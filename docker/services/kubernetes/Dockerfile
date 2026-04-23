ARG K8S_VERSION=v1.35.1
FROM kindest/node:${K8S_VERSION}

# 1. containerd 설정
RUN sed -i 's/snapshotter = "overlayfs"/snapshotter = "native"/g' /etc/containerd/config.toml \
    && sed -i 's/SystemdCgroup = false/SystemdCgroup = true/g' /etc/containerd/config.toml

# 2. SSH 서버 설치 및 설정 (mkdir -p 옵션 추가)
RUN apt-get update && apt-get install -y openssh-server openssh-client git curl \
    && mkdir -p /var/run/sshd \
    && sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config \
    && sed -i 's/^#\?PasswordAuthentication .*/PasswordAuthentication no/' /etc/ssh/sshd_config \
    && sed -i 's/^#\?StrictHostKeyChecking .*/StrictHostKeyChecking no/' /etc/ssh/ssh_config \
    && echo "    StrictHostKeyChecking no" >> /etc/ssh/ssh_config \
    && echo "    UserKnownHostsFile /dev/null" >> /etc/ssh/ssh_config \
    && apt-get autoremove -y --no-install-recommends \
    && apt-get clean && rm -rf /var/lib/apt/lists/*    

# 3. 표준 CNI 플러그인(bridge, portmap 등) 설치
RUN CNI_PLUGINS_VERSION="v1.6.0" \
    && ARCH=$(uname -m | sed 's/x86_64/amd64/' | sed 's/aarch64/arm64/') \
    && mkdir -p /opt/cni/bin \
    && curl -L "https://github.com/containernetworking/plugins/releases/download/${CNI_PLUGINS_VERSION}/cni-plugins-linux-${ARCH}-${CNI_PLUGINS_VERSION}.tgz" | tar -xz -C /opt/cni/bin

# 4. Helm 설치
RUN curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 \
    && chmod 700 get_helm.sh \
    && ./get_helm.sh \
    && rm get_helm.sh

# 6. K8s Tools 설치 (Kasm과 공유되는 모듈 사용)
COPY modules /modules
RUN chmod +x /modules/* && /modules/k8s_tools.sh

WORKDIR /root

COPY startup /startup
RUN chmod +x /startup/*

# SSH 포트 노출
EXPOSE 22

CMD ["/startup/sshd.sh"]
