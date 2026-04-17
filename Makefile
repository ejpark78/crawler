# Variables
SOURCE ?= GeekNews
URL ?= https://news.hada.io/
DATE ?= $(shell date +%Y-%m-%d)
PAGE ?= 1
DAG_ID = geeknews

.PHONY: *

# --- Infrastructure ---

# Start all services
up:
	docker compose up -d

# Stop all services and remove containers
down:
	docker compose down

# Restart services
restart: down up

# Build the app image
build:
	docker compose build app

# View logs
logs:
	docker compose logs -f

# Access the app container shell
shell:
	docker compose exec app zsh

# --- Collection & Testing ---

# Single collection run (Local test)
# Example: make collect DATE=2026-04-16 PAGE=1
collect:
	docker run --rm \
	  -v $(shell pwd):/app \
	  --network crawler_default \
	  crawler-app:latest \
	  python -m app.main --source $(SOURCE) --url $(URL) --date $(DATE) --page $(PAGE)

# Airflow Backfill
# Example: make backfill START=2026-04-01 END=2026-04-17
backfill:
	docker compose exec airflow airflow dags backfill \
	  -s $(START) -e $(END) \
	  $(DAG_ID)

# Clear Airflow Task States
# Example: make clear START=2026-04-01 END=2026-04-17
clear:
	docker compose exec airflow airflow tasks clear \
	  -s $(START) -e $(END) \
	  $(DAG_ID)

init-pw:
	docker compose exec airflow airflow users reset-password \
	   --username admin \
	   --password admin
