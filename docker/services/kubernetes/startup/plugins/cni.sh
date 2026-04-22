#!/usr/bin/env bash
#
# Kubernetes CNI(Container Network Interface) 설치 스크립트
# CNI_NAME 환경 변수에 따라 적절한 CNI 플러그인을 설치합니다.
#

CNI_NAME=${CNI_NAME:-flannel}
KUBECONFIG=${KUBECONFIG:-/etc/kubernetes/admin.conf}

echo "CNI_NAME: $CNI_NAME"
echo "KUBECONFIG: $KUBECONFIG"

# 0. 표준 CNI 플러그인(bridge, portmap 등) 확인 및 설치
# Flannel 등 대다수 CNI는 bridge 플러그인이 미리 존재해야 정상 작동합니다.
if [ ! -f /opt/cni/bin/bridge ]; then
    echo "표준 CNI 플러그인이 누락되었습니다. 설치를 시작합니다..."
    CNI_PLUGINS_VERSION="v1.6.0"
    ARCH="amd64"
    [ "$(uname -m)" = "aarch64" ] && ARCH="arm64"
    
    mkdir -p /opt/cni/bin
    curl -L https://github.com/containernetworking/plugins/releases/download/${CNI_PLUGINS_VERSION}/cni-plugins-linux-${ARCH}-${CNI_PLUGINS_VERSION}.tgz | tar -xz -C /opt/cni/bin
    echo "표준 CNI 플러그인 설치 완료."
fi


case $CNI_NAME in
  cilium)
    echo "Installing Cilium using Cilium CLI..."
    # Cilium 설치 (kube-proxy 대체 및 Hubble 활성화 설정)
    cilium install \
        --set kubeProxyReplacement=true \
        --set k8sServiceHost=control-plane \
        --set k8sServicePort=6443 \
        --set hubble.enabled=true \
        --set hubble.ui.enabled=true \
        --set hubble.relay.enabled=true \
        --set operator.replicas=1 \
        --set prometheus.enabled=true

    echo "Waiting for Cilium to be ready..."
    cilium status --wait
    
    echo "Enabling Hubble..."
    cilium hubble enable --ui
    ;;

  flannel)
    echo "Installing Flannel..."
    kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml
    
    echo "Waiting for Flannel pods to be ready..."
    kubectl rollout status ds/kube-flannel -n kube-flannel --timeout=120s
    
    echo "Flannel Pod Status:"
    kubectl get pods -n kube-flannel
    ;;

  calico)
    echo "Installing Calico using calicoctl..."
    
    # Calico Operator 및 Custom Resources 설치
    # (참고: Calico는 CLI 자체에 'install' 명령이 내장되어 있지 않으므로 매니페스트를 적용합니다)
    kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.29.1/manifests/tigera-operator.yaml
    kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.29.1/manifests/custom-resources.yaml
    
    # 설치 상태 확인 (calicoctl 사용)
    echo "Calico 상태를 확인합니다..."
    calicoctl node status || true
    ;;

  *)
    echo "지원되지 않는 CNI_NAME입니다: $CNI_NAME"
    exit 1
    ;;
esac
