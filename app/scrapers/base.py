"""
BaseScraper 모듈

이 모듈은 모든 뉴스 크롤러의 기반이 되는 추상 기본 클래스(BaseScraper)를 정의합니다.
새로운 사이트를 추가할 때는 이 클래스를 상속받아 구현해야 합니다.

주요 추상 메서드:
- _do_fetch(url): 실제 HTTP 요청을 수행하여 HTML을 반환합니다.
- parse(html, db_connection): HTML을 파싱하여 NewsItem 객체 리스트를 생성합니다.

공통 기능:
- fetch(url): 요청 전 랜덤 딜레이(5~10초)를 부여하여 봇 탐지를 우회합니다.
- save(items, db_connection): 수집된 데이터를 MongoDB에 Upsert 방식으로 저장합니다.
- run(url, db_connection, ...): 전체 크롤링 프로세스(Fetch -> Parse -> Save)를 제어합니다.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
import time
import random
import logging
from app.models import NewsItem
from scrapling import StealthyFetcher
from bs4 import BeautifulSoup

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("BaseScraper")

class BaseScraper(ABC):
    """모든 크롤러의 추상 기본 클래스"""

    def __init__(self, source_name: str):
        self.source_name = source_name
        self.collection_name = f"{source_name.lower()}_pages"
        self.crawler = StealthyFetcher()

    def fetch(self, url: str) -> str:
        """웹 페이지 HTML을 가져오는 인터페이스 (요청 전 랜덤 딜레이 추가)"""
        delay = random.uniform(5, 10)
        logger.info(f"Waiting {delay:.2f}s before fetching {url}...")
        time.sleep(delay)
        return self._do_fetch(url)

    @abstractmethod
    def _do_fetch(self, url: str) -> str:
        """실제 HTML을 가져오는 내부 구현 메서드"""
        pass

    @abstractmethod
    def parse(self, html: str, db_connection=None) -> List[NewsItem]:
        """HTML을 파싱하여 NewsItem 리스트로 변환하는 인터페이스"""
        pass

    def save(self, items: List[NewsItem], db_connection, html: Optional[str] = None):
        """MongoDB에 데이터 저장 (Upsert 방식)"""
        if db_connection is None:
            logger.warning("Database connection is missing. Skipping database save.")
            return

        try:
            db = db_connection["crawler_db"]
            collection = db[self.collection_name]
        except Exception as e:
            logger.error(f"Failed to access database: {e}")
            return

        saved_count = 0
        for item in items:
            try:
                doc = item.model_dump(mode='json')
                doc.pop("json_ld_raw", None)
                doc["_id"] = item.url
                doc["html"] = html

                collection.update_one(
                    {"_id": item.url},
                    {"$set": doc},
                    upsert=True
                )
                saved_count += 1
            except Exception as e:
                logger.error(f"Failed to save item {item.url}: {e}")

        logger.info(f"Successfully saved {saved_count}/{len(items)} items to {self.collection_name} collection.")

    def run(self, url: str, db_connection, backfill_date: Optional[str] = None, page: Optional[int] = None) -> Tuple[List[NewsItem], str]:
        """전체 수집 프로세스 실행 (Backfill 및 페이지네이션 지원)"""
        print(f"Starting collection from {self.source_name}...")
        if backfill_date:
            print(f"Backfilling data for date: {backfill_date}, page: {page}")
            url = self._get_backfill_url(url, backfill_date, page=page)

        html = self.fetch(url)
        items = self.parse(html, db_connection=db_connection)
        self.save(items, db_connection, html)
        print(f"Successfully collected {len(items)} items from {self.source_name}.")
        return items, html

    def _get_backfill_url(self, base_url: str, date_str: str, page: Optional[int] = None) -> str:
        """날짜 및 페이지별 백필 URL 생성 (자식 클래스에서 오버라이드)"""
        return base_url
