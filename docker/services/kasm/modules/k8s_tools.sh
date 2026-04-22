#!/usr/bin/env bash
set -e

if [ "$EUID" -ne 0 ]; then
  echo "Error: Please run as root"
  exit 1
fi

echo "Installing Kubernetes tools..."

echo "# 1. Installing kubectl..."
KUBECTL_VERSION=$(curl -L -s https://dl.k8s.io/release/stable.txt)
# Detect architecture
ARCH=$(uname -m)
case $ARCH in
    x86_64)  K8S_ARCH="amd64" ;;
    aarch64) K8S_ARCH="arm64" ;;
    *)       echo "Unsupported architecture: $ARCH"; exit 1 ;;
esac
curl -LO "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/${K8S_ARCH}/kubectl"
install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
rm kubectl

echo "# 2. Installing helm..."
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

echo "# 3. Installing k9s..."
K9S_JSON=$(curl -sL "https://api.github.com/repos/derailed/k9s/releases/latest")
K9S_VERSION=$(echo "$K9S_JSON" | grep -Po '"tag_name": "v\K[^"]*' || true)
if [ -z "$K9S_VERSION" ]; then
    echo "Error: Could not determine k9s version from GitHub API."
    echo "Response: $K9S_JSON"
    exit 1
fi
echo "k9s version: $K9S_VERSION"
curl -Lo k9s.tar.gz "https://github.com/derailed/k9s/releases/download/v${K9S_VERSION}/k9s_Linux_amd64.tar.gz"
tar -xzf k9s.tar.gz k9s
mv k9s /usr/local/bin/k9s
rm k9s.tar.gz

echo "# 4. Installing kubectx & kubens..."
git clone https://github.com/ahmetb/kubectx /opt/kubectx
ln -sf /opt/kubectx/kubectx /usr/local/bin/kubectx
ln -sf /opt/kubectx/kubens /usr/local/bin/kubens

echo "# 5. Installing stern..."
STERN_JSON=$(curl -sL "https://api.github.com/repos/stern/stern/releases/latest")
STERN_VERSION=$(echo "$STERN_JSON" | grep -Po '"tag_name": "v\K[^"]*' || true)
if [ -z "$STERN_VERSION" ]; then
    echo "Error: Could not determine stern version from GitHub API."
    echo "Response: $STERN_JSON"
    exit 1
fi
echo "stern version: $STERN_VERSION"
curl -Lo stern.tar.gz "https://github.com/stern/stern/releases/download/v${STERN_VERSION}/stern_${STERN_VERSION}_linux_amd64.tar.gz"
tar -xzf stern.tar.gz stern
mv stern /usr/local/bin/stern
rm stern.tar.gz

echo "# 6. Installing cilium cli..."
CILIUM_CLI_VERSION=$(curl -sL https://raw.githubusercontent.com/cilium/cilium-cli/main/stable.txt)
curl -L --fail --remote-name-all "https://github.com/cilium/cilium-cli/releases/download/${CILIUM_CLI_VERSION}/cilium-linux-amd64.tar.gz"
tar xzf cilium-linux-amd64.tar.gz
mv cilium /usr/local/bin
rm cilium-linux-amd64.tar.gz

echo "# 7. Installing calicoctl..."
CALICO_JSON=$(curl -sL "https://api.github.com/repos/projectcalico/calico/releases/latest")
CALICO_VERSION=$(echo "$CALICO_JSON" | grep -Po '"tag_name": "\K[^"]*' || true)
if [ -z "$CALICO_VERSION" ]; then
    echo "Error: Could not determine calico version from GitHub API."
    echo "Response: $CALICO_JSON"
    exit 1
fi
echo "calico version: $CALICO_VERSION"
curl -L "https://github.com/projectcalico/calico/releases/download/${CALICO_VERSION}/calicoctl-linux-amd64" -o calicoctl
chmod +x calicoctl
mv calicoctl /usr/local/bin/

echo "# 8. Installing headlamp..."

# GUI Dependencies for Electron apps
apt-get update && apt-get install -y --no-install-recommends \
    libfuse2 libgbm1 libasound2t64 libnss3 libxshmfence1 libatk1.0-0 \
    libatk-bridge2.0-0 libcups2 libdrm2 libgtk-3-0 libsecret-1-0

# Detect architecture
ARCH=$(uname -m)
case $ARCH in
    x86_64)  DEB_ARCH="amd64" ;;
    aarch64) DEB_ARCH="arm64" ;;
    *)       echo "Unsupported architecture: $ARCH"; exit 1 ;;
esac

HEADLAMP_JSON=$(curl -sL "https://api.github.com/repos/headlamp-k8s/headlamp/releases/latest")
HEADLAMP_VERSION=$(echo "$HEADLAMP_JSON" | grep -Po '"tag_name": "v\K[^"]*' || true)

if [ -z "$HEADLAMP_VERSION" ]; then
    echo "Error: Could not determine Headlamp version from GitHub API."
    echo "Response: $HEADLAMP_JSON"
    exit 1
fi
echo "Headlamp version: $HEADLAMP_VERSION"

set -x
curl -Lfo headlamp.deb "https://github.com/headlamp-k8s/headlamp/releases/download/v${HEADLAMP_VERSION}/headlamp_${HEADLAMP_VERSION}_${DEB_ARCH}.deb"
if ! apt-get install -y --no-install-recommends ./headlamp.deb; then
    echo "Warning: apt-get install ./headlamp.deb failed, trying with --fix-broken"
    apt-get install -y --fix-broken
    apt-get install -y --no-install-recommends ./headlamp.deb
fi
rm headlamp.deb
set +x

# Patch Headlamp to run with --no-sandbox (required for container environments)
if [ -f /usr/bin/headlamp ]; then
    echo "Patching Headlamp for Electron sandbox..."
    echo -e '#!/usr/bin/env bash\n/usr/bin/headlamp --no-sandbox "$@"' > /usr/local/bin/headlamp-wrapped
    chmod +x /usr/local/bin/headlamp-wrapped
    # Optional: Patch the .desktop file as well
    if [ -f /usr/share/applications/headlamp.desktop ]; then
        sed -i 's/Exec=\/usr\/bin\/headlamp %U/Exec=\/usr\/local\/bin\/headlamp-wrapped %U/g' /usr/share/applications/headlamp.desktop
    fi
else
    echo "Warning: /usr/bin/headlamp not found, skip patching"
fi

# 9. Installing istioctl...
echo "# 9. Installing istioctl..."
ISTIO_JSON=$(curl -sL https://api.github.com/repos/istio/istio/releases/latest)
ISTIO_VERSION=$(echo "$ISTIO_JSON" | grep -Po '"tag_name": "\K[^"]*' || true)

if [ -z "$ISTIO_VERSION" ]; then
    echo "Error: Could not determine Istio version from GitHub API."
    echo "Response: $ISTIO_JSON"
    exit 1
fi
echo "Istio version: $ISTIO_VERSION"

curl -L https://istio.io/downloadIstio | ISTIO_VERSION=$ISTIO_VERSION sh -
if [ -d istio-$ISTIO_VERSION ]; then
    mv istio-$ISTIO_VERSION/bin/istioctl /usr/local/bin/
    rm -rf istio-$ISTIO_VERSION
else
    # In case the directory name is different
    ISTIO_DIR=$(ls -d istio-* | head -n 1)
    if [ -n "$ISTIO_DIR" ]; then
        mv $ISTIO_DIR/bin/istioctl /usr/local/bin/
        rm -rf $ISTIO_DIR
    fi
fi

echo "Kubernetes tools installation completed."
