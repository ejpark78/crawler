from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
import os

from app.scrapers.registry import SCRAPER_REGISTRY
from dags.utils.pg_helper import get_pg_connection, release_pg_connection


# --- 설정 영역 ---
# 수집 대상 소스와 각 소스별 수집할 페이지 범위 설정
# (소스명, 기본URL, 페이지범위)
SOURCES_CONFIG = {
    "GeekNews": {
        "base_url": "https://news.hada.io/",
        "pages": list(range(1, 6))  # 보통 1~5페이지까지 수집
    },
    # 신규 소스 추가 시 여기에 설정 추가
}

COLLECTION_NAME = "news_items"
# ----------------

def collect_news_task(source_name, page, logical_date, **context):
    """
    특정 소스의 특정 페이지 데이터를 수집하여 PostgreSQL에 저장하는 워커 함수
    """
    print(f"Executing collection for {source_name} - Page {page} - Date {logical_date}")

    # 1. 레지스트리에서 스크래퍼 클래스 가져오기
    scraper_cls = SCRAPER_REGISTRY.get(source_name)
    if not scraper_cls:
        raise ValueError(f"Scraper for {source_name} not found in registry.")

    scraper = scraper_cls()

    # 2. PostgreSQL 연결
    conn = get_pg_connection()

    # 3. 수집 실행
    base_url = SOURCES_CONFIG[source_name]["base_url"]
    ds = context.get('ds')

    try:
        scraper.run(
            url=base_url,
            db_connection=conn,
            backfill_date=ds,
            page=page
        )
    except Exception as e:
        print(f"Error collecting {source_name} page {page} for date {ds}: {e}")
        raise e
    finally:
        release_pg_connection(conn)

# DAG 정의
with DAG(
    dag_id="news_collection_pipeline",
    start_date=days_ago(7), # 최근 7일부터 백필 시작
    schedule_interval="@daily",
    catchup=True,            # 과거 누락 데이터 자동 수집 활성화
    tags=["crawler", "news"],
    doc_string="다양한 소스로부터 뉴스를 수집하는 동적 DAG"
) as dag:

    # 소스별, 페이지별로 태스크 동적 생성
    # (Airflow 2.3+ Dynamic Task Mapping을 사용할 수도 있으나,
    #  설정의 유연성을 위해 현재는 명시적 루프로 생성)
    for source_name, config in SOURCES_CONFIG.items():
        for page_num in config["pages"]:
            task_id = f"collect_{source_name.lower()}_p{page_num}"

            PythonOperator(
                task_id=task_id,
                python_callable=collect_news_task,
                op_kwargs={
                    "source_name": source_name,
                    "page": page_num,
                }
            )
