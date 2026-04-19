"""
GeekNews 뉴스 수집 DAG

이 모듈은 GeekNews 사이트의 데이터를 정기적으로 수집하기 위한 Airflow DAG을 정의합니다.

주요 기능:
1. Dynamic Task Mapping: PAGES 리스트(1~5페이지)를 기반으로 각 페이지 수집 태스크를 동적으로 생성하여 병렬 처리합니다.
2. Containerized Execution: BashOperator를 통해 독립된 워커 컨테이너(worker)에서 수집 로직을 실행하여 환경 격리를 보장합니다.
3. 실시간 증분 수집: 각 뉴스 항목별로 추출 즉시 MongoDB와 로컬 파일 시스템에 저장하는 구조를 지원합니다.
4. Backfill 및 Catchup: 과거 날짜에 대한 소급 수집이 가능하도록 설정되어 있습니다.

환경 변수:
- GEEKNEWS_MAX_ACTIVE_RUNS: 동시 실행 가능한 DAG Run의 최대 개수 (기본값: 1)
- GEEKNEWS_CONCURRENCY: DAG 내에서 동시 실행 가능한 태스크의 최대 개수 (기본값: 1)
"""
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
        cwd="/app",
    ).expand(
        bash_command=[
            "docker compose run --rm worker uv run python -m app.main "
            f"--source GeekNews --date {{{{ ds }}}} --page {p}"
            for p in PAGES
        ],
    )
