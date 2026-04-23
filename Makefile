# ==============================================================================
# GeekNews Crawler Infrastructure Management
# ==============================================================================
# 이 파일은 크롤러 서비스의 빌드, 배포, 데이터 수집 및 Airflow 운영을 관리합니다.
# 인프라 제어부터 데이터 수집 및 테스트까지 통합된 인터페이스를 제공합니다.
#
# [주요 변수 가이드]
#   PRJ      - 프로젝트 모드 선택 (crawler: 메인 크롤러 스택, k8s: K8s 테스트 환경)
#   SOURCE   - 수집 대상 소스 이름 (app/scrapers/ 하위 클래스명과 매칭)
#   DATE     - 수집/백필 기준 날짜 (YYYY-MM-DD)
#   PAGE     - 수집할 페이지 번호 (기본: 1)
#   WORKERS  - Kubernetes 워커 노드 개수 (PRJ=k8s 환경에서 사용)
#
# [실행 그룹]
#   1. Infrastructure : 컨테이너 기동/정지, 빌드, 상태 확인 (up, down, build, ps)
#   2. Collection     : 로컬 수집 테스트 및 데이터 저장 (test, debug, run)
#   3. Quality & Test : 유닛 테스트 및 무결성 검증 (pytest)
#   4. Airflow        : DAG 관리, Backfill 소급 적용 및 계정 관리 (backfill, clear)
#   5. Kubernetes     : K8s 전용 타겟 호출 (k8s-up, k8s-status, k8s-init 등)
# ==============================================================================

SHELL := /bin/bash

# Variables
SOURCE ?= GeekNews
DATE ?= $(shell date +%Y-%m-%d)
PAGE ?= 1
START_DATE ?= 2026-04-11
END_DATE ?= 2026-04-17
DAG_ID = geeknews
OUT_PATH ?= /app/volumes/debug/$(shell date +"%Y-%m-%d_%H%M")/$(SOURCE)_$(DATE)_$(PAGE)
LOG_LEVEL ?= INFO
NET_NAME = airflow-net

PRJ ?= crawler
ifeq ($(PRJ),k8s)
  COMPOSE_FILE := --env-file docker/services/kubernetes/.env -f docker/compose.kubernetes.yml
else
  COMPOSE_FILE := --env-file docker/.env -f compose.yml
endif

.PHONY: *

help: ## 도움말 출력
	@echo "Usage: make [target] [PRJ=crawler|k8s]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# --- Ollama ---
# ollama pull gemma4:31b-cloud
# ollama run gemma4:31b-cloud

login:
	ollama login

logout:
	ollama signout

claude:
	ollama launch claude --model gemma4:31b-cloud -- --dangerously-skip-permissions

# --- Infrastructure ---
up: ## 컨테이너 실행 (PRJ=k8s 가능)
	docker compose $(COMPOSE_FILE) up -d

down: ## 컨테이너 정지
	docker compose $(COMPOSE_FILE) down

restart: ## 재시작
	$(MAKE) down
	$(MAKE) up

build: ## 이미지 빌드
	cp docker/services/kubernetes/modules/k8s_tools.sh docker/services/kasm/modules/k8s_tools.sh
	
	docker compose $(COMPOSE_FILE) build
	rm docker/services/kasm/modules/k8s_tools.sh

logs: ## 로그 확인
	docker compose $(COMPOSE_FILE) logs -f

ps: ## 컨테이너 상태 확인 (실시간)
	watch -d -t -c -n 5 "echo \"[$$(date +'%Y-%m-%d %H:%M:%S')] 🚀 CONTAINER STATUS\" && docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}' | (read -r header; echo \"\$$header\"; sort -k2,3 -r)"

top: ## 리소스 사용량 확인 (실시간)
	watch -d -t -c -n 5 "echo \"[$$(date +'%Y-%m-%d %H:%M:%S')] 🚀 CONTAINER STATS\" && docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}'"

# --- Collection & Testing ---
# Example: make test SOURCE=PyTorchKR PAGE=1 LOG_LEVEL=DEBUG
test: ## 로컬 테스트 수집 실행
	docker compose $(COMPOSE_FILE) run --rm -v .:/app -w /app -e LOG_LEVEL=$(LOG_LEVEL) \
		worker uv run python -m app.main \
		--source $(SOURCE) \
		--date $(DATE) \
		--page $(PAGE) \
		--out_path $(OUT_PATH)

# Example: make debug SOURCE=GeekNews DATE=2026-04-18 PAGE=1 LOG_LEVEL=DEBUG
# Example: make debug SOURCE=PyTorchKR PAGE=1 LOG_LEVEL=DEBUG
debug:
	docker run --rm -v .:/app -w /app \
		-e LOG_LEVEL=$(LOG_LEVEL) \
		crawler/worker:latest \
		uv run python -m app.main \
		--source $(SOURCE) \
		--date $(DATE) \
		--page $(PAGE) \
		--out_path $(OUT_PATH)

