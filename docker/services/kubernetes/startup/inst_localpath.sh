#!/usr/bin/env bash
#
# Rancher Local Path Provisioner 설치 스크립트
# 노드의 로컬 디렉토리를 사용하여 동적 볼륨 프로비저닝(Dynamic PVC)을 가능하게 합니다.
#

VERSION=${LOCALPATH_VERSION:-v0.0.31}
KUBECONFIG=${KUBECONFIG:-/etc/kubernetes/admin.conf}

echo "Installing Local Path Provisioner $VERSION..."
kubectl apply -f https://raw.githubusercontent.com/rancher/local-path-provisioner/$VERSION/deploy/local-path-storage.yaml

# 기본 StorageClass로 설정
echo "Setting local-path as default StorageClass..."
kubectl patch storageclass local-path -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'

echo "Local Path Provisioner installation completed."
