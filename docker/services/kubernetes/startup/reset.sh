#!/usr/bin/env bash

rm -rf /root/.kube/config
rm -rf /root/.kube/join.sh

kubeadm reset -f
