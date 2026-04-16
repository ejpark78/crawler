from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.utils.dates import days_ago
import os

# --- 설정 영역 ---
SOURCES_CONFIG = {
    "GeekNews": {
        "base_url": "https://news.hada.io/",
        "pages": list(range(1, 6))
    },
}

# ----------------

with DAG(
    dag_id="news_collection_pipeline",
    start_date=days_ago(7),
    schedule_interval="@daily",
    catchup=True,
    tags=["crawler", "news"],
    max_active_runs=1,  # 한 번에 하나의 실행 회차(날짜)만 처리하여 서버 부하 및 차단 방지
    concurrency=1,      # 한 날짜 내에서도 페이지 수집 태스크를 순차적으로 처리하여 요청 간격 확보
) as dag:
    dag.doc_str = "다양한 소스로부터 뉴스를 수집하는 동적 DAG (DockerOperator-based)"

    for source_name, config in SOURCES_CONFIG.items():
        for page_num in config["pages"]:
            task_id = f"collect_{source_name.lower()}_p{page_num}"

            # DockerOperator는 새 컨테이너를 띄워 명령을 실행합니다.
            # uv run python -m app.main 명령어를 통해 수집 수행
            DockerOperator(
                task_id=task_id,
                image="crawler-app:latest",
                command=f"uv run python -m app.main --source {source_name} --url {config['base_url']} --date {{{{ ds }}}} --page {page_num}",
                docker_url="unix://var/run/docker.sock",
                network_mode="crawler_default",
                mounts=[
                    {"source": "/home/ejpark/workspace/crawler", "target": "/app", "type": "bind"}
                ],
                working_dir="/app",
                do_xcom_push=False
            )
