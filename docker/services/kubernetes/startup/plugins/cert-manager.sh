#!/usr/bin/env bash
#
# Cert-Manager 설치 스크립트
# 클러스터 내에서 SSL/TLS 인증서를 자동으로 발급 및 관리합니다.
#

echo "Installing Cert-Manager using Helm..."
helm repo add jetstack https://charts.jetstack.io
helm repo update jetstack

helm upgrade --install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set installCRDs=true

echo "Waiting for Cert-Manager pods to be ready..."
kubectl rollout status deployment/cert-manager -n cert-manager --timeout=120s
kubectl rollout status deployment/cert-manager-webhook -n cert-manager --timeout=120s

echo "Cert-Manager installation completed."
