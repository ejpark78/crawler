#!/usr/bin/env bash

kubeadm reset -f

rm -rf /root/.kube/config
rm -rf /root/.kube/cache
rm -rf /root/.kube/state
rm -rf /root/.kube/tmp
