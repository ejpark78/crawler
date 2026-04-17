from typing import List, Optional
import json
import logging
from datetime import datetime
from app.scrapers.base import BaseScraper
from app.models import NewsItem, CommentItem
from scrapling import StealthyFetcher
from bs4 import BeautifulSoup
from curl_cffi import requests


logger = logging.getLogger("GeekNewsScraper")

class GeekNewsScraper(BaseScraper):
    """GeekNews 크롤러 구현체"""

    def __init__(self):
        super().__init__(source_name="GeekNews")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    def save(self, items: List[NewsItem], db_connection, html: Optional[str] = None):
        """GeekNews 전용 저장 로직: 메인 데이터와 JSON-LD 원본 데이터를 분리하여 저장"""
        super().save(items, db_connection, html)

        db = db_connection["crawler_db"]
        json_ld_collection = db["geeknews"]

        count = 0
        for item in items:
            if item.json_ld_raw:
                try:
                    json_data = json.loads(item.json_ld_raw)
                    doc = {"_id": item.url, "url": item.url, "updated_at": datetime.utcnow()}
                    if isinstance(json_data, dict):
                        doc.update(json_data)
                    else:
                        doc["json_ld_content"] = json_data

                    json_ld_collection.update_one(
                        {"_id": item.url}, {"$set": doc}, upsert=True
                    )
                    count += 1
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON-LD for {item.url}: {e}")

        if count > 0:
            logger.info(f"Successfully saved {count} JSON-LD documents to geeknews collection.")

    def _do_fetch(self, url: str) -> str:
        """curl-cffi를 사용하여 curl과 동일한 핑거프린트로 HTML 가져오기"""
        logger.info(f"Fetching {url} using curl-cffi (Impersonating Chrome)...")

        try:
            response = requests.get(
                url, headers=self.headers, impersonate="chrome110", timeout=30
            )
            response.raise_for_status()
            html = response.text

            if not html or len(html) < 1000 or "<html" not in html.lower():
                raise ValueError("curl-cffi returned insufficient HTML content")

            return html
        except Exception as e:
            logger.error(f"curl-cffi fetch failed for {url}: {e}")
            raise

    def parse(self, html: str) -> List[NewsItem]:
        """GeekNews HTML 파싱 로직"""
        soup = BeautifulSoup(html, 'html.parser')

        rows = soup.select('div.topic_row')

        items = []
        for row in rows:
            title_element = row.select_one('.topictitle a')
            desc_element = row.select_one('.topicdesc a')
            if not title_element:
                continue

            title = title_element.get_text(strip=True)
            url = title_element.get('href')
            content = desc_element.get_text(strip=True) if desc_element else ""

            if title and url:
                if url.startswith('/'):
                    url = f"https://news.hada.io{url}"
                if 'topic?id=' in url:
                    continue

                # 댓글 및 JSON-LD 수집을 위해 상세 페이지 URL 추출
                comment_link_el = row.select_one('.topicinfo a[href*="topic?id="]')
                topic_url = None
                if comment_link_el:
                    href = comment_link_el.get('href')
                    if href.startswith('/'):
                        topic_url = f"https://news.hada.io{href}"
                    else:
                        topic_url = f"https://news.hada.io/{href}"

                items.append(NewsItem(
                    title=title,
                    url=url,
                    source=self.source_name,
                    content=content,
                    comments=None # JSON 저장 시 제외하기 위해 None 설정
                ))

                # 상세 페이지에서 댓글 및 JSON-LD 원본 데이터 수집
                if topic_url:
                    try:
                        comments, json_ld_raw = self.fetch_comments(topic_url)
                        items[-1].comments = comments
                        items[-1].json_ld_raw = json_ld_raw
                    except Exception as e:
                        print(f"Error fetching comments for {topic_url}: {e}")

        seen_urls = set()
        unique_items = []
        for item in items:
            if item.url not in seen_urls:
                unique_items.append(item)
                seen_urls.add(item.url)

        return unique_items

    def fetch_comments(self, url: str) -> tuple[List[CommentItem], Optional[str]]:
        """상세 페이지에서 JSON-LD와 HTML을 결합하여 댓글 리스트 및 원본 JSON-LD를 수집"""
        html = self.fetch(url)
        soup = BeautifulSoup(html, 'html.parser')

        # JSON-LD 스크립트 태그 찾기
        script_tag = soup.find('script', type='application/ld+json')
        if not script_tag:
            print(f"No JSON-LD found for {url}")
            return [], None

        json_ld_raw = script_tag.string

        try:
            data = json.loads(json_ld_raw)
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Failed to parse JSON-LD for {url}: {e}")
            return [], json_ld_raw

        comments = []

        def extract_comments_recursive(comment_data):
            """중첩된 댓글 구조를 평탄화하여 추출"""
            if not comment_data or not isinstance(comment_data, dict):
                return

            # 고유 식별자 및 기본 정보 추출
            comment_url = comment_data.get('url', '')
            comment_id = comment_url.split('id=')[-1] if 'id=' in comment_url else ''
            author = comment_data.get('author', {}).get('name') if isinstance(comment_data.get('author'), dict) else None
            text = comment_data.get('text')

            if author and text:
                # HTML에서 해당 댓글의 innerHTML 추출 시도
                raw_html = None
                if comment_id:
                    # id=cidXXXX 형태의 element 찾기
                    comment_el = soup.find(id=f"cid{comment_id}")
                    if comment_el:
                        # .comment_contents 스팬 내부의 HTML 추출
                        contents_el = comment_el.select_one('.comment_contents')
                        raw_html = str(contents_el) if contents_el else str(comment_el)

                comments.append(CommentItem(
                    comment_id=comment_id,
                    author=author,
                    content=text,
                    raw_html=raw_html
                ))

            # 자식 댓글 재귀 처리
            children = comment_data.get('comment')
            if isinstance(children, list):
                for child in children:
                    extract_comments_recursive(child)
            elif isinstance(children, dict):
                extract_comments_recursive(children)

        # 루트 댓글 리스트 처리
        root_comments = data.get('comment')
        if isinstance(root_comments, list):
            for root in root_comments:
                extract_comments_recursive(root)
        elif isinstance(root_comments, dict):
            extract_comments_recursive(root_comments)

        return comments, json_ld_raw

    def _get_backfill_url(self, base_url: str, date_str: str, page: int = None) -> str:
        """
        GeekNews의 과거 데이터 URL 구조를 처리합니다.
        1. date_str이 숫자(페이지 번호)인 경우:
           - 1~5페이지: /?page=N
           - 6페이지 이상: /past?page=N
        2. date_str이 날짜 형식(YYYY-MM-DD)인 경우:
           - /past?day=YYYY-MM-DD (&page=N 추가 가능)
        3. date_str이 'comments'인 경우:
           - /comments?page=N (page 인자 필수)
        """
        base = base_url.rstrip('/')

        if date_str == 'comments':
            if page is None:
                raise ValueError("Page number is required when date_str is 'comments'")
            return f"{base}/comments?page={page}"

        import re
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            url = f"{base}/past?day={date_str}"
            return f"{url}&page={page}" if page else url

        if date_str.isdigit():
            page_num = int(date_str)
            prefix = "" if page_num <= 5 else "/past"
            return f"{base}{prefix}?page={page_num}"

        return base_url
