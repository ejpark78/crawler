"""
크롤러 통합 컨트롤러 및 CLI 엔트리포인트 (Main)

이 모듈은 프로젝트의 핵심 실행 엔진으로, CLI 인자를 분석하여 적절한 스크래퍼를 구동하고
수집된 데이터를 실시간으로 증분 저장하는 컨트롤러 역할을 수행합니다.

주요 처리 프로세스:
1. 하이브리드 실행 엔진: 
   - 동기(Sync) 및 비동기(Async) 스크래퍼를 모두 지원합니다. 
   - `inspect` 모듈을 사용하여 스크래퍼의 `run` 메서드 타입을 자동으로 판별하고 
     필요시 `asyncio` 루프를 통해 실행합니다.
2. 3-Way 멀티 레이어 저장:
   - Pages: 정제된 구조화 데이터 저장 (검색 및 분석용)
   - HTML: 원본 소스 코드 저장 (데이터 재추출 및 검증용)
   - Comments: 상세 댓글 및 피드백 데이터 분리 보존
3. 소스 기반 데이터 격리:
   - `--source` 인자에 따라 독립적인 MongoDB 데이터베이스를 자동으로 생성하고 연결합니다.
4. 실시간 증분 수집 (Incremental Save):
   - 전체 수집이 완료될 때까지 기다리지 않고, 항목별 파싱 즉시 DB에 반영하여 
     네트워크 장애 등에 따른 데이터 유실을 최소화합니다.
5. 계층적 로컬 아카이빙:
   - `--out_path` 지정 시, DB 외에도 로컬 파일 시스템에 구조화된 디렉토리 형태로 
     데이터를 백업합니다.

실행 예시:
    docker compose run --rm -v .:/app -w /app uv run python -m app.main --source LinkedIn --page 1
    docker compose run --rm -v .:/app -w /app uv run python -m app.main --source GeekNews --date 2026-04-20 --page 1
"""
import argparse
import logging
import os
import sys
import asyncio
import inspect
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from app.scrapers.registry import SCRAPER_REGISTRY

# Default logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("Main")

def main():
    """
    CLI 인자를 분석하여 등록된 스크래퍼를 실행하고 수집 프로세스를 제어합니다.

    동작 순서:
    1. CLI 인자 파싱: 수집 대상(source), 날짜, 페이지 등 설정 로드
    2. 환경 변수 적용: LOG_LEVEL 등을 통한 로깅 세부 설정
    3. 스크래퍼 초기화: SCRAPER_REGISTRY에서 적절한 클래스를 찾아 인스턴스화
    4. DB 연결: 해당 소스 전용 MongoDB 데이터베이스 연결 및 컬렉션 준비
    5. 실행(Run): 동기/비동기 방식을 자동 판별하여 스크래퍼 구동
    6. 결과 출력: 수집된 아이템 개수 및 상태 보고

    Args:
        --source (str): 수집 대상 소스 이름 (필수: LinkedIn, GeekNews, PyTorchKR 등)
        --date (str): 과거 데이터 소급 수집 시 대상 날짜 (YYYY-MM-DD 형식)
        --page (int): 수집할 페이지 번호 (기본값: 1)
        --out_path (str): 수집 결과를 파일로 저장할 로컬 루트 디렉토리 경로
    """
    parser = argparse.ArgumentParser(description="고급 뉴스 및 소셜 미디어 크롤러 통합 CLI")
    parser.add_argument("--source", required=True, help="스크래퍼 레지스트리에 등록된 소스 이름 (예: LinkedIn, GeekNews)")
    parser.add_argument("--date", help="수집 대상 날짜 (YYYY-MM-DD)")
    parser.add_argument("--page", type=int, default=1, help="수집 대상 페이지 번호 (기본값: 1)")
    parser.add_argument("--out_path", help="구조화된 결과를 저장할 로컬 디렉토리 경로")

    args = parser.parse_args()

    # Handle LOG_LEVEL from environment variable
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.getLogger().setLevel(log_level)

    # Initialize scraper and local storage
    scraper_cls = SCRAPER_REGISTRY.get(args.source)
    if not scraper_cls:
        logger.error(f"Error: Scraper for source '{args.source}' is not registered.")
        sys.exit(1)

    scraper = scraper_cls()

    if args.out_path:
        target_dir = args.out_path
        os.makedirs(target_dir, exist_ok=True)

        # Log all activities to crawler.log in the target directory
        log_file = os.path.join(target_dir, "crawler.log")
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))
        logging.getLogger().addHandler(file_handler)

        logger.info(f"Structured storage initialized at: {target_dir}")
        logger.info(f"Detailed logs being written to: {log_file}")
        scraper.debug_path = target_dir

    logger.info(f"System initialized. Log Level: {log_level}, Source: {args.source}")

    # MongoDB connection attempt (2s timeout)
    client = None
    db_conn = None
    try:
        client = MongoClient("mongodb://mongodb:27017/", serverSelectionTimeoutMS=2000)
        client.admin.command('ping')
        db_conn = client
        logger.info("Successfully established connection to MongoDB.")
    except (ServerSelectionTimeoutError, Exception) as e:
        logger.warning(f"MongoDB connection failed: {e}. Data will only be saved locally if --out_path is set.")
        db_conn = None

    try:
        # Execution
        run_result = scraper.run(
            db_connection=db_conn,
            backfill_date=args.date,
            page=args.page
        )
        
        # Handle both sync and async scrapers
        if inspect.iscoroutine(run_result):
            items, _ = asyncio.run(run_result)
        else:
            items, _ = run_result
            
        # Output result for Airflow XCom capture
        print(f"RESULT_COUNT: {len(items)}")
    finally:
        if client:
            client.close()
            logger.debug("MongoDB connection closed.")

if __name__ == "__main__":
    main()
