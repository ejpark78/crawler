#!/usr/bin/env bash
# docker-setup.sh
# Detects the GID of /var/run/docker.sock and adds kasm-user to the group.

echo "Setting up Docker-out-of-Docker (DooD) permissions..."

DOCKER_SOCK="/var/run/docker.sock"
if [ -S "$DOCKER_SOCK" ]; then
    DOCKER_GID=$(stat -c '%g' "$DOCKER_SOCK")
    echo "Detected Docker socket GID: $DOCKER_GID"
    
    # Check if a group with this GID already exists
    GROUP_NAME=$(getent group "$DOCKER_GID" | cut -d: -f1)
    
    if [ -z "$GROUP_NAME" ]; then
        GROUP_NAME="docker_host"
        echo "Creating group $GROUP_NAME with GID $DOCKER_GID"
        sudo groupadd -g "$DOCKER_GID" "$GROUP_NAME"
    fi
    
    # Add user to the group
    if ! id -nG "$USER" | grep -qw "$GROUP_NAME"; then
        echo "Adding $USER to group $GROUP_NAME"
        sudo usermod -aG "$GROUP_NAME" "$USER"
    fi
else
    echo "Warning: /var/run/docker.sock not found. Docker CLI will not work."
fi

echo "Docker setup complete."
