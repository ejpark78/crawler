# Variables
SOURCE ?= GeekNews
URL ?= https://news.hada.io/
DATE ?= $(shell date +%Y-%m-%d)
PAGE ?= 1
DAG_ID = geeknews

.PHONY: *

# --- Ollama ---
login:
	ollama login

logout:
	ollama signout

claude:
	ollama launch claude --model gemma4:31b-cloud

# --- Infrastructure ---

# Start all services
up:
	docker compose --profile airflow up -d

# Stop all services and remove containers
down:
	docker compose --profile airflow down

# Restart services
restart: down up

# Build the app image
build:
	docker compose --profile airflow build
	docker compose --profile worker build

# View logs
logs:
	docker compose --profile airflow logs -f

# --- Collection & Testing ---

# Single collection run (Local test)
# Example: make collect DATE=2026-03-25 PAGE=1
collect:
	docker compose --profile worker run \
		--rm -e PYTHONPATH=/app worker uv run python -m app.main \
		--source $(SOURCE) \
		--url $(URL) \
		--date $(DATE) \
		--page $(PAGE)

# Run tests inside the app container
test:
	docker compose --profile worker exec worker uv run pytest

# --- Airflow ---

# Airflow Backfill
# Example: make backfill START=2026-04-01 END=2026-04-17
backfill:
	docker compose --profile airflow exec airflow airflow dags backfill \
	  -s $(START) -e $(END) $(DAG_ID)

# Clear Airflow Task States
# Example: make clear START=2026-04-01 END=2026-04-17
clear:
	docker compose --profile airflow exec -T airflow airflow tasks clear -y \
	  -s $(START) -e $(END) $(DAG_ID)

# Reset Airflow admin password
init-pw:
	docker compose --profile airflow exec airflow users reset-password \
		--username admin --password admin

# --- Database ---

# Access MongoDB shell
mongo-shell:
	docker compose --profile worker exec mongodb mongosh crawler_db

# Access PostgreSQL shell
pg-shell:
	docker compose --profile airflow exec postgres bash
# 	docker compose exec postgres psql -U airflow -d airflow

airflow-bash:
	docker compose --profile airflow exec airflow bash

worker-bash:
	docker compose --profile worker exec worker bash
