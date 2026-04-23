# ==============================================================================
# Kubernetes Infrastructure Management (Docker-in-Docker Cluster)
# ==============================================================================
# This Makefile manages the Kubernetes cluster running via Docker Compose.
# It is located in docker/services/kubernetes/

# Variables
CNI_NAME ?= flannel
N ?= 1

# Paths relative to this Makefile
COMPOSE_DIR = ../..
ENV_FILE = $(COMPOSE_DIR)/.env.kubernetes
COMPOSE_FILE = $(COMPOSE_DIR)/compose.kubernetes.yml

.PHONY: help config build up scale down kasm control-plane worker status

help: ## 도움말 출력
	@echo "Usage: make [target] [CNI_NAME=flannel|calico|cilium] [N=count]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

config: ## Compose 설정 확인
	docker compose --env-file $(ENV_FILE) -f $(COMPOSE_FILE) config

build: ## 컨트롤 플레인 이미지 빌드
	cp modules/k8s_tools.sh ../kasm/modules/k8s_tools.sh
	docker compose --env-file $(ENV_FILE) -f $(COMPOSE_FILE) build control-plane
	rm ../kasm/modules/k8s_tools.sh

up: ## 클러스터 실행 (예: make up CNI_NAME=calico)
	CNI_NAME=$(CNI_NAME) docker compose --env-file $(ENV_FILE) -f $(COMPOSE_FILE) up -d

scale: ## 워커 노드 스케일링 (예: make scale N=3)
	docker compose --env-file $(ENV_FILE) -f $(COMPOSE_FILE) up -d --scale worker=$(N)

down: ## 클러스터 정지
	docker compose --env-file $(ENV_FILE) -f $(COMPOSE_FILE) down

kasm: ## Kasm 컨테이너 접속
	docker compose --env-file $(ENV_FILE) -f $(COMPOSE_FILE) exec -it kasm bash

control-plane: ## 컨트롤 플레인 노드 접속
	docker compose --env-file $(ENV_FILE) -f $(COMPOSE_FILE) exec -it control-plane bash

worker: ## 워커 노드 접속 (예: make worker N=1)
	docker compose --env-file $(ENV_FILE) -f $(COMPOSE_FILE) exec -it --index=$(N) worker bash

status: ## 클러스터 상태 확인 (Nodes, Pods)
	@docker compose --env-file $(ENV_FILE) -f $(COMPOSE_FILE) exec -it control-plane kubectl get nodes -o wide
	@echo "--------------------------------------------------------------------------------"
	@docker compose --env-file $(ENV_FILE) -f $(COMPOSE_FILE) exec -it control-plane kubectl get pods -A
