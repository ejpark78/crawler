#!/usr/bin/env bash
#
# Portainer 설치 스크립트
# Docker 및 Kubernetes 리소스를 쉽게 관리할 수 있는 GUI를 제공합니다.
#

echo "Installing Portainer using Helm..."
helm repo add portainer https://portainer.github.io/k8s/
helm repo update portainer

# MetalLB가 설치되어 있으므로 LoadBalancer 타입을 사용하여 외부 IP 할당
helm upgrade --install portainer portainer/portainer \
  --namespace portainer \
  --create-namespace \
  --set service.type=LoadBalancer

echo "Waiting for Portainer pods to be ready..."
kubectl rollout status deployment/portainer -n portainer --timeout=120s

echo "Portainer installation completed."
echo "접속 방법: 'kubectl get svc -n portainer' 명령어로 할당된 EXTERNAL-IP 확인 후 접속 (기본 포트: 9443)"
