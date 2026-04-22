#!/usr/bin/env bash

echo "# 1. 일단 이미지가 컨테이너 안에 있는지 확인"
crictl images

echo "# 2. kubeadm 설정 파일 생성"
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

echo "# 3. swap 비활성화"
swapoff -a

echo "# 4. kubeadm init"
kubeadm init \
  --config kubeadm-config.yaml \
  --skip-phases=addon/kube-proxy \
  --node-name=control-plane \
  --ignore-preflight-errors=ImagePull \
  | tee kubeadm-init.log

grep -A 2 "kubeadm join " kubeadm-init.log | tee /root/.kube/join.sh
chmod +x /root/.kube/join.sh

cp -i /etc/kubernetes/admin.conf /root/.kube/config
chown $(id -u):$(id -g) /root/.kube/config
