import os
from datetime import timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago

PAGES = list(range(1, 6))

with DAG(
    dag_id="geeknews",
    start_date=days_ago(7),
    schedule_interval="@daily",
    catchup=True,
    tags=["Crawler", "GeekNews"],
    max_active_runs=int(os.getenv("GEEKNEWS_MAX_ACTIVE_RUNS", 1)),
    concurrency=int(os.getenv("GEEKNEWS_CONCURRENCY", 1)),
) as dag:
    dag.doc_str = "GeekNews 뉴스 수집 DAG (Dynamic Task Mapping)"

    # Dynamic Task Mapping: 실행 시점에 pages 리스트만큼 태스크가 동적으로 생성됨
    collect = BashOperator.partial(
        task_id="collect",
        execution_timeout=timedelta(hours=1),
    ).expand(
        bash_command=[
            "docker compose -f /app/docker/compose.worker.yml "
            "run --rm worker uv run python -m app.main "
            "--source GeekNews --url https://news.hada.io/ "
            f"--date {{{{ ds }}}} --page {p}"
            for p in PAGES
        ],
    )
