"""
Crawler CLI Entrypoint (Main)

이 모듈은 크롤러 프로젝트의 통합 실행 제어기입니다. CLI를 통해 스크래퍼를 구동하고, 실시간 증분 수집 방식으로 데이터를 저장합니다.

핵심 프로세스:
1. CLI 인자 파싱 및 실행 환경 설정 (Log Level 등)
2. 실시간 증분 저장 (Incremental Save): 수집 중단 시 데이터 손실을 방지하기 위해 각 항목을 추출 즉시 저장합니다.
3. 3-way Storage: 각 수집 항목을 세 가지 컬렉션(pages, html, comments)에 분산 저장하여 데이터 활용도를 높입니다.
4. 소스별 DB 격리: --source 인자 값을 기반으로 독립적인 MongoDB 데이터베이스를 자동 생성 및 연결합니다.
5. 계층적 로컬 아카이빙: --out_path 지정 시 DB 구조와 동일한 3개 디렉토리({source}_pages, {source}_htmls, {source})를 생성하여 파일로 백업합니다.

사용 예시:
    make test SOURCE=GeekNews DATE=2026-03-25 PAGE=1 LOG_LEVEL=DEBUG
"""
import argparse
import json
import logging
import os
import sys
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from app.scrapers.registry import SCRAPER_REGISTRY

# 기본 로깅 설정 (Stdout)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("Main")

def main():
    """
    CLI 인자를 분석하고 적절한 스크래퍼를 실행하는 메인 함수.
    
    지원하는 CLI 인자:
        --source (str): 스크래퍼 레지스트리에 등록된 소스명 (필수)
        --url (str): 수집 시작점인 베이스 URL (필수)
        --date (str): 백필 시 사용할 날짜 (YYYY-MM-DD 형식 권장)
        --page (int): 수집할 페이지 번호
        --out_path (str): 수집 결과를 파일로 저장할 루트 디렉토리 경로
    """
    parser = argparse.ArgumentParser(description="CLI Wrapper for Advanced Scrapers")
    parser.add_argument("--source", required=True, help="Source name from registry (e.g., GeekNews)")
    parser.add_argument("--url", required=True, help="Base URL to start scraping")
    parser.add_argument("--date", help="Target date for backfilling (YYYY-MM-DD)")
    parser.add_argument("--page", type=int, help="Target page number")
    parser.add_argument("--out_path", help="Local directory path to save structured output")

    args = parser.parse_args()

    # 환경 변수 LOG_LEVEL 처리 (기본값: INFO)
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.getLogger().setLevel(log_level)

    # 출력 경로 설정 및 파일 로깅 시스템 구축
    target_dir = None
    if args.out_path:
        # 몽고디비 구조를 본뜬 하위 폴더 구성: {out_path}/{Source}/{Collection}
        scraper_cls = SCRAPER_REGISTRY.get(args.source)
        if scraper_cls:
            # 임시 인스턴스 생성을 통해 collection_name 확인
            temp_scraper = scraper_cls()
            target_dir = args.out_path
            os.makedirs(target_dir, exist_ok=True)
            
            # 파일 핸들러 추가: 모든 로그를 out_path/crawler.log에도 기록
            log_file = os.path.join(target_dir, "crawler.log")
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))
            logging.getLogger().addHandler(file_handler)
            
            logger.info(f"Structured storage initialized at: {target_dir}")
            logger.info(f"Detailed logs being written to: {log_file}")
            
            # 스크래퍼에 디버그 데이터 저장용 경로 전달
            temp_scraper.debug_path = target_dir
            scraper = temp_scraper
        else:
            logger.error(f"Error: Scraper for source '{args.source}' is not registered.")
            sys.exit(1)
    else:
        # DB 저장만 수행하거나 출력 없이 실행하는 경우
        scraper_cls = SCRAPER_REGISTRY.get(args.source)
        if not scraper_cls:
            logger.error(f"Error: Scraper for source '{args.source}' is not registered.")
            sys.exit(1)
        scraper = scraper_cls()

    logger.info(f"System initialized. Log Level: {log_level}, Source: {args.source}")

    # MongoDB 서비스 연결 시도 (Timeout 2초)
    client = None
    db_conn = None
    try:
        # 도커 컴포즈 환경의 'mongodb' 호스트 연결
        client = MongoClient("mongodb://mongodb:27017/", serverSelectionTimeoutMS=2000)
        client.admin.command('ping') # 연결 유효성 즉시 확인
        db_conn = client
        logger.info("Successfully established connection to MongoDB.")
    except (ServerSelectionTimeoutError, Exception) as e:
        logger.warning(f"MongoDB connection failed: {e}. Data will only be saved locally if --out_path is set.")
        db_conn = None

    try:
        # 스크래퍼 실행 및 데이터 확보
        items, html = scraper.run(
            url=args.url,
            db_connection=db_conn,
            backfill_date=args.date,
            page=args.page
        )


    finally:
        # 리소스 정리
        if client:
            client.close()
            logger.debug("MongoDB connection closed.")

if __name__ == "__main__":
    main()
