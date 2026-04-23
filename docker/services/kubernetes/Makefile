# ==============================================================================
# Kubernetes Infrastructure Management (Docker-in-Docker Cluster)
# ==============================================================================
# 이 파일은 Docker Compose 내에서 실행되는 Kubernetes 클러스터를 관리합니다.
# 노드 빌드, 클러스터 초기화(init), 조인(join) 및 상태 확인 기능을 제공합니다.
#
# [주요 변수 가이드]
#   CNI_NAME - 사용할 CNI 플러그인 (flannel, calico, cilium / 기본: calico)
#   WORKERS  - 생성할 워커 노드의 개수 (기본: 1)
#   PLUGINS  - 설치할 플러그인 목록 (기본: cni.sh dashboard.sh 등 전체)
#
# [타겟 분류]
#   1. Infra   : 컨테이너 실행/정지 및 이미지 빌드 (up, down, build, scale)
#   2. Access  : 노드 쉘 접속 (control-plane, worker, kasm)
#   3. Cluster : K8s 초기화 및 상태 점검 (init, join, status)
# ==============================================================================

# Variables
WORKERS ?= 1
CNI_NAME ?= calico

PLUGINS += cni.sh
PLUGINS += localpath.sh
PLUGINS += metrics-server.sh
PLUGINS += metallb.sh
PLUGINS += cert-manager.sh
PLUGINS += prometheus.sh
PLUGINS += portainer.sh

# Paths relative to this Makefile
ENV_FILE = .env
COMPOSE_DIR = ../..
COMPOSE_FILE = $(COMPOSE_DIR)/compose.kubernetes.yml

.PHONY: *

help: ## 도움말 출력
	@echo "Usage: make [target] [CNI_NAME=flannel|calico|cilium] [WORKERS=count]"
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

scale: ## 워커 노드 스케일링 (예: make scale WORKERS=3)
	docker compose --env-file $(ENV_FILE) -f $(COMPOSE_FILE) up -d --scale worker=$(WORKERS)

down: ## 클러스터 정지
	docker compose --env-file $(ENV_FILE) -f $(COMPOSE_FILE) down

kasm: ## Kasm 컨테이너 접속
	docker compose --env-file $(ENV_FILE) -f $(COMPOSE_FILE) exec -it kasm bash

control-plane: ## 컨트롤 플레인 노드 접속
	docker compose --env-file $(ENV_FILE) -f $(COMPOSE_FILE) exec -it control-plane bash

worker: ## 워커 노드 접속 (예: make worker WORKERS=1)
	docker compose --env-file $(ENV_FILE) -f $(COMPOSE_FILE) exec -it --index=$(WORKERS) worker bash

status: ## 클러스터 상태 확인 (Nodes, Pods)
	@docker compose --env-file $(ENV_FILE) -f $(COMPOSE_FILE) exec -it control-plane kubectl get nodes -o wide
	@echo "--------------------------------------------------------------------------------"
	@docker compose --env-file $(ENV_FILE) -f $(COMPOSE_FILE) exec -it control-plane kubectl get pods -A

init:
	docker compose --env-file $(ENV_FILE) -f $(COMPOSE_FILE) exec -it control-plane /startup/init.sh

join: ## 모든 워커 노드를 클러스터에 조인
	@for i in $$(seq 1 $(WORKERS)); do \
		echo ">>> Joining worker $$i..."; \
		docker compose --env-file $(ENV_FILE) -f $(COMPOSE_FILE) exec --index=$$i worker bash /root/.kube/join.sh; \
	done

config:
	mkdir -p ~/.kube
	docker compose --env-file $(ENV_FILE) -f $(COMPOSE_FILE) exec -it control-plane cat /root/.kube/config > ~/.kube/config

plugin: ## 클러스터 플러그인 설치 (기본값: 전체, 선택: PLUGINS="cni.sh dashboard.sh")
	@for plugin in $(PLUGINS); do \
		echo "--------------------------------------------------------------------------------"; \
		echo ">>> Installing plugin: $$plugin..."; \
		docker compose --env-file $(ENV_FILE) -f $(COMPOSE_FILE) exec -it control-plane bash /startup/plugins/$$plugin; \
	done
