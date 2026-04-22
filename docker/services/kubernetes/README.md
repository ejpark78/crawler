# Kubernetes Service 상세 분석

이 디렉토리는 `kindest/node` 이미지를 기반으로 커스텀 Kubernetes 클러스터 노드를 구축하기 위한 설정과 스크립트를 포함하고 있습니다. 특히, 노드 간 SSH 통신 및 `kubeadm`을 이용한 클러스터 구성을 자동화하는 데 초점을 맞추고 있습니다.

## 🏗️ 시스템 아키텍쳐

```text
       +-------------------------------------------------------+
       |                    호스트 머신 (Host)                   |
       +-------------------------------------------------------+
                   | (포트 포워딩 2222:22)
                   v
+-----------------------------------+       +-----------------------------------+
|      control-plane 컨테이너        |       |         worker 컨테이너           |
|  (kindest/node + SSH + 커스텀)     |       |   (kindest/node + SSH + 커스텀)   |
+-----------------------------------+       +-----------------------------------+
| [주요 프로세스]                    |       | [주요 프로세스]                    |
|  - kubelet                        |       |  - kubelet                        |
|  - containerd                     |       |  - containerd                     |
|  - sshd (22번 포트) <-------------+-------+--> sshd (22번 포트)               |
|                                   |  SSH  |                                   |
| [주요 파일 및 볼륨]                 |       | [주요 파일 및 볼륨]                 |
|  - /init.sh (초기화 스크립트)       |       |                                   |
|  - /root/.kube/config <-----------+-------+--> (공유 볼륨: kube)              |
|  - /root/.kube/join.sh <----------+-------+--> (공유 볼륨: kube)              |
|  - /root/.ssh/id_rsa <------------+-------+--> (공유 볼륨: ssh_keys)          |
+-----------------------------------+       +-----------------------------------+
                  |                                     ^
                  |           kubeadm init              |
                  +-------------------------------------+
                             kubeadm join
```

## 🔄 Init -> Join 프로세스 관계

클러스터 구축은 `control-plane` 노드에서 시작하여 `worker` 노드가 참여하는 방식으로 이루어집니다.

1.  **`kubeadm init` (Control Plane)**:
    *   `startup/init.sh` 스크립트가 실행되면서 `kubeadm init` 명령을 통해 마스터 노드를 초기화합니다.
    *   초기화 과정에서 생성되는 로그에서 `kubeadm join` 명령어를 추출합니다.
    *   추출된 명령어는 `/root/.kube/join.sh` 파일로 저장됩니다.

2.  **`kubeadm join` (Worker)**:
    *   `control-plane`과 `worker`는 `kube`라는 이름의 Docker 볼륨을 공유합니다.
    *   `worker` 노드는 공유된 볼륨을 통해 `/root/.kube/join.sh` 파일에 접근할 수 있습니다.
    *   `worker` 노드에서 이 스크립트를 실행함으로써 클러스터에 안전하게 참여하게 됩니다.

## 🛠️ 주요 구성 요소

### 1. Dockerfile
*   **Base Image**: `kindest/node:v1.35.1` (버전은 ARG로 변경 가능)
*   **Containerd 설정**: 스냅샷터를 `native`로, Cgroup 드라이버를 `systemd`로 설정하여 성능과 호환성을 높였습니다.
*   **SSH 서버**: `openssh-server`를 설치하고 root 로그인을 허용(키 기반)하도록 설정했습니다.
*   **보안**: 패스워드 인증을 비활성화하고 SSH 키 기반 인증만 허용합니다.

### 2. startup/sshd.sh
*   컨테이너 시작 시 실행되는 엔트리포인트 스크립트입니다.
*   `/root/.ssh` 디렉토리가 없거나 키 쌍이 없는 경우 자동으로 생성합니다.
*   마운트된 볼륨 내의 키 파일 권한을 SSH 보안 요구사항(600, 700)에 맞게 강제 재설정합니다.
*   `sshd` 데몬을 백그라운드에서 실행합니다.

### 3. startup/init.sh
*   Kubernetes 클러스터 초기화를 담당합니다.
*   `kubeadm-config.yaml`을 동적으로 생성하여 파드 서브넷 및 `cgroupDriver` 등을 설정합니다.
*   `swapoff -a`를 통해 K8s 요구사항을 충족합니다.
*   `join.sh`를 생성하고 `admin.conf`를 `~/.kube/config`로 복사하여 `kubectl` 사용 환경을 구축합니다.

## 🔑 SSH 접속 및 보안

*   **호스트 -> 컨테이너**: 호스트에 생성된 `.pem` 키(또는 `id_rsa`)를 사용하여 `ssh -i <key> root@localhost -p 2222`로 접속 가능합니다.
*   **노드 간 접속**: 모든 노드가 `ssh_keys` 볼륨을 공유하므로, `control-plane`에서 `worker`로(또는 그 반대로) 비밀번호 없이 SSH 접속이 가능합니다. 이는 `StrictHostKeyChecking no` 설정으로 자동화되어 있습니다.

## 📝 참고 사항
*   이 설정은 개발 및 테스트 환경을 위한 것이며, 실제 운영 환경에서는 보다 엄격한 보안 설정이 필요할 수 있습니다.
*   `kindest/node` 이미지의 특성상 `privileged: true` 옵션이 필요합니다.
