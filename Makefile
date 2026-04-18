# ==============================================================================
# GeekNews Crawler Infrastructure Management
# ==============================================================================
# 이 파일은 크롤러 서비스의 빌드, 배포, 데이터 수집 및 Airflow 운영을 관리합니다.
#
# [주요 변수 가이드]
#   SOURCE   - 수집 대상 소스 이름 (SCRAPER_REGISTRY에 등록된 값, 기본: GeekNews)
#   URL      - 수집 대상 기본 URL (기본: https://news.hada.io/)
#   DATE     - 백필 및 과거 데이터 조회 시 기준 날짜 (YYYY-MM-DD)
#   PAGE     - 수집할 페이지 번호 (기본: 1)
#   OUT_PATH - 수집된 결과를 JSON 파일로 저장할 경로 (기본: volumes/ 하위)
#
# [실행 그룹]
#   1. Infrastructure : 컨테이너 기동, 정지, 재시작 및 상태 확인
#   2. Collection     : 로컬 수집 실행 및 파일 저장 (collect-docker)
#   3. Testing        : 유닛 테스트 및 무결성 검사
#   4. Airflow        : DAG 관리, Backfill 소급 적용 및 관리자 계정 초기화
# ==============================================================================

# Variables
SOURCE ?= GeekNews
URL ?= https://news.hada.io/
DATE ?= $(shell date +%Y-%m-%d)
PAGE ?= 1
DAG_ID = geeknews
OUT_PATH ?= /app/volumes/debuging/$(shell date +"%Y-%m-%d_%H%M")/$(SOURCE)_$(DATE)_$(PAGE)
LOG_LEVEL ?= INFO

.PHONY: *

# --- Ollama ---
# ollama pull gemma4:31b-cloud
# ollama run gemma4:31b-cloud

login:
	ollama login

logout:
	ollama signout

claude:
	ollama launch claude --model gemma4:31b-cloud

# --- Infrastructure ---
up:
	docker compose up -d

down:
	docker compose down

restart: down up

build:
	docker compose build

logs:
	docker compose logs -f

ps:
	watch -d -n 5 docker ps

stats:
	docker stats

# --- Collection & Testing ---
# Example: make collect DATE=2026-03-25 PAGE=1
collect:
	docker compose run \
		--rm worker uv run python -m app.main \
		--source $(SOURCE) \
		--url $(URL) \
		--date $(DATE) \
		--page $(PAGE) \
		--out_path $(OUT_PATH)

# Example: make collect-test DATE=2026-03-25 PAGE=1 LOG_LEVEL=DEBUG
collect-docker:
	docker run --rm -v .:/app -w /app \
		-e LOG_LEVEL=$(LOG_LEVEL) \
		crawler/worker:latest \
		uv run python -m app.main \
		--source $(SOURCE) \
		--url $(URL) \
		--date $(DATE) \
		--page $(PAGE) \
		--out_path $(OUT_PATH)

test:
	docker compose exec worker uv run pytest

# --- Airflow ---
# Example: make backfill START=2023-04-16 END=2026-04-01
backfill:
	docker compose exec airflow airflow dags backfill \
	  -s $(START) -e $(END) $(DAG_ID)

# Example: make clear START=2026-04-01 END=2026-04-17
clear:
	docker compose exec -T airflow airflow tasks clear -y \
	  -s $(START) -e $(END) $(DAG_ID)

reset-pw:
	docker compose exec airflow \
		airflow users reset-password \
			--username admin --password admin

# --- Database ---
mongo-bash:
	docker compose exec mongodb mongosh crawler_db

pg-bash:
	docker compose exec postgres bash

# /opt/airflow/dags/
# /opt/airflow/logs/dag_id=geeknews/
airflow-bash:
	docker compose exec airflow bash

worker-bash:
	docker compose exec worker bash

pgsql:
	docker compose exec postgres psql -U airflow -d airflow

# docker compose exec postgres psql -U airflow -d airflow -c "DELETE FROM task_instance WHERE dag_id='geeknews';"  

init-net:
	docker network create -d bridge airflow-net
	docker network ls
