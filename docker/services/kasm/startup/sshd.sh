#!/usr/bin/env bash
echo "Starting SSH server..."

# Ensure the runtime directory exists
sudo mkdir -p /var/run/sshd

# Start sshd in the background (daemon mode)
sudo /usr/sbin/sshd
