#!/usr/bin/env bash
#
# Rancher Local Path Provisioner 설치 스크립트
# 노드의 로컬 디렉토리를 사용하여 동적 볼륨 프로비저닝(Dynamic PVC)을 가능하게 합니다.
#

echo "Installing Local Path Provisioner using manifests..."
kubectl apply -f https://raw.githubusercontent.com/rancher/local-path-provisioner/v0.0.35/deploy/local-path-storage.yaml

# Set as default storage class
kubectl patch storageclass local-path -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'

echo "Local Path Provisioner installation completed."
