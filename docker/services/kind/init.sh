#!/usr/bin/env bash

echo "# 1. 일단 이미지가 컨테이너 안에 있는지 확인"
crictl images

# echo "# 2. snapshotter를 native로 변경"
# sed -i 's/snapshotter = "overlayfs"/snapshotter = "native"/g' /etc/containerd/config.toml

# echo "# 3. SystemdCgroup 설정 다시 확인 (이전 단계에서 했더라도 확실히 함)"
# sed -i 's/SystemdCgroup = false/SystemdCgroup = true/g' /etc/containerd/config.toml

# echo "# 4. containerd 재시작"
# systemctl restart containerd

echo "# 5. kubeadm 설정 파일 생성"
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

echo "# 6. swap 비활성화"
swapoff -a

echo "# 7. kubeadm init"
kubeadm init \
  --config kubeadm-config.yaml \
  --skip-phases=addon/kube-proxy \
  --node-name=control-plane \
  --ignore-preflight-errors=ImagePull

