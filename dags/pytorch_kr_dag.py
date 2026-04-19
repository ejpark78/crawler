"""
PyTorchKR 뉴스 수집 DAG

이 모듈은 PyTorch Korea 사이트의 데이터를 정기적으로 수집하기 위한 Airflow DAG을 정의합니다.

주요 기능:
1. Dynamic Task Mapping: PAGES 리스트(1~5페이지)를 기반으로 각 페이지 수집 태스크를 동적으로 생성하여 병렬 처리합니다.
2. Containerized Execution: BashOperator를 통해 독립된 워커 컨테이너(worker)에서 수집 로직을 실행하여 환경 격리를 보장합니다.
3. 실시간 증분 수집: 각 뉴스 항목별로 추출 즉시 MongoDB와 로컬 파일 시스템에 저장하는 구조를 지원합니다.
4. Backfill 및 Catchup: 과거 날짜에 대한 소급 수집이 가능하도록 설정되어 있습니다.

환경 변수:
- PYTORCH_KR_MAX_ACTIVE_RUNS: 동시 실행 가능한 DAG Run의 최대 개수 (기본값: 1)
- PYTORCH_KR_CONCURRENCY: DAG 내에서 동시 실행 가능한 태스크의 최대 개수 (기본값: 1)
"""
from datetime import timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import ShortCircuitOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.utils.dates import days_ago

with DAG(
    dag_id="pytorch_kr",
    start_date=days_ago(1),
    schedule_interval=None,  # Recursive DAGs are usually triggered manually or via start_date
    catchup=False,
    tags=["Crawler", "PyTorchKR", "Recursive"],
    max_active_runs=1,
) as dag:
    dag.doc_str = "PyTorchKR 뉴스 수집 DAG (Recursive Pagination)"

    # Get current page from dag_run.conf (default to 1)
    page = "{{ dag_run.conf.get('page', 1) }}"

    # 1. Collect specific page
    collect = BashOperator(
        task_id="collect",
        bash_command=(
            "docker compose run --rm worker uv run python -m app.main "
            f"--source PyTorchKR --page {page}"
        ),
        cwd="/app",
        do_xcom_push=True,
    )

    # 2. Check if we should continue (items found > 0)
    def _check_continuation(ti):
        # Capture the last line of stdout which contains RESULT_COUNT
        output = ti.xcom_pull(task_ids='collect')
        if not output:
            return False
        
        import re
        match = re.search(r"RESULT_COUNT: (\d+)", output)
        if match:
            count = int(match.group(1))
            return count > 0
        return False

    check = ShortCircuitOperator(
        task_id="check_more_data",
        python_callable=_check_continuation,
    )

    # 3. Trigger next page
    trigger_next = TriggerDagRunOperator(
        task_id="trigger_next_page",
        trigger_dag_id="pytorch_kr",
        conf={"page": "{{ (dag_run.conf.get('page', 1) | int) + 1 }}"},
    )

    collect >> check >> trigger_next
