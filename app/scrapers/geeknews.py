"""
GeekNewsScraper 모듈

이 모듈은 GeekNews(https://news.hada.io) 사이트의 뉴스를 수집하는 전용 크롤러를 구현합니다.

주요 특징:
1. JSON-LD 및 HTML 하이브리드 수집: 상세 페이지의 댓글 데이터를 수집할 때 JSON-LD 구조화 데이터를 우선적으로 활용하며, 데이터가 없거나 불완전할 경우 HTML 스크래핑(Fallback)을 수행합니다.
2. 중복 방지 로직: 리스트 파싱 과정에서 MongoDB를 조회하여 이미 수집된 항목인 경우 상세 페이지(댓글) 수집을 건너뜁니다.
3. 다양한 URL 패턴 지원: 페이지 번호 기반 수집 외에도 특정 날짜(YYYY-MM-DD)나 '예전글' 패턴에 대응하는 URL 생성 로직을 포함합니다.
4. 보안 수집: curl-cffi의 Impersonate 기능을 사용하여 Chrome 브라우저의 요청으로 위장, 봇 차단을 우회합니다.
"""
import json
import logging
import re
from typing import List, Optional, Tuple
from bs4 import BeautifulSoup
from curl_cffi import requests

from app.scrapers.base import BaseScraper
from app.models import NewsItem, CommentItem

logger = logging.getLogger("GeekNewsScraper")

class GeekNewsScraper(BaseScraper):
    def __init__(self):
        super().__init__(source_name="GeekNews")
        self.base_url = "https://news.hada.io"

    def _do_fetch(self, url: str) -> str:
        """실제 네트워크 요청 수행 (curl-cffi 활용)"""
        logger.info(f"Fetching {url} using curl-cffi (Impersonating Chrome)...")
        try:
            response = requests.get(url, impersonate="chrome", timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Network error while fetching {url}: {e}")
            return ""

    def scrape(self, date_str: str = "1", db_connection=None) -> List[NewsItem]:
        """GeekNews를 크롤링합니다."""
        url = self._get_backfill_url(self.base_url, date_str)
        html = self.fetch(url)
        if not html:
            return []
        return self.parse(html, db_connection=db_connection)

    def parse(self, html: str, db_connection=None) -> List[NewsItem]:
        """GeekNews 리스트 페이지를 파싱합니다."""
        soup = BeautifulSoup(html, 'html.parser')
        items = []
        
        collection = None
        if db_connection is not None:
            collection = db_connection[self.db_name][self.collection_name]

        rows = soup.select('div.topic_row')
        for row in rows:
            try:
                title_element = row.select_one('.topictitle a')
                if not title_element: continue
                
                title = title_element.get_text(strip=True)
                url = title_element.get('href', '')
                if not (title and url): continue

                if url and not url.startswith('http'):
                    # /로 시작하든 아니든 절대 경로로 변환
                    url = f"https://news.hada.io/{url.lstrip('/')}"
                
                # 정보 추출
                desc_element = row.select_one('.topicdesc')
                content = desc_element.get_text(strip=True) if desc_element else ""
                
                # 중복 체크
                existing_item = collection.find_one({"_id": url}) if collection is not None else None
                
                # 이미 수집된 항목이고 content가 비어있지 않으면 스킵
                if existing_item and existing_item.get('content'):
                    logger.info(f"Skip duplicate: {title}")
                    continue

                logger.info(f"Processing item: {title}...")
                comments, json_ld_raw, detail_html = self.fetch_comments(url)

                item = NewsItem(
                    title=title,
                    url=url,
                    content=content,
                    source=self.source_name,
                    comments=comments,
                    json_ld_raw=json_ld_raw,
                    html=detail_html
                )
                # 즉시 저장 (DB 및 로컬 파일)
                self.save(item, db_connection, detail_html)
                items.append(item)
            except Exception as e:
                logger.error(f"Row parsing error: {e}")
                continue
        return items

    def fetch_comments(self, url: str) -> Tuple[List[CommentItem], Optional[str], Optional[str]]:
        """상세 페이지에서 댓글 수집 (JSON-LD 우선, HTML Fallback)"""
        html = self.fetch(url)
        if not html: return [], None, None
        
        soup = BeautifulSoup(html, 'html.parser')
        comments = []
        
        try:
            # 1. JSON-LD 시도
            json_ld_script = soup.find('script', type='application/ld+json')
            if json_ld_script:
                json_ld_raw = json_ld_script.string
                data = json.loads(json_ld_raw)
                comment_data_list = data.get('comment', [])
                if isinstance(comment_data_list, dict): comment_data_list = [comment_data_list]
                for comment_data in comment_data_list:
                    self._process_json_ld_comment(comment_data, comments)

            # 2. HTML Fallback
            if not comments:
                for row in soup.select('div.comment_row'):
                    author_el = row.select_one('.commentinfo a[href^="/@"]')
                    content_el = row.select_one('.comment_contents')
                    if content_el:
                        comments.append(CommentItem(
                            comment_id=row.get('id', ''),
                            author=author_el.get_text(strip=True) if author_el else "Unknown",
                            content=content_el.get_text(separator="\n", strip=True)
                        ))
        except Exception as e:
            logger.error(f"Comments error at {url}: {e}")
        return comments, json_ld_raw if 'json_ld_raw' in locals() else None, html

    def _process_json_ld_comment(self, comment_data: dict, comments: List[CommentItem]):
        if not isinstance(comment_data, dict): return
        text = comment_data.get('text')
        if text:
            url = comment_data.get('url', '')
            comments.append(CommentItem(
                comment_id=url.split('id=')[-1] if 'id=' in url else '',
                author=comment_data.get('author', {}).get('name') if isinstance(comment_data.get('author'), dict) else "Unknown",
                content=text
            ))
        children = comment_data.get('comment', [])
        if isinstance(children, dict): children = [children]
        for child in children:
            self._process_json_ld_comment(child, comments)

    def _get_backfill_url(self, base_url: str, date_str: str, page: int = None) -> str:
        base = base_url.rstrip('/')
        if date_str == 'comments':
            return f"{base}/comments?page={page}" if page else f"{base}/comments"
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            url = f"{base}/past?day={date_str}"
            return f"{url}&page={page}" if page else url
        if date_str.isdigit():
            p = int(date_str)
            return f"{base}/?page={p}" if p <= 5 else f"{base}/past?page={p}"
        return f"{base}/"
