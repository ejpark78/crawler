#!/usr/bin/env bash
#
# Metrics Server 설치 스크립트
# 'kubectl top nodes/pods' 명령을 사용할 수 있게 합니다.
#

echo "Installing Metrics Server using Helm..."
helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server/
helm repo update metrics-server

helm upgrade --install metrics-server metrics-server/metrics-server \
    --namespace kube-system \
    --set "args={--kubelet-insecure-tls}"

echo "Waiting for Metrics Server to be ready..."
kubectl wait \
    --namespace kube-system \
    --for=condition=Available deployment/metrics-server \
    --timeout=120s

echo "Metrics Server installation completed."
