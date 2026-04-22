#!/usr/bin/env bash
set -e

if [ "$EUID" -ne 0 ]; then
  echo "Error: Please run as root"
  exit 1
fi

echo "Installing SSH Server..."

apt-get update && apt-get install -y --no-install-recommends openssh-server openssh-client

mkdir -p /var/run/sshd
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
sed -i 's/#StrictHostKeyChecking ask/StrictHostKeyChecking no/' /etc/ssh/ssh_config

echo "    StrictHostKeyChecking no" >> /etc/ssh/ssh_config
echo "    UserKnownHostsFile /dev/null" >> /etc/ssh/ssh_config

# Cleanup apt
apt-get autoremove -y --no-install-recommends
apt-get clean && rm -rf /var/lib/apt/lists/*

# SSH Key Generation for kasm-user
echo "Generating SSH keys for kasm-user..."
USER_HOME="/home/kasm-user"
USER_NAME="kasm-user"

# Ensure .ssh directory exists
mkdir -p "$USER_HOME/.ssh"

# Generate keys if they don't exist
if [ ! -f "$USER_HOME/.ssh/id_rsa.pem" ]; then
    ssh-keygen -t rsa -b 2048 -m PEM -f "$USER_HOME/.ssh/id_rsa.pem" -N ""
    cp "$USER_HOME/.ssh/id_rsa.pem.pub" "$USER_HOME/.ssh/authorized_keys"
fi

# Set permissions
chown -R "$USER_NAME:$USER_NAME" "$USER_HOME/.ssh"
chmod 700 "$USER_HOME/.ssh"
chmod 600 "$USER_HOME/.ssh/id_rsa.pem"
chmod 644 "$USER_HOME/.ssh/id_rsa.pem.pub"
chmod 600 "$USER_HOME/.ssh/authorized_keys"

echo "SSH setup completed successfully."
