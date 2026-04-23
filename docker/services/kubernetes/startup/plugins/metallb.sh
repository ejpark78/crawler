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

# 기본 IP 풀 설정 (Docker 네트워크 대역에 맞게 조정 필요)
# 현재 k8s_default 네트워크가 172.20.0.0/16을 사용하므로 해당 대역 끝부분을 할당
cat <<EOF | kubectl apply -f -
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: default-pool
  namespace: metallb-system
spec:
  addresses:
  - 172.20.255.200-172.20.255.250
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
