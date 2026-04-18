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
import json
import os
import re
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
        self.db_name = source_name.lower()
        self.collection_name = "pages"
        self.html_collection_name = "html"
        self.jsonld_collection_name = "comments"
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

    def save(self, item: NewsItem, db_connection, html: Optional[str] = None):
        """단일 데이터 저장 (로컬 파일 및 MongoDB)"""
        # 1. 로컬 파일 저장 로직 실행 (DB 연결 여부와 무관)
        if hasattr(self, 'debug_path') and self.debug_path:
            self._save_to_file(item)

        # 2. MongoDB 저장
        if db_connection is None:
            logger.warning("Database connection is missing. Skipping database save.")
            return

        try:
            db = db_connection[self.db_name]
            
            # 1. 페이지 정보 저장
            collection = db[self.collection_name]
            doc = item.model_dump(mode='json')
            doc.pop("json_ld_raw", None)
            collection.update_one(
                {"_id": item.url},
                {"$set": doc},
                upsert=True
            )

            # 2. HTML 원본 별도 저장
            if html:
                html_collection = db[self.html_collection_name]
                html_collection.update_one(
                    {"_id": item.url},
                    {"$set": {
                        "url": item.url,
                        "raw_html": html,
                        "created_at": doc.get("created_at")
                    }},
                    upsert=True
                )
            
            # 3. JSON-LD 별도 저장 (comments 컬렉션)
            if item.json_ld_raw:
                jsonld_collection = db[self.jsonld_collection_name]
                try:
                    json_data = json.loads(item.json_ld_raw)
                    # JSON-LD가 리스트인 경우 첫 번째 항목 사용
                    if isinstance(json_data, list) and len(json_data) > 0:
                        json_data = json_data[0]
                    
                    jsonld_collection.update_one(
                        {"_id": item.url},
                        {"$set": {
                            "url": item.url,
                            "json_ld": json_data,
                            "created_at": doc.get("created_at")
                        }},
                        upsert=True
                    )
                except Exception as e:
                    # JSON 파싱 실패 시 원본 문자열 저장
                    jsonld_collection.update_one(
                        {"_id": item.url},
                        {"$set": {
                            "url": item.url,
                            "json_ld_raw": item.json_ld_raw,
                            "created_at": doc.get("created_at")
                        }},
                        upsert=True
                    )
            
            logger.debug(f"Successfully saved item, HTML, and JSON-LD to {self.db_name} database.")
        except Exception as e:
            logger.error(f"Failed to save item {item.url}: {e}")

    def _save_to_file(self, item: NewsItem):
        """
        사용자 요청에 따른 3가지 경로 기반 파일 저장 구현:
        1. pages/{id}.json: 기본 정보
        2. htmls/{id}.html: 원문 HTML
        3. htmls/url.txt: URL 매핑
        4. comments/{id}.json: JSON-LD 정보
        """
        try:
            source_lower = self.source_name.lower()
            base_dir = os.path.join(self.debug_path, source_lower)
            
            # 디렉토리 생성
            pages_dir = os.path.join(base_dir, f"{source_lower}_pages")
            htmls_dir = os.path.join(base_dir, f"{source_lower}_htmls")
            jsonld_dir = os.path.join(base_dir, source_lower)
            
            for d in [pages_dir, htmls_dir, jsonld_dir]:
                os.makedirs(d, exist_ok=True)

            # ID 추출 (GeekNews 특화: id=NNNN)
            if 'id=' in item.url:
                item_id = item.url.split('id=')[-1].split('&')[0]
            else:
                # 외부 링크 등의 경우 URL 해시 사용
                import hashlib
                item_id = hashlib.md5(item.url.encode()).hexdigest()[:10]
            item_id = re.sub(r'[^\w\-]', '_', item_id)

            # 1. geeknews_pages/{id}.json
            page_path = os.path.join(pages_dir, f"{item_id}.json")
            with open(page_path, 'w', encoding='utf-8') as f:
                json.dump(item.model_dump(mode='json'), f, ensure_ascii=False, indent=2)

            # 2. geeknews_htmls/{id}.html 및 url.txt
            if item.html:
                html_path = os.path.join(htmls_dir, f"{item_id}.html")
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(item.html)
                
                # url.txt 기록 (append)
                url_list_path = os.path.join(htmls_dir, "url.txt")
                with open(url_list_path, 'a', encoding='utf-8') as f:
                    f.write(f"{item_id}.html | {item.url}\n")

            # 3. geeknews/{id}.json (JSON-LD)
            if item.json_ld_raw:
                jsonld_path = os.path.join(jsonld_dir, f"{item_id}.json")
                try:
                    json_data = json.loads(item.json_ld_raw)
                    # JSON-LD가 리스트인 경우 첫 번째 항목 사용
                    if isinstance(json_data, list) and len(json_data) > 0:
                        json_data = json_data[0]
                    with open(jsonld_path, 'w', encoding='utf-8') as f:
                        json.dump(json_data, f, ensure_ascii=False, indent=2)
                except:
                    with open(jsonld_path, 'w', encoding='utf-8') as f:
                        f.write(item.json_ld_raw)

            logger.debug(f"Local file persistence completed for item: {item_id}")
        except Exception as e:
            logger.error(f"Failed to save local file: {e}")

    def run(self, url: str, db_connection, backfill_date: Optional[str] = None, page: Optional[int] = None) -> Tuple[List[NewsItem], str]:
        """전체 수집 프로세스 실행 (Backfill 및 페이지네이션 지원)"""
        print(f"Starting collection from {self.source_name}...")
        if backfill_date:
            print(f"Backfilling data for date: {backfill_date}, page: {page}")
            url = self._get_backfill_url(url, backfill_date, page=page)

        html = self.fetch(url)
        items = self.parse(html, db_connection=db_connection)
        print(f"Successfully collected {len(items)} items from {self.source_name}.")
        return items, html

    def _get_backfill_url(self, base_url: str, date_str: str, page: Optional[int] = None) -> str:
        """날짜 및 페이지별 백필 URL 생성 (자식 클래스에서 오버라이드)"""
        return base_url
