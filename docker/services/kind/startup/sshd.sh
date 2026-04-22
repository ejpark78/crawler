#!/usr/bin/env bash
set -e  # 에러 발생 시 즉시 중단

echo "Starting SSH server setup..."

# 1. 디렉토리 생성 및 권한 강제 부여
mkdir -p /root/.ssh
chmod 700 /root/.ssh

# 2. 파일 생성 로직 확인 (디버깅용 echo 추가)
if [ ! -f /root/.ssh/id_rsa.pem ]; then
    echo "No SSH key found. Generating new key pair..."
    ssh-keygen -t rsa -b 2048 -m PEM -f /root/.ssh/id_rsa.pem -N ""
    cp /root/.ssh/id_rsa.pem.pub /root/.ssh/authorized_keys
    echo "Key generation completed."
else
    echo "Existing SSH key found in volume. Skipping generation."
fi

# 3. 마운트된 볼륨 내 파일 권한 재설정 (중요)
# 외부에서 마운트된 파일은 권한이 꼬일 수 있으므로 다시 한번 설정합니다.
chmod 600 /root/.ssh/id_rsa.pem
chmod 600 /root/.ssh/authorized_keys
chmod 644 /root/.ssh/id_rsa.pem.pub

# 4. SSHD 실행 (경로 확인)
mkdir -p /var/run/sshd

echo "Launching sshd..."
exec /usr/sbin/sshd -D &
