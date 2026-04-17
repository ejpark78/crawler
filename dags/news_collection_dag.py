from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
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
    dag_id="geeknews",
    start_date=days_ago(7),
    schedule_interval="@daily",
    catchup=True,
    tags=["crawler", "news"],
    max_active_runs=1,
    concurrency=1,
) as dag:
    dag.doc_str = "다양한 소스로부터 뉴스를 수집하는 동적 DAG (BashOperator-based)"

    for source_name, config in SOURCES_CONFIG.items():
        for page_num in config["pages"]:
            task_id = f"collect_{source_name.lower()}_p{page_num}"

            # 이미 실행 중인 crawler_app 컨테이너에 명령어를 전달하는 방식
            # 이 방식은 DockerOperator의 컨테이너 생성 오버헤드와 권한 문제를 완전히 우회합니다.
            bash_command = (
                f"docker exec crawler_app uv run python -m app.main "
                f"--source {source_name} "
                f"--url {config['base_url']} "
                f"--date {{{{ ds }}}} "
                f"--page {page_num}"
            )

            BashOperator(
                task_id=task_id,
                bash_command=bash_command
            )