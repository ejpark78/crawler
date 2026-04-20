기술적인 도전 정신이 멋지시네요! KinD(Kubernetes in Docker)를 사용하면서도 그 내부 동작 원리(Hard Way)를 이해하기 위해 **Docker Compose로 노드들을 직접 정의하고, 그 안에서 `kubeadm`으로 클러스터를 구성**하는 방법을 찾으시는군요.

이 방식은 KinD가 내부적으로 사용하는 `kindest/node` 이미지를 활용하여, Docker Compose로 인프라(노드)를 띄운 뒤 수동으로 `kubeadm` 명령어를 날리는 방식입니다.

### docker network subnet

```shell
docker network ls -q | xargs docker network inspect --format '{{.Name}}: {{range .IPAM.Config}}{{.Subnet}}{{end}}'


docker network create --driver bridge \
  --subnet=172.20.0.0/16 \
  --ip-range=172.20.0.0/24 \
  --gateway=172.20.0.1 \
  k8s-net

```

### 1. `docker-compose.yml` 구성 (인프라 준비)
먼저 마스터 노드(Control-plane) 1개와 워커 노드 2개를 정의합니다. 각 컨테이너는 K8s 실행을 위해 `privileged` 권한이 필요합니다.

```yaml
services:
  control-plane:
    image: kindest/node:v1.35.1
    privileged: true
    networks:
      k8s-net:
        ipv4_address: 172.20.0.10
    volumes:
      - /lib/modules:/lib/modules:ro

  worker1:
    image: kindest/node:v1.35.1
    privileged: true
    networks:
      k8s-net:
        ipv4_address: 172.20.0.11
    volumes:
      - /lib/modules:/lib/modules:ro

  worker2:
    image: kindest/node:v1.35.1
    privileged: true
    networks:
      k8s-net:
        ipv4_address: 172.20.0.12
    volumes:
      - /lib/modules:/lib/modules:ro

networks:
  k8s-net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

```shell

# 1. 일단 이미지가 컨테이너 안에 있는지 확인 (결과가 나오면 이미 있는 것임)
crictl images 

cat <<EOF > kubeadm-config.yaml
kind: ClusterConfiguration
apiVersion: kubeadm.k8s.io/v1beta4
kubernetesVersion: v1.35.1
networking:
  podSubnet: "10.244.0.0/16"
---
kind: KubeletConfiguration
apiVersion: kubelet.config.k8s.io/v1beta1
cgroupDriver: systemd
failSwapOn: false
EOF

# 2. 이미지가 있다면, 이미지 풀링 단계를 건너뛰고 실행
kubeadm init --config kubeadm-config.yaml \
  --skip-phases=addon/kube-proxy \
  --node-name=control-plane \
  --ignore-preflight-errors=ImagePull



```


---

### 2. "Hard Way" 설치 단계 (수동 설정)

Compose로 컨테이너를 띄운 후(`docker-compose up -d`), 아래 순서대로 직접 명령어를 입력하여 클러스터를 완성합니다.

#### 단계 1: 마스터 노드 초기화 (`kubeadm init`)
마스터 컨테이너에 접속하여 `kubeadm`을 실행합니다. (KinD 이미지는 이미 필요한 바이너리가 다 들어있습니다.)
```bash
docker exec -it k8s-master bash

# 마스터 노드 내부에서 실행
kubeadm init --pod-network-cidr=192.168.0.0/16 --apiserver-advertise-address=172.20.0.10
```
명령어 결과 마지막에 나오는 `kubeadm join ...` 토큰을 복사해 두세요.

#### 단계 2: 마스터 노드 설정 (kubectl 사용 준비)
```bash
mkdir -p $HOME/.kube
cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
chown $(id -u):$(id -g) $HOME/.kube/config
```

#### 단계 3: 워커 노드 조인 (`kubeadm join`)
각 워커 컨테이너에서 마스터로부터 복사한 join 명령어를 실행합니다.
```bash
docker exec -it k8s-worker1 kubeadm join 172.20.0.10:6443 --token <토큰> --discovery-token-ca-cert-hash sha256:<해시값>
docker exec -it k8s-worker2 kubeadm join 172.20.0.10:6443 --token <토큰> --discovery-token-ca-cert-hash sha256:<해시값>
```

#### 단계 4: CNI 설치 (사용자 실습 포인트)
마스터 노드에서 원하는 CNI를 설치합니다. (예: Calico)
```bash
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.25.0/manifests/calico.yaml
```

---

### 3. 이 방식의 장점 (CNI 실습 관점)

1.  **IP 고정:** `docker-compose`의 고정 IP 기능을 사용하여 각 노드의 IP 주소를 명확히 알 수 있어, CNI가 노드 간 통신을 어떻게 잡는지 분석하기 좋습니다.
2.  **멀티 노드 환경:** KinD CLI를 쓰지 않고 직접 `kubeadm join`을 해봄으로써 클러스터 형성 과정을 완벽히 이해할 수 있습니다.
3.  **네트워크 격리:** `k8s-net`이라는 독립된 브릿지 네트워크에서 패킷이 어떻게 흐르는지 `tcpdump` 등으로 추적하기 용이합니다.

이제 `docker-compose up -d`를 실행한 후, **마스터 노드에서 직접 `kubeadm init`을 때리는 것**부터 시작해 보세요! 어떤 CNI부터 설치해 보실 계획인가요?




---

### 1. 세부 의미 분석
* **`/lib/modules` (앞부분):** **호스트 머신**(당신의 실제 컴퓨터나 VM)의 경로입니다. 여기에는 운영체제 커널이 사용하는 드라이버와 네트워크 관련 모듈들이 들어 있습니다.
* **`:/lib/modules` (뒷부분):** **컨테이너 내부**의 경로입니다. 컨테이너 안에서도 똑같은 경로로 접근하겠다는 뜻입니다.
* **`:ro` (Read-Only):** **"읽기 전용"** 권한입니다. 컨테이너가 호스트의 커널 모듈 파일을 실수로 삭제하거나 수정하지 못하도록 보호하는 안전장치입니다.

---

### 2. 왜 이게 KinD나 Kubeadm 실습에 필요한가요?

컨테이너는 기본적으로 호스트의 **커널(Kernel)**을 공유해서 사용합니다. 하지만 Kubernetes 클러스터를 운영하려면 단순한 앱 실행을 넘어, 커널의 복잡한 기능을 직접 건드려야 합니다.

특히 **CNI(네트워크 플러그인) 실습**을 할 때 반드시 필요한 이유들입니다:

* **IPVS / IPTables:** 로드밸런싱이나 서비스 라우팅을 구현할 때 커널의 이 기능들을 사용합니다.
* **Overlay Networks (VXLAN, Geneve):** Calico나 Cilium 같은 CNI가 노드 간에 가상 터널을 만들 때 커널 모듈을 로드해야 합니다.
* **파일 시스템 (XFS, Quota):** 컨테이너 저장소 용량을 제한하거나 관리할 때 필요합니다.

---

### 3. 한 줄 요약
> **"컨테이너(노드)가 네트워크를 구성하거나 시스템 설정을 할 때, 호스트의 커널 기능을 빌려 쓸 수 있도록 통로를 열어주는 것"**

만약 이 설정이 없으면, `kubeadm init`을 할 때나 CNI를 설치할 때 **"Can't load kernel module"** 또는 **"Iptables/IPVS not found"** 같은 에러를 뿜으며 실패할 확률이 매우 높습니다. 
