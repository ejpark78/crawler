"""
GeekNewsScraper Module

Implements a specialized crawler for GeekNews (https://news.hada.io).

Key Features:
1. Hybrid Collection: Uses JSON-LD as the primary source for comment data,
   falling back to HTML scraping if necessary.
2. Incremental Persistence: Immediately saves items to 'geeknews' DB collections
   (pages, html, comments) upon extraction.
3. Content Extraction: Captures the summary description (.topicdesc) into the 'content' field.
4. Duplicate Prevention: Skips previously collected items unless the 'content' field
   needs to be populated/updated.
5. Stealth Collection: Employs curl-cffi's Impersonate feature (Chrome) to
   bypass bot detection.
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
        """Performs network requests using curl-cffi with Chrome impersonation."""
        logger.info(f"Fetching {url} using curl-cffi (Impersonating Chrome)...")
        try:
            response = requests.get(url, impersonate="chrome", timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Network error while fetching {url}: {e}")
            return ""

    def scrape(self, date_str: str = "1", db_connection=None) -> List[NewsItem]:
        """Executes the GeekNews scraping process."""
        url = self._get_backfill_url(self.base_url, date_str)
        html = self.fetch(url)
        if not html:
            return []
        return self.parse(html, db_connection=db_connection)

    def parse(self, html: str, db_connection=None) -> List[NewsItem]:
        """Parses the GeekNews list page."""
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
                    url = f"https://news.hada.io/{url.lstrip('/')}"

                desc_element = row.select_one('.topicdesc')
                content = desc_element.get_text(strip=True) if desc_element else ""

                # Duplicate Check
                existing_item = collection.find_one({"_id": url}) if collection is not None else None

                # Skip if already collected and content is not empty
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
                # Immediate persistence (DB & Local)
                self.save(item, db_connection, detail_html)
                items.append(item)
            except Exception as e:
                logger.error(f"Row parsing error: {e}")
                continue
        return items

    def fetch_comments(self, url: str) -> Tuple[List[CommentItem], Optional[str], Optional[str]]:
        """Collects comments from the detail page (JSON-LD primary, HTML fallback)."""
        html = self.fetch(url)
        if not html: return [], None, None

        soup = BeautifulSoup(html, 'html.parser')
        comments = []
        json_ld_raw = None

        try:
            # 1. JSON-LD Strategy
            json_ld_script = soup.find('script', type='application/ld+json')
            if json_ld_script:
                json_ld_raw = json_ld_script.string
                data = json.loads(json_ld_raw)
                comment_data_list = data.get('comment', [])
                if isinstance(comment_data_list, dict): comment_data_list = [comment_data_list]
                for comment_data in comment_data_list:
                    self._process_json_ld_comment(comment_data, comments)

            # 2. HTML Fallback Strategy
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
        return comments, json_ld_raw, html

    def _process_json_ld_comment(self, comment_data: dict, comments: List[CommentItem]):
        """Recursively processes JSON-LD comment structures."""
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
        """Constructs the target URL for backfilling based on date/page patterns."""
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
