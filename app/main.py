import argparse
from pymongo import MongoClient
from app.scrapers.registry import SCRAPER_REGISTRY

def main():
    parser = argparse.ArgumentParser(description="CLI Wrapper for Scrapers")
    parser.add_argument("--source", required=True, help="Source name from registry")
    parser.add_argument("--url", required=True, help="Base URL")
    parser.add_argument("--date", help="Backfill date (YYYY-MM-DD)")
    parser.add_argument("--page", type=int, help="Page number")

    args = parser.parse_args()

    scraper_cls = SCRAPER_REGISTRY.get(args.source)
    if not scraper_cls:
        print(f"Error: Scraper for {args.source} not found")
        exit(1)

    scraper = scraper_cls()

    # MongoDB 연결 설정
    client = MongoClient("mongodb://mongodb:27017/")
    try:
        scraper.run(
            url=args.url,
            db_connection=client,
            backfill_date=args.date,
            page=args.page
        )
    finally:
        client.close()

if __name__ == "__main__":
    main()
