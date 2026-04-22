ARG K8S_VERSION=v1.35.1
FROM kindest/node:${K8S_VERSION}

# 1. SSH 서버 설치 및 설정 (mkdir -p 옵션 추가)
RUN apt-get update && apt-get install -y openssh-server \
    && mkdir -p /var/run/sshd \
    && echo 'root:root' | chpasswd \
    && sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config \
    && sed -i 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' /etc/pam.d/sshd

# 2. 기존 containerd 설정 유지 
RUN sed -i 's/snapshotter = "overlayfs"/snapshotter = "native"/g' /etc/containerd/config.toml \
    && sed -i 's/SystemdCgroup = false/SystemdCgroup = true/g' /etc/containerd/config.toml

# SSH 포트 노출
EXPOSE 22

# SSH 서비스 실행 (기존 entrypoint가 있다면 주의가 필요합니다)
CMD ["/usr/sbin/sshd", "-D"]
