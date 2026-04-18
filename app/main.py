"""
Crawler Main Entry Point

이 모듈은 크롤러 프로젝트의 메인 실행 진입점(CLI Wrapper)입니다.
등록된 스크래퍼를 호출하고, 수집된 데이터를 MongoDB 또는 로컬 파일로 저장하는 역할을 수행합니다.

주요 인자:
- --source: 실행할 스크래퍼 이름 (예: GeekNews)
- --url: 수집 대상 베이스 URL
- --date: 과거 데이터 수집 시 사용할 날짜 (YYYY-MM-DD)
- --page: 수집할 페이지 번호
- --out_path: 결과를 저장할 로컬 JSON 파일 경로 (옵션)

특징:
1. 유연한 저장소 관리: MongoDB 연결에 실패하더라도 크롤링 프로세스는 중단되지 않으며, --out_path가 지정된 경우 파일 저장을 우선적으로 수행합니다.
2. 예외 처리: DB 서버 타임아웃 설정을 통해 인프라 장애 시에도 데이터 수집 안정성을 보장합니다.
"""
import argparse
import json
import logging
import os
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from app.scrapers.registry import SCRAPER_REGISTRY

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger("Main")

def main():
    parser = argparse.ArgumentParser(description="CLI Wrapper for Scrapers")
    parser.add_argument("--source", required=True, help="Source name from registry")
    parser.add_argument("--url", required=True, help="Base URL")
    parser.add_argument("--date", help="Backfill date (YYYY-MM-DD)")
    parser.add_argument("--page", type=int, help="Page number")
    parser.add_argument("--out_path", help="Path to save output as JSON file")

    args = parser.parse_args()

    scraper_cls = SCRAPER_REGISTRY.get(args.source)
    if not scraper_cls:
        logger.error(f"Scraper for {args.source} not found")
        exit(1)

    scraper = scraper_cls()

    # MongoDB 연결 시도 (타임아웃 설정)
    client = None
    db_conn = None
    try:
        # 도커 환경이 아닐 경우를 대비해 localhost와 mongodb 호스트 시도 가능하나 일단 mongodb 고정
        client = MongoClient("mongodb://mongodb:27017/", serverSelectionTimeoutMS=2000)
        # 연결 확인을 위해 간단한 명령 실행
        client.admin.command('ping')
        db_conn = client
        logger.info("Successfully connected to MongoDB.")
    except (ServerSelectionTimeoutError, Exception) as e:
        logger.warning(f"Could not connect to MongoDB: {e}. Proceeding without database save.")
        db_conn = None

    try:
        # 크롤링 실행
        items, html = scraper.run(
            url=args.url,
            db_connection=db_conn,
            backfill_date=args.date,
            page=args.page
        )

        # 파일 저장 옵션이 있는 경우
        if args.out_path:
            try:
                # NewsItem 리스트를 딕셔너리 리스트로 변환
                data_to_save = [item.model_dump(mode='json') for item in items]
                
                # 디렉토리 생성
                os.makedirs(os.path.dirname(os.path.abspath(args.out_path)), exist_ok=True)
                
                with open(args.out_path, 'w', encoding='utf-8') as f:
                    json.dump(data_to_save, f, ensure_ascii=False, indent=2)
                logger.info(f"Successfully saved results to {args.out_path}")
            except Exception as e:
                logger.error(f"Failed to save results to file: {e}")

    finally:
        if client:
            client.close()

if __name__ == "__main__":
    main()
