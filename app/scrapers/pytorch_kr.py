import json
import logging
from typing import List, Optional, Tuple
from app.models import PytorchKRContents
from app.scrapers.base import BaseScraper
import re

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
        # For PyTorchKR, we use StealthyFetcher's internal fetch logic
        return self.crawler.fetch(url).text

    def _get_backfill_url(self, base_url: str, date_str: str, page: Optional[int] = None) -> str:
        # PyTorchKR's JSON API uses page parameters.
        # Date-based filtering is usually done on the client side or via search.
        # For the purpose of this implementation, we support page-based pagination.
        url = base_url if base_url else self.base_url
        page_val = page if page else 1
        return f"{url}?no_definitions=true&page={page_val}"

    def parse(self, html: str, db_connection=None) -> List[PytorchKRContents]:
        """Parses JSON or HTML from PyTorchKR."""
        items = []

        # Determine if content is JSON or HTML
        trimmed_html = html.strip()
        if trimmed_html.startswith('{'):
            try:
                data = json.loads(trimmed_html)
                topics = data.get('topic_list', {}).get('topics', [])
                for topic in topics:
                    # Use a dict to build the item to avoid passing None to created_at
                    item_data = {
                        "title": topic.get('title'),
                        "url": f"https://discuss.pytorch.kr/t/{topic.get('slug')}/{topic.get('id')}",
                        "source": self.source_name,
                        "content": f"Posts: {topic.get('posts_count')}, Replies: {topic.get('reply_count')}",
                    }
                    if topic.get('created_at'):
                        item_data["published_at"] = topic.get('created_at')
                    
                    item = PytorchKRContents(**item_data)
                    items.append(item)
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON response")
        else:
            # Basic HTML parsing for content pages handled in parse_content
            pass

        return items

    def parse_content(self, html: str, url: str) -> PytorchKRContents:
        """Parses a single topic page to extract full content and metadata."""
        # This is a simplified implementation for the TDD requirements
        # In production, this would use the scraper's adaptive tools

        # Extract canonical URL if available
        url_match = re.search(r'<link rel="canonical" href="(.*?)"', html)
        if url_match:
            url = url_match.group(1)

        title_match = re.search(r'<title>(.*?)</title>', html)
        title = title_match.group(1) if title_match else "Unknown Title"
        # Discourse titles usually follow "Topic Title - Category - Site Name"
        if " - " in title:
            title = title.split(" - ")[0]
        
        # Extract publication date
        published_at = None
        time_match = re.search(r'datetime=[\'"]([^\'"]+)[\'"]', html)
        if time_match:
            published_at = time_match.group(1)

        # Extract main text - simplified for this version
        # Real implementation would target the .post div
        content = "Full content extraction not implemented in this version"
        if '<div class="post" itemprop="text">' in html:
            # Rough extraction of the first post content
            start = html.find('<div class="post" itemprop="text">') + len('<div class="post" itemprop="text">')
            end = html.find('</div>', start)
            content = html[start:end].strip()
            # Basic HTML tag stripping to match plain text samples
            content = re.sub(r'<[^>]+>', '', content)

        return PytorchKRContents(
            title=title,
            url=url,
            source=self.source_name,
            content=content,
            published_at=published_at
        )
