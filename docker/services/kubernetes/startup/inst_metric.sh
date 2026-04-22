#!/usr/bin/env bash
#
# Metrics Server 설치 스크립트
# 'kubectl top nodes/pods' 명령을 사용할 수 있게 합니다.
#

KUBECONFIG=${KUBECONFIG:-/etc/kubernetes/admin.conf}

echo "Installing Metrics Server..."
# 공식 매니페스트 다운로드 및 수정 (kubelet-insecure-tls 옵션 추가)
# 로컬 테스트 환경에서는 인증서 검증을 건너뛰어야 정상 작동합니다.
curl -L https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml | \
sed 's/--metric-resolution=15s/--metric-resolution=15s\n        - --kubelet-insecure-tls/' | \
kubectl apply -f -


echo "Waiting for Metrics Server to be ready..."
kubectl wait \
    --namespace kube-system \
    --for=condition=Available deployment/metrics-server \
    --timeout=120s

echo "Metrics Server installation completed."
