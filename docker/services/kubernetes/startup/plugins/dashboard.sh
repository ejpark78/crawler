#!/usr/bin/env bash
#
# Kubernetes Dashboard 설치 스크립트
# 웹 브라우저를 통해 클러스터 상태를 확인하고 관리할 수 있습니다.
#

echo "Installing Kubernetes Dashboard using Helm..."
helm repo add kubernetes-dashboard https://kubernetes-sigs.github.io/dashboard/
helm repo update kubernetes-dashboard

# 최신 버전(v7+)은 Kong을 의존성으로 사용하므로 단일 커맨드로 설치
helm upgrade --install kubernetes-dashboard kubernetes-dashboard/kubernetes-dashboard \
  --namespace kubernetes-dashboard \
  --create-namespace

echo "Kubernetes Dashboard installation completed."
echo "접속 방법: 'kubectl proxy' 실행 후 아래 주소로 접속"
echo "http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard-kong-proxy:443/proxy/"
