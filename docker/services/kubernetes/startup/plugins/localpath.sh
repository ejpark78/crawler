#!/usr/bin/env bash
#
# Rancher Local Path Provisioner 설치 스크립트
# 노드의 로컬 디렉토리를 사용하여 동적 볼륨 프로비저닝(Dynamic PVC)을 가능하게 합니다.
#

echo "Installing Local Path Provisioner using Helm..."
helm repo add local-path-provisioner https://rancher.github.io/local-path-provisioner
helm repo update local-path-provisioner

helm upgrade --install local-path-provisioner local-path-provisioner/local-path-provisioner \
    --namespace local-path-storage \
    --create-namespace \
    --set storageClass.defaultClass=true

echo "Local Path Provisioner installation completed."
