# Kubernetes Service 상세 분석

이 디렉토리는 `kindest/node` 이미지를 기반으로 커스텀 Kubernetes 클러스터 노드를 구축하기 위한 설정과 스크립트를 포함하고 있습니다. 특히, 노드 간 SSH 통신 및 `kubeadm`을 이용한 클러스터 구성을 자동화하는 데 초점을 맞추고 있습니다.

## 🏗️ 시스템 아키텍쳐

```text
       +-------------------------------------------------------+
       |                    호스트 머신 (Host)                   |
       +-------------------------------------------------------+
                    | (docker exec / SSH)
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

---

## 🛠️ 주요 구성 요소 및 도구

### 1. 사전 설치된 도구 (Dockerfile)
*   **Base Image**: `kindest/node:v1.35.1` (K8s v1.35.1 대응)
*   **Helm**: Kubernetes 패키지 매니저 (`helm` 명령어 즉시 사용 가능)
*   **CNI Plugins**: 표준 CNI 바이너리(bridge, portmap, loopback 등) 포함
*   **K8s Tools**: `kubectl`, `kubeadm`, `kubelet` 외에도 운영에 필요한 유틸리티 포함
*   **SSH 서버**: `openssh-server`를 통한 노드 간 키 기반 자동 접속 설정

### 2. 네트워크 및 CNI 지원
다양한 CNI(Container Network Interface)를 선택하여 클러스터를 구성할 수 있습니다.
*   **지원 목록**: `flannel` (기본값), `calico`, `cilium`
*   **설정 방식**: `make up CNI_NAME=calico`와 같이 실행 시 변수를 전달하면 `init.sh`에서 해당 CNI에 맞는 Pod Subnet을 자동으로 설정합니다.

---

## 🔄 클러스터 구축 프로세스

1.  **`kubeadm init` (Control Plane)**:
    *   `startup/init.sh`가 실행되면서 `kubeadm-config.yaml`을 동적으로 생성하고 클러스터를 초기화합니다.
    *   초기화 후 워커 노드용 `join.sh`를 생성하여 공유 볼륨(`kube`)에 저장합니다.

2.  **`kubeadm join` (Worker)**:
    *   워커 노드는 `control-plane`의 헬스체크가 완료된 후 실행됩니다.
    *   공유된 `join.sh`를 실행하여 자동으로 클러스터에 참여합니다.

---

## ⌨️ Makefile 명령어 가이드

편리한 클러스터 관리를 위해 `Makefile`이 제공됩니다.

| 명령어 | 설명 | 비고 |
| :--- | :--- | :--- |
| `make build` | 컨트롤 플레인 이미지 빌드 | |
| `make up` | 클러스터 실행 | `CNI_NAME=calico` 등 옵션 가능 |
| `make init` | 마스터 노드 초기화 실행 | 컨테이너 내부 `init.sh` 호출 |
| `make join` | 모든 워커 노드 조인 실행 | |
| `make status` | 노드 및 파드 상태 확인 | `kubectl get nodes/pods` 결과 출력 |
| `make scale` | 워커 노드 개수 조정 | `WORKERS=3` 옵션 사용 |
| `make control-plane` | 마스터 노드 쉘 접속 | `docker exec` 방식 |
| `make down` | 클러스터 완전 정지 및 삭제 | |

---

## 🔑 접속 및 보안

*   **노드 접속**: 기본적으로 `docker exec` 또는 `make control-plane`을 통해 접속하는 것을 권장합니다.
*   **노드 간 SSH**: `ssh_keys` 볼륨을 통해 모든 노드가 동일한 SSH 키를 공유하며, `StrictHostKeyChecking no` 설정으로 인해 비밀번호 없이 서로 접속이 가능합니다.
*   **외부 접속 (Kubectl)**: 호스트의 `volumes/kube/config` 파일을 호스트의 `~/.kube/config`로 복사하여 로컬에서 클러스터를 제어할 수 있습니다.

---

## 📝 참고 사항
*   이 환경은 개발/테스트용이며, 컨테이너가 `privileged: true` 모드로 실행됩니다.
*   Swap은 `init.sh` 실행 시 자동으로 비활성화(`swapoff -a`)됩니다.
