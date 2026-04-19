"""
Crawler CLI Entrypoint (Main)

This module serves as the integration controller for the crawler project.
It drives scrapers via CLI and persists data using a real-time incremental collection method.

Key Processes:
1. CLI Argument Parsing: Configures execution environment and log levels.
2. Incremental Save: Persists items immediately upon extraction to prevent data loss.
3. 3-way Storage: Distributes data across three collections (pages, html, comments) for maximum utility.
4. Source-based Isolation: Automatically creates and connects to independent MongoDB databases based on the --source argument.
5. Hierarchical Archiving: Backs up data to local directories ({source}_pages, {source}_htmls, {source}) when --out_path is provided.

Example:
    make test SOURCE=GeekNews DATE=2026-03-25 PAGE=1 LOG_LEVEL=DEBUG
"""
import argparse
import logging
import os
import sys
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from app.scrapers.registry import SCRAPER_REGISTRY

# Default logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("Main")

def main():
    """
    Analyzes CLI arguments and executes the appropriate scraper.

    Args:
        --source (str): Source name registered in SCRAPER_REGISTRY (Required).
        --date (str): Target date for backfilling (YYYY-MM-DD).
        --page (int): Target page number.
        --out_path (str): Local root directory for structured output.
    """
    parser = argparse.ArgumentParser(description="CLI Wrapper for Advanced Scrapers")
    parser.add_argument("--source", required=True, help="Source name from registry (e.g., GeekNews)")
    parser.add_argument("--date", help="Target date for backfilling (YYYY-MM-DD)")
    parser.add_argument("--page", type=int, help="Target page number")
    parser.add_argument("--out_path", help="Local directory path to save structured output")

    args = parser.parse_args()

    # Handle LOG_LEVEL from environment variable
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.getLogger().setLevel(log_level)

    # Initialize scraper and local storage
    scraper_cls = SCRAPER_REGISTRY.get(args.source)
    if not scraper_cls:
        logger.error(f"Error: Scraper for source '{args.source}' is not registered.")
        sys.exit(1)

    scraper = scraper_cls()

    if args.out_path:
        target_dir = args.out_path
        os.makedirs(target_dir, exist_ok=True)

        # Log all activities to crawler.log in the target directory
        log_file = os.path.join(target_dir, "crawler.log")
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))
        logging.getLogger().addHandler(file_handler)

        logger.info(f"Structured storage initialized at: {target_dir}")
        logger.info(f"Detailed logs being written to: {log_file}")
        scraper.debug_path = target_dir

    logger.info(f"System initialized. Log Level: {log_level}, Source: {args.source}")

    # MongoDB connection attempt (2s timeout)
    client = None
    db_conn = None
    try:
        client = MongoClient("mongodb://mongodb:27017/", serverSelectionTimeoutMS=2000)
        client.admin.command('ping')
        db_conn = client
        logger.info("Successfully established connection to MongoDB.")
    except (ServerSelectionTimeoutError, Exception) as e:
        logger.warning(f"MongoDB connection failed: {e}. Data will only be saved locally if --out_path is set.")
        db_conn = None

    try:
        # Execution
        items, _ = scraper.run(
            db_connection=db_conn,
            backfill_date=args.date,
            page=args.page
        )
        # Output result for Airflow XCom capture
        print(f"RESULT_COUNT: {len(items)}")
    finally:
        if client:
            client.close()
            logger.debug("MongoDB connection closed.")

if __name__ == "__main__":
    main()