pytest: ## 유닛 테스트 실행
	docker compose $(COMPOSE_FILE) run --rm -v .:/app worker uv run pytest -v -s tests/ 

# Example: make run START_DATE=2026-04-18 END_DATE=2026-04-18
run:
	@current_date=$(START_DATE); \
	until [[ "$$current_date" > "$(END_DATE)" ]]; do \
		echo "------------------------------------------"; \
		echo "Processing date: $$current_date"; \
		for page in 1 2 3 4 5; do \
			echo "Executing: Date=$$current_date, Page=$$page"; \
			docker compose $(COMPOSE_FILE) -f docker/compose.worker.yml run --rm worker \
				uv run python -m app.main \
				--source $(SOURCE) \
				--date $$current_date \
				--page $$page; \
		done; \
		current_date=$$(date -I -d "$$current_date + 1 day"); \
	done

# --- Airflow ---
# Example: make backfill SOURCE=GeekNews START_DATE=2023-04-01 END_DATE=2024-06-17
backfill: ## Airflow Backfill 실행 (날짜 범위 반복)
	@current_date=$(END_DATE); \
	until [[ "$$current_date" < "$(START_DATE)" ]]; do \
		echo "------------------------------------------"; \
		echo "Backfilling date: $$current_date"; \
		docker compose $(COMPOSE_FILE) exec airflow airflow dags backfill \
			-s $$current_date -e $$current_date $(DAG_ID); \
		current_date=$$(date -I -d "$$current_date - 1 day"); \
	done

# Example: make backfill START_DATE=2023-04-01 END_DATE=2026-04-10
# Example: make backfill START_DATE=2026-03-01 END_DATE=2026-03-31
backfill-rg:
	docker compose $(COMPOSE_FILE) exec airflow airflow dags backfill \
	  -s $(START_DATE) -e $(END_DATE) $(DAG_ID)

# Example: make clear START_DATE=2026-04-01 END_DATE=2026-04-17
clear:
	docker compose $(COMPOSE_FILE) exec -T airflow airflow tasks clear -y \
	  -s $(START_DATE) -e $(END_DATE) $(DAG_ID)

reset-pw:
	docker compose $(COMPOSE_FILE) exec airflow \
		airflow users reset-password \
			--username admin --password admin

# --- Database ---
mongo-bash: ## MongoDB 쉘 접속
	docker compose $(COMPOSE_FILE) exec mongodb mongosh crawler_db

pg-bash:
	docker compose $(COMPOSE_FILE) exec postgres bash

# /opt/airflow/dags/
# /opt/airflow/logs/dag_id=geeknews/
airflow-bash:
	docker compose $(COMPOSE_FILE) exec airflow bash

worker-bash:
	docker compose $(COMPOSE_FILE) exec worker bash

# DELETE FROM task_instance WHERE dag_id='geeknews';
pgsql:
	docker compose $(COMPOSE_FILE) exec postgres psql -U airflow -d airflow

init-net:
	docker network create -d bridge $(NET_NAME)
	docker network ls

ipconfig: ## 모든 Docker 네트워크 및 컨테이너 상세 정보 표시
	@{ \
	echo "NETWORK|SUBNET|CONTAINER|IP_ADDRESS"; \
	for net in $$(docker network ls --format "{{.Name}}"); do \
		subnet=$$(docker network inspect $$net --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}' | xargs); \
		[ -z "$$subnet" ] && subnet="none"; \
		docker network inspect $$net --format '{{range .Containers}}'$$net'|'$$subnet'|{{.Name}}|{{.IPv4Address}}{{"\n"}}{{end}}' | grep . || \
		echo "$$net|$$subnet|-|-"; \
	done; \
	} | column -t -s '|'



ls-net: ## Docker 네트워크 상세 정보 확인 (프로젝트별)
	@PROJECT_NAME=$$(docker compose $(COMPOSE_FILE) config | grep '^name:' | awk '{print $$2}'); \
	NET_NAME=$$(docker network ls --filter "label=com.docker.compose.project=$$PROJECT_NAME" --format "{{.Name}}" | head -n 1); \
	if [ -z "$$NET_NAME" ]; then echo "No network found for project $$PROJECT_NAME"; exit 1; fi; \
	{ echo -e "NETWORK\tNAME\tIP_ADDRESS"; docker network inspect $$NET_NAME --format "{{range .Containers}}$$NET_NAME	{{.Name}}	{{.IPv4Address}}{{\"\n\"}}{{end}}"; } | column -t


# --- Kubernetes ---
k8s-%: ## Kubernetes 관련 명령 실행 (up, down, status 등)
	@$(MAKE) -C docker/services/kubernetes $*


