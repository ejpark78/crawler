#!/usr/bin/env bash
#
# kube-prometheus-stack 설치 스크립트
# Prometheus, Grafana, Alertmanager를 포함한 통합 모니터링 솔루션입니다.
#

echo "Installing kube-prometheus-stack using Helm..."
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update prometheus-community

# Grafana를 외부로 노출하기 위해 LoadBalancer 설정
# 리소스가 부족한 환경을 고려하여 필요한 경우 replica 수 등을 조정할 수 있습니다.
helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set grafana.service.type=LoadBalancer

echo "Waiting for Prometheus Operator to be ready..."
kubectl rollout status deployment/prometheus-kube-prometheus-operator -n monitoring --timeout=120s

echo "Monitoring stack installation completed."
echo "접속 방법: 'kubectl get svc -n monitoring' 명령어로 Grafana의 EXTERNAL-IP 확인 후 접속"
echo "기본 계정: admin / prom-operator"
