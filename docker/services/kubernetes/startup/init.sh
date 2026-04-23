#!/usr/bin/env bash
#
# Kubernetes Control Plane 초기화 및 Join 스크립트 생성 모듈
# 이 스크립트는 kubeadm을 사용하여 클러스터를 초기화하고, 
# 워커 노드가 클러스터에 참여할 수 있도록 join 명령어를 추출하여 저장합니다.
#

CNI_NAME=${CNI_NAME:-flannel}
FLANNEL_SUBNET=${FLANNEL_SUBNET:-"10.244.0.0/16"}
CALICO_SUBNET=${CALICO_SUBNET:-"192.168.0.0/16"}
CILIUM_SUBNET=${CILIUM_SUBNET:-"10.0.0.0/16"}

echo "# 0. CNI 설정 확인 (Name: $CNI_NAME)"

case $CNI_NAME in
  flannel)
    POD_SUBNET=${FLANNEL_SUBNET}
    ;;
  calico)
    POD_SUBNET=${CALICO_SUBNET:-"192.168.0.0/16"}
    ;;
  cilium)
    POD_SUBNET=${CILIUM_SUBNET:-"10.0.0.0/16"}
    ;;
  *)
    POD_SUBNET=${FLANNEL_SUBNET:-"10.244.0.0/16"}
    ;;
esac

echo "# 1. 일단 이미지가 컨테이너 안에 있는지 확인"
crictl images

echo "# 2. kubeadm 설정 파일 생성 (Subnet: $POD_SUBNET)"
cat <<EOF > kubeadm-config.yaml
kind: ClusterConfiguration
apiVersion: kubeadm.k8s.io/v1beta4
kubernetesVersion: v1.35.1
networking:
  podSubnet: "$POD_SUBNET"

---
kind: KubeletConfiguration
apiVersion: kubelet.config.k8s.io/v1beta1
cgroupDriver: systemd
failSwapOn: false
---
kind: KubeProxyConfiguration
apiVersion: kubeproxy.config.k8s.io/v1alpha1
conntrack:
  maxPerCore: 0
EOF

echo "# 3. swap 비활성화"
swapoff -a

SKIP_PHASES=""
if [ "$CNI_NAME" == "cilium" ]; then
    SKIP_PHASES="--skip-phases=addon/kube-proxy"
fi

echo "# 4. kubeadm init (Skip Phases: $SKIP_PHASES)"
kubeadm init \
  --config kubeadm-config.yaml \
  $SKIP_PHASES \
  --node-name=control-plane \
  --ignore-preflight-errors=ImagePull \
  | tee kubeadm-init.log

grep -A 2 "kubeadm join " kubeadm-init.log | tee /root/.kube/join.sh
chmod +x /root/.kube/join.sh

rm -rf /root/.kube/config
rm -rf /root/.kube/cache
rm -rf /root/.kube/state
rm -rf /root/.kube/tmp

cp -i /etc/kubernetes/admin.conf /root/.kube/config
chown $(id -u):$(id -g) /root/.kube/config
