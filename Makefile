# Variables
SOURCE ?= GeekNews
URL ?= https://news.hada.io/
DATE ?= $(shell date +%Y-%m-%d)
PAGE ?= 1
DAG_ID = geeknews

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
	docker compose stats

# --- Collection & Testing ---
# Example: make collect DATE=2026-03-25 PAGE=1
collect:
	docker compose run \
		--rm -e PYTHONPATH=/app worker uv run python -m app.main \
		--source $(SOURCE) \
		--url $(URL) \
		--date $(DATE) \
		--page $(PAGE)

test:
	docker compose exec worker uv run pytest

# --- Airflow ---
# Example: make backfill START=2026-04-01 END=2026-04-17
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
