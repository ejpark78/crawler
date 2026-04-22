AWS EC2에서 사용하는 `.pem` 키 방식(Key Pair)을 `Dockerfile`과 `k8s.yml` 환경에서 구현하려면, 호스트에서 키를 생성한 후 이를 컨테이너의 `authorized_keys`에 심어주는 과정이 필요합니다.

### 1. 호스트에서 .pem 키 생성
AWS EC2의 키 페어와 동일한 형식인 RSA 방식의 프라이빗 키를 생성합니다.

```bash
# 2048 비트 RSA 키 생성 (EC2 표준 형식)
ssh-keygen -t rsa -b 2048 -m PEM -f my-cluster-key.pem -N ""
```
* `my-cluster-key.pem`: 실제 접속 시 사용할 프라이빗 키입니다.
* `my-cluster-key.pem.pub`: 컨테이너 내부에 등록할 퍼블릭 키입니다.

---

### 2. Dockerfile 수정 (퍼블릭 키 등록)
[cite_start]AWS가 인스턴스 생성 시 퍼블릭 키를 `~/.ssh/authorized_keys`에 넣어주는 것과 동일한 원리로 작성합니다[cite: 1].

```dockerfile
# ... 상단 생략 ...

# 1. SSH 설치 및 설정
RUN apt-get update && apt-get install -y openssh-server openssh-client \
    && mkdir -p /root/.ssh \
    && chmod 700 /root/.ssh

# 2. 퍼블릭 키 복사 (EC2의 'Key Pair' 주입 과정과 동일)
COPY my-cluster-key.pem.pub /root/.ssh/authorized_keys
RUN chmod 600 /root/.ssh/authorized_keys

# 3. 비밀번호 로그인 비활성화 (선택 사항, EC2 스타일 보안)
RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config \
    && sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# ... 하단 생략 ...
```

---

### 3. k8s.yml 설정 (노드 간 공유)
[cite_start]`control-plane`에서 `worker`로 접속하기 위해 프라이빗 키(`.pem`)도 같이 마운트해줍니다[cite: 2].

```yaml
services:
  control-plane:
    volumes:
      - /lib/modules:/lib/modules:ro
      - ./my-cluster-key.pem:/root/.ssh/id_rsa:ro # 노드 간 접속용 프라이빗 키
      - ./my-cluster-key.pem.pub:/root/.ssh/authorized_keys:ro
    # ... 생략 ...

  worker:
    volumes:
      - /lib/modules:/lib/modules:ro
      - ./my-cluster-key.pem.pub:/root/.ssh/authorized_keys:ro
```

---

### 4. 접속 방법 (EC2와 동일)

#### 외부(호스트)에서 컨테이너 접속 시:
AWS EC2에 접속할 때와 똑같은 명령어를 사용합니다.
```bash
# 키 권한 변경 (필수)
chmod 400 my-cluster-key.pem

# 접속 (2222 포트로 포워딩 설정 시)
ssh -i my-cluster-key.pem root@localhost -p 2222
```

#### 노드 간 접속 시 (`control-plane` -> `worker`):
이미 `id_rsa` 경로로 프라이빗 키를 마운트했으므로, 옵션 없이도 접속됩니다.
```bash
ssh root@worker
```

**주의:** EC2 방식처럼 `.pem` 키를 사용하려면 `PasswordAuthentication no` 설정을 통해 비밀번호 접속을 막는 것이 보안상 좋지만, 설정 오류 시 접속이 아예 차단될 수 있으니 주의하세요.






***







`control-plane`과 `worker` 노드 간에 비밀번호 없이 SSH 접속을 하려면, 동일한 SSH 키 쌍(Key Pair)을 공유하고 서로의 `authorized_keys`에 등록해야 합니다.

`kindest/node` 이미지 기반 환경에서 이를 자동화하는 가장 효율적인 방법은 다음과 같습니다.

### 1. 호스트에서 SSH 키 생성
먼저, 공유할 키가 없다면 호스트 머신(프로젝트 루트 등)에서 키를 생성합니다.
```bash
ssh-keygen -t rsa -b 4096 -f ./id_rsa -N ""
```

---

### 2. Dockerfile 수정 (키 복사 및 권한 설정)
[cite_start]빌드 시점에 생성한 키를 이미지 내부로 복사하고, SSH 클라이언트가 이를 자동으로 사용하도록 설정합니다. [cite: 1, 2]

```dockerfile
# ... 기존 설정 생략 ...

# 3. SSH 키 공유 설정
# 호스트의 키 파일을 컨테이너 내부로 복사
COPY id_rsa /root/.ssh/id_rsa
COPY id_rsa.pub /root/.ssh/id_rsa.pub
COPY id_rsa.pub /root/.ssh/authorized_keys

# 권한 설정 (SSH는 권한에 매우 엄격합니다)
RUN chmod 700 /root/.ssh \
    && chmod 600 /root/.ssh/id_rsa \
    && chmod 644 /root/.ssh/id_rsa.pub \
    && chmod 600 /root/.ssh/authorized_keys \
    && echo "StrictHostKeyChecking no" >> /etc/ssh/ssh_config

# ... 이하 생략 ...
```

---

### 3. k8s.yml 수정 (볼륨 공유 방식)
[cite_start]이미지를 매번 빌드하지 않고 유연하게 관리하고 싶다면, `k8s.yml`의 `volumes`를 통해 호스트의 키를 직접 마운트할 수 있습니다. [cite: 2]

```yaml
services:
  control-plane:
    # ... 빌드 설정 ...
    volumes:
      - /lib/modules:/lib/modules:ro
      - ./id_rsa:/root/.ssh/id_rsa:ro
      - ./id_rsa.pub:/root/.ssh/id_rsa.pub:ro
      - ./id_rsa.pub:/root/.ssh/authorized_keys:ro
    # ... 생략 ...

  worker:
    # ... 빌드 설정 ...
    volumes:
      - /lib/modules:/lib/modules:ro
      - ./id_rsa:/root/.ssh/id_rsa:ro
      - ./id_rsa.pub:/root/.ssh/id_rsa.pub:ro
      - ./id_rsa.pub:/root/.ssh/authorized_keys:ro
    # ... 생략 ...
```

---

### 4. 핵심 포인트 요약
* [cite_start]**파일 공유**: `control-plane`과 `worker`가 동일한 `id_rsa`와 `authorized_keys`(본인의 public key 포함)를 가지게 합니다. [cite: 1, 2]
* [cite_start]**권한 세팅**: `.ssh` 디렉토리는 `700`, `id_rsa` 파일은 반드시 `600` 권한이어야 SSH 접속이 거부되지 않습니다. [cite: 1]
* **StrictHostKeyChecking**: 처음 접속 시 "Are you sure you want to continue connecting?" [cite_start]메시지가 뜨지 않도록 `/etc/ssh/ssh_config`에서 `StrictHostKeyChecking no` 설정을 추가하는 것이 자동화에 유리합니다. [cite: 2]

이렇게 설정하면 `control-plane` 컨테이너 터미널에서 `ssh worker-node-ip` 명령만으로 비밀번호 없이 즉시 접속이 가능해집니다.