ARG K8S_VERSION=v1.35.1
FROM kindest/node:${K8S_VERSION}

# 1. containerd 설정
RUN sed -i 's/snapshotter = "overlayfs"/snapshotter = "native"/g' /etc/containerd/config.toml \
    && sed -i 's/SystemdCgroup = false/SystemdCgroup = true/g' /etc/containerd/config.toml

# 2. SSH 서버 설치 및 설정 (mkdir -p 옵션 추가)
RUN apt-get update && apt-get install -y openssh-server openssh-client \
    && mkdir -p /var/run/sshd \
    && sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config \
    && sed -i 's/^#\?PasswordAuthentication .*/PasswordAuthentication no/' /etc/ssh/sshd_config \
    && sed -i 's/^#\?StrictHostKeyChecking .*/StrictHostKeyChecking no/' /etc/ssh/ssh_config \
    && echo "    StrictHostKeyChecking no" >> /etc/ssh/ssh_config \
    && echo "    UserKnownHostsFile /dev/null" >> /etc/ssh/ssh_config \
    && apt-get autoremove -y --no-install-recommends \
    && apt-get clean && rm -rf /var/lib/apt/lists/*    

# 3. SSH 키 공유 설정: 호스트의 키 파일을 컨테이너 내부로 복사
WORKDIR /root

COPY startup /startup
RUN chmod +x /startup/*

# SSH 포트 노출
EXPOSE 22

CMD ["/startup/sshd.sh"]
