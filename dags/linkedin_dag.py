"""
LinkedIn 피드 및 댓글 상세 수집 DAG

이 모듈은 LinkedIn의 메인 피드 데이터와 각 게시물에 달린 상세 댓글을 정기적으로 수집하기 위한 
Airflow DAG을 정의합니다. Playwright(Chromium) 기반의 브라우저 자동화 기술을 사용하여 
동적인 소셜 미디어 콘텐츠를 지능적으로 추출합니다.

주요 아키텍처 및 특징:
1. 브라우저 자동화 (Playwright): 동적 로딩되는 LinkedIn 피드와 레이지 로딩(Lazy Loading)되는 
   댓글 섹션을 수집하기 위해 헤드리스 브라우저 환경을 활용합니다.
2. 세션 기반 수집: MongoDB(`linkedin.config`)에 저장된 로그인 세션(session.json) 정보를 
   동기화하여 자동 로그인을 수행하고, 수집 완료 후 최신 쿠키 상태를 다시 백업합니다.
3. 지능형 스크롤링: 사용자 동작을 모방한 스무스 스크롤링을 통해 피드를 확장하고, 
   추가적인 데이터(URN, 본문, 반응도 등)를 탐색합니다.
4. 3-Way 저장 구조: 
   - 정제된 데이터: `linkedin.pages` 컬렉션에 URN 식별자 기반으로 저장
   - 원본 HTML 스냅샷: `linkedin.pages_html` 컬렉션에 분석용으로 별도 보존
   - 로컬 백업: `volumes/linkedin/` 경로에 실행 ID별 파일 저장
5. 안정성 제어: 계정 보호 및 리소스 관리를 위해 동시 실행을 1개로 제한(`max_active_runs=1`)하며, 
   충분한 실행 타임아웃을 제공합니다.

환경 변수 및 설정:
- LINKEDIN_TOTAL_SCROLLS: 수집 깊이를 결정하는 총 스크롤 횟수 (기본값: 30)
- DOCKER_MODE: 도커 컨테이너 최적화 환경 설정 (기본값: true)
- HEADLESS: 브라우저 가시화 여부 설정 (기본값: true)
"""
import os
from datetime import timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago

# LinkedIn 수집 설정
TOTAL_SCROLLS = os.getenv("LINKEDIN_TOTAL_SCROLLS", "30")

default_args = {
    'owner': 'antigravity',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id="linkedin_feed",
    default_args=default_args,
    start_date=days_ago(1),
    schedule_interval="@daily",
    catchup=False,
    tags=["Crawler", "LinkedIn", "Browser"],
    max_active_runs=1,
    concurrency=1,
) as dag:
    dag.doc_md = """
    ### LinkedIn 메인 피드 및 상세 댓글 수집 DAG
    
    이 DAG은 Playwright(Chromium)를 사용하여 LinkedIn의 메인 피드를 수집합니다.
    
    **주요 설정:**
    - `TOTAL_SCROLLS`: 피드 수집 시 스크롤 횟수 (기본 30회)
    - `DOCKER_MODE`: 브라우저 실행 옵션 최적화
    - `HEADLESS`: GUI 없이 실행
    
    **브라우저 세션:**
    - MongoDB: `linkedin.config.session`

    **수집 데이터:**
    - MongoDB: `linkedin.pages`, `linkedin.pages_html`
    - Local: `volumes/linkedin/` 하위
    """

    collect_task = BashOperator(
        task_id="collect_linkedin_feed",
        bash_command=(
            "docker compose run --rm "
            "-e DOCKER_MODE=true "
            "-e HEADLESS=true "
            "-e TOTAL_SCROLLS={{ params.total_scrolls }} "
            "worker uv run python -m app.main --source LinkedIn"
        ),
        params={
            "total_scrolls": TOTAL_SCROLLS
        },
        execution_timeout=timedelta(hours=2),
        cwd="/app",
    )
