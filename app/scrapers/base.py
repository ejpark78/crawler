"""
BaseScraper Module

This module defines the BaseScraper abstract base class, providing a standardized
interface for all news crawlers in the project.

Key Features:
1. Incremental Saving: Items are persisted immediately upon extraction to minimize data loss.
2. 3-way Persistence: Ensures data is stored in three formats:
   - pages: Refined news metadata and comments.
   - html: Original raw HTML for future reprocessing.
   - comments: Structured data (e.g., JSON-LD) specifically for comments.
3. Dual-Storage Support: Simultaneous persistence to MongoDB (Upsert) and local file system.
4. Source-based Isolation: Uses the source name (e.g., 'geeknews') as the MongoDB database name.
5. Bot Evasion: Implements random delays and uses StealthyFetcher to ensure stability.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
import time
import random
import logging
import json
import os
import re
import hashlib
from app.models import GeekNewsList, PytorchKRContents
from scrapling import StealthyFetcher


# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("BaseScraper")

class BaseScraper(ABC):
    """Abstract base class for all scrapers."""

    def __init__(self, source_name: str):
        self.source_name = source_name
        self.db_name = source_name.lower()
        self.collection_pages = "pages"
        self.collection_html = "html"
        self.collection_contents = "comments"
        self.crawler = StealthyFetcher()

    def fetch(self, url: str) -> str:
        """Fetches page HTML with a random delay to evade bot detection."""
        delay = random.uniform(5, 10)
        logger.info(f"Waiting {delay:.2f}s before fetching {url}...")
        time.sleep(delay)
        return self._do_fetch(url)

    @abstractmethod
    def _do_fetch(self, url: str) -> str:
        """Internal implementation for the actual network request."""
        pass

    @abstractmethod
    def parse(self, html: str, db_connection=None) -> List[GeekNewsList | PytorchKRContents]:
        """Parses HTML and converts it into a list of model objects."""
        pass

    def save(self, item: GeekNewsList, db_connection, html: Optional[str] = None):
        """Persists a single item to MongoDB and local storage."""
        # 1. Local file persistence (regardless of DB connection)
        if getattr(self, 'debug_path', None):
            self._save_to_file(item)

        # 2. MongoDB persistence
        if db_connection is None:
            logger.warning("Database connection is missing. Skipping database save.")
            return

        try:
            db = db_connection[self.db_name]

            # a. Page metadata (Upsert by URL)
            collection = db[self.collection_pages]
            doc = item.model_dump(mode='json')
            doc.pop("json_ld_raw", None)
            collection.update_one(
                {"_id": item.url},
                {"$set": doc},
                upsert=True
            )

            # b. Raw HTML storage
            if html:
                html_collection = db[self.collection_html]
                html_collection.update_one(
                    {"_id": item.url},
                    {"$set": {
                        "url": item.url,
                        "raw_html": html,
                        "created_at": doc.get("created_at")
                    }},
                    upsert=True
                )

            # c. Structured JSON-LD storage (comments collection)
            json_ld_raw = getattr(item, 'json_ld_raw', None)
            if json_ld_raw:
                collection_contents = db[self.collection_contents]
                try:
                    json_data = json.loads(json_ld_raw)
                    if isinstance(json_data, list) and len(json_data) > 0:
                        json_data = json_data[0]

                    collection_contents.update_one(
                        {"_id": item.url},
                        {"$set": {
                            "url": item.url,
                            "json_ld": json_data,
                            "created_at": doc.get("created_at")
                        }},
                        upsert=True
                    )
                except Exception as e:
                    # Fallback: save as raw string if JSON parsing fails
                    collection_contents.update_one(
                        {"_id": item.url},
                        {"$set": {
                            "url": item.url,
                            "json_ld_raw": json_ld_raw,
                            "created_at": doc.get("created_at")
                        }},
                        upsert=True
                    )

            logger.debug(f"Successfully saved item, HTML, and JSON-LD to {self.db_name} database.")
        except Exception as e:
            logger.error(f"Failed to save item {item.url}: {e}")

    def _save_to_file(self, item: GeekNewsList | PytorchKRContents):
        """Implements a 3-tier hierarchical local backup system."""
        try:
            source_lower = self.source_name.lower()
            base_dir = os.path.join(self.debug_path, source_lower)

            # Directory setup
            pages_dir = os.path.join(base_dir, "pages")
            htmls_dir = os.path.join(base_dir, "htmls")
            jsonld_dir = os.path.join(base_dir, "comments")

            for d in [pages_dir, htmls_dir, jsonld_dir]:
                os.makedirs(d, exist_ok=True)

            # Generate stable ID (Prefer URL param 'id', fallback to hash)
            if 'id=' in item.url:
                item_id = item.url.split('id=')[-1].split('&')[0]
            else:
                item_id = hashlib.md5(item.url.encode()).hexdigest()[:10]
            item_id = re.sub(r'[^\w\-]', '_', item_id)

            # 1. Metadata JSON
            page_path = os.path.join(pages_dir, f"{item_id}.json")
            with open(page_path, 'w', encoding='utf-8') as f:
                json.dump(item.model_dump(mode='json'), f, ensure_ascii=False, indent=2)

            # 2. Raw HTML and URL mapping
            if item.html:
                html_path = os.path.join(htmls_dir, f"{item_id}.html")
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(item.html)

                url_list_path = os.path.join(htmls_dir, "url.txt")
                with open(url_list_path, 'a', encoding='utf-8') as f:
                    f.write(f"{item_id}.html | {item.url}\n")

            # 3. Structured JSON-LD
            json_ld_raw = getattr(item, 'json_ld_raw', None)
            if json_ld_raw:
                jsonld_path = os.path.join(jsonld_dir, f"{item_id}.json")
                try:
                    json_data = json.loads(json_ld_raw)
                    if isinstance(json_data, list) and len(json_data) > 0:
                        json_data = json_data[0]
                    with open(jsonld_path, 'w', encoding='utf-8') as f:
                        json.dump(json_data, f, ensure_ascii=False, indent=2)
                except Exception:
                    with open(jsonld_path, 'w', encoding='utf-8') as f:
                        f.write(json_ld_raw)

            logger.debug(f"Local file persistence completed for item: {item_id}")
        except Exception as e:
            logger.error(f"Failed to save local file: {e}")

    def run(self, db_connection, backfill_date: Optional[str] = None, page: Optional[int] = None) -> Tuple[List[GeekNewsList | PytorchKRContents], str]:
        """Executes the full collection process (Backfill and Pagination support)."""
        logger.info(f"Starting collection from {self.source_name}...")
        
        # Use provided URL or fallback to scraper's base_url
        target_url = getattr(self, 'base_url', None)
        if not target_url:
            raise ValueError(f"No target URL provided for {self.source_name}")

        target_url = self._get_backfill_url(target_url, backfill_date, page=page)
        logger.info(f"Target URL: {target_url}, date: {backfill_date}, page: {page}")

        html = self.fetch(target_url)
        items = self.parse(html, db_connection=db_connection)
        logger.info(f"Successfully collected {len(items)} items from {self.source_name}.")
        return items, html
