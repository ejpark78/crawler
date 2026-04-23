#!/usr/bin/env bash
#
# NGINX Ingress Controller 설치 스크립트
# HTTP/HTTPS 트래픽을 클러스터 내부 서비스로 라우팅합니다.
#

echo "Installing NGINX Ingress Controller using Helm..."
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update ingress-nginx

helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace

echo "Waiting for Ingress NGINX controller to be ready..."
kubectl rollout status deployment/ingress-nginx-controller -n ingress-nginx --timeout=120s

echo "NGINX Ingress Controller installation completed."
