"""
PyTorchKR 뉴스 수집 DAG

이 모듈은 PyTorch Korea 사이트의 데이터를 정기적으로 수집하기 위한 Airflow DAG을 정의합니다.

주요 기능:
1. Dynamic Task Mapping: PAGES 리스트(1~3페이지)를 기반으로 각 페이지 수집 태스크를 동적으로 생성하여 병렬 처리합니다.
2. Containerized Execution: BashOperator를 통해 독립된 워커 컨테이너(worker)에서 수집 로직을 실행하여 환경 격리를 보장합니다.
3. 실시간 증분 수집: 각 뉴스 항목별로 추출 즉시 MongoDB와 로컬 파일 시스템에 저장하는 구조를 지원합니다.
4. Backfill 및 Catchup: 과거 날짜에 대한 소급 수집이 가능하도록 설정되어 있습니다.

환경 변수:
- PYTORCH_KR_MAX_ACTIVE_RUNS: 동시 실행 가능한 DAG Run의 최대 개수 (기본값: 1)
- PYTORCH_KR_CONCURRENCY: DAG 내에서 동시 실행 가능한 태스크의 최대 개수 (기본값: 1)
"""
import os
from datetime import timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago

PAGES = list(range(1, 4))

with DAG(
    dag_id="pytorch_kr",
    start_date=days_ago(1),
    schedule_interval=timedelta(hours=2),
    catchup=False,
    tags=["Crawler", "PyTorchKR"],
    max_active_runs=int(os.getenv("PYTORCH_KR_MAX_ACTIVE_RUNS", 2)),
    concurrency=int(os.getenv("PYTORCH_KR_CONCURRENCY", 1)),
) as dag:
    dag.doc_md = """
    ### PyTorchKR 뉴스 수집 DAG (Dynamic Task Mapping)
    
    이 DAG은 [PyTorch 한국 사용자 모임](https://discuss.pytorch.kr/)의 최신 게시글과 토론 데이터를 수집합니다.
    
    **주요 특징:**
    - **Dynamic Task Mapping**: 최신 게시글 목록(1~3페이지)을 병렬 태스크로 매핑하여 효율적으로 수집합니다.
    - **Discourse API 연동**: 사이트의 JSON 엔드포인트를 활용하여 구조화된 게시글 목록을 추출합니다.
    - **콘텐츠 정문화**: 본문 내 이미지 알트 텍스트 치환, 라이트박스 메타데이터 추출 등 포럼 특화 파싱 로직이 적용되어 있습니다.
    
    **데이터 저장:**
    - **MongoDB**: `pytorch_kr` DB의 `list` 및 `contents` 컬렉션에 증분 저장
    - **Local Storage**: `volumes/pytorch_kr/` 하위에 실행 ID별 정밀 백업 생성
    
    **실행 주기:** 매일 정기적으로 포럼의 새로운 소식을 수집합니다.
    """

    # Dynamic Task Mapping: 실행 시점에 pages 리스트만큼 태스크가 동적으로 생성됨
    collect = BashOperator.partial(
        task_id="collect",
        execution_timeout=timedelta(hours=1),
        cwd="/app",
    ).expand(
        bash_command=[
            "docker compose run --rm worker uv run python -m app.main "
            f"--source PyTorchKR --page {p}"
            for p in PAGES
        ],
    )
