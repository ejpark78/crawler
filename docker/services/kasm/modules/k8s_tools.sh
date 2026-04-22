#!/usr/bin/env bash
set -e

if [ "$EUID" -ne 0 ]; then
  echo "Error: Please run as root"
  exit 1
fi

echo "Installing Kubernetes tools..."

# 1. kubectl
echo "Installing kubectl..."
KUBECTL_VERSION=$(curl -L -s https://dl.k8s.io/release/stable.txt)
curl -LO "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl"
install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
rm kubectl

# 2. helm
echo "Installing helm..."
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# 3. k9s
echo "Installing k9s..."
K9S_VERSION=$(curl -s "https://api.github.com/repos/derailed/k9s/releases/latest" | grep -Po '"tag_name": "v\K[^"]*')
curl -Lo k9s.tar.gz "https://github.com/derailed/k9s/releases/download/v${K9S_VERSION}/k9s_Linux_amd64.tar.gz"
tar -xzf k9s.tar.gz k9s
mv k9s /usr/local/bin/k9s
rm k9s.tar.gz

# 4. kubectx & kubens
echo "Installing kubectx & kubens..."
git clone https://github.com/ahmetb/kubectx /opt/kubectx
ln -sf /opt/kubectx/kubectx /usr/local/bin/kubectx
ln -sf /opt/kubectx/kubens /usr/local/bin/kubens

# 5. stern
echo "Installing stern..."
STERN_VERSION=$(curl -s "https://api.github.com/repos/stern/stern/releases/latest" | grep -Po '"tag_name": "v\K[^"]*')
curl -Lo stern.tar.gz "https://github.com/stern/stern/releases/download/v${STERN_VERSION}/stern_${STERN_VERSION}_linux_amd64.tar.gz"
tar -xzf stern.tar.gz stern
mv stern /usr/local/bin/stern
rm stern.tar.gz

# 6. cilium cli
echo "Installing cilium cli..."
CILIUM_CLI_VERSION=$(curl -s https://raw.githubusercontent.com/cilium/cilium-cli/main/stable.txt)
curl -L --fail --remote-name-all "https://github.com/cilium/cilium-cli/releases/download/${CILIUM_CLI_VERSION}/cilium-linux-amd64.tar.gz"
tar xzf cilium-linux-amd64.tar.gz
mv cilium /usr/local/bin
rm cilium-linux-amd64.tar.gz

# 7. calico cli (calicoctl)
echo "Installing calicoctl..."
CALICO_VERSION=$(curl -s "https://api.github.com/repos/projectcalico/calico/releases/latest" | grep -Po '"tag_name": "\K[^"]*')
curl -L "https://github.com/projectcalico/calico/releases/download/${CALICO_VERSION}/calicoctl-linux-amd64" -o calicoctl
chmod +x calicoctl
mv calicoctl /usr/local/bin/

# 8. headlamp (Desktop App)
echo "Installing headlamp..."

# GUI Dependencies for Electron apps
apt-get update && apt-get install -y --no-install-recommends \
    libfuse2 libgbm1 libasound2t64 libnss3 libxshmfence1 libatk1.0-0 \
    libatk-bridge2.0-0 libcups2 libdrm2 libgtk-3-0 libsecret-1-0

HEADLAMP_VERSION=$(curl -s "https://api.github.com/repos/headlamp-k8s/headlamp/releases/latest" | grep -Po '"tag_name": "v\K[^"]*')
curl -Lo headlamp.deb "https://github.com/headlamp-k8s/headlamp/releases/download/v${HEADLAMP_VERSION}/headlamp_${HEADLAMP_VERSION}_amd64.deb"
apt-get install -y --no-install-recommends ./headlamp.deb
rm headlamp.deb

# Patch Headlamp to run with --no-sandbox (required for container environments)
if [ -f /usr/bin/headlamp ]; then
    echo -e '#!/usr/bin/env bash\n/usr/bin/headlamp --no-sandbox "$@"' > /usr/local/bin/headlamp-wrapped
    chmod +x /usr/local/bin/headlamp-wrapped
    # Optional: Patch the .desktop file as well
    if [ -f /usr/share/applications/headlamp.desktop ]; then
        sed -i 's/Exec=\/usr\/bin\/headlamp %U/Exec=\/usr\/local\/bin\/headlamp-wrapped %U/g' /usr/share/applications/headlamp.desktop
    fi
fi

# 9. istioctl
echo "Installing istioctl..."
curl -L https://istio.io/downloadIstio | ISTIO_VERSION=$(curl -s https://api.github.com/repos/istio/istio/releases/latest | grep -Po '"tag_name": "\K[^"]*') sh -
cd istio-*
mv bin/istioctl /usr/local/bin/
cd ..
rm -rf istio-*

echo "Kubernetes tools installation completed."
