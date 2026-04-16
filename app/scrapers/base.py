from abc import ABC, abstractmethod
from typing import List, Optional
from app.models import NewsItem
from scrapling import StealthyFetcher

class BaseScraper(ABC):
    """모든 크롤러의 추상 기본 클래스"""

    def __init__(self, source_name: str):
        self.source_name = source_name
        # Scrapling의 Stealth 모드 사용
        self.crawler = StealthyFetcher()

    @abstractmethod
    def fetch(self, url: str) -> str:
        """웹 페이지 HTML을 가져오는 인터페이스"""
        pass

    @abstractmethod
    def parse(self, html: str) -> List[NewsItem]:
        """HTML을 파싱하여 NewsItem 리스트로 변환하는 인터페이스"""
        pass

    def save(self, items: List[NewsItem], db_collection):
        """MongoDB에 Upsert 방식으로 저장 (공통 로직)"""
        for item in items:
            db_collection.update_one(
                {"url": item.url},
                {"$set": item.model_dump()},
                upsert=True
            )

    def save_to_json(self, items: List[NewsItem], file_path: str):
        """수집된 데이터를 JSON 파일로 저장 (comments 필드는 제외하여 저장)"""
        import json
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
        import requests
        print(f"Using fallback simple fetch for {url}...")
        response = requests.get(url, headers=getattr(self, 'headers', {}), timeout=10)
        response.raise_for_status()
        return response.text

    def collect_sample_html(self, url: str, file_path: str):
        """테스트를 위한 샘플 HTML 수집 및 저장"""
        import os
        from bs4 import BeautifulSoup
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

    def run(self, url: str, db_collection, backfill_date: Optional[str] = None):
        """전체 수집 프로세스 실행 (Backfill 지원)"""
        print(f"Starting collection from {self.source_name}...")
        if backfill_date:
            print(f"Backfilling data for date: {backfill_date}")
            url = self._get_backfill_url(url, backfill_date)

        html = self.fetch(url)
        items = self.parse(html)
        self.save(items, db_collection)
        print(f"Successfully collected {len(items)} items from {self.source_name}.")

    def _get_backfill_url(self, base_url: str, date_str: str) -> str:
        """날짜별 백필 URL 생성 (자식 클래스에서 오버라이드)"""
        return base_url

