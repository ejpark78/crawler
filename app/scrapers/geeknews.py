"""
GeekNewsScraper 모듈 (JSON-LD 우선 하이브리드)

이 모듈은 GeekNews(https://news.hada.io) 사이트의 데이터를 수집합니다.
사용자의 요청에 따라 JSON-LD 수집을 최우선으로 하되, 큐레이션 기사처럼 
구조화 데이터에 댓글 목록이 누락된 경우에만 제한적으로 HTML 파싱을 수행합니다.

특징:
1. JSON-LD 우선: 본문과 댓글을 구조화 데이터에서 먼저 찾습니다.
2. 엔티티 디코딩: JSON-LD description 내의 HTML 엔티티를 자동 복원합니다.
3. 지능형 Fallback: commentCount는 있으나 목록이 없는 경우 HTML에서 보충합니다.
"""
import json
import logging
import re
import html as html_parser
from typing import List, Optional, Tuple
from bs4 import BeautifulSoup
from curl_cffi import requests

from app.scrapers.base import BaseScraper
from app.models import NewsItem, CommentItem

# 로깅 설정
logger = logging.getLogger("GeekNewsScraper")

class GeekNewsScraper(BaseScraper):
    """
    GeekNews 사이트 전용 스크래퍼.
    JSON-LD 데이터의 정합성과 HTML 파싱의 완전성을 결합한 하이브리드 로직을 구현합니다.
    """
    
    def __init__(self):
        super().__init__(source_name="GeekNews")
        self.base_url = "https://news.hada.io"

    def _do_fetch(self, url: str) -> str:
        try:
            response = requests.get(url, impersonate="chrome", timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"GeekNews network error ({url}): {e}")
            return ""

    def parse(self, html: str, db_connection=None) -> List[NewsItem]:
        soup = BeautifulSoup(html, 'html.parser')
        items = []
        
        collection = None
        if db_connection is not None:
            collection = db_connection["crawler_db"][self.collection_name]

        rows = soup.select('div.topic_row')
        for row in rows:
            try:
                title_el = row.select_one('.topictitle a')
                if not title_el: continue
                
                title = title_el.get_text(strip=True)
                url = title_el.get('href', '')
                if not (title and url): continue

                if url and not url.startswith('http'):
                    url = f"https://news.hada.io/{url.lstrip('/')}"
                
                topic_el = row.select_one('.topicinfo a[href*="topic?id="]')
                topic_url = None
                if topic_el:
                    href = topic_el.get('href', '')
                    topic_url = href if href.startswith('http') else f"https://news.hada.io/{href.lstrip('/')}"
                
                if collection is not None and collection.find_one({"_id": url}):
                    logger.debug(f"Skipping duplicate: {title}")
                    continue

                content = None
                comments = []

                if topic_url:
                    logger.info(f"Processing item: {title}")
                    content, comments = self.fetch_comments(topic_url)
                
                items.append(NewsItem(
                    title=title,
                    url=url,
                    source=self.source_name,
                    content=content,
                    comments=comments
                ))
            except Exception as e:
                logger.error(f"Row parsing error: {e}")
                
        return items

    def fetch_comments(self, url: str) -> Tuple[Optional[str], List[CommentItem]]:
        """
        상세 페이지에서 JSON-LD를 우선 수집하고, 데이터 누락 시 HTML Fallback을 수행합니다.
        """
        try:
            html_text = self.fetch(url)
            if not html_text: return None, []
            
            soup = BeautifulSoup(html_text, "html.parser")
            json_ld_script = soup.find('script', type='application/ld+json')
            
            content = None
            comments = []
            comment_count_in_ld = 0

            # 1. JSON-LD 파싱 시도
            if json_ld_script:
                try:
                    data = json.loads(json_ld_script.string)
                    # 본문 추출 및 디코딩
                    raw_content = data.get('text') or data.get('articleBody') or data.get('description')
                    if raw_content:
                        content = html_parser.unescape(raw_content)
                    
                    comment_count_in_ld = data.get('commentCount', 0)
                    comment_data_list = data.get('comment', [])
                    
                    if isinstance(comment_data_list, dict):
                        comment_data_list = [comment_data_list]
                        
                    for comment_data in comment_data_list:
                        self._process_json_ld_comment(comment_data, comments)
                except Exception as e:
                    logger.error(f"JSON-LD parse error at {url}: {e}")

            # 2. HTML Fallback (JSON-LD에 댓글 리스트가 없거나 부족한 경우)
            # 큐레이션 기사(GN+)의 경우 JSON-LD에 댓글 본문이 빠져있음
            if not comments or (comment_count_in_ld > len(comments)):
                logger.debug(f"JSON-LD comments missing or incomplete ({len(comments)}/{comment_count_in_ld}). Falling back to HTML.")
                html_comments = self._parse_comments_from_html(soup)
                
                # 중복을 피하면서 HTML에서 찾은 댓글 추가
                existing_ids = {c.comment_id for c in comments}
                for hc in html_comments:
                    if hc.comment_id not in existing_ids:
                        comments.append(hc)

            # 본문이 여전히 없다면 HTML에서 추출
            if not content:
                content_el = soup.select_one('.topic_contents')
                if content_el:
                    content = content_el.get_text("\n", strip=True)

            if comments:
                logger.debug(f"Final collection: {len(comments)} comments for {url}")
            
            return content, comments
        except Exception as e:
            logger.error(f"Extraction failed ({url}): {e}")
            return None, []

    def _process_json_ld_comment(self, comment_data: dict, comments: List[CommentItem]):
        """JSON-LD 내의 댓글 데이터를 재귀적으로 파싱합니다."""
        if not isinstance(comment_data, dict): return
        
        text = comment_data.get('text')
        if text:
            url = comment_data.get('url', '')
            author_data = comment_data.get('author', {})
            author = author_data.get('name') if isinstance(author_data, dict) else "Unknown"
            
            comments.append(CommentItem(
                comment_id=url.split('id=')[-1] if 'id=' in url else f"ld_{hash(text)}",
                author=author or "Unknown",
                content=text
            ))
            
        children = comment_data.get('comment', [])
        if isinstance(children, dict):
            children = [children]
        for child in children:
            self._process_json_ld_comment(child, comments)

    def _parse_comments_from_html(self, soup: BeautifulSoup) -> List[CommentItem]:
        """HTML DOM에서 댓글을 직접 추출합니다 (Fallback 전용)."""
        comments = []
        comment_threads = soup.select('.comment_thread')
        for thread in comment_threads:
            try:
                # 작성자 추출
                author_el = thread.select_one('.commentuser a')
                author = author_el.get_text(strip=True) if author_el else "Unknown"
                
                # 댓글 본문 추출
                content_el = thread.select_one('.comment_text')
                if not content_el: continue
                text = content_el.get_text(strip=True)
                
                # ID 추출 (링크 id=... 형태)
                id_el = thread.select_one('.commentinfo a[href*="comment?id="]')
                comment_id = None
                if id_el:
                    href = id_el.get('href', '')
                    comment_id = href.split('id=')[-1]
                
                if not comment_id:
                    comment_id = f"{author}_{hash(text)}"

                comments.append(CommentItem(
                    comment_id=comment_id,
                    author=author,
                    content=text
                ))
            except Exception as e:
                logger.debug(f"HTML comment parsing skip: {e}")
        return comments

    def _get_backfill_url(self, base_url: str, date_str: str, page: Optional[int] = None) -> str:
        base = base_url.rstrip('/')
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            url = f"{base}/past?day={date_str}"
            return f"{url}&page={page}" if page else url
        if date_str.isdigit():
            p = int(date_str)
            return f"{base}/?page={p}" if p <= 5 else f"{base}/past?page={p}"
        return f"{base}/"
