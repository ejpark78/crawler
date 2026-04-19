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
        from bs4 import BeautifulSoup
        import re

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
