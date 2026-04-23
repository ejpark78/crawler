#!/usr/bin/env bash
#
# Kubernetes CNI(Container Network Interface) 설치 스크립트
# CNI_NAME 환경 변수에 따라 적절한 CNI 플러그인을 설치합니다.
#

CNI_NAME=${CNI_NAME:-flannel}
KUBECONFIG=${KUBECONFIG:-/etc/kubernetes/admin.conf}

echo "CNI_NAME: $CNI_NAME"
echo "KUBECONFIG: $KUBECONFIG"

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
    echo "Installing Calico using operator..."
    
    # 1. Calico Operator 설치
    kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.29.1/manifests/tigera-operator.yaml
    
    # 2. Custom Resources 설정 (Subnet 맞춤)
    # .env.kubernetes 또는 init.sh에서 설정한 값을 사용합니다.
    CALICO_SUBNET=${CALICO_SUBNET:-"192.168.0.0/16"}
    echo "Configuring Calico IP Pool with subnet: $CALICO_SUBNET"
    
    curl -L https://raw.githubusercontent.com/projectcalico/calico/v3.29.1/manifests/custom-resources.yaml -o /tmp/calico-custom-resources.yaml
    sed -i "s|cidr: 192.168.0.0/16|cidr: ${CALICO_SUBNET}|g" /tmp/calico-custom-resources.yaml
    
    kubectl create -f /tmp/calico-custom-resources.yaml
    
    echo "Waiting for Tigera Operator to be ready..."
    kubectl rollout status deployment/tigera-operator -n tigera-operator --timeout=60s
    ;;

  *)
    echo "지원되지 않는 CNI_NAME입니다: $CNI_NAME"
    exit 1
    ;;
esac
