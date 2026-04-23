#!/usr/bin/env bash
#
# MetalLB LoadBalancer 설치 및 설정 스크립트
# 로컬 클러스터에서 외부 IP(LoadBalancer)를 사용할 수 있게 합니다.
#

echo "Installing MetalLB using Helm..."
helm repo add metallb https://metallb.github.io/metallb
helm repo update metallb

helm upgrade --install metallb metallb/metallb \
  --namespace metallb-system \
  --create-namespace

echo "Waiting for MetalLB controllers to be ready..."
kubectl wait \
  --namespace metallb-system \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/name=metallb \
  --timeout=180s

# 현재 노드의 IP를 확인하여 MetalLB용 IP 대역을 동적으로 설정합니다.
# eth0 인터페이스의 IP 대역(첫 3옥텟)을 사용하여 .200-.250 범위를 할당합니다.
NODE_IP=$(ip -4 addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
IP_BASE=$(echo $NODE_IP | cut -d. -f1-3)
METALLB_RANGE="${IP_BASE}.200-${IP_BASE}.250"

echo "Detected Node IP: $NODE_IP"
echo "Configuring MetalLB IP Pool with range: $METALLB_RANGE"

cat <<EOF | kubectl apply -f -
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: default-pool
  namespace: metallb-system
spec:
  addresses:
  - ${METALLB_RANGE}
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: default-advertisement
  namespace: metallb-system
spec:
  ipAddressPools:
  - default-pool
EOF

echo "MetalLB installation and configuration completed."
