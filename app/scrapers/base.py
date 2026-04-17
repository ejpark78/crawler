from abc import ABC, abstractmethod
from typing import List, Optional
import time
import random
import logging
from app.models import NewsItem
from scrapling import StealthyFetcher
from bs4 import BeautifulSoup
from curl_cffi import requests
import json
import requests
import os

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
        delay = random.uniform(1, 3)
        logger.info(f"Waiting {delay:.2f}s before fetching {url}...")
        time.sleep(delay)
        return self._do_fetch(url)

    @abstractmethod
    def _do_fetch(self, url: str) -> str:
        """실제 HTML을 가져오는 내부 구현 메서드"""
        pass

    @abstractmethod
    def parse(self, html: str) -> List[NewsItem]:
        """HTML을 파싱하여 NewsItem 리스트로 변환하는 인터페이스"""
        pass

    def save(self, items: List[NewsItem], db_connection, html: Optional[str] = None):
        """MongoDB에 데이터 저장 (Upsert 방식)"""
        db = db_connection["crawler_db"]
        collection = db[self.collection_name]

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

    def save_to_json(self, items: List[NewsItem], file_path: str):
        """수집된 데이터를 JSON 파일로 저장 (comments 필드는 제외하여 저장)"""
        data = []
        for item in items:
            item_dict = item.model_dump()
            # comments 필드는 별도 파일(예: comment_sample.json)로 관리하므로 메인 JSON에서는 제외
            item_dict.pop('comments', None)
            data.append(item_dict)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4, default=str)
        print(f"Saved {len(items)} items (excluding comments) to {file_path}")

    def fetch_simple(self, url: str) -> str:
        """브라우저 없이 HTTP 요청만으로 HTML을 가져오는 가벼운 메서드 (Fallback용)"""
        print(f"Using fallback simple fetch for {url}...")
        response = requests.get(url, headers=getattr(self, 'headers', {}), timeout=10)
        response.raise_for_status()
        return response.text

    def collect_sample_html(self, url: str, file_path: str):
        """테스트를 위한 샘플 HTML 수집 및 저장"""
        print(f"Collecting sample HTML from {url}...")
        try:
            html = self.fetch(url)
        except Exception as e:
            print(f"Stealth fetch failed: {e}. Trying fallback simple fetch...")
            try:
                html = self.fetch_simple(url)
            except Exception as e2:
                print(f"Simple fetch also failed: {e2}")
                return

        # Ensure html is a string and not empty
        html_content = str(html) if html is not None else ""
        content_len = len(html_content)
        print(f"Fetched HTML length: {content_len} characters")

        # 1차 검증: 최소 길이 및 HTML 태그 확인
        if content_len < 500 or "<html" not in html_content.lower():
            print(f"Warning: Fetched HTML is too short or invalid for {url}")
            return

        # 2차 검증: 실제 데이터(뉴스 항목)가 존재하는지 확인
        # 자식 클래스의 parse 메서드를 활용하여 데이터 추출 시도
        try:
            items = self.parse(html_content)
            if not items:
                print(f"Warning: No news items found in the HTML for {url}. Likely a bot-block page.")
                return
            print(f"Verified: {len(items)} news items found. This is a valid sample.")
        except Exception as e:
            print(f"Verification failed during parsing: {e}")
            return

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            f.flush()
            os.fsync(f.fileno())

        os.chmod(file_path, 0o666)
        print(f"Sample HTML successfully saved to {file_path} ({content_len} bytes)")

    def run(self, url: str, db_connection, backfill_date: Optional[str] = None, page: Optional[int] = None):
        """전체 수집 프로세스 실행 (Backfill 및 페이지네이션 지원)"""
        print(f"Starting collection from {self.source_name}...")
        if backfill_date:
            print(f"Backfilling data for date: {backfill_date}, page: {page}")
            url = self._get_backfill_url(url, backfill_date, page=page)

        html = self.fetch(url)
        items = self.parse(html)
        self.save(items, db_connection, html)
        print(f"Successfully collected {len(items)} items from {self.source_name}.")

    def _get_backfill_url(self, base_url: str, date_str: str, page: Optional[int] = None) -> str:
        """날짜 및 페이지별 백필 URL 생성 (자식 클래스에서 오버라이드)"""
        return base_url

