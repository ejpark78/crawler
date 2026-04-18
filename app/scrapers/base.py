"""
BaseScraper 모듈

이 모듈은 모든 뉴스 크롤러의 근간이 되는 추상 기본 클래스(BaseScraper)를 정의합니다.
프로젝트 내의 모든 개별 사이트용 스크래퍼는 이 클래스를 상속받아 구현되어야 합니다.

핵심 기능:
1. 표준화된 수집 인터페이스 (run, fetch, save) 제공
2. 수집 매너 준수: 요청 전 임의 딜레이(Random Delay)를 통한 사이트 부하 방지
3. 관측 가능성(Observability): 모든 요청 URL 및 응답 HTML의 전수 아카이빙 (debug_path 설정 시)
4. 데이터 영속성: Pydantic 모델을 활용한 MongoDB Upsert 로직 내장
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
import json
import time
import random
import logging
import os
import hashlib
from app.models import NewsItem
from scrapling import StealthyFetcher
from bs4 import BeautifulSoup

# 로깅 설정
logger = logging.getLogger("BaseScraper")

class BaseScraper(ABC):
    """
    모든 크롤러가 상속받아야 하는 추상 기본 클래스.
    
    속성:
        source_name (str): 수집 대상 소스의 고유 명칭 (예: 'GeekNews')
        collection_name (str): MongoDB에 저장될 컬렉션 이름
        crawler (StealthyFetcher): 봇 탐지 우회를 위한 고급 HTTP 클라이언트
        debug_path (str): 수집 과정의 모든 원본 데이터를 저장할 로컬 디렉토리 경로
    """

    def __init__(self, source_name: str):
        """
        BaseScraper 초기화.
        
        Args:
            source_name (str): 수집 소스 이름
        """
        self.source_name = source_name
        self.collection_name = f"{source_name.lower()}_pages"
        self.crawler = StealthyFetcher()
        self.debug_path = None # main.py에서 동적으로 설정됨

    def fetch(self, url: str) -> str:
        """
        지정된 URL에서 HTML을 가져오고, 설정된 경우 디버그용 아카이브를 생성합니다.
        
        요청 전 5~10초 사이의 랜덤 딜레이를 적용하여 사이트 차단을 방지합니다.
        
        Args:
            url (str): 요청할 대상 URL
            
        Returns:
            str: 수집된 HTML 텍스트. 실패 시 빈 문자열 반환.
        """
        delay = random.uniform(5, 10)
        logger.info(f"Waiting {delay:.2f}s before fetching {url}...")
        time.sleep(delay)
        
        html = self._do_fetch(url)
        logger.debug(f"Fetched HTML from {url} (Length: {len(html)})")
        
        # 디버그 경로가 활성화된 경우 모든 요청의 흔적을 남김
        if self.debug_path:
            self._save_debug_html(url, html)
            
        return html

    def _save_debug_html(self, url: str, html: str):
        """
        수집된 원본 HTML과 URL 매핑 정보를 로컬 파일로 저장합니다.
        
        저장 구조:
            {debug_path}/htmls/{url_hash}.html
            {debug_path}/htmls/urls.txt (매핑 인덱스)
            
        Args:
            url (str): 원본 요청 URL
            html (str): 수집된 HTML 내용
        """
        try:
            html_dir = os.path.join(self.debug_path, "htmls")
            os.makedirs(html_dir, exist_ok=True)
            
            # URL 식별을 위한 MD5 해시 파일명 생성
            url_hash = hashlib.md5(url.encode()).hexdigest()
            filename = f"{url_hash}.html"
            file_path = os.path.join(html_dir, filename)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"<!-- Source URL: {url} -->\n")
                f.write(html)
            
            # URL 매핑 로그 기록 (append 모드)
            mapping_file = os.path.join(html_dir, "urls.txt")
            with open(mapping_file, 'a', encoding='utf-8') as f:
                f.write(f"{filename} | {url}\n")
                
            logger.debug(f"Archived debug HTML: {filename} for {url}")
        except Exception as e:
            logger.error(f"Failed to archive debug HTML for {url}: {e}")

    @abstractmethod
    def _do_fetch(self, url: str) -> str:
        """
        실제 HTTP 요청을 수행하는 내부 메서드. 하위 클래스에서 각 사이트 특성에 맞게 구현해야 합니다.
        (예: curl-cffi impersonation 사용 등)
        """
        pass

    @abstractmethod
    def parse(self, html: str, db_connection=None) -> List[NewsItem]:
        """
        수집된 HTML을 파싱하여 NewsItem 객체 리스트로 변환합니다.
        
        Args:
            html (str): 수집된 원본 HTML
            db_connection (MongoClient, optional): 중복 체크 등을 위한 DB 연결 객체
            
        Returns:
            List[NewsItem]: 파싱된 뉴스 항목 리스트
        """
        pass

    def save(self, items: List[NewsItem], db_connection, html: Optional[str] = None):
        """
        수집된 데이터를 MongoDB에 저장하거나 업데이트합니다.
        
        Upsert 방식을 사용하여 URL이 중복되는 경우 기존 데이터를 최신 상태로 갱신합니다.
        
        Args:
            items (List[NewsItem]): 저장할 항목 리스트
            db_connection (MongoClient): MongoDB 연결 객체
            html (str, optional): 상세 페이지가 아닌 목록 페이지의 원본 HTML (검증용)
        """
        # 개별 아이템에 원본 목록 HTML 바인딩 (사후 검증용)
        for item in items:
            item.html = html

        if db_connection is None:
            logger.warning("Database connection unavailable. Skipping persistence layer.")
            return

        try:
            db = db_connection["crawler_db"]
            collection = db[self.collection_name]
        except Exception as e:
            logger.error(f"DB access error: {e}")
            return

        saved_count = 0
        for item in items:
            try:
                # Pydantic 모델을 JSON 직렬화 가능 형식으로 변환
                doc = item.model_dump(mode='json')
                doc["_id"] = item.url # URL을 고유 ID로 설정하여 중복 방지
                
                collection.update_one(
                    {"_id": item.url},
                    {"$set": doc},
                    upsert=True
                )
                saved_count += 1
            except Exception as e:
                logger.error(f"Failed to upsert item {item.url}: {e}")

        logger.info(f"Persistence complete: {saved_count}/{len(items)} items processed in {self.collection_name}.")

    def run(self, url: str, db_connection, backfill_date: Optional[str] = None, page: Optional[int] = None) -> Tuple[List[NewsItem], str]:
        """
        수집, 파싱, 저장을 아우르는 전체 스크래핑 파이프라인을 실행합니다.
        
        Args:
            url (str): 시작 URL
            db_connection (MongoClient): 데이터 저장용 DB 연결 객체
            backfill_date (str, optional): 과거 데이터 수집 시 기준 날짜
            page (int, optional): 수집할 페이지 번호
            
        Returns:
            Tuple[List[NewsItem], str]: 수집된 아이템 리스트와 메인 HTML 원본
        """
        logger.info(f"Initializing scraping pipeline for {self.source_name}...")
        
        # 백필 요청인 경우 타겟 URL 생성 로직 실행
        if backfill_date:
            logger.info(f"Target set to Backfill - Date: {backfill_date}, Page: {page}")
            url = self._get_backfill_url(url, backfill_date, page=page)

        html = self.fetch(url)
        items = self.parse(html, db_connection=db_connection)
        self.save(items, db_connection, html)
        
        logger.info(f"Pipeline finished for {self.source_name}. Total {len(items)} items handled.")
        return items, html

    def _get_backfill_url(self, base_url: str, date_str: str, page: Optional[int] = None) -> str:
        """
        특정 날짜나 페이지에 해당하는 백필용 URL을 생성합니다. 
        기본 구현은 base_url을 그대로 반환하며, 사이트별 스크래퍼에서 오버라이드해야 합니다.
        """
        return base_url
