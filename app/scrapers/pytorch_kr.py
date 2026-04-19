"""
PyTorch KR 스크레이퍼 모듈

이 모듈은 PyTorch 한국 사용자 모임(https://discuss.pytorch.kr)의 게시글을 수집하기 위한 
전문 크롤러를 구현합니다. Discourse 기반의 포럼 구조를 처리합니다.

주요 기능:
1. JSON API 연동: 최신 게시글 목록을 추출하기 위해 사이트의 전용 JSON 엔드포인트를 활용합니다.
2. BeautifulSoup 기반 상세 파싱: 게시글 본문의 복잡한 HTML 구조를 분석하여 정규화된 텍스트를 추출합니다.
3. 특수 요소 처리: 
   - 이미지 라이트박스(Lightbox) 구조에서 메타데이터를 추출하고 텍스트로 변환합니다.
   - 본문 내 이미지를 알트(Alt) 텍스트로 치환하거나 불필요한 이모지를 제거합니다.
   - 제목을 본문에 포함시켜 문서의 맥락을 보존합니다.
4. 테스트 기반 검증: 수집된 실제 HTML 샘플과 골든 레코드(JSON)를 비교하여 파싱 정확도를 보장합니다.
"""
import json
import logging
from typing import List, Optional
from app.models import PytorchKRContents
from app.scrapers.base import BaseScraper
import re
from curl_cffi import requests
from bs4 import BeautifulSoup


logger = logging.getLogger("PyTorchKRScraper")

class PyTorchKRScraper(BaseScraper):
    """Scraper for PyTorch Korea (discuss.pytorch.kr)"""

    def __init__(self):
        super().__init__("PyTorchKR")
        self.db_name = "pytorch_kr"
        self.collection_list = "list"
        self.collection_contents = "contents"
        self.base_url = "https://discuss.pytorch.kr/latest.json"

    def _do_fetch(self, url: str) -> str:
        """Fetches URL using curl-cffi with Chrome impersonation."""
        try:
            response = requests.get(url, impersonate="chrome", timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Network error while fetching {url}: {e}")
            return ""

    def _get_backfill_url(self, base_url: str, date_str: str = None, page: int = None) -> str:
        # PyTorchKR's JSON API uses page parameters.
        # Date-based filtering is usually done on the client side or via search.
        # For the purpose of this implementation, we support page-based pagination.
        url = base_url if base_url else self.base_url
        page_val = page if page else 1
        return f"{url}?no_definitions=true&page={page_val}"

    def parse(self, html: str, db_connection=None) -> List[PytorchKRContents]:
        """Parses JSON list from PyTorchKR and fetches/parses each topic detail."""
        items = []

        # Determine if content is JSON or HTML
        trimmed_html = html.strip()
        if not trimmed_html.startswith('{'):
            logger.error(f"PyTorchKR parse expected JSON list but received: {trimmed_html[:100]}...")
            return []

        try:
            data = json.loads(trimmed_html)
            # Discourse API structure: topics are usually under topic_list.topics
            topics = data.get('topic_list', {}).get('topics', [])
            logger.info(f"Found {len(topics)} topics in the list.")

            if db_connection is not None:
                collection_list = db_connection[self.db_name][self.collection_list]
                collection_contents = db_connection[self.db_name][self.collection_contents]
            else:
                collection_list = None
                collection_contents = None

            for topic in topics:
                try:
                    if collection_list is not None:
                        collection_list.update_one(
                            {"_id": f"{topic.get('slug')}_{topic.get('id')}"},
                            {"$set": topic},
                            upsert=True
                        )

                    title = topic.get('title')
                    # Construct topic URL
                    topic_id = topic.get('id')
                    slug = topic.get('slug')
                    if not (topic_id and slug): continue
                    
                    url = f"https://discuss.pytorch.kr/t/{slug}/{topic_id}"
                    logger.info(f"Processing topic: {title} ({url})...")
                    
                    # 1. Fetch detail page
                    detail_html = self.fetch(url)
                    if not detail_html:
                        logger.warning(f"Failed to fetch detail for: {url}")
                        continue
                        
                    # 2. Parse detail page
                    item = self.parse_content(detail_html, url)
                    
                    # 3. Persistence (DB & Local)
                    if collection_contents is not None:
                        doc = item.model_dump(mode='json')
                        collection_contents.update_one(
                            {"_id": f"{topic.get('slug')}_{topic.get('id')}"},
                            {"$set": {**topic, 'contents': doc}},
                            upsert=True
                        )

                    if getattr(self, 'debug_path', None):
                        self._save_to_file(item)
                    items.append(item)
                except Exception as e:
                    logger.error(f"Error processing topic {topic.get('id')}: {e}")
                    continue
        except json.JSONDecodeError:
            logger.error("Failed to decode JSON from PyTorchKR list response")
        except Exception as e:
            logger.error(f"Unexpected error in PyTorchKR.parse: {e}")

        return items

    def parse_content(self, html: str, url: str) -> PytorchKRContents:
        """Parses a single topic page to extract full content and metadata."""
        soup = BeautifulSoup(html, 'html.parser')

        # Extract canonical URL
        canonical = soup.find('link', rel='canonical')
        if canonical and canonical.get('href'):
            url = canonical['href']

        # Extract title
        title_tag = soup.find('title')
        title = title_tag.get_text() if title_tag else "Unknown Title"
        if " - " in title:
            title = title.split(" - ")[0]
        
        # Extract publication date
        published_at = None
        time_tag = soup.find('time', datetime=True)
        if time_tag:
            published_at = time_tag['datetime']

        # Extract main text
        post_div = soup.find('div', class_='post', itemprop='text')
        if post_div:
            # Handle lightbox wrappers specifically to match sample output
            for lb in post_div.find_all('div', class_='lightbox-wrapper'):
                img = lb.find('img')
                alt = img.get('alt', '') if img else ''
                info = lb.find('span', class_='informations')
                info_text = info.get_text() if info else ""
                
                parts = []
                # Only keep alt text if it's different from the title
                if alt and alt != title:
                    parts.append(alt)
                if info_text:
                    parts.append(info_text)
                
                lb.replace_with('\n'.join(parts))

            # Handle other images (like emojis)
            for img in post_div.find_all('img'):
                alt = img.get('alt', '')
                if alt.startswith(':'): # Emojis
                    img.decompose()
                elif alt and alt != title:
                    img.replace_with(alt)
                else:
                    img.decompose()
            
            # Get text with normalized whitespace
            raw_text = post_div.get_text(separator='\n')
            lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
            content_text = '\n'.join(lines)
            
            # The expected output starts with the title
            content = f"{title}\n{content_text}"
        else:
            content = "Full content extraction not implemented in this version"

        return PytorchKRContents(
            title=title,
            url=url,
            source=self.source_name,
            content=content,
            published_at=published_at,
            html=html
        )
